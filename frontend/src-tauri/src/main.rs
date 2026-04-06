#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod ai;
mod bundles;
mod commands;
mod db;
mod tts;

use tauri::Manager;

const APP_VERSION: &str = env!("CARGO_PKG_VERSION");
const BUNDLE_ID: &str = "com.scriptures.app";

/// Clear stale caches when app version changes (ensures clean upgrade).
fn clear_caches_on_upgrade() {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let version_file = format!("{}/.scriptures/last_version", home);

    // Read last version
    let last_version = std::fs::read_to_string(&version_file).unwrap_or_default();
    let last_version = last_version.trim();

    if last_version == APP_VERSION {
        return; // Same version, no cleanup needed
    }

    // Version changed (or first install) — clear caches
    eprintln!(
        "[upgrade] Version changed: {} → {}. Clearing caches.",
        if last_version.is_empty() { "fresh" } else { last_version },
        APP_VERSION
    );

    // Clear Tauri WebKit/webview caches and Application Support webview data
    for dir in [
        format!("{}/Library/WebKit/{}", home, BUNDLE_ID),
        format!("{}/Library/Caches/{}", home, BUNDLE_ID),
        format!("{}/Library/WebKit/com.scriptures.app", home),
        format!("{}/Library/Caches/com.scriptures.app", home),
        format!("{}/Library/Application Support/{}/EBWebView", home, BUNDLE_ID),
        format!("{}/Library/Application Support/com.scriptures.app/EBWebView", home),
    ] {
        let _ = std::fs::remove_dir_all(&dir);
    }

    // Reset launch services to clear any cached app metadata
    let _ = std::process::Command::new("sh")
        .arg("-c")
        .arg("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local 2>/dev/null")
        .output();

    // Clear TTS temp files from previous sessions
    let _ = std::fs::remove_dir_all("/tmp/scriptures_tts_chunks");

    // Kill any stale processes from old version
    let _ = std::process::Command::new("sh")
        .arg("-c")
        .arg("pkill -9 -f 'afplay.*/tmp/scriptures_tts_chunks' 2>/dev/null; lsof -ti:8095 | xargs kill -9 2>/dev/null")
        .output();

    // Write current version
    let dir = format!("{}/.scriptures", home);
    let _ = std::fs::create_dir_all(&dir);
    let _ = std::fs::write(&version_file, APP_VERSION);
}

fn main() {
    clear_caches_on_upgrade();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let db_state = db::init_db(app.handle())?;
            app.manage(db_state);
            app.manage(tts::TtsState::new());
            // Start Piper TTS server in background so voices are ready
            let tts_state = app.state::<tts::TtsState>();
            tts::start_piper_on_launch(tts_state);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Scripture commands
            commands::get_volumes,
            commands::get_books,
            commands::get_chapter,
            commands::get_verse,
            commands::search_scriptures,
            // Hymn commands
            commands::get_hymns,
            commands::search_hymns,
            commands::get_hymn,
            // Talk commands
            commands::get_related_talks,
            commands::search_talks,
            // Stats & bundles
            commands::get_volume_stats,
            bundles::list_bundles,
            // Highlight commands
            commands::add_highlight,
            commands::remove_highlight,
            commands::get_highlights_for_chapter,
            // Note commands
            commands::add_note,
            commands::update_note,
            commands::delete_note,
            commands::get_notes_for_chapter,
            // Reading progress
            commands::save_reading_progress,
            commands::get_reading_progress,
            // Settings
            commands::get_setting,
            commands::set_setting,
            // Study view
            commands::get_all_highlights,
            commands::get_all_notes,
            // TTS
            tts::list_voices,
            tts::prefetch_audio,
            tts::is_prefetch_ready,
            tts::read_aloud,
            tts::pause_reading,
            tts::resume_reading,
            tts::stop_reading,
            tts::is_reading,
            // AI + Ollama management
            ai::check_ollama_status,
            ai::check_ollama_installed,
            ai::install_ollama,
            ai::start_ollama,
            ai::pull_ollama_model,
            ai::ai_query,
            ai::ai_explain,
            ai::translate_chapter,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(tts) = app.try_state::<tts::TtsState>() {
                    // Signal cancellation to playback thread
                    tts.cancelled.store(true, std::sync::atomic::Ordering::Relaxed);
                    tts.paused.store(false, std::sync::atomic::Ordering::Relaxed);
                    // Kill current afplay
                    if let Ok(mut proc) = tts.process.lock() {
                        if let Some(ref mut child) = *proc {
                            let _ = child.kill();
                        }
                        *proc = None;
                    }
                    if let Ok(mut pf) = tts.prefetch.lock() {
                        if let Some(ref mut child) = *pf {
                            let _ = child.kill();
                        }
                        *pf = None;
                    }
                    if let Ok(mut srv) = tts.piper_server.lock() {
                        if let Some(ref mut child) = *srv {
                            let _ = child.kill();
                        }
                        *srv = None;
                    }
                }
                // Kill any orphaned afplay and Piper server
                let _ = std::process::Command::new("sh")
                    .arg("-c")
                    .arg("pkill -9 -f 'afplay.*/tmp/scriptures_tts_chunks' 2>/dev/null; lsof -ti:8095 | xargs kill -9 2>/dev/null")
                    .status();
                let _ = std::fs::remove_dir_all("/tmp/scriptures_tts_chunks");
            }
        });
}
