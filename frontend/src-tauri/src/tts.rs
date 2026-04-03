use serde_json::{json, Value};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::State;

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

impl Drop for TtsState {
    fn drop(&mut self) {
        for mutex in [&self.vibevoice_server, &self.process, &self.prefetch] {
            if let Ok(mut guard) = mutex.lock() {
                if let Some(ref mut child) = *guard {
                    let _ = child.kill();
                }
            }
        }
    }
}

const PLAYBACK_SCRIPT: &str = "/tmp/scriptures_tts_play.sh";
const PREFETCH_DIR: &str = "/tmp/scriptures_tts_chunks";

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

fn vibevoice_binary_path() -> std::path::PathBuf {
    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            let bundled = exe_dir.join("../Resources/vibevoice/vibevoice-tts");
            if bundled.exists() {
                return bundled;
            }
        }
    }
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    std::path::PathBuf::from(home)
        .join(".scriptures")
        .join("vibevoice-tts")
}

/// Split text into sentences (~10-20 words each) for fast synthesis
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
/// First audio within ~3 seconds. Subsequent sentences overlap synthesis + playback.
fn generate_playback_script(sentences: &[String], voice: &str, rate: f32) -> String {
    let rate_mult = format!("{:.2}", rate / 175.0);
    let mut script = String::from("#!/bin/bash\nset -e\n");
    script.push_str(&format!("mkdir -p {}\n", PREFETCH_DIR));

    for (i, sentence) in sentences.iter().enumerate() {
        let escaped = sentence.replace('\'', "'\\''");
        let wav_path = format!("{}/chunk_{:04}.wav", PREFETCH_DIR, i);

        // Synthesize this sentence
        script.push_str(&format!(
            "curl -sN -X POST http://localhost:8095/synthesize \\\n  -H 'Content-Type: application/json' \\\n  -d '{{\"text\":\"{}\",\"voice\":\"{}\"}}' \\\n  -o '{}' 2>/dev/null\n",
            escaped.replace('\"', "\\\"").replace('\n', " "),
            voice,
            wav_path,
        ));

        // Play it immediately (blocks until done, then next sentence starts)
        script.push_str(&format!(
            "[ -f '{}' ] && afplay -r {} '{}' 2>/dev/null\n",
            wav_path, rate_mult, wav_path,
        ));
    }

    // Cleanup
    script.push_str(&format!("rm -rf {}\n", PREFETCH_DIR));
    script
}

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

/// Prefetch first sentence only (for near-instant first play)
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

    if text.is_empty() || !vibevoice_available() {
        return Ok(());
    }

    // Only prefetch the FIRST sentence for fast start
    let sentences = split_into_sentences(&text);
    let first = sentences.first().cloned().unwrap_or_default();
    if first.is_empty() {
        return Ok(());
    }

    let voice_id = voice.unwrap_or_else(|| "en-Emma_woman".to_string());
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
            "http://localhost:8095/synthesize",
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

/// Play chapter: sentence-by-sentence synthesis + playback.
/// First audio within ~3 seconds. Each subsequent sentence synthesized while previous plays.
#[tauri::command]
pub fn read_aloud(
    text: String,
    rate: Option<f32>,
    voice: Option<String>,
    tts: State<TtsState>,
) -> Result<(), String> {
    // Kill existing
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

    if !vibevoice_available() {
        return Err("VibeVoice server not running. Start it from Settings.".to_string());
    }

    let rate_val = rate.unwrap_or(175.0).clamp(50.0, 500.0);
    let voice_id = voice.unwrap_or_else(|| "en-Emma_woman".to_string());

    // Split into sentences for fast first-audio
    let sentences = split_into_sentences(&text);
    if sentences.is_empty() {
        return Ok(());
    }

    // Generate a shell script that synthesizes + plays sentence by sentence
    let script = generate_playback_script(&sentences, &voice_id, rate_val);
    std::fs::write(PLAYBACK_SCRIPT, &script)
        .map_err(|e| format!("Failed to write playback script: {}", e))?;

    // Make executable and run
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
                    // SIGSTOP the entire process group (bash + curl + afplay)
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
    // Cleanup temp files
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

// ── VibeVoice Server Management ──

const VIBEVOICE_BINARY_URL: &str =
    "https://ark-data-bundles.s3.us-west-2.amazonaws.com/vibevoice-tts-macos-arm64";

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

#[tauri::command]
pub fn install_vibevoice() -> Result<Value, String> {
    let path = vibevoice_binary_path();
    let dir = path.parent().ok_or("Invalid path")?;
    std::fs::create_dir_all(dir).map_err(|e| format!("Failed to create dir: {}", e))?;

    if path.exists()
        && path
            .metadata()
            .map(|m| m.len() > 1_000_000)
            .unwrap_or(false)
    {
        return Ok(json!({"status": "already_installed"}));
    }

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

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o755));
    }

    Ok(json!({"status": "installed", "path": path.to_string_lossy()}))
}

#[tauri::command]
pub fn start_vibevoice(tts: State<TtsState>) -> Result<Value, String> {
    if vibevoice_available() {
        return Ok(json!({"status": "already_running"}));
    }

    let path = vibevoice_binary_path();
    if !path.exists() {
        return Err("VibeVoice not installed.".to_string());
    }

    {
        let mut server = tts.vibevoice_server.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = *server {
            let _ = child.kill();
        }
        *server = None;
    }

    let voices_dir = path.parent().unwrap_or(&path).join("voices");
    let child = Command::new(&path)
        .env("VOICES_DIR", voices_dir.to_str().unwrap_or(""))
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start VibeVoice: {}", e))?;

    {
        let mut server = tts.vibevoice_server.lock().map_err(|e| e.to_string())?;
        *server = Some(child);
    }

    for _ in 0..30 {
        std::thread::sleep(std::time::Duration::from_secs(1));
        if vibevoice_available() {
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
