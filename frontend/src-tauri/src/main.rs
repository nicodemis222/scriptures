#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod ai;
mod bundles;
mod commands;
mod db;
mod tts;

use tauri::Manager;

fn main() {
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
            tts::is_vibevoice_installed,
            tts::install_vibevoice,
            tts::start_vibevoice,
            tts::check_ollama_installed,
            tts::install_ollama,
            tts::start_ollama,
            tts::pull_ollama_model,
            // AI
            ai::check_ollama_status,
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
