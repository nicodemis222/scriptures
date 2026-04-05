use crate::db::DbState;
use serde_json::{json, Value};
use std::collections::HashSet;
use tauri::State;

/// Helper to call Ollama API via curl with proper timeouts.
/// Returns the parsed JSON response or an error string.
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

/// Retrieve context verses from a specific chapter (owned results).
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

/// Search for relevant verses via FTS5 (owned results, lock released after).
fn fts_search_context(db: &State<DbState>, query: &str) -> Result<Vec<String>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let fts_query = crate::commands::sanitize_fts_query(query);
    let mut stmt = conn
        .prepare(
            "SELECT v.text, v.reference
             FROM scriptures_fts fts
             JOIN verses v ON fts.rowid = v.id
             WHERE scriptures_fts MATCH ?1
             ORDER BY rank
             LIMIT 10",
        )
        .map_err(|e| e.to_string())?;

    let verses: Vec<String> = stmt
        .query_map([&fts_query], |row| {
            let text: String = row.get(0)?;
            let reference: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
            Ok(format!("{}: {}", reference, text))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(verses)
}

/// RAG-augmented query using FTS5 for retrieval and Ollama for generation.
/// DB lock is released BEFORE calling Ollama to avoid blocking other commands.
#[tauri::command]
pub fn ai_query(
    db: State<DbState>,
    prompt: String,
    context_book: Option<String>,
    context_chapter: Option<i64>,
    model: Option<String>,
) -> Result<Value, String> {
    // Step 1: Retrieve context (DB lock acquired and released per call)
    let mut context_verses = Vec::new();
    let mut seen = HashSet::new();

    if let (Some(ref book), Some(chapter)) = (&context_book, context_chapter) {
        for entry in retrieve_chapter_context(&db, book, chapter)? {
            seen.insert(entry.clone());
            context_verses.push(entry);
        }
    }

    let search_terms: String = prompt
        .split_whitespace()
        .take(10)
        .collect::<Vec<_>>()
        .join(" ");
    for entry in fts_search_context(&db, &search_terms)? {
        if seen.insert(entry.clone()) {
            context_verses.push(entry);
        }
    }

    // Step 2: Build augmented prompt (no DB lock held)
    let scripture_context = context_verses.join("\n");
    let augmented_prompt = format!(
        "You are a knowledgeable scripture study assistant. Answer questions about the scriptures \
         with reverence and accuracy. Always cite specific verses when possible.\n\n\
         ## Relevant Scripture Passages:\n{}\n\n\
         ## Question:\n{}\n\n\
         ## Answer:",
        scripture_context, prompt
    );

    // Step 3: Call Ollama (no DB lock held)
    let model_name = model.unwrap_or_else(|| "llama3.2:latest".to_string());
    // Validate model name
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
/// DB lock is released BEFORE calling Ollama.
#[tauri::command]
pub fn ai_explain(db: State<DbState>, verse_id: i64) -> Result<Value, String> {
    // Fetch verse data + surrounding context (lock acquired and released here)
    let (text, reference, book_title, surrounding) = {
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

        // Fetch 2 verses before and after for context
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

        (main.0, main.1, main.2, context_verses.join("\n"))
    }; // conn dropped here — lock released

    let context_section = if surrounding.is_empty() {
        String::new()
    } else {
        format!("\n\nSurrounding verses for context:\n{}", surrounding)
    };

    let prompt = format!(
        "Provide a brief, reverent explanation of this scripture verse. \
         Include historical context and how it applies to daily life.\n\n\
         {}: \"{}\"{}\n\nExplanation:",
        reference, text, context_section
    );

    let request_body = json!({
        "model": "llama3.2:latest",
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
/// Uses translation_cache table to avoid re-translating.
/// Falls back to Ollama LLM for translation.
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
    // Validate target language against allowlist
    const VALID_LANGUAGES: &[&str] = &[
        "Spanish",
        "French",
        "Portuguese",
        "German",
        "Italian",
        "Chinese",
        "Korean",
        "Japanese",
        "Russian",
        "Arabic",
    ];
    if !VALID_LANGUAGES.contains(&target_language.as_str()) {
        return Err(format!("Unsupported language: {}", target_language));
    }

    let conn = db.conn.lock().map_err(|e| e.to_string())?;

    // Get all verses for this chapter
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
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, i64>(1)?,
                row.get::<_, String>(2)?,
            ))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    if verses.is_empty() {
        return Err("No verses found for this chapter".to_string());
    }

    // Check cache — single query for all verses (avoid N+1)
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

    // If all cached, return immediately
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

    // Collect uncached verses for batch translation
    let uncached: Vec<&(i64, i64, String)> = verses
        .iter()
        .filter(|(id, _, _)| !cached.contains_key(id))
        .collect();

    // Build batch translation prompt — translate up to 20 verses at a time
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
        "model": "llama3.2:latest",
        "prompt": prompt,
        "stream": false,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096
        }
    });

    let response = call_ollama("/api/generate", &request_body)?;
    let translated_text = response
        .get("response")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    // Parse translated lines back to verse numbers
    let mut translated_map: std::collections::HashMap<i64, String> =
        std::collections::HashMap::new();
    for line in translated_text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        // Try to match [N] prefix
        if let Some(rest) = line.strip_prefix('[') {
            if let Some(bracket_end) = rest.find(']') {
                if let Ok(vn) = rest[..bracket_end].trim().parse::<i64>() {
                    let text = rest[bracket_end + 1..].trim().to_string();
                    // Find the verse_id for this verse_number
                    if let Some((id, _, _)) = batch.iter().find(|(_, n, _)| *n == vn) {
                        translated_map.insert(*id, text);
                    }
                }
            }
        }
    }

    // Cache the translations (log errors but don't fail the request)
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

    // Merge cached + newly translated
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
