use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicI64, AtomicU16, Ordering};
use std::sync::{Arc, Mutex};
use tauri::{Emitter as _, State};

/// Default port for the Piper TTS server. If occupied by a non-Piper
/// process, we hop to the next free port in [8095..8105) — never killing
/// strangers.
const TTS_PORT_DEFAULT: u16 = 8095;
const TTS_PORT_RANGE_END: u16 = 8105;

/// The active TTS port, written once by `start_piper_on_launch` and read
/// by every other tts.rs function via `tts_port()`. Static rather than
/// State-bound so non-command helpers don't have to thread it through.
static TTS_PORT_ACTIVE: AtomicU16 = AtomicU16::new(TTS_PORT_DEFAULT);

fn tts_port() -> u16 {
    TTS_PORT_ACTIVE.load(Ordering::Relaxed)
}

/// Probe a port via /health and return whether the responder is OUR Piper
/// (i.e. it returned JSON with `"engine":"piper"`).
fn is_our_piper(port: u16) -> bool {
    let url = format!("http://127.0.0.1:{}/health", port);
    let out = Command::new("curl")
        .args(["-s", "--connect-timeout", "1", "--max-time", "2", &url])
        .output();
    match out {
        Ok(o) if o.status.success() => {
            let body = String::from_utf8_lossy(&o.stdout);
            body.contains("\"engine\"") && body.contains("\"piper\"")
        }
        _ => false,
    }
}

/// Returns true if no one is listening on the loopback port.
///
/// We probe by CONNECTING rather than binding: on macOS, binding a specific
/// address (127.0.0.1) succeeds even when another process holds the wildcard
/// (0.0.0.0) on the same port — so a bind-test would falsely report "free" for
/// e.g. `python -m http.server`. A connect attempt to 127.0.0.1 is delivered to
/// a wildcard listener too, so it reliably detects occupancy. ECONNREFUSED
/// (connect fails fast) means free.
fn port_is_free(port: u16) -> bool {
    use std::net::TcpStream;
    use std::time::Duration;
    let addr = std::net::SocketAddr::from(([127, 0, 0, 1], port));
    // Ok(_) = something accepted the connection → occupied; Err = refused/timeout → free.
    TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_err()
}

/// Pick the port to use for Piper:
/// 1. If 8095 already has OUR Piper running, reuse it.
/// 2. Else find the first free port in [8095..8105).
/// 3. Falls back to 8095 if everything is occupied (caller will surface the bind error).
fn pick_tts_port() -> u16 {
    if is_our_piper(TTS_PORT_DEFAULT) {
        return TTS_PORT_DEFAULT;
    }
    for port in TTS_PORT_DEFAULT..TTS_PORT_RANGE_END {
        if port_is_free(port) {
            return port;
        }
    }
    TTS_PORT_DEFAULT
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerseInput {
    pub id: i64,
    pub text: String,
}

pub struct TtsState {
    pub process: Arc<Mutex<Option<Child>>>,
    pub paused: Arc<AtomicBool>,
    pub cancelled: Arc<AtomicBool>,
    pub playing: Arc<AtomicBool>,
    /// Set to a verse index to skip to; -1 means no skip pending
    pub skip_to: Arc<AtomicI64>,
    pub prefetch: Mutex<Option<Child>>,
    /// Piper server child. Arc-wrapped so the spawn-on-launch thread can write to it.
    pub piper_server: Arc<Mutex<Option<Child>>>,
}

impl TtsState {
    pub fn new() -> Self {
        TtsState {
            process: Arc::new(Mutex::new(None)),
            paused: Arc::new(AtomicBool::new(false)),
            cancelled: Arc::new(AtomicBool::new(false)),
            playing: Arc::new(AtomicBool::new(false)),
            skip_to: Arc::new(AtomicI64::new(-1)),
            prefetch: Mutex::new(None),
            piper_server: Arc::new(Mutex::new(None)),
        }
    }
}

impl Drop for TtsState {
    fn drop(&mut self) {
        // Kill playback process (afplay).
        // NOTE: previously sent SIGKILL to -pid (process group). That was a
        // serious bug — afplay is spawned without setsid/process_group, so it
        // shares the Tauri parent's process group. Negative-pid kill would have
        // signalled the entire app group, including the parent. We just kill
        // the child here; the orphaned-afplay pkill below catches stragglers.
        if let Ok(mut guard) = self.process.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill();
            }
            *guard = None;
        }
        if let Ok(mut guard) = self.prefetch.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill();
            }
            *guard = None;
        }
        if let Ok(mut guard) = self.piper_server.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill();
            }
            *guard = None;
        }
        // Kill any orphaned afplay we may have left behind.
        // NOTE: do NOT kill arbitrary listeners on tts_port() — that may belong
        // to a totally unrelated process. Our spawned child is already killed above.
        let _ = Command::new("sh")
            .arg("-c")
            .arg("pkill -9 -f 'afplay.*/tmp/scriptures_tts_chunks' 2>/dev/null")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
        let _ = std::fs::remove_dir_all(PREFETCH_DIR);
    }
}

const PREFETCH_DIR: &str = "/tmp/scriptures_tts_chunks";

fn home_dir() -> String {
    std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string())
}

fn venv_python_path() -> String {
    format!("{}/.scriptures/piper-env/bin/python", home_dir())
}

fn venv_dir_path() -> String {
    format!("{}/.scriptures/piper-env", home_dir())
}

/// Bootstrap the Piper Python venv if it doesn't exist.
/// Emits tts-setup-progress events so the frontend can show status.
fn ensure_piper_venv(emitter: &tauri::AppHandle) -> Result<(), String> {
    let venv_dir = venv_dir_path();
    let venv_python = venv_python_path();

    // Already bootstrapped — check that piper is importable
    if std::path::Path::new(&venv_python).exists() {
        let check = Command::new(&venv_python)
            .args(["-c", "import piper"])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
        if check.map(|s| s.success()).unwrap_or(false) {
            return Ok(());
        }
        // venv exists but piper not installed — remove and recreate
        eprintln!("[tts] Existing venv missing piper, recreating...");
        let _ = std::fs::remove_dir_all(&venv_dir);
    }

    eprintln!("[tts] First launch: setting up voice engine...");
    let _ = emitter.emit("tts-setup-progress", json!({
        "stage": "creating-venv",
        "message": "Setting up voice engine...",
        "percent": 5
    }));

    let _ = std::fs::create_dir_all(format!("{}/.scriptures", home_dir()));

    let venv_output = Command::new("python3")
        .args(["-m", "venv", &venv_dir])
        .output()
        .map_err(|e| format!("python3 not found: {}. Install Xcode Command Line Tools.", e))?;

    if !venv_output.status.success() {
        let msg = format!("Failed to create venv: {}", String::from_utf8_lossy(&venv_output.stderr));
        let _ = emitter.emit("tts-setup-progress", json!({"stage": "error", "message": &msg, "percent": 0}));
        return Err(msg);
    }

    let _ = emitter.emit("tts-setup-progress", json!({
        "stage": "installing",
        "message": "Downloading voice engine — this may take a minute...",
        "percent": 15
    }));

    // Run pip with line-buffered output so we can report progress
    let pip = format!("{}/bin/pip", venv_dir);
    let pip_child = Command::new(&pip)
        .args(["install", "--progress-bar", "off", "piper-tts", "onnxruntime"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("pip install failed to start: {}", e))?;

    // Poll pip output for progress estimation while it runs
    // pip install typically: collecting → downloading → installing
    let emitter_clone = emitter.clone();
    let progress_thread = std::thread::spawn(move || {
        // Estimate progress based on elapsed time (pip doesn't give %)
        // Typical install: ~30-50 seconds
        let start = std::time::Instant::now();
        let estimated_duration = std::time::Duration::from_secs(45);
        loop {
            std::thread::sleep(std::time::Duration::from_secs(3));
            let elapsed = start.elapsed();
            if elapsed > estimated_duration {
                break;
            }
            // Map elapsed time to 15-85% range
            let frac = elapsed.as_secs_f64() / estimated_duration.as_secs_f64();
            let percent = 15.0 + frac * 70.0;
            let _ = emitter_clone.emit("tts-setup-progress", json!({
                "stage": "installing",
                "message": "Downloading voice engine — this may take a minute...",
                "percent": percent as u32
            }));
        }
    });

    let pip_output = pip_child.wait_with_output()
        .map_err(|e| format!("pip install failed: {}", e))?;

    // Stop the progress thread (it'll finish on its own after estimated_duration)
    let _ = progress_thread.join();

    if !pip_output.status.success() {
        let stderr = String::from_utf8_lossy(&pip_output.stderr);
        let _ = std::fs::remove_dir_all(&venv_dir);
        let msg = "Voice engine install failed. Check your internet connection.".to_string();
        eprintln!("[tts] pip install stderr: {}", stderr);
        let _ = emitter.emit("tts-setup-progress", json!({"stage": "error", "message": &msg, "percent": 0}));
        return Err(msg);
    }

    let _ = emitter.emit("tts-setup-progress", json!({
        "stage": "complete",
        "message": "Voice engine ready!",
        "percent": 100
    }));
    eprintln!("[tts] Voice engine setup complete.");
    Ok(())
}

/// Pick a free port and spawn the Piper server on it. NEVER kills foreign
/// processes — if 8095 is taken by something else, we hop to 8096..8104.
/// On success, updates `TTS_PORT_ACTIVE` and returns the Child.
fn spawn_piper_server() -> Option<Child> {
    let (python, server_py, model_dir) = piper_server_paths();
    if server_py.is_empty() || !std::path::Path::new(&python).exists() {
        eprintln!("[tts] Piper server.py not found or python missing");
        return None;
    }

    // If our Piper is already running on the default port, do not re-spawn —
    // the caller checked piper_server_available() but a leftover from a prior
    // session may exist that we don't own. Picking the next free port avoids
    // colliding with it.
    let port = pick_tts_port();
    TTS_PORT_ACTIVE.store(port, Ordering::Relaxed);
    eprintln!("[tts] Starting Piper server on port {}", port);

    Command::new(&python)
        .arg(&server_py)
        .env("TTS_PORT", port.to_string())
        .env("MODEL_DIR", &model_dir)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .ok()
}

/// Start the Piper TTS server on app launch.
/// Runs on a background thread so setup() returns immediately.
pub fn start_piper_on_launch(tts: tauri::State<TtsState>, app_handle: tauri::AppHandle) {
    // If OUR Piper is already running on the default port (e.g. relaunch after
    // a crash where the orphan survived), reuse it instead of starting another.
    if is_our_piper(TTS_PORT_DEFAULT) {
        TTS_PORT_ACTIVE.store(TTS_PORT_DEFAULT, Ordering::Relaxed);
        return;
    }

    // Clone the Arc so the spawned thread can write the child back into TtsState.
    let server_handle: Arc<Mutex<Option<Child>>> = tts.piper_server.clone();

    std::thread::spawn(move || {
        if let Err(e) = ensure_piper_venv(&app_handle) {
            eprintln!("[tts] Failed to bootstrap piper venv: {}", e);
            return;
        }

        if let Some(child) = spawn_piper_server() {
            if let Ok(mut guard) = server_handle.lock() {
                *guard = Some(child);
            }
        }
    });
}

#[tauri::command]
pub fn tts_status() -> Result<Value, String> {
    let venv_exists = std::path::Path::new(&venv_python_path()).exists();
    let server_running = piper_server_available();

    Ok(json!({
        "venv_ready": venv_exists,
        "server_running": server_running,
        "status": if server_running {
            "ready"
        } else if venv_exists {
            "starting"
        } else {
            "bootstrapping"
        }
    }))
}

/// Validate voice ID: alphanumeric, hyphens, underscores only
fn is_valid_voice_id(voice: &str) -> bool {
    !voice.is_empty()
        && voice.len() <= 64
        && voice
            .chars()
            .all(|c| c.is_alphanumeric() || c == '-' || c == '_')
}

fn piper_server_available() -> bool {
    Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "1",
            &format!("http://localhost:{}/health", tts_port()),
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

/// Find the Piper TTS server.py and models directory.
fn piper_server_paths() -> (String, String, String) {
    let venv_python = venv_python_path();
    let python = if std::path::Path::new(&venv_python).exists() {
        venv_python
    } else {
        "python3".to_string()
    };

    // Build a list of candidate locations for server.py.
    // Tauri maps `../../` resource paths to `_up_/_up_/` inside .app/Contents/Resources/.
    let mut server_locations: Vec<std::path::PathBuf> = Vec::new();
    if let Ok(exe) = std::env::current_exe() {
        if let Some(bin_dir) = exe.parent() {
            let res = bin_dir.join("../Resources");
            server_locations.push(res.join("_up_/_up_/services/piper-tts/server.py"));
            server_locations.push(res.join("piper/server.py"));
            server_locations.push(res.join("services/piper-tts/server.py"));
        }
    }
    // Dev path (relative to Cargo.toml → frontend/src-tauri → ../../services)
    if let Some(dev) = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|p| p.parent())
        .map(|p| p.join("services/piper-tts/server.py"))
    {
        server_locations.push(dev);
    }
    // User home fallback
    server_locations.push(
        std::path::PathBuf::from(home_dir())
            .join(".scriptures/piper/server.py"),
    );

    let server_py = server_locations
        .iter()
        .find(|p| p.exists())
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_default();

    let model_dir = if !server_py.is_empty() {
        std::path::Path::new(&server_py)
            .parent()
            .map(|p| p.join("models").to_string_lossy().to_string())
            .unwrap_or_default()
    } else {
        String::new()
    };

    (python, server_py, model_dir)
}

/// Split text into sentences for fast synthesis
fn split_into_sentences(text: &str) -> Vec<String> {
    let mut sentences = Vec::new();
    let mut current = String::new();

    for ch in text.chars() {
        current.push(ch);
        if (ch == '.' || ch == '!' || ch == '?' || ch == ';') && current.len() > 10 {
            let trimmed = current.trim().to_string();
            if !trimmed.is_empty() {
                sentences.push(trimmed);
            }
            current.clear();
        }
    }
    let trimmed = current.trim().to_string();
    if !trimmed.is_empty() {
        sentences.push(trimmed);
    }
    sentences
}

/// Synthesize a single sentence via Piper HTTP API. Returns path to WAV file.
fn synthesize_sentence(sentence: &str, voice: &str, index: usize) -> Option<String> {
    let wav_path = format!("{}/chunk_{:04}.wav", PREFETCH_DIR, index);
    let body = json!({"text": sentence, "voice": voice});

    let output = Command::new("curl")
        .args([
            "-sN",
            "--connect-timeout",
            "5",
            "--max-time",
            "30",
            "-X",
            "POST",
            &format!("http://localhost:{}/synthesize", tts_port()),
            "-H",
            "Content-Type: application/json",
            "-d",
            &body.to_string(),
            "-o",
            &wav_path,
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .output()
        .ok()?;

    if output.status.success() {
        let size = std::fs::metadata(&wav_path).map(|m| m.len()).unwrap_or(0);
        if size > 1024 {
            return Some(wav_path);
        }
    }
    None
}

#[tauri::command]
pub fn list_voices() -> Result<Value, String> {
    if !piper_server_available() {
        return Ok(json!([]));
    }

    let output = Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "2",
            &format!("http://localhost:{}/voices", tts_port()),
        ])
        .output()
        .map_err(|e| e.to_string())?;

    if !output.status.success() {
        return Ok(json!([]));
    }

    let data: Value = serde_json::from_slice(&output.stdout).unwrap_or(json!({}));
    if let Some(voices_arr) = data.get("voices").and_then(|v| v.as_array()) {
        let normalized: Vec<Value> = voices_arr
            .iter()
            .map(|v| {
                json!({
                    "name": v.get("name").and_then(|n| n.as_str()).unwrap_or(""),
                    "voice_id": v.get("id").and_then(|n| n.as_str()).unwrap_or(""),
                    "description": v.get("description").and_then(|n| n.as_str()).unwrap_or(""),
                    "language": v.get("language").and_then(|n| n.as_str()).unwrap_or("en"),
                    "locale": "piper",
                    "engine": "piper",
                })
            })
            .collect();
        Ok(json!(normalized))
    } else {
        Ok(json!([]))
    }
}

#[tauri::command]
pub fn prefetch_audio(
    text: String,
    voice: Option<String>,
    tts: State<TtsState>,
) -> Result<(), String> {
    {
        let mut pf = tts.prefetch.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *pf {
            let _ = child.kill();
        }
        *pf = None;
    }

    if text.is_empty() || !piper_server_available() {
        return Ok(());
    }

    let sentences = split_into_sentences(&text);
    let first = sentences.first().cloned().unwrap_or_default();
    if first.is_empty() {
        return Ok(());
    }

    let voice_id = voice
        .filter(|v| is_valid_voice_id(v))
        .unwrap_or_else(|| "en_US-lessac-high".to_string());
    let body = json!({"text": first, "voice": voice_id});

    let _ = std::fs::create_dir_all(PREFETCH_DIR);
    let prefetch_path = format!("{}/chunk_0000.wav", PREFETCH_DIR);

    let child = Command::new("curl")
        .args([
            "-sN",
            "--connect-timeout",
            "3",
            "--max-time",
            "30",
            "-X",
            "POST",
            &format!("http://localhost:{}/synthesize", tts_port()),
            "-H",
            "Content-Type: application/json",
            "-d",
            &body.to_string(),
            "-o",
            &prefetch_path,
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Prefetch failed: {}", e))?;

    let mut pf = tts.prefetch.lock().map_err(|e| e.to_string())?;
    *pf = Some(child);
    Ok(())
}

#[tauri::command]
pub fn is_prefetch_ready() -> Result<bool, String> {
    let path = format!("{}/chunk_0000.wav", PREFETCH_DIR);
    let size = std::fs::metadata(&path).map(|m| m.len()).unwrap_or(0);
    Ok(size > 1024)
}

/// Start Piper TTS server, waiting up to 10s for it to become available.
fn auto_start_piper(tts: &State<TtsState>) -> bool {
    if let Some(child) = spawn_piper_server() {
        if let Ok(mut server) = tts.piper_server.lock() {
            *server = Some(child);
        }
        for _ in 0..20 {
            std::thread::sleep(std::time::Duration::from_millis(500));
            if piper_server_available() {
                return true;
            }
        }
    }
    false
}

/// Play sentences using direct Command API calls (no shell script generation).
/// Runs on a background thread. Uses AtomicBool flags for pause/cancel.
fn play_sentences(
    sentences: Vec<String>,
    voice: String,
    rate: f32,
    cancelled: Arc<AtomicBool>,
    paused: Arc<AtomicBool>,
    playing: Arc<AtomicBool>,
    process: Arc<Mutex<Option<Child>>>,
) {
    let rate_mult = format!("{:.2}", rate / 175.0);
    let _ = std::fs::create_dir_all(PREFETCH_DIR);

    for (i, sentence) in sentences.iter().enumerate() {
        if cancelled.load(Ordering::Relaxed) {
            break;
        }

        // Wait while paused
        while paused.load(Ordering::Relaxed) {
            if cancelled.load(Ordering::Relaxed) {
                break;
            }
            std::thread::sleep(std::time::Duration::from_millis(100));
        }
        if cancelled.load(Ordering::Relaxed) {
            break;
        }

        // Synthesize
        let wav_path = match synthesize_sentence(sentence, &voice, i) {
            Some(p) => p,
            None => continue,
        };

        if cancelled.load(Ordering::Relaxed) {
            break;
        }

        // Play with afplay (blocks until done)
        let child = Command::new("afplay")
            .args(["-r", &rate_mult, &wav_path])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();

        if let Ok(mut child) = child {
            // Store the afplay process so pause/stop can signal it
            if let Ok(mut proc) = process.lock() {
                *proc = Some(child);
            } else {
                let _ = child.wait();
                continue;
            }

            // Wait for afplay to finish, checking cancel flag
            loop {
                if cancelled.load(Ordering::Relaxed) {
                    if let Ok(mut proc) = process.lock() {
                        if let Some(ref mut c) = *proc {
                            let _ = c.kill();
                        }
                        *proc = None;
                    }
                    break;
                }

                if let Ok(mut proc) = process.lock() {
                    if let Some(ref mut c) = *proc {
                        match c.try_wait() {
                            Ok(Some(_)) => {
                                *proc = None;
                                break;
                            }
                            Ok(None) => {}
                            Err(_) => {
                                *proc = None;
                                break;
                            }
                        }
                    } else {
                        break;
                    }
                }
                std::thread::sleep(std::time::Duration::from_millis(50));
            }
        }
    }

    playing.store(false, Ordering::Relaxed);
    // Cleanup
    let _ = std::fs::remove_dir_all(PREFETCH_DIR);
}

#[tauri::command]
pub fn read_aloud(
    text: String,
    rate: Option<f32>,
    voice: Option<String>,
    tts: State<TtsState>,
) -> Result<(), String> {
    // Kill existing playback
    tts.cancelled.store(true, Ordering::Relaxed);
    {
        let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *proc {
            let _ = child.kill();
        }
        *proc = None;
    }
    // Brief pause for previous thread to notice cancel
    std::thread::sleep(std::time::Duration::from_millis(100));

    tts.cancelled.store(false, Ordering::Relaxed);
    tts.paused.store(false, Ordering::Relaxed);

    // Auto-start Piper server if not running
    if !piper_server_available() && !auto_start_piper(&tts) {
        return Err("Piper TTS server not available. Install it from Settings.".to_string());
    }

    let rate_val = rate.unwrap_or(175.0).clamp(50.0, 500.0);
    let voice_id = voice
        .filter(|v| is_valid_voice_id(v))
        .unwrap_or_else(|| "en_US-lessac-high".to_string());

    let sentences = split_into_sentences(&text);
    if sentences.is_empty() {
        return Ok(());
    }

    tts.playing.store(true, Ordering::Relaxed);

    let cancelled = tts.cancelled.clone();
    let paused = tts.paused.clone();
    let playing = tts.playing.clone();
    let process = tts.process.clone();

    std::thread::spawn(move || {
        play_sentences(sentences, voice_id, rate_val, cancelled, paused, playing, process);
    });

    Ok(())
}

#[tauri::command]
pub fn read_aloud_verses(
    verses: Vec<VerseInput>,
    rate: Option<f32>,
    voice: Option<String>,
    tts: State<TtsState>,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    // Kill existing playback
    tts.cancelled.store(true, Ordering::Relaxed);
    {
        let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *proc {
            let _ = child.kill();
        }
        *proc = None;
    }
    std::thread::sleep(std::time::Duration::from_millis(100));

    tts.cancelled.store(false, Ordering::Relaxed);
    tts.paused.store(false, Ordering::Relaxed);
    tts.skip_to.store(-1, Ordering::Relaxed);

    if !piper_server_available() && !auto_start_piper(&tts) {
        return Err("Piper TTS server not available.".to_string());
    }

    if verses.is_empty() {
        return Ok(());
    }

    let rate_val = rate.unwrap_or(175.0).clamp(50.0, 500.0);
    let voice_id = voice
        .filter(|v| is_valid_voice_id(v))
        .unwrap_or_else(|| "en_US-lessac-high".to_string());

    tts.playing.store(true, Ordering::Relaxed);

    let cancelled = tts.cancelled.clone();
    let paused = tts.paused.clone();
    let playing = tts.playing.clone();
    let process = tts.process.clone();
    let skip_to = tts.skip_to.clone();

    std::thread::spawn(move || {
        play_verses(verses, voice_id, rate_val, cancelled, paused, playing, process, skip_to, app_handle);
    });

    Ok(())
}

/// Play verse-by-verse, emitting tts-verse-playing events for each verse.
/// Supports skip_to for forward/back navigation.
#[allow(clippy::too_many_arguments)]
fn play_verses(
    verses: Vec<VerseInput>,
    voice: String,
    rate: f32,
    cancelled: Arc<AtomicBool>,
    paused: Arc<AtomicBool>,
    playing: Arc<AtomicBool>,
    process: Arc<Mutex<Option<Child>>>,
    skip_to: Arc<AtomicI64>,
    emitter: tauri::AppHandle,
) {
    let rate_mult = format!("{:.2}", rate / 175.0);
    let _ = std::fs::create_dir_all(PREFETCH_DIR);
    let total = verses.len();
    let mut i = 0usize;

    while i < total {
        if cancelled.load(Ordering::Relaxed) {
            break;
        }

        // Check for skip request
        let skip = skip_to.swap(-1, Ordering::Relaxed);
        if skip >= 0 {
            let target = (skip as usize).min(total.saturating_sub(1));
            i = target;
            // Kill current afplay if playing
            if let Ok(mut proc) = process.lock() {
                if let Some(ref mut c) = *proc {
                    let _ = c.kill();
                }
                *proc = None;
            }
        }

        // Wait while paused
        while paused.load(Ordering::Relaxed) {
            if cancelled.load(Ordering::Relaxed) {
                break;
            }
            // Also check skip while paused
            let skip = skip_to.swap(-1, Ordering::Relaxed);
            if skip >= 0 {
                i = (skip as usize).min(total.saturating_sub(1));
                paused.store(false, Ordering::Relaxed);
                break;
            }
            std::thread::sleep(std::time::Duration::from_millis(100));
        }
        if cancelled.load(Ordering::Relaxed) {
            break;
        }

        let verse = &verses[i];

        // Emit which verse is now playing (include index + total for UI)
        let _ = emitter.emit("tts-verse-playing", json!({
            "verseId": verse.id,
            "verseIndex": i,
            "totalVerses": total
        }));

        // Synthesize the entire verse as one audio chunk
        let wav_path = match synthesize_sentence(&verse.text, &voice, i) {
            Some(p) => p,
            None => { i += 1; continue; },
        };

        if cancelled.load(Ordering::Relaxed) {
            break;
        }

        // Play with afplay
        let child = Command::new("afplay")
            .args(["-r", &rate_mult, &wav_path])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();

        if let Ok(mut child) = child {
            if let Ok(mut proc) = process.lock() {
                *proc = Some(child);
            } else {
                let _ = child.wait();
                i += 1;
                continue;
            }

            loop {
                if cancelled.load(Ordering::Relaxed) {
                    if let Ok(mut proc) = process.lock() {
                        if let Some(ref mut c) = *proc {
                            let _ = c.kill();
                        }
                        *proc = None;
                    }
                    break;
                }

                // Check for skip — kill current afplay and jump
                let skip = skip_to.load(Ordering::Relaxed);
                if skip >= 0 {
                    if let Ok(mut proc) = process.lock() {
                        if let Some(ref mut c) = *proc {
                            let _ = c.kill();
                        }
                        *proc = None;
                    }
                    break; // Outer loop will handle the skip
                }

                // Check if paused — kill afplay cleanly
                if paused.load(Ordering::Relaxed) {
                    if let Ok(mut proc) = process.lock() {
                        if let Some(ref mut c) = *proc {
                            let _ = c.kill();
                        }
                        *proc = None;
                    }
                    break;
                }

                if let Ok(mut proc) = process.lock() {
                    if let Some(ref mut c) = *proc {
                        match c.try_wait() {
                            Ok(Some(_)) => { *proc = None; break; }
                            Ok(None) => {}
                            Err(_) => { *proc = None; break; }
                        }
                    } else {
                        break;
                    }
                }
                std::thread::sleep(std::time::Duration::from_millis(50));
            }
        }

        // Only advance if no skip is pending (skip handling sets i directly)
        if skip_to.load(Ordering::Relaxed) < 0 {
            i += 1;
        }
    }

    // Clear highlight
    let _ = emitter.emit("tts-verse-playing", json!({"verseId": null}));
    playing.store(false, Ordering::Relaxed);
    let _ = std::fs::remove_dir_all(PREFETCH_DIR);
}

#[tauri::command]
pub fn pause_reading(tts: State<TtsState>) -> Result<(), String> {
    tts.paused.store(true, Ordering::Relaxed);
    // Kill current afplay so pause is immediate (no SIGSTOP clipping).
    // The play loop will wait at the paused check before the next sentence.
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        let _ = child.kill();
    }
    *proc = None;
    Ok(())
}

#[tauri::command]
pub fn resume_reading(tts: State<TtsState>) -> Result<(), String> {
    tts.paused.store(false, Ordering::Relaxed);
    Ok(())
}

#[tauri::command]
pub fn skip_verse(index: i64, tts: State<TtsState>) -> Result<(), String> {
    tts.skip_to.store(index, Ordering::Relaxed);
    // Kill current afplay so skip is immediate
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        let _ = child.kill();
    }
    *proc = None;
    Ok(())
}

#[tauri::command]
pub fn stop_reading(tts: State<TtsState>) -> Result<(), String> {
    tts.cancelled.store(true, Ordering::Relaxed);
    tts.paused.store(false, Ordering::Relaxed);
    tts.playing.store(false, Ordering::Relaxed);

    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        let _ = child.kill();
    }
    *proc = None;

    let _ = Command::new("sh")
        .arg("-c")
        .arg("pkill -9 -f 'afplay.*/tmp/scriptures_tts_chunks' 2>/dev/null")
        .output();
    let _ = std::fs::remove_dir_all(PREFETCH_DIR);
    Ok(())
}

#[tauri::command]
pub fn is_reading(tts: State<TtsState>) -> Result<Value, String> {
    let playing = tts.playing.load(Ordering::Relaxed);
    let paused = tts.paused.load(Ordering::Relaxed);
    Ok(json!({"playing": playing && !paused, "paused": playing && paused}))
}


