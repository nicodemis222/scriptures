use serde_json::{json, Value};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::State;

/// TTS state: current playback process + prefetch process
pub struct TtsState {
    pub process: Mutex<Option<Child>>,
    pub paused: Mutex<bool>,
    pub prefetch: Mutex<Option<Child>>,
    pub vibevoice_server: Mutex<Option<Child>>,
}

impl TtsState {
    pub fn new() -> Self {
        TtsState {
            process: Mutex::new(None),
            paused: Mutex::new(false),
            prefetch: Mutex::new(None),
            vibevoice_server: Mutex::new(None),
        }
    }
}

const PREFETCH_PATH: &str = "/tmp/scriptures_prefetch.wav";
const PLAYBACK_PATH: &str = "/tmp/scriptures_tts.wav";

fn vibevoice_available() -> bool {
    Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "1",
            "http://localhost:8095/health",
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

/// List VibeVoice voices
#[tauri::command]
pub fn list_voices() -> Result<Value, String> {
    if !vibevoice_available() {
        return Ok(json!([]));
    }

    let output = Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "2",
            "http://localhost:8095/voices",
        ])
        .output()
        .map_err(|e| e.to_string())?;

    if !output.status.success() {
        return Ok(json!([]));
    }

    let data: Value = serde_json::from_slice(&output.stdout).unwrap_or(json!({}));
    // Server returns {"voices": [...], "default": "..."} — extract the array
    // and normalize field names for the frontend
    if let Some(voices_arr) = data.get("voices").and_then(|v| v.as_array()) {
        let normalized: Vec<Value> = voices_arr
            .iter()
            .map(|v| {
                json!({
                    "name": v.get("name").and_then(|n| n.as_str()).unwrap_or(""),
                    "voice_id": v.get("id").and_then(|n| n.as_str()).unwrap_or(""),
                    "description": v.get("description").and_then(|n| n.as_str()).unwrap_or(""),
                    "language": v.get("language").and_then(|n| n.as_str()).unwrap_or("en"),
                    "locale": "vibevoice",
                    "engine": "vibevoice",
                })
            })
            .collect();
        Ok(json!(normalized))
    } else {
        Ok(json!([]))
    }
}

/// Start prefetching audio for a chapter in background.
/// Call this when user navigates to a chapter (before they hit play).
#[tauri::command]
pub fn prefetch_audio(
    text: String,
    voice: Option<String>,
    tts: State<TtsState>,
) -> Result<(), String> {
    // Kill any existing prefetch
    {
        let mut pf = tts.prefetch.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *pf {
            let _ = child.kill();
        }
        *pf = None;
    }

    if text.is_empty() || !vibevoice_available() {
        return Ok(());
    }

    let voice_id = voice.unwrap_or_else(|| "en-Emma_woman".to_string());
    let body = json!({"text": text, "voice": voice_id});

    // Remove old prefetch file
    let _ = std::fs::remove_file(PREFETCH_PATH);

    // Start streaming to prefetch file in background
    let child = Command::new("curl")
        .args([
            "-sN",
            "--connect-timeout",
            "3",
            "--max-time",
            "120",
            "-X",
            "POST",
            "http://localhost:8095/synthesize",
            "-H",
            "Content-Type: application/json",
            "-d",
            &body.to_string(),
            "-o",
            PREFETCH_PATH,
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Prefetch failed: {}", e))?;

    let mut pf = tts.prefetch.lock().map_err(|e| e.to_string())?;
    *pf = Some(child);
    Ok(())
}

/// Check if prefetch has audio ready (file exists and > 1KB)
#[tauri::command]
pub fn is_prefetch_ready() -> Result<bool, String> {
    let size = std::fs::metadata(PREFETCH_PATH)
        .map(|m| m.len())
        .unwrap_or(0);
    Ok(size > 1024)
}

/// Play audio. Uses prefetched file if available, otherwise starts fresh stream.
#[tauri::command]
pub fn read_aloud(
    text: String,
    rate: Option<f32>,
    voice: Option<String>,
    tts: State<TtsState>,
) -> Result<(), String> {
    // Kill existing playback
    {
        let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *proc {
            let _ = child.kill();
        }
        *proc = None;
    }
    {
        let mut p = tts.paused.lock().map_err(|e| e.to_string())?;
        *p = false;
    }

    let rate_multiplier = rate.map(|r| r / 175.0).unwrap_or(1.0).clamp(0.5, 3.0);

    // Check if prefetch is ready
    let prefetch_ready = std::fs::metadata(PREFETCH_PATH)
        .map(|m| m.len() > 4096)
        .unwrap_or(false);

    let child = if prefetch_ready {
        // Use prefetched audio — instant playback!
        // Copy prefetch to playback path (prefetch may still be growing)
        let _ = std::fs::copy(PREFETCH_PATH, PLAYBACK_PATH);

        Command::new("afplay")
            .arg("-r")
            .arg(format!("{:.2}", rate_multiplier))
            .arg(PLAYBACK_PATH)
            .spawn()
            .map_err(|e| format!("Failed to play: {}", e))?
    } else if vibevoice_available() {
        // No prefetch — stream fresh from VibeVoice
        // Use curl to stream WAV to file, start afplay after brief delay
        let voice_id = voice.unwrap_or_else(|| "en-Emma_woman".to_string());
        let body = json!({"text": text, "voice": voice_id});

        let _ = std::fs::remove_file(PLAYBACK_PATH);

        // Start streaming download in background
        let _curl = Command::new("curl")
            .args([
                "-sN",
                "--connect-timeout",
                "3",
                "--max-time",
                "120",
                "-X",
                "POST",
                "http://localhost:8095/synthesize",
                "-H",
                "Content-Type: application/json",
                "-d",
                &body.to_string(),
                "-o",
                PLAYBACK_PATH,
            ])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("Stream failed: {}", e))?;

        // Wait briefly for first chunks to arrive, then start playback
        // afplay can play a WAV file while it's still being written
        std::thread::sleep(std::time::Duration::from_millis(1500));

        Command::new("afplay")
            .arg("-r")
            .arg(format!("{:.2}", rate_multiplier))
            .arg(PLAYBACK_PATH)
            .spawn()
            .map_err(|e| format!("Failed to play: {}", e))?
    } else {
        return Err("VibeVoice server not running. Start it from Settings.".to_string());
    };

    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    *proc = Some(child);
    Ok(())
}

/// Pause playback using SIGSTOP
#[tauri::command]
pub fn pause_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        match child.try_wait() {
            Ok(None) => {
                #[cfg(unix)]
                unsafe {
                    libc::kill(child.id() as libc::pid_t, libc::SIGSTOP);
                }
            }
            _ => {
                *proc = None;
                return Ok(());
            }
        }
    }
    let mut p = tts.paused.lock().map_err(|e| e.to_string())?;
    *p = true;
    Ok(())
}

/// Resume playback using SIGCONT
#[tauri::command]
pub fn resume_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        match child.try_wait() {
            Ok(None) => {
                #[cfg(unix)]
                unsafe {
                    libc::kill(child.id() as libc::pid_t, libc::SIGCONT);
                }
            }
            _ => {
                *proc = None;
                return Ok(());
            }
        }
    }
    let mut p = tts.paused.lock().map_err(|e| e.to_string())?;
    *p = false;
    Ok(())
}

/// Stop playback
#[tauri::command]
pub fn stop_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        #[cfg(unix)]
        unsafe {
            libc::kill(child.id() as libc::pid_t, libc::SIGCONT);
        }
        let _ = child.kill();
    }
    *proc = None;
    let mut p = tts.paused.lock().map_err(|e| e.to_string())?;
    *p = false;
    Ok(())
}

/// Check playback status
#[tauri::command]
pub fn is_reading(tts: State<TtsState>) -> Result<Value, String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    let paused = *tts.paused.lock().map_err(|e| e.to_string())?;

    if let Some(ref mut child) = *proc {
        match child.try_wait() {
            Ok(Some(_)) => {
                *proc = None;
                Ok(json!({"playing": false, "paused": false}))
            }
            Ok(None) => Ok(json!({"playing": !paused, "paused": paused})),
            Err(_) => {
                *proc = None;
                Ok(json!({"playing": false, "paused": false}))
            }
        }
    } else {
        Ok(json!({"playing": false, "paused": false}))
    }
}

// ── Ollama Management ──

#[tauri::command]
pub fn check_ollama_installed() -> Result<Value, String> {
    let installed = Command::new("which")
        .arg("ollama")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    let running = Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "1",
            "http://localhost:11434/api/tags",
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    Ok(json!({"installed": installed, "running": running}))
}

#[tauri::command]
pub fn install_ollama() -> Result<Value, String> {
    let already = Command::new("which")
        .arg("ollama")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    if already {
        return Ok(json!({"status": "already_installed"}));
    }

    if cfg!(target_os = "macos") {
        let output = Command::new("brew").args(["install", "ollama"]).output();
        match output {
            Ok(o) if o.status.success() => Ok(json!({"status": "installed", "method": "brew"})),
            _ => {
                let output = Command::new("sh")
                    .arg("-c")
                    .arg("curl -fsSL https://ollama.com/install.sh | sh")
                    .output()
                    .map_err(|e| format!("Install failed: {}", e))?;
                if output.status.success() {
                    Ok(json!({"status": "installed", "method": "curl"}))
                } else {
                    Err(format!(
                        "Install failed: {}",
                        String::from_utf8_lossy(&output.stderr)
                    ))
                }
            }
        }
    } else {
        Err("Visit ollama.ai to download.".to_string())
    }
}

#[tauri::command]
pub fn start_ollama() -> Result<Value, String> {
    let running = Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "1",
            "http://localhost:11434/api/tags",
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    if running {
        return Ok(json!({"status": "already_running"}));
    }

    let _child = Command::new("ollama")
        .arg("serve")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start Ollama: {}", e))?;

    std::thread::sleep(std::time::Duration::from_secs(2));

    let running_now = Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "2",
            "http://localhost:11434/api/tags",
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    Ok(json!({"status": if running_now { "started" } else { "starting" }}))
}

#[tauri::command]
pub fn pull_ollama_model(model: String) -> Result<Value, String> {
    if model.len() > 64
        || !model
            .chars()
            .all(|c| c.is_alphanumeric() || ":.-_".contains(c))
    {
        return Err("Invalid model name".to_string());
    }

    let output = Command::new("ollama")
        .args(["pull", &model])
        .output()
        .map_err(|e| format!("Failed to pull model: {}", e))?;

    if output.status.success() {
        Ok(json!({"status": "pulled", "model": model}))
    } else {
        Err(format!(
            "Pull failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ))
    }
}

// ── VibeVoice Server Management ──

const VIBEVOICE_BINARY_URL: &str =
    "https://ark-data-bundles.s3.us-west-2.amazonaws.com/vibevoice-tts-macos-arm64";

fn vibevoice_binary_path() -> std::path::PathBuf {
    // Check if bundled inside the app first
    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            let bundled = exe_dir.join("../Resources/vibevoice/vibevoice-tts");
            if bundled.exists() {
                return bundled;
            }
        }
    }
    // Fall back to user-downloaded location
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    std::path::PathBuf::from(home)
        .join(".scriptures")
        .join("vibevoice-tts")
}

/// Check if VibeVoice binary is downloaded
#[tauri::command]
pub fn is_vibevoice_installed() -> Result<Value, String> {
    let path = vibevoice_binary_path();
    let installed = path.exists()
        && path
            .metadata()
            .map(|m| m.len() > 1_000_000)
            .unwrap_or(false);
    let running = vibevoice_available();
    Ok(json!({"installed": installed, "running": running, "path": path.to_string_lossy()}))
}

/// Download VibeVoice binary from S3 (one-time, ~328 MB)
#[tauri::command]
pub fn install_vibevoice() -> Result<Value, String> {
    let path = vibevoice_binary_path();
    let dir = path.parent().ok_or("Invalid path")?;
    std::fs::create_dir_all(dir).map_err(|e| format!("Failed to create dir: {}", e))?;

    // Check if already downloaded
    if path.exists()
        && path
            .metadata()
            .map(|m| m.len() > 1_000_000)
            .unwrap_or(false)
    {
        return Ok(json!({"status": "already_installed"}));
    }

    // Download from S3
    let output = Command::new("curl")
        .args([
            "-fSL",
            "--progress-bar",
            "-o",
            path.to_str().unwrap_or(""),
            VIBEVOICE_BINARY_URL,
        ])
        .output()
        .map_err(|e| format!("Download failed: {}", e))?;

    if !output.status.success() {
        return Err("Failed to download VibeVoice binary".to_string());
    }

    // Make executable
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o755));
    }

    Ok(json!({"status": "installed", "path": path.to_string_lossy()}))
}

/// Cleanup: kill VibeVoice server, TTS process, prefetch on drop
impl Drop for TtsState {
    fn drop(&mut self) {
        if let Ok(mut server) = self.vibevoice_server.lock() {
            if let Some(ref mut child) = *server {
                let _ = child.kill();
            }
        }
        if let Ok(mut proc) = self.process.lock() {
            if let Some(ref mut child) = *proc {
                let _ = child.kill();
            }
        }
        if let Ok(mut pf) = self.prefetch.lock() {
            if let Some(ref mut child) = *pf {
                let _ = child.kill();
            }
        }
    }
}

/// Start VibeVoice server from the downloaded binary
#[tauri::command]
pub fn start_vibevoice(tts: State<TtsState>) -> Result<Value, String> {
    if vibevoice_available() {
        return Ok(json!({"status": "already_running"}));
    }

    let path = vibevoice_binary_path();
    if !path.exists() {
        return Err("VibeVoice not installed. Click 'Install Voice Engine' first.".to_string());
    }

    // Set voices dir relative to the binary
    let voices_dir = path.parent().unwrap_or(&path).join("voices");
    // Kill any existing server first
    {
        let mut server = tts.vibevoice_server.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *server {
            let _ = child.kill();
        }
        *server = None;
    }

    let child = Command::new(&path)
        .env("VOICES_DIR", voices_dir.to_str().unwrap_or(""))
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start VibeVoice: {}", e))?;

    // Store the server process for cleanup on app exit
    {
        let mut server = tts.vibevoice_server.lock().map_err(|e| e.to_string())?;
        *server = Some(child);
    }

    // Wait for model to load
    for _ in 0..30 {
        std::thread::sleep(std::time::Duration::from_secs(1));
        if vibevoice_available() {
            return Ok(json!({"status": "started"}));
        }
    }

    Ok(json!({"status": "starting"}))
}
