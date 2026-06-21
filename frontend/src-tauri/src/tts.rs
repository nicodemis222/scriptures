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

// ── TTS engine selection ──
//
// Read Aloud has two engines:
//   • Piper (bundled neural voices) — preferred, but needs a python venv that
//     only exists after the user opts into "enhanced voices".
//   • macOS `say` — always present, zero dependencies, works offline on every
//     Mac. This is the default so Read Aloud works on a clean Mac with NO
//     python3, NO Xcode Command Line Tools, NO internet, and NO surprise modal.
//
// TTS_USE_SAY is set per playback by read_aloud*/. When true, synthesis uses
// `say`; when false, Piper. Static (like TTS_PORT_ACTIVE) so the synth helper
// doesn't have to thread it through.
static TTS_USE_SAY: AtomicBool = AtomicBool::new(true);

/// True only if Xcode Command Line Tools are installed — checked via
/// `xcode-select -p` EXIT CODE, which does NOT invoke the python3/clang shim and
/// therefore never pops Apple's "install developer tools" modal.
fn clt_installed() -> bool {
    Command::new("xcode-select")
        .arg("-p")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// True if the Piper venv is already bootstrapped AND piper imports. Invokes
/// the VENV's python (a real interpreter), never the system `python3` shim, so
/// it's safe to call on a clean Mac (the venv path won't exist → returns false).
fn piper_venv_ready() -> bool {
    let venv_python = venv_python_path();
    if !std::path::Path::new(&venv_python).exists() {
        return false;
    }
    Command::new(&venv_python)
        .args(["-c", "import piper"])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// Validate a macOS `say` voice name (e.g. "Samantha"). Curated voices are
/// single tokens, so the strict alphanumeric rule is fine and keeps the value
/// safe to pass to `say -v`.
fn is_valid_say_voice(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 64
        && name.chars().all(|c| c.is_alphanumeric())
}

/// Curated macOS `say` voices to surface when Piper isn't set up. We probe
/// `say -v '?'` and keep only single-token English voices that actually exist
/// on this machine, so the picker never offers a voice `say` can't use.
fn list_say_voices() -> Vec<Value> {
    const PREFERRED: &[(&str, &str)] = &[
        ("Samantha", "American English (female)"),
        ("Alex", "American English (male)"),
        ("Daniel", "British English (male)"),
        ("Karen", "Australian English (female)"),
        ("Moira", "Irish English (female)"),
        ("Tessa", "South African English (female)"),
        ("Rishi", "Indian English (male)"),
    ];
    let installed: String = Command::new("say")
        .args(["-v", "?"])
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
        .unwrap_or_default();
    let mut out = Vec::new();
    for (name, desc) in PREFERRED {
        // `say -v '?'` lists "Name   locale  # sample" — match the leading token.
        let present = installed
            .lines()
            .any(|l| l.split_whitespace().next() == Some(*name));
        if present {
            out.push(json!({
                "name": name,
                "voice_id": name,
                "description": desc,
                "language": "en",
                "locale": "say",
                "engine": "say",
            }));
        }
    }
    out
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

/// Start the Piper TTS server on app launch — ONLY if the user has already set
/// up enhanced voices (the venv exists and piper imports).
///
/// CRITICAL: this must NEVER invoke the system `python3` to bootstrap a venv.
/// On a clean Mac `/usr/bin/python3` is the Xcode CLT shim, and invoking it pops
/// Apple's "install developer tools" modal with no context. So on first launch
/// (no venv) we do nothing here and Read Aloud transparently uses macOS `say`.
/// The venv is only ever created from the explicit, consent-gated
/// `setup_enhanced_voices` command.
pub fn start_piper_on_launch(tts: tauri::State<TtsState>, _app_handle: tauri::AppHandle) {
    // Reuse our own Piper if it's already running (relaunch / orphan survivor).
    if is_our_piper(TTS_PORT_DEFAULT) {
        TTS_PORT_ACTIVE.store(TTS_PORT_DEFAULT, Ordering::Relaxed);
        return;
    }

    // Only auto-start when enhanced voices are already set up. Never bootstrap.
    if !piper_venv_ready() {
        eprintln!("[tts] Enhanced voices not set up; Read Aloud will use macOS 'say'.");
        return;
    }

    let server_handle: Arc<Mutex<Option<Child>>> = tts.piper_server.clone();
    std::thread::spawn(move || {
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

/// Status for the Settings "enhanced voices" panel. Lets the UI decide what to
/// show WITHOUT ever invoking the python3 shim.
#[tauri::command]
pub fn enhanced_voices_status() -> Result<Value, String> {
    Ok(json!({
        "clt_installed": clt_installed(),
        "venv_ready": piper_venv_ready(),
        "server_running": piper_server_available(),
        // The default engine is always macOS `say` until Piper is set up.
        "active_engine": if piper_server_available() { "piper" } else { "say" },
    }))
}

/// Open Apple's official Command Line Tools installer. This is the ONLY place we
/// touch CLT, and only when the user explicitly clicks "Install" — so the system
/// dialog appears WITH context (the user just asked for enhanced voices), never
/// as a surprise. The actual install is driven by macOS, not us.
#[tauri::command]
pub fn install_command_line_tools() -> Result<Value, String> {
    if clt_installed() {
        return Ok(json!({"status": "already_installed"}));
    }
    Command::new("xcode-select")
        .arg("--install")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|e| format!("Could not open the installer: {}", e))?;
    Ok(json!({"status": "installer_opened"}))
}

/// Explicit, consent-gated setup of Piper "enhanced voices". Only runs after the
/// user clicks Set Up in Settings. Refuses (with a clear message) if Xcode CLT
/// isn't present, so we never blindly invoke the python3 shim. Bootstraps the
/// venv on a background thread and emits tts-setup-progress events.
#[tauri::command]
pub fn setup_enhanced_voices(
    tts: State<TtsState>,
    app_handle: tauri::AppHandle,
) -> Result<Value, String> {
    if piper_venv_ready() {
        // Already set up — just (re)start the server.
        if !piper_server_available() {
            if let Some(child) = spawn_piper_server() {
                if let Ok(mut guard) = tts.piper_server.lock() {
                    *guard = Some(child);
                }
            }
        }
        return Ok(json!({"status": "already_ready"}));
    }
    if !clt_installed() {
        return Err(
            "Enhanced voices need Apple's Command Line Tools. Install them first, then try again."
                .to_string(),
        );
    }

    let server_handle: Arc<Mutex<Option<Child>>> = tts.piper_server.clone();
    std::thread::spawn(move || {
        // Safe: CLT is present, so `python3` resolves to a real interpreter.
        if let Err(e) = ensure_piper_venv(&app_handle) {
            eprintln!("[tts] enhanced-voices setup failed: {}", e);
            return;
        }
        if let Some(child) = spawn_piper_server() {
            if let Ok(mut guard) = server_handle.lock() {
                *guard = Some(child);
            }
        }
    });
    Ok(json!({"status": "setting_up"}))
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

/// Synthesize a single sentence to an audio file. Uses Piper (neural) when
/// TTS_USE_SAY is false, else macOS `say` (always available). Returns the path.
/// `rate` is words-per-minute (applied by `say`; Piper rate is handled via the
/// afplay playback rate in the caller).
fn synthesize_sentence(sentence: &str, voice: &str, index: usize, rate: f32) -> Option<String> {
    if TTS_USE_SAY.load(Ordering::Relaxed) {
        return synthesize_say(sentence, voice, index, rate);
    }
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

/// Synthesize a sentence with macOS `say` to an AIFF file (played via afplay).
/// Zero dependencies — works on any Mac, offline. Voice is used only if it's a
/// valid `say` voice name (Piper ids are ignored → system default voice).
fn synthesize_say(sentence: &str, voice: &str, index: usize, rate: f32) -> Option<String> {
    let aiff_path = format!("{}/chunk_{:04}.aiff", PREFETCH_DIR, index);
    let _ = std::fs::remove_file(&aiff_path);
    let wpm = (rate as i32).clamp(50, 500).to_string();

    let mut cmd = Command::new("say");
    // Default AIFF format — robust across macOS versions (explicit data-format
    // strings vary and can fail). afplay handles the default fine.
    cmd.args(["-r", &wpm, "-o", &aiff_path]);
    if is_valid_say_voice(voice) {
        cmd.args(["-v", voice]);
    }
    // Pass the text as a final argument (not stdin) — bounded by sentence split.
    cmd.arg(sentence);

    let status = cmd.stdout(Stdio::null()).stderr(Stdio::null()).status().ok()?;
    if status.success() {
        let size = std::fs::metadata(&aiff_path).map(|m| m.len()).unwrap_or(0);
        if size > 256 {
            return Some(aiff_path);
        }
    }
    None
}

#[tauri::command]
pub fn list_voices() -> Result<Value, String> {
    // When Piper isn't running, offer macOS `say` voices so the picker still
    // works on a clean Mac (Read Aloud falls back to `say`).
    if !piper_server_available() {
        return Ok(json!(list_say_voices()));
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
    // In `say` mode the rate is baked into synthesis, so afplay plays at 1.0.
    // In Piper mode afplay applies the rate multiplier.
    let rate_mult = if TTS_USE_SAY.load(Ordering::Relaxed) {
        "1.00".to_string()
    } else {
        format!("{:.2}", rate / 175.0)
    };
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
        let wav_path = match synthesize_sentence(sentence, &voice, i, rate) {
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

    // Pick engine: Piper if its server is up or can start from an already-set-up
    // venv; otherwise macOS `say`. `say` is always available so Read Aloud never
    // hard-fails — even on a clean Mac with no python3.
    let use_piper =
        piper_server_available() || (piper_venv_ready() && auto_start_piper(&tts));
    TTS_USE_SAY.store(!use_piper, Ordering::Relaxed);

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

    // Pick engine (Piper if ready, else macOS `say` — always available).
    let use_piper =
        piper_server_available() || (piper_venv_ready() && auto_start_piper(&tts));
    TTS_USE_SAY.store(!use_piper, Ordering::Relaxed);

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
    let rate_mult = if TTS_USE_SAY.load(Ordering::Relaxed) {
        "1.00".to_string()
    } else {
        format!("{:.2}", rate / 175.0)
    };
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
        let wav_path = match synthesize_sentence(&verse.text, &voice, i, rate) {
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


