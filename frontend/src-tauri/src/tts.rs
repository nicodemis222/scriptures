use serde_json::{json, Value};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::State;

pub struct TtsState {
    pub process: Mutex<Option<Child>>,
    pub paused: Mutex<bool>,
}

impl TtsState {
    pub fn new() -> Self {
        TtsState {
            process: Mutex::new(None),
            paused: Mutex::new(false),
        }
    }
}

fn sanitize_tts_text(text: &str) -> String {
    text.chars()
        .filter(|c| !c.is_control() || *c == '\n' || *c == ' ')
        .take(50_000)
        .collect()
}

fn validate_voice_name(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 100
        && !name.contains("..")
        && name
            .chars()
            .next()
            .map(|c| c.is_alphanumeric())
            .unwrap_or(false)
        && name
            .chars()
            .all(|c| c.is_alphanumeric() || " ()-_".contains(c))
}

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

fn vibevoice_synthesize(text: &str, voice: Option<&str>) -> Result<String, String> {
    let body = json!({
        "text": text,
        "voice": voice.unwrap_or("en-Emma_woman"),
    });

    let temp_path = std::env::temp_dir().join("scriptures_tts.wav");
    let temp_str = temp_path.to_str().ok_or("Invalid temp path")?.to_string();

    let output = Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "5",
            "--max-time",
            "60",
            "-X",
            "POST",
            "http://localhost:8095/synthesize",
            "-H",
            "Content-Type: application/json",
            "-d",
            &body.to_string(),
            "-o",
            &temp_str,
        ])
        .output()
        .map_err(|e| format!("Failed to call VibeVoice: {}", e))?;

    if !output.status.success() {
        return Err("VibeVoice synthesis failed".to_string());
    }

    let size = std::fs::metadata(&temp_path).map(|m| m.len()).unwrap_or(0);
    if size < 100 {
        return Err("VibeVoice returned empty audio".to_string());
    }

    Ok(temp_str)
}

#[tauri::command]
pub fn list_voices() -> Result<Value, String> {
    let mut voices: Vec<Value> = Vec::new();

    if vibevoice_available() {
        let output = Command::new("curl")
            .args([
                "-s",
                "--connect-timeout",
                "2",
                "http://localhost:8095/voices",
            ])
            .output();

        if let Ok(out) = output {
            if out.status.success() {
                if let Ok(data) = serde_json::from_slice::<Value>(&out.stdout) {
                    if let Some(arr) = data.as_array() {
                        for v in arr {
                            let name = v["voice_id"].as_str().unwrap_or("");
                            let desc = v["description"].as_str().unwrap_or("");
                            if !name.is_empty() {
                                voices.push(json!({
                                    "name": name,
                                    "locale": "vibevoice",
                                    "description": desc,
                                    "engine": "vibevoice",
                                }));
                            }
                        }
                    }
                }
            }
        }
    }

    if cfg!(target_os = "macos") {
        if let Ok(output) = Command::new("say").arg("-v").arg("?").output() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let novelty = [
                "Bad News",
                "Bahh",
                "Bells",
                "Boing",
                "Bubbles",
                "Cellos",
                "Wobble",
                "Whisper",
                "Zarvox",
                "Trinoids",
                "Organ",
                "Jester",
                "Superstar",
                "Deranged",
                "Hyper",
                "Good News",
                "Junior",
                "Ralph",
            ];

            for line in stdout.lines() {
                let line = line.trim();
                if let Some(space_idx) = line.find("  ") {
                    let name = line[..space_idx].trim().to_string();
                    let rest = line[space_idx..].trim();
                    let locale = rest.split_whitespace().next().unwrap_or("").to_string();
                    let is_english = locale.starts_with("en_");
                    let is_novelty = novelty.iter().any(|n| name.contains(n));

                    if is_english && !is_novelty {
                        voices.push(json!({
                            "name": name,
                            "locale": locale,
                            "engine": "system",
                        }));
                    }
                }
            }
        }
    }

    if voices.is_empty() {
        voices.push(json!({"name": "default", "locale": "en_US", "engine": "system"}));
    }

    Ok(json!(voices))
}

#[tauri::command]
pub fn read_aloud(
    text: String,
    rate: Option<f32>,
    voice: Option<String>,
    tts: State<TtsState>,
) -> Result<(), String> {
    // Stop any existing playback (non-blocking)
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

    let rate_val = rate.unwrap_or(175.0).clamp(50.0, 500.0);
    let safe_text = sanitize_tts_text(&text);

    let valid_voice = voice.as_deref().and_then(|v| {
        if v == "default" || v.is_empty() {
            None
        } else if validate_voice_name(v) {
            Some(v)
        } else {
            None
        }
    });

    // Try VibeVoice first
    let child = if vibevoice_available() {
        match vibevoice_synthesize(&safe_text, valid_voice) {
            Ok(wav_path) => {
                if cfg!(target_os = "macos") {
                    Command::new("afplay")
                        .arg("-r")
                        .arg(format!("{:.2}", rate_val / 175.0))
                        .arg(&wav_path)
                        .spawn()
                        .map_err(|e| format!("Failed to play audio: {}", e))?
                } else {
                    Command::new("aplay")
                        .arg(&wav_path)
                        .spawn()
                        .map_err(|e| format!("Failed to play audio: {}", e))?
                }
            }
            Err(_) => spawn_system_tts(&safe_text, rate_val, valid_voice)?,
        }
    } else {
        spawn_system_tts(&safe_text, rate_val, valid_voice)?
    };

    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    *proc = Some(child);
    Ok(())
}

fn spawn_system_tts(text: &str, rate: f32, voice: Option<&str>) -> Result<Child, String> {
    // Write text to temp file to avoid pipe blocking on large chapters
    let temp_path = std::env::temp_dir().join("scriptures_tts_text.txt");
    std::fs::write(&temp_path, text)
        .map_err(|e| format!("Failed to write TTS text file: {}", e))?;

    if cfg!(target_os = "macos") {
        let mut cmd = Command::new("say");
        cmd.arg("-r").arg(rate.to_string());
        if let Some(v) = voice {
            if !v.contains('-') || !v.contains('_') {
                cmd.arg("-v").arg(v);
            }
        }
        // Use -f to read from file (non-blocking, handles any text length)
        cmd.arg("-f").arg(&temp_path);
        let child = cmd
            .spawn()
            .map_err(|e| format!("Failed to start TTS: {}", e))?;
        Ok(child)
    } else if cfg!(target_os = "linux") {
        let mut cmd = Command::new("espeak");
        cmd.arg("-s").arg(rate.to_string());
        cmd.arg("-f").arg(&temp_path);
        let child = cmd
            .spawn()
            .map_err(|e| format!("Failed to start TTS (espeak): {}", e))?;
        Ok(child)
    } else {
        Err("TTS not supported on this platform".to_string())
    }
}

/// Pause TTS playback using SIGSTOP (freezes the process without killing it)
#[tauri::command]
pub fn pause_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        // Only send signal if process is still running
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

/// Resume TTS playback using SIGCONT (unfreezes the process)
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

#[tauri::command]
pub fn stop_reading(tts: State<TtsState>) -> Result<(), String> {
    let mut proc = tts.process.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut child) = *proc {
        // Resume first if paused (so kill works)
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
            Err(e) => {
                eprintln!("[tts] try_wait error: {}", e);
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
                // Fallback: official install script
                let output = Command::new("sh")
                    .arg("-c")
                    .arg("curl -fsSL https://ollama.com/install.sh | sh")
                    .output()
                    .map_err(|e| format!("Install failed: {}", e))?;

                if output.status.success() {
                    Ok(json!({"status": "installed", "method": "curl"}))
                } else {
                    let err = String::from_utf8_lossy(&output.stderr);
                    Err(format!("Install failed: {}", err))
                }
            }
        }
    } else if cfg!(target_os = "linux") {
        let output = Command::new("sh")
            .arg("-c")
            .arg("curl -fsSL https://ollama.com/install.sh | sh")
            .output()
            .map_err(|e| format!("Install failed: {}", e))?;

        if output.status.success() {
            Ok(json!({"status": "installed", "method": "curl"}))
        } else {
            let err = String::from_utf8_lossy(&output.stderr);
            Err(format!("Install failed: {}", err))
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

    Ok(json!({
        "status": if running_now { "started" } else { "starting" },
    }))
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
        let err = String::from_utf8_lossy(&output.stderr);
        Err(format!("Pull failed: {}", err))
    }
}
