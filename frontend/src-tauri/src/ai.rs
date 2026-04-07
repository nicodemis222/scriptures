use crate::db::DbState;
use serde_json::{json, Value};
use std::collections::HashSet;
use tauri::State;

/// Helper to call Ollama API via curl with proper timeouts.
fn call_ollama(endpoint: &str, body: &Value) -> Result<Value, String> {
    let url = format!("http://localhost:11434{}", endpoint);
    let output = std::process::Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "5",
            "--max-time",
            "120",
            "-X",
            "POST",
            &url,
            "-H",
            "Content-Type: application/json",
            "-d",
            &body.to_string(),
        ])
        .output()
        .map_err(|e| format!("Failed to call Ollama: {}. Is curl installed?", e))?;

    if !output.status.success() {
        return Err("Ollama request failed. Is Ollama running?".to_string());
    }

    let response_body = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&response_body)
        .map_err(|e| format!("Failed to parse Ollama response: {}", e))
}

/// Check if Ollama is running and available
#[tauri::command]
pub fn check_ollama_status() -> Result<Value, String> {
    let output = std::process::Command::new("curl")
        .args([
            "-s",
            "--connect-timeout",
            "2",
            "--max-time",
            "5",
            "http://localhost:11434/api/tags",
        ])
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let body = String::from_utf8_lossy(&out.stdout);
            match serde_json::from_str::<Value>(&body) {
                Ok(data) => Ok(json!({
                    "available": true,
                    "models": data.get("models").cloned().unwrap_or(json!([]))
                })),
                Err(_) => Ok(json!({"available": false, "models": []})),
            }
        }
        _ => Ok(json!({"available": false, "models": []})),
    }
}

// ── Ollama Management ──

/// Find the ollama binary, checking multiple locations.
fn find_ollama() -> Option<String> {
    let candidates = [
        "/usr/local/bin/ollama",
        "/opt/homebrew/bin/ollama",
        "/Applications/Ollama.app/Contents/Resources/ollama",
    ];
    // Check PATH first
    if let Ok(output) = std::process::Command::new("which").arg("ollama").output() {
        if output.status.success() {
            let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !path.is_empty() {
                return Some(path);
            }
        }
    }
    // Check known locations
    for path in &candidates {
        if std::path::Path::new(path).exists() {
            return Some(path.to_string());
        }
    }
    None
}

fn ollama_api_available() -> bool {
    std::process::Command::new("curl")
        .args(["-s", "--connect-timeout", "1", "http://localhost:11434/api/tags"])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

#[tauri::command]
pub fn check_ollama_installed() -> Result<Value, String> {
    let installed = find_ollama().is_some();
    let running = ollama_api_available();
    Ok(json!({"installed": installed, "running": running}))
}

#[tauri::command]
pub fn install_ollama() -> Result<Value, String> {
    if find_ollama().is_some() {
        return Ok(json!({"status": "already_installed"}));
    }
    if cfg!(target_os = "macos") {
        // Try brew first
        match std::process::Command::new("brew")
            .args(["install", "ollama"])
            .output()
        {
            Ok(o) if o.status.success() => Ok(json!({"status": "installed", "method": "brew"})),
            _ => {
                // Download Ollama.app directly (avoids sudo symlink issue)
                let script = r#"
                    cd /tmp
                    curl -fsSL -o ollama-darwin.tgz https://ollama.com/download/Ollama-darwin.zip 2>/dev/null \
                    || curl -fsSL -o ollama-darwin.tgz https://github.com/ollama/ollama/releases/latest/download/Ollama-darwin.zip
                    if [ -f ollama-darwin.tgz ]; then
                        rm -rf /Applications/Ollama.app
                        unzip -o ollama-darwin.tgz -d /Applications/ 2>/dev/null
                        rm -f ollama-darwin.tgz
                    fi
                "#;
                let output = std::process::Command::new("sh")
                    .arg("-c")
                    .arg(script)
                    .output()
                    .map_err(|e| format!("Install failed: {}", e))?;

                // Verify it worked
                if std::path::Path::new("/Applications/Ollama.app/Contents/Resources/ollama").exists() {
                    Ok(json!({"status": "installed", "method": "direct"}))
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
    if ollama_api_available() {
        return Ok(json!({"status": "already_running"}));
    }
    let ollama = find_ollama().ok_or("Ollama not found. Click Install first.")?;
    let _child = std::process::Command::new(&ollama)
        .arg("serve")
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start: {}", e))?;
    std::thread::sleep(std::time::Duration::from_secs(2));
    let running = ollama_api_available();
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
    let ollama = find_ollama().ok_or("Ollama not found. Click Install first.")?;
    let output = std::process::Command::new(&ollama)
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

// ── RAG Retrieval ──

/// Retrieve verses from the current chapter (highest priority context).
fn retrieve_chapter_context(
    db: &State<DbState>,
    book: &str,
    chapter: i64,
) -> Result<Vec<String>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT v.text, v.reference FROM verses v
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             WHERE b.title = ?1 AND c.chapter_number = ?2
             ORDER BY v.verse_number LIMIT 20",
        )
        .map_err(|e| e.to_string())?;

    let verses: Vec<String> = stmt
        .query_map(rusqlite::params![book, chapter], |row| {
            let text: String = row.get(0)?;
            let reference: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
            Ok(format!("{}: {}", reference, text))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(verses)
}

/// FTS5 search scoped to a specific book (same book, other chapters).
fn fts_search_book(db: &State<DbState>, query: &str, book: &str, limit: usize) -> Result<Vec<String>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let fts_query = crate::commands::sanitize_fts_query(query);
    let mut stmt = conn
        .prepare(
            "SELECT v.text, v.reference
             FROM scriptures_fts fts
             JOIN verses v ON fts.rowid = v.id
             WHERE scriptures_fts MATCH ?1
               AND fts.book_title = ?2
             ORDER BY rank
             LIMIT ?3",
        )
        .map_err(|e| e.to_string())?;

    let verses: Vec<String> = stmt
        .query_map(rusqlite::params![&fts_query, book, limit as i64], |row| {
            let text: String = row.get(0)?;
            let reference: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
            Ok(format!("{}: {}", reference, text))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(verses)
}

/// FTS5 search scoped to a specific volume (same volume, other books).
fn fts_search_volume(db: &State<DbState>, query: &str, book: &str, limit: usize) -> Result<Vec<String>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let fts_query = crate::commands::sanitize_fts_query(query);

    // First find the volume for this book
    let volume_title: String = conn
        .query_row(
            "SELECT vol.title FROM books b
             JOIN volumes vol ON b.volume_id = vol.id
             WHERE b.title = ?1 LIMIT 1",
            [book],
            |row| row.get(0),
        )
        .unwrap_or_default();

    if volume_title.is_empty() {
        return Ok(Vec::new());
    }

    let mut stmt = conn
        .prepare(
            "SELECT v.text, v.reference
             FROM scriptures_fts fts
             JOIN verses v ON fts.rowid = v.id
             WHERE scriptures_fts MATCH ?1
               AND fts.volume_title = ?2
               AND fts.book_title != ?3
             ORDER BY rank
             LIMIT ?4",
        )
        .map_err(|e| e.to_string())?;

    let verses: Vec<String> = stmt
        .query_map(rusqlite::params![&fts_query, &volume_title, book, limit as i64], |row| {
            let text: String = row.get(0)?;
            let reference: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
            Ok(format!("{}: {}", reference, text))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(verses)
}

/// FTS5 search across ALL volumes (global cross-canon search).
fn fts_search_global(db: &State<DbState>, query: &str, exclude_volume: &str, limit: usize) -> Result<Vec<String>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let fts_query = crate::commands::sanitize_fts_query(query);

    let mut stmt = if exclude_volume.is_empty() {
        conn.prepare(
            "SELECT v.text, v.reference
             FROM scriptures_fts fts
             JOIN verses v ON fts.rowid = v.id
             WHERE scriptures_fts MATCH ?1
             ORDER BY rank
             LIMIT ?2",
        )
        .map_err(|e| e.to_string())?
    } else {
        conn.prepare(
            "SELECT v.text, v.reference
             FROM scriptures_fts fts
             JOIN verses v ON fts.rowid = v.id
             WHERE scriptures_fts MATCH ?1
               AND fts.volume_title != ?2
             ORDER BY rank
             LIMIT ?3",
        )
        .map_err(|e| e.to_string())?
    };

    let verses: Vec<String> = if exclude_volume.is_empty() {
        stmt.query_map(rusqlite::params![&fts_query, limit as i64], |row| {
            let text: String = row.get(0)?;
            let reference: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
            Ok(format!("{}: {}", reference, text))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?
    } else {
        stmt.query_map(rusqlite::params![&fts_query, exclude_volume, limit as i64], |row| {
            let text: String = row.get(0)?;
            let reference: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
            Ok(format!("{}: {}", reference, text))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?
    };

    Ok(verses)
}

/// Look up the volume title for a given book.
fn get_volume_for_book(db: &State<DbState>, book: &str) -> String {
    let conn = match db.conn.lock() {
        Ok(c) => c,
        Err(_) => return String::new(),
    };
    conn.query_row(
        "SELECT vol.title FROM books b JOIN volumes vol ON b.volume_id = vol.id WHERE b.title = ?1 LIMIT 1",
        [book],
        |row| row.get(0),
    )
    .unwrap_or_default()
}

/// RAG-augmented query with tiered cross-canon retrieval.
/// Priority: current chapter > same book > same volume > all other volumes.
/// DB lock is released BEFORE calling Ollama.
#[tauri::command]
pub fn ai_query(
    db: State<DbState>,
    prompt: String,
    context_book: Option<String>,
    context_chapter: Option<i64>,
    model: Option<String>,
) -> Result<Value, String> {
    let mut context_verses = Vec::new();
    let mut seen = HashSet::new();

    let search_terms: String = prompt
        .split_whitespace()
        .take(10)
        .collect::<Vec<_>>()
        .join(" ");

    let volume_title = context_book
        .as_ref()
        .map(|b| get_volume_for_book(&db, b))
        .unwrap_or_default();

    // Tier 1: Current chapter verses (up to 20)
    if let (Some(ref book), Some(chapter)) = (&context_book, context_chapter) {
        for entry in retrieve_chapter_context(&db, book, chapter).unwrap_or_default() {
            seen.insert(entry.clone());
            context_verses.push(entry);
        }
    }

    // Tier 2: Same book, other chapters via FTS (up to 8)
    if let Some(ref book) = context_book {
        for entry in fts_search_book(&db, &search_terms, book, 8).unwrap_or_default() {
            if seen.insert(entry.clone()) {
                context_verses.push(entry);
            }
        }
    }

    // Tier 3: Same volume, other books via FTS (up to 6)
    if let Some(ref book) = context_book {
        for entry in fts_search_volume(&db, &search_terms, book, 6).unwrap_or_default() {
            if seen.insert(entry.clone()) {
                context_verses.push(entry);
            }
        }
    }

    // Tier 4: All other volumes via FTS (up to 6)
    for entry in fts_search_global(&db, &search_terms, &volume_title, 6).unwrap_or_default() {
        if seen.insert(entry.clone()) {
            context_verses.push(entry);
        }
    }

    // Build augmented prompt (no DB lock held)
    let scripture_context = context_verses.join("\n");
    let augmented_prompt = format!(
        "You are a knowledgeable scripture study assistant with access to the Book of Mormon, \
         Holy Bible (KJV), Doctrine & Covenants, Pearl of Great Price, Coptic Bible, \
         Dead Sea Scrolls, Russian Orthodox texts, Ancient Witnesses, and Hymns.\n\n\
         Answer questions with reverence and accuracy. Cite specific verses when possible. \
         Draw connections across different scripture volumes when relevant.\n\n\
         ## Relevant Scripture Passages:\n{}\n\n\
         ## Question:\n{}\n\n\
         ## Answer:",
        scripture_context, prompt
    );

    // Call Ollama (no DB lock held)
    let model_name = model.unwrap_or_else(|| "qwen2.5:latest".to_string());
    if model_name.len() > 64
        || !model_name
            .chars()
            .all(|c| c.is_alphanumeric() || ":.-_".contains(c))
    {
        return Err("Invalid model name".to_string());
    }
    let request_body = json!({
        "model": model_name,
        "prompt": augmented_prompt,
        "stream": false,
        "options": {
            "temperature": 0.3,
            "num_predict": 1024
        }
    });

    let response = call_ollama("/api/generate", &request_body)?;

    Ok(json!({
        "response": response.get("response").cloned().unwrap_or(json!("")),
        "model": model_name,
        "context_verses_used": context_verses.len(),
    }))
}

/// Explain a specific verse using the local LLM.
/// Includes surrounding verses + cross-reference search for richer context.
/// DB lock is released BEFORE calling Ollama.
#[tauri::command]
pub fn ai_explain(db: State<DbState>, verse_id: i64) -> Result<Value, String> {
    let (text, reference, book_title, surrounding, cross_refs) = {
        let conn = db.conn.lock().map_err(|e| e.to_string())?;
        let main = conn.query_row(
            "SELECT v.text, v.reference, b.title, v.chapter_id, v.verse_number
             FROM verses v
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             WHERE v.id = ?1",
            [verse_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, Option<String>>(1)?.unwrap_or_default(),
                    row.get::<_, String>(2)?,
                    row.get::<_, i64>(3)?,
                    row.get::<_, i64>(4)?,
                ))
            },
        )
        .map_err(|e| e.to_string())?;

        // Fetch 2 verses before and after
        let mut stmt = conn
            .prepare(
                "SELECT v.verse_number, v.text FROM verses v
                 WHERE v.chapter_id = ?1
                   AND v.verse_number BETWEEN ?2 AND ?3
                   AND v.id != ?4
                 ORDER BY v.verse_number",
            )
            .map_err(|e| e.to_string())?;
        let context_verses: Vec<String> = stmt
            .query_map(
                rusqlite::params![main.3, main.4 - 2, main.4 + 2, verse_id],
                |row| {
                    Ok(format!(
                        "v{}: {}",
                        row.get::<_, i64>(0)?,
                        row.get::<_, String>(1)?
                    ))
                },
            )
            .map_err(|e| e.to_string())?
            .filter_map(|r| r.ok())
            .collect();

        // Cross-reference: search for key terms across all volumes
        let key_words: String = main.0
            .split_whitespace()
            .filter(|w| w.len() > 4)
            .take(5)
            .collect::<Vec<_>>()
            .join(" ");
        let fts_query = crate::commands::sanitize_fts_query(&key_words);
        let cross: Vec<String> = if !key_words.is_empty() {
            let mut fts_stmt = conn
                .prepare(
                    "SELECT v.text, v.reference
                     FROM scriptures_fts fts
                     JOIN verses v ON fts.rowid = v.id
                     WHERE scriptures_fts MATCH ?1
                       AND v.id != ?2
                     ORDER BY rank
                     LIMIT 5",
                )
                .map_err(|e| e.to_string())?;
            let results: Vec<String> = fts_stmt
                .query_map(rusqlite::params![&fts_query, verse_id], |row| {
                    let t: String = row.get(0)?;
                    let r: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
                    Ok(format!("{}: {}", r, t))
                })
                .map_err(|e| e.to_string())?
                .filter_map(|r| r.ok())
                .collect();
            results
        } else {
            Vec::new()
        };

        (main.0, main.1, main.2, context_verses.join("\n"), cross.join("\n"))
    }; // conn dropped — lock released

    let context_section = if surrounding.is_empty() {
        String::new()
    } else {
        format!("\n\nSurrounding verses:\n{}", surrounding)
    };

    let cross_ref_section = if cross_refs.is_empty() {
        String::new()
    } else {
        format!("\n\nRelated passages from other scriptures:\n{}", cross_refs)
    };

    let prompt = format!(
        "Provide a brief, reverent explanation of this scripture verse. \
         Include historical context, how it applies to daily life, and \
         connections to related passages in other scripture volumes.\n\n\
         {}: \"{}\"{}{}\n\nExplanation:",
        reference, text, context_section, cross_ref_section
    );

    let request_body = json!({
        "model": "qwen2.5:latest",
        "prompt": prompt,
        "stream": false,
        "options": { "temperature": 0.3, "num_predict": 512 }
    });

    let response = call_ollama("/api/generate", &request_body)?;

    Ok(json!({
        "verse_reference": reference,
        "verse_text": text,
        "book_title": book_title,
        "explanation": response.get("response").cloned().unwrap_or(json!("")),
    }))
}

/// Translate a chapter of verses to a target language.
#[tauri::command]
pub fn translate_chapter(
    db: State<DbState>,
    book: String,
    chapter: i64,
    target_language: String,
) -> Result<Value, String> {
    if target_language == "English" {
        return Err("Already in English".to_string());
    }
    const VALID_LANGUAGES: &[&str] = &[
        "Spanish", "French", "Portuguese", "German", "Italian",
        "Chinese", "Korean", "Japanese", "Russian", "Arabic",
    ];
    if !VALID_LANGUAGES.contains(&target_language.as_str()) {
        return Err(format!("Unsupported language: {}", target_language));
    }

    let conn = db.conn.lock().map_err(|e| e.to_string())?;

    let mut stmt = conn
        .prepare(
            "SELECT v.id, v.verse_number, v.text
             FROM verses v
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             WHERE b.title = ?1 AND c.chapter_number = ?2
             ORDER BY v.verse_number",
        )
        .map_err(|e| e.to_string())?;

    let verses: Vec<(i64, i64, String)> = stmt
        .query_map(rusqlite::params![&book, chapter], |row| {
            Ok((row.get(0)?, row.get(1)?, row.get(2)?))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    if verses.is_empty() {
        return Err("No verses found for this chapter".to_string());
    }

    // Check cache
    let mut cached: std::collections::HashMap<i64, String> = std::collections::HashMap::new();
    let verse_ids: Vec<i64> = verses.iter().map(|(id, _, _)| *id).collect();
    if !verse_ids.is_empty() {
        let placeholders: String = verse_ids.iter().map(|_| "?").collect::<Vec<_>>().join(",");
        let sql = format!(
            "SELECT verse_id, translated_text FROM translation_cache WHERE language = ? AND verse_id IN ({})",
            placeholders
        );
        let mut cache_stmt = conn.prepare(&sql).map_err(|e| e.to_string())?;
        let mut params: Vec<Box<dyn rusqlite::types::ToSql>> =
            vec![Box::new(target_language.clone())];
        for vid in &verse_ids {
            params.push(Box::new(*vid));
        }
        let param_refs: Vec<&dyn rusqlite::types::ToSql> =
            params.iter().map(|p| p.as_ref()).collect();
        let rows = cache_stmt
            .query_map(param_refs.as_slice(), |row| {
                Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?))
            })
            .map_err(|e| e.to_string())?;
        for (vid, text) in rows.flatten() {
            cached.insert(vid, text);
        }
    }

    if cached.len() == verses.len() {
        let results: Vec<Value> = verses
            .iter()
            .map(|(id, vn, _)| {
                json!({
                    "verse_id": id,
                    "verse_number": vn,
                    "translated_text": cached.get(id).unwrap_or(&String::new()),
                })
            })
            .collect();
        return Ok(json!({"translations": results, "from_cache": true}));
    }

    let uncached: Vec<&(i64, i64, String)> = verses
        .iter()
        .filter(|(id, _, _)| !cached.contains_key(id))
        .collect();

    let batch_size = 20.min(uncached.len());
    let batch = &uncached[..batch_size];
    let verses_text: String = batch
        .iter()
        .map(|(_, vn, text)| format!("[{}] {}", vn, text))
        .collect::<Vec<_>>()
        .join("\n");

    // Release DB lock before calling Ollama
    drop(stmt);
    drop(conn);

    let prompt = format!(
        "Translate the following scripture verses to {}. \
         Preserve the verse numbers in brackets. \
         Output ONLY the translations, one per line, keeping [N] prefix.\n\n{}",
        target_language, verses_text
    );

    let request_body = json!({
        "model": "qwen2.5:latest",
        "prompt": prompt,
        "stream": false,
        "options": { "temperature": 0.1, "num_predict": 4096 }
    });

    let response = call_ollama("/api/generate", &request_body)?;
    let translated_text = response
        .get("response")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    let mut translated_map: std::collections::HashMap<i64, String> =
        std::collections::HashMap::new();
    for line in translated_text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(rest) = line.strip_prefix('[') {
            if let Some(bracket_end) = rest.find(']') {
                if let Ok(vn) = rest[..bracket_end].trim().parse::<i64>() {
                    let text = rest[bracket_end + 1..].trim().to_string();
                    if let Some((id, _, _)) = batch.iter().find(|(_, n, _)| *n == vn) {
                        translated_map.insert(*id, text);
                    }
                }
            }
        }
    }

    {
        let conn = db.conn.lock().map_err(|e| e.to_string())?;
        for (vid, text) in &translated_map {
            if let Err(e) = conn.execute(
                "INSERT OR REPLACE INTO translation_cache (verse_id, language, translated_text) VALUES (?1, ?2, ?3)",
                rusqlite::params![vid, &target_language, text],
            ) {
                eprintln!("[translate] Cache write failed for verse {}: {}", vid, e);
            }
        }
    }

    let mut all_translations = cached;
    all_translations.extend(translated_map);

    let results: Vec<Value> = verses
        .iter()
        .map(|(id, vn, original)| {
            json!({
                "verse_id": id,
                "verse_number": vn,
                "translated_text": all_translations.get(id).unwrap_or(original),
            })
        })
        .collect();

    Ok(json!({"translations": results, "from_cache": false}))
}
