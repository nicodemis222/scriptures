use serde_json::{json, Value};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::State;

pub struct TtsState {
    pub process: Mutex<Option<Child>>,
    pub paused: Mutex<bool>,
    pub prefetch: Mutex<Option<Child>>,
    pub piper_server: Mutex<Option<Child>>,
}

impl TtsState {
    pub fn new() -> Self {
        TtsState {
            process: Mutex::new(None),
            paused: Mutex::new(false),
            prefetch: Mutex::new(None),
            piper_server: Mutex::new(None),
        }
    }
}

impl Drop for TtsState {
    fn drop(&mut self) {
        // Kill playback process group (bash + afplay + curl children)
        if let Ok(mut guard) = self.process.lock() {
            if let Some(ref mut child) = *guard {
                #[cfg(unix)]
                unsafe {
                    // SIGKILL the entire process group so afplay/curl die too
                    libc::kill(-(child.id() as libc::pid_t), libc::SIGKILL);
                }
                let _ = child.kill();
            }
            *guard = None;
        }
        // Kill prefetch
        if let Ok(mut guard) = self.prefetch.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill();
            }
            *guard = None;
        }
        // Kill Piper server
        if let Ok(mut guard) = self.piper_server.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill();
            }
            *guard = None;
        }
        // Belt-and-suspenders: kill any orphaned afplay from our temp dir
        let _ = Command::new("sh")
            .arg("-c")
            .arg("pkill -9 -f 'afplay.*/tmp/scriptures_tts_chunks' 2>/dev/null; lsof -ti:8095 | xargs kill -9 2>/dev/null")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
        // Cleanup temp files
        let _ = std::fs::remove_dir_all(PREFETCH_DIR);
        let _ = std::fs::remove_file(PLAYBACK_SCRIPT);
    }
}

const PLAYBACK_SCRIPT: &str = "/tmp/scriptures_tts_play.sh";
const PREFETCH_DIR: &str = "/tmp/scriptures_tts_chunks";
const TTS_PORT: u16 = 8095;

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
/// Returns (python_path, server_py_path, model_dir)
fn piper_server_paths() -> (String, String, String) {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());

    // Check for venv in ~/.scriptures/piper-env/
    let venv_python = format!("{}/.scriptures/piper-env/bin/python", home);
    let venv_exists = std::path::Path::new(&venv_python).exists();

    let python = if venv_exists {
        venv_python
    } else {
        "python3".to_string()
    };

    // Server script location: check bundled first, then project, then ~/.scriptures
    let server_locations = vec![
        // Inside .app bundle
        std::env::current_exe()
            .ok()
            .and_then(|exe| exe.parent().map(|p| p.join("../Resources/piper/server.py")))
            .unwrap_or_default(),
        // Development: project services dir
        std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(|p| p.parent())
            .map(|p| p.join("services/piper-tts/server.py"))
            .unwrap_or_default(),
        // Fallback: home dir
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

    // Model directory: next to server.py
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

/// Generate a shell script that synthesizes sentences one at a time and plays each immediately.
fn generate_playback_script(sentences: &[String], voice: &str, rate: f32) -> String {
    let rate_mult = format!("{:.2}", rate / 175.0);
    let mut script = String::from("#!/bin/bash\nset -e\n");
    script.push_str(&format!("mkdir -p {}\n", PREFETCH_DIR));

    for (i, sentence) in sentences.iter().enumerate() {
        let escaped = sentence.replace('\'', "'\\''");
        let wav_path = format!("{}/chunk_{:04}.wav", PREFETCH_DIR, i);

        script.push_str(&format!(
            "curl -sN -X POST http://localhost:{}/synthesize \\\n  -H 'Content-Type: application/json' \\\n  -d '{{\"text\":\"{}\",\"voice\":\"{}\"}}' \\\n  -o '{}' 2>/dev/null\n",
            TTS_PORT,
            escaped.replace('\"', "\\\"").replace('\n', " "),
            voice,
            wav_path,
        ));

        script.push_str(&format!(
            "[ -f '{}' ] && [ -s '{}' ] && afplay -r {} '{}' 2>/dev/null\n",
            wav_path, wav_path, rate_mult, wav_path,
        ));
    }

    script.push_str(&format!("rm -rf {}\n", PREFETCH_DIR));
    script
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

    let voice_id = voice.unwrap_or_else(|| "en_US-lessac-high".to_string());
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

/// Start Piper TTS server using venv Python + server.py
fn auto_start_piper(tts: &State<TtsState>) -> bool {
    let (python, server_py, model_dir) = piper_server_paths();
    if server_py.is_empty() || !std::path::Path::new(&python).exists() {
        return false;
    }

    // Kill any stale process on the port
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
        // Wait for server to come up (model load takes a few seconds)
        for _ in 0..20 {
            std::thread::sleep(std::time::Duration::from_millis(500));
            if piper_server_available() {
                return true;
            }
        }
    }
    false
}

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

    // Auto-start Piper server if not running
    if !piper_server_available() {
        if !auto_start_piper(&tts) {
            return Err("Piper TTS server not available. Install it from Settings.".to_string());
        }
    }

    let rate_val = rate.unwrap_or(175.0).clamp(50.0, 500.0);
    let voice_id = voice.unwrap_or_else(|| "en_US-lessac-high".to_string());

    let sentences = split_into_sentences(&text);
    if sentences.is_empty() {
        return Ok(());
    }

    let script = generate_playback_script(&sentences, &voice_id, rate_val);
    std::fs::write(PLAYBACK_SCRIPT, &script)
        .map_err(|e| format!("Failed to write playback script: {}", e))?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(PLAYBACK_SCRIPT, std::fs::Permissions::from_mode(0o755));
    }

    let child = Command::new("bash")
        .arg(PLAYBACK_SCRIPT)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start playback: {}", e))?;

    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    *proc = Some(child);
    Ok(())
}

#[tauri::command]
pub fn pause_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        match child.try_wait() {
            Ok(None) => {
                #[cfg(unix)]
                unsafe {
                    libc::kill(-(child.id() as libc::pid_t), libc::SIGSTOP);
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

#[tauri::command]
pub fn resume_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        match child.try_wait() {
            Ok(None) => {
                #[cfg(unix)]
                unsafe {
                    libc::kill(-(child.id() as libc::pid_t), libc::SIGCONT);
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

#[tauri::command]
pub fn stop_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        #[cfg(unix)]
        unsafe {
            libc::kill(-(child.id() as libc::pid_t), libc::SIGCONT);
            libc::kill(-(child.id() as libc::pid_t), libc::SIGTERM);
        }
        let _ = child.kill();
    }
    *proc = None;
    let mut p = tts.paused.lock().map_err(|e| e.to_string())?;
    *p = false;
    let _ = Command::new("sh")
        .arg("-c")
        .arg("pkill -f 'afplay.*/tmp/scriptures_tts_chunks' 2>/dev/null")
        .output();
    let _ = std::fs::remove_dir_all(PREFETCH_DIR);
    let _ = std::fs::remove_file(PLAYBACK_SCRIPT);
    Ok(())
}

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

// ── Piper TTS Server Management ──
// Note: Command names kept as is_vibevoice_installed/install_vibevoice/start_vibevoice
// to maintain frontend API compatibility. They now manage Piper TTS.

#[tauri::command]
pub fn is_vibevoice_installed() -> Result<Value, String> {
    let (python, server_py, model_dir) = piper_server_paths();
    let has_python = std::path::Path::new(&python).exists();
    let has_server = !server_py.is_empty() && std::path::Path::new(&server_py).exists();
    let has_models = !model_dir.is_empty() && std::path::Path::new(&model_dir).exists();
    let installed = has_python && has_server && has_models;
    let running = piper_server_available();
    Ok(json!({
        "installed": installed,
        "running": running,
        "path": server_py,
    }))
}

#[tauri::command]
pub fn install_vibevoice() -> Result<Value, String> {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let venv_path = format!("{}/.scriptures/piper-env", home);
    let venv_python = format!("{}/bin/python", venv_path);

    // Check if already installed
    if std::path::Path::new(&venv_python).exists() {
        let check = Command::new(&venv_python)
            .args(["-c", "import piper"])
            .output();
        if check.map(|o| o.status.success()).unwrap_or(false) {
            return Ok(json!({"status": "already_installed"}));
        }
    }

    // Create venv
    let output = Command::new("python3")
        .args(["-m", "venv", &venv_path])
        .output()
        .map_err(|e| format!("Failed to create venv: {}", e))?;
    if !output.status.success() {
        return Err("Failed to create Python venv".to_string());
    }

    // Install piper-tts
    let pip = format!("{}/bin/pip", venv_path);
    let output = Command::new(&pip)
        .args(["install", "piper-tts"])
        .output()
        .map_err(|e| format!("pip install failed: {}", e))?;
    if !output.status.success() {
        return Err(format!(
            "Failed to install piper-tts: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    Ok(json!({"status": "installed", "path": venv_path}))
}

#[tauri::command]
pub fn start_vibevoice(tts: State<TtsState>) -> Result<Value, String> {
    if piper_server_available() {
        return Ok(json!({"status": "already_running"}));
    }

    let (python, server_py, model_dir) = piper_server_paths();
    if server_py.is_empty() || !std::path::Path::new(&python).exists() {
        return Err("Piper TTS not installed. Click Install first.".to_string());
    }

    // Kill anything on the port first
    let _ = Command::new("sh")
        .arg("-c")
        .arg(format!("lsof -ti:{} | xargs kill -9 2>/dev/null", TTS_PORT))
        .output();
    std::thread::sleep(std::time::Duration::from_millis(500));

    {
        let mut server = tts.piper_server.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *server {
            let _ = child.kill();
        }
        *server = None;
    }

    let child = Command::new(&python)
        .arg(&server_py)
        .env("TTS_PORT", TTS_PORT.to_string())
        .env("MODEL_DIR", &model_dir)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start Piper TTS: {}", e))?;

    {
        let mut server = tts.piper_server.lock().map_err(|e| e.to_string())?;
        *server = Some(child);
    }

    for _ in 0..30 {
        std::thread::sleep(std::time::Duration::from_millis(500));
        if piper_server_available() {
            return Ok(json!({"status": "started"}));
        }
    }

    Ok(json!({"status": "starting"}))
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
    if Command::new("which")
        .arg("ollama")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
    {
        return Ok(json!({"status": "already_installed"}));
    }
    if cfg!(target_os = "macos") {
        match Command::new("brew").args(["install", "ollama"]).output() {
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
    if Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "1",
            "http://localhost:11434/api/tags",
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
    {
        return Ok(json!({"status": "already_running"}));
    }
    let _child = Command::new("ollama")
        .arg("serve")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed: {}", e))?;
    std::thread::sleep(std::time::Duration::from_secs(2));
    let running = Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "2",
            "http://localhost:11434/api/tags",
        ])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);
    Ok(json!({"status": if running { "started" } else { "starting" }}))
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
        .map_err(|e| format!("Failed: {}", e))?;
    if output.status.success() {
        Ok(json!({"status": "pulled", "model": model}))
    } else {
        Err(format!(
            "Pull failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ))
    }
}
