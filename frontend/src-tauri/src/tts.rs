use serde_json::{json, Value};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use tauri::State;

pub struct TtsState {
    pub process: Arc<Mutex<Option<Child>>>,
    pub paused: Arc<AtomicBool>,
    pub cancelled: Arc<AtomicBool>,
    pub playing: Arc<AtomicBool>,
    pub prefetch: Mutex<Option<Child>>,
    pub piper_server: Mutex<Option<Child>>,
}

impl TtsState {
    pub fn new() -> Self {
        TtsState {
            process: Arc::new(Mutex::new(None)),
            paused: Arc::new(AtomicBool::new(false)),
            cancelled: Arc::new(AtomicBool::new(false)),
            playing: Arc::new(AtomicBool::new(false)),
            prefetch: Mutex::new(None),
            piper_server: Mutex::new(None),
        }
    }
}

impl Drop for TtsState {
    fn drop(&mut self) {
        // Kill playback process (afplay)
        if let Ok(mut guard) = self.process.lock() {
            if let Some(ref mut child) = *guard {
                #[cfg(unix)]
                {
                    let pid = child.id();
                    if pid <= i32::MAX as u32 {
                        // SAFETY: kill process group so afplay children die too
                        unsafe { libc::kill(-(pid as libc::pid_t), libc::SIGKILL); }
                    }
                }
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
        // Kill any orphaned afplay and Piper server
        let _ = Command::new("sh")
            .arg("-c")
            .arg("pkill -9 -f 'afplay.*/tmp/scriptures_tts_chunks' 2>/dev/null; lsof -ti:8095 | xargs kill -9 2>/dev/null")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
        let _ = std::fs::remove_dir_all(PREFETCH_DIR);
    }
}

const PREFETCH_DIR: &str = "/tmp/scriptures_tts_chunks";
const TTS_PORT: u16 = 8095;

/// Start the Piper TTS server on app launch (called from setup, runs on background thread).
pub fn start_piper_on_launch(tts: tauri::State<TtsState>) {
    if piper_server_available() {
        return;
    }
    let (python, server_py, model_dir) = piper_server_paths();
    if server_py.is_empty() || !std::path::Path::new(&python).exists() {
        return;
    }
    // Kill stale process on port
    let _ = Command::new("sh")
        .arg("-c")
        .arg(format!("lsof -ti:{} | xargs kill -9 2>/dev/null", TTS_PORT))
        .output();

    let child = Command::new(&python)
        .arg(&server_py)
        .env("TTS_PORT", TTS_PORT.to_string())
        .env("MODEL_DIR", &model_dir)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn();

    if let Ok(child) = child {
        if let Ok(mut server) = tts.piper_server.lock() {
            *server = Some(child);
        }
    }
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
            &format!("http://localhost:{}/health", TTS_PORT),
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

/// Find the Piper TTS server.py and models directory.
fn piper_server_paths() -> (String, String, String) {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());

    let venv_python = format!("{}/.scriptures/piper-env/bin/python", home);
    let python = if std::path::Path::new(&venv_python).exists() {
        venv_python
    } else {
        "python3".to_string()
    };

    let server_locations = [
        std::env::current_exe()
            .ok()
            .and_then(|exe| exe.parent().map(|p| p.join("../Resources/piper/server.py")))
            .unwrap_or_default(),
        std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(|p| p.parent())
            .map(|p| p.join("services/piper-tts/server.py"))
            .unwrap_or_default(),
        std::path::PathBuf::from(&home)
            .join(".scriptures")
            .join("piper")
            .join("server.py"),
    ];

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
            &format!("http://localhost:{}/synthesize", TTS_PORT),
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
            &format!("http://localhost:{}/voices", TTS_PORT),
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
            &format!("http://localhost:{}/synthesize", TTS_PORT),
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

/// Start Piper TTS server using venv Python + server.py (non-blocking on separate thread)
fn auto_start_piper(tts: &State<TtsState>) -> bool {
    let (python, server_py, model_dir) = piper_server_paths();
    if server_py.is_empty() || !std::path::Path::new(&python).exists() {
        return false;
    }

    let _ = Command::new("sh")
        .arg("-c")
        .arg(format!("lsof -ti:{} | xargs kill -9 2>/dev/null", TTS_PORT))
        .output();
    std::thread::sleep(std::time::Duration::from_millis(300));

    let child = Command::new(&python)
        .arg(&server_py)
        .env("TTS_PORT", TTS_PORT.to_string())
        .env("MODEL_DIR", &model_dir)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn();

    if let Ok(child) = child {
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
pub fn pause_reading(tts: State<TtsState>) -> Result<(), String> {
    tts.paused.store(true, Ordering::Relaxed);
    // Also SIGSTOP current afplay if running
    let proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref child) = *proc {
        #[cfg(unix)]
        {
            let pid = child.id();
            if pid <= i32::MAX as u32 {
                // SAFETY: SIGSTOP the afplay process
                unsafe { libc::kill(pid as libc::pid_t, libc::SIGSTOP); }
            }
        }
    }
    Ok(())
}

#[tauri::command]
pub fn resume_reading(tts: State<TtsState>) -> Result<(), String> {
    tts.paused.store(false, Ordering::Relaxed);
    let proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref child) = *proc {
        #[cfg(unix)]
        {
            let pid = child.id();
            if pid <= i32::MAX as u32 {
                // SAFETY: SIGCONT the afplay process
                unsafe { libc::kill(pid as libc::pid_t, libc::SIGCONT); }
            }
        }
    }
    Ok(())
}

#[tauri::command]
pub fn stop_reading(tts: State<TtsState>) -> Result<(), String> {
    tts.cancelled.store(true, Ordering::Relaxed);
    tts.paused.store(false, Ordering::Relaxed);
    tts.playing.store(false, Ordering::Relaxed);

    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        #[cfg(unix)]
        {
            let pid = child.id();
            if pid <= i32::MAX as u32 {
                // SAFETY: Resume then kill
                unsafe {
                    libc::kill(pid as libc::pid_t, libc::SIGCONT);
                    libc::kill(pid as libc::pid_t, libc::SIGKILL);
                }
            }
        }
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


