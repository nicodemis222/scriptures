use crate::db::DbState;
use serde_json::{json, Value};
use tauri::State;

/// Sanitize FTS5 query input to prevent query syntax abuse.
/// Tokenizes on whitespace, quotes each token as a phrase, and ANDs them.
/// `faith hope` becomes `"faith" AND "hope"` so verses containing both
/// (in any order) match, while users cannot inject FTS5 operators.
/// Falls back to a single quoted phrase if there are no tokens after split.
pub fn sanitize_fts_query(q: &str) -> String {
    let trimmed: String = q.chars().take(500).collect();
    let tokens: Vec<String> = trimmed
        .split_whitespace()
        .filter(|t| !t.is_empty())
        .map(|t| {
            // Strip characters FTS5 treats as syntax (quotes, parens, asterisk,
            // colon, AND/OR/NOT can only be neutralised by quoting). We keep
            // the token's letters, digits, and a small set of safe punctuation.
            let safe: String = t
                .chars()
                .filter(|c| c.is_alphanumeric() || matches!(c, '-' | '\'' | '&'))
                .collect();
            safe
        })
        .filter(|t| !t.is_empty())
        .map(|t| format!("\"{}\"", t.replace('"', "\"\"")))
        .collect();
    if tokens.is_empty() {
        // Empty after sanitisation — return a phrase that matches nothing safely.
        return "\"\"".to_string();
    }
    tokens.join(" AND ")
}

#[tauri::command]
pub fn get_volumes(db: State<DbState>) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT id, title, abbreviation, description FROM volumes ORDER BY id")
        .map_err(|e| e.to_string())?;

    let volumes: Vec<Value> = stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "title": row.get::<_, String>(1)?,
                "abbreviation": row.get::<_, String>(2)?,
                "description": row.get::<_, Option<String>>(3)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(volumes))
}

#[tauri::command]
pub fn get_books(db: State<DbState>, volume: String) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT b.id, b.title, b.book_order, b.num_chapters, v.title as volume_title
             FROM books b JOIN volumes v ON b.volume_id = v.id
             WHERE v.abbreviation = ?1
             ORDER BY b.book_order",
        )
        .map_err(|e| e.to_string())?;

    let books: Vec<Value> = stmt
        .query_map([&volume], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "title": row.get::<_, String>(1)?,
                "book_order": row.get::<_, i64>(2)?,
                "num_chapters": row.get::<_, i64>(3)?,
                "volume_title": row.get::<_, String>(4)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(books))
}

#[tauri::command]
pub fn get_chapter(db: State<DbState>, book: String, chapter: i64) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT v.id, v.verse_number, v.text, v.reference, b.title as book_title,
                vol.title as volume_title, c.chapter_number
             FROM verses v
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             JOIN volumes vol ON b.volume_id = vol.id
             WHERE b.title = ?1 AND c.chapter_number = ?2
             ORDER BY v.verse_number",
        )
        .map_err(|e| e.to_string())?;

    let verses: Vec<Value> = stmt
        .query_map(rusqlite::params![&book, chapter], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "verse_number": row.get::<_, i64>(1)?,
                "text": row.get::<_, String>(2)?,
                "reference": row.get::<_, Option<String>>(3)?,
                "book_title": row.get::<_, String>(4)?,
                "volume_title": row.get::<_, String>(5)?,
                "chapter_number": row.get::<_, i64>(6)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(verses))
}

/// Resolve a free-text scripture reference like "Alma 32", "John 3:16",
/// "1 Nephi 3:7", "D&C 76", or just "Genesis" into a canonical
/// {found, book_title, chapter, verse, volume_title}. Powers go-to-reference:
/// the search bar tries this BEFORE a keyword search so a reference jumps
/// straight to the chapter. No regex crate needed — manual token parse.
#[tauri::command]
pub fn resolve_reference(db: State<DbState>, query: String) -> Result<Value, String> {
    let q = query.trim();
    if q.is_empty() {
        return Ok(json!({"found": false}));
    }

    // Split trailing "<chapter>" or "<chapter>:<verse>" off the end.
    let tokens: Vec<&str> = q.split_whitespace().collect();
    let (book_part, chapter, verse): (String, i64, Option<i64>) = {
        let last = *tokens.last().unwrap();
        let parse_ch_vs = |s: &str| -> Option<(i64, Option<i64>)> {
            let mut it = s.splitn(2, ':');
            let ch = it.next()?.parse::<i64>().ok()?;
            let vs = match it.next() {
                Some(v) => Some(v.parse::<i64>().ok()?),
                None => None,
            };
            Some((ch, vs))
        };
        if tokens.len() >= 2 {
            if let Some((ch, vs)) = parse_ch_vs(last) {
                (tokens[..tokens.len() - 1].join(" "), ch, vs)
            } else {
                // No trailing number → treat whole thing as a book, chapter 1.
                (q.to_string(), 1, None)
            }
        } else if let Some((ch, _)) = parse_ch_vs(last) {
            // A bare number alone isn't a reference.
            let _ = ch;
            return Ok(json!({"found": false}));
        } else {
            (q.to_string(), 1, None)
        }
    };

    // Common aliases that prefix-matching won't catch.
    let bp_lower = book_part.to_lowercase();
    let alias = match bp_lower.as_str() {
        "d&c" | "dc" | "d and c" => Some("Doctrine and Covenants"),
        "jst" => Some("Joseph Smith Translation"),
        _ => None,
    };

    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    // Match: exact (case-insensitive) first, then shortest title that starts
    // with the query (so "Alma"→Alma, "1 Ne"→1 Nephi, "Gen"→Genesis).
    let book_title: Option<String> = conn
        .query_row(
            "SELECT b.title FROM books b
             WHERE LOWER(b.title) = LOWER(?1) OR LOWER(b.title) LIKE LOWER(?1) || '%'
             ORDER BY (LOWER(b.title) = LOWER(?1)) DESC, LENGTH(b.title) ASC
             LIMIT 1",
            [alias.unwrap_or(book_part.as_str())],
            |r| r.get(0),
        )
        .ok();

    let book_title = match book_title {
        Some(b) => b,
        None => return Ok(json!({"found": false})),
    };

    // Verify the chapter exists for this book; grab its volume.
    let row: Option<(String, i64)> = conn
        .query_row(
            "SELECT vol.title, c.chapter_number
             FROM chapters c JOIN books b ON c.book_id = b.id
             JOIN volumes vol ON b.volume_id = vol.id
             WHERE b.title = ?1 AND c.chapter_number = ?2
             LIMIT 1",
            rusqlite::params![&book_title, chapter],
            |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?)),
        )
        .ok();

    match row {
        Some((volume, ch)) => Ok(json!({
            "found": true,
            "book_title": book_title,
            "chapter": ch,
            "verse": verse,
            "volume_title": volume,
        })),
        None => Ok(json!({"found": false})),
    }
}

/// A deterministic "verse of the day" rotating through a curated list of
/// well-known passages (changes daily, same for everyone on a given date).
#[tauri::command]
pub fn daily_verse(db: State<DbState>) -> Result<Value, String> {
    const FEATURED: &[&str] = &[
        "John 3:16", "Alma 32:21", "1 Nephi 3:7", "Proverbs 3:5", "Psalms 23:1",
        "Matthew 11:28", "Moroni 10:4", "2 Nephi 2:25", "Philippians 4:13",
        "Joshua 1:9", "Isaiah 40:31", "Romans 8:28", "Jeremiah 29:11",
        "Mosiah 2:17", "Doctrine and Covenants 6:36", "Ether 12:27",
        "Matthew 5:16", "Psalms 46:1", "Joshua 24:15", "3 Nephi 11:11",
    ];
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let day: i64 = conn
        .query_row("SELECT CAST(julianday('now','localtime') AS INTEGER)", [], |r| r.get(0))
        .unwrap_or(0);
    let reference = FEATURED[(day.rem_euclid(FEATURED.len() as i64)) as usize];

    conn.query_row(
        "SELECT v.id, v.verse_number, v.text, v.reference, b.title, vol.title, c.chapter_number
         FROM verses v
         JOIN chapters c ON v.chapter_id = c.id
         JOIN books b ON c.book_id = b.id
         JOIN volumes vol ON b.volume_id = vol.id
         WHERE v.reference = ?1 LIMIT 1",
        [reference],
        |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "verse_number": row.get::<_, i64>(1)?,
                "text": row.get::<_, String>(2)?,
                "reference": row.get::<_, Option<String>>(3)?,
                "book_title": row.get::<_, String>(4)?,
                "volume_title": row.get::<_, String>(5)?,
                "chapter_number": row.get::<_, i64>(6)?,
            }))
        },
    )
    .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_verse(
    db: State<DbState>,
    book: String,
    chapter: i64,
    verse: i64,
) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let result = conn
        .query_row(
            "SELECT v.id, v.verse_number, v.text, v.reference, b.title as book_title,
                vol.title as volume_title, c.chapter_number
             FROM verses v
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             JOIN volumes vol ON b.volume_id = vol.id
             WHERE b.title = ?1 AND c.chapter_number = ?2 AND v.verse_number = ?3",
            rusqlite::params![&book, chapter, verse],
            |row| {
                Ok(json!({
                    "id": row.get::<_, i64>(0)?,
                    "verse_number": row.get::<_, i64>(1)?,
                    "text": row.get::<_, String>(2)?,
                    "reference": row.get::<_, Option<String>>(3)?,
                    "book_title": row.get::<_, String>(4)?,
                    "volume_title": row.get::<_, String>(5)?,
                    "chapter_number": row.get::<_, i64>(6)?,
                }))
            },
        )
        .map_err(|e| e.to_string())?;

    Ok(result)
}

#[tauri::command]
pub fn search_scriptures(
    db: State<DbState>,
    q: String,
    volume: Option<String>,
    limit: Option<i64>,
    offset: Option<i64>,
) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let limit = limit.unwrap_or(50).clamp(1, 200);
    let offset = offset.unwrap_or(0).max(0);
    let safe_q = sanitize_fts_query(&q);

    let base_sql = "SELECT v.id, v.verse_number, v.text, v.reference, b.title as book_title,
                        vol.title as volume_title, c.chapter_number
                 FROM scriptures_fts fts
                 JOIN verses v ON fts.rowid = v.id
                 JOIN chapters c ON v.chapter_id = c.id
                 JOIN books b ON c.book_id = b.id
                 JOIN volumes vol ON b.volume_id = vol.id
                 WHERE scriptures_fts MATCH ?1";

    let vol_param = volume.unwrap_or_default();
    let has_volume = !vol_param.is_empty();
    let sql = if has_volume {
        format!(
            "{} AND vol.abbreviation = ?2 ORDER BY rank LIMIT ?3 OFFSET ?4",
            base_sql
        )
    } else {
        format!("{} ORDER BY rank LIMIT ?2 OFFSET ?3", base_sql)
    };
    let params: Vec<&dyn rusqlite::types::ToSql> = if has_volume {
        vec![
            &safe_q as &dyn rusqlite::types::ToSql,
            &vol_param,
            &limit,
            &offset,
        ]
    } else {
        vec![&safe_q as &dyn rusqlite::types::ToSql, &limit, &offset]
    };

    let mut stmt = conn.prepare(&sql).map_err(|e| e.to_string())?;
    let results: Vec<Value> = stmt
        .query_map(params.as_slice(), |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "verse_number": row.get::<_, i64>(1)?,
                "text": row.get::<_, String>(2)?,
                "reference": row.get::<_, Option<String>>(3)?,
                "book_title": row.get::<_, String>(4)?,
                "volume_title": row.get::<_, String>(5)?,
                "chapter_number": row.get::<_, i64>(6)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(results))
}

#[tauri::command]
pub fn get_hymns(db: State<DbState>) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT hymn_number, title, author, composer, first_line FROM hymns ORDER BY hymn_number",
        )
        .map_err(|e| e.to_string())?;

    let hymns: Vec<Value> = stmt
        .query_map([], |row| {
            Ok(json!({
                "hymn_number": row.get::<_, i64>(0)?,
                "title": row.get::<_, String>(1)?,
                "author": row.get::<_, Option<String>>(2)?,
                "composer": row.get::<_, Option<String>>(3)?,
                "first_line": row.get::<_, Option<String>>(4)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(hymns))
}

#[tauri::command]
pub fn search_hymns(db: State<DbState>, q: String) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let safe_q = sanitize_fts_query(&q);
    let mut stmt = conn
        .prepare(
            "SELECT h.hymn_number, h.title, h.author, h.composer, h.first_line
             FROM hymns_fts fts
             JOIN hymns h ON fts.rowid = h.id
             WHERE hymns_fts MATCH ?1
             ORDER BY rank
             LIMIT 50",
        )
        .map_err(|e| e.to_string())?;

    let hymns: Vec<Value> = stmt
        .query_map([&safe_q as &str], |row| {
            Ok(json!({
                "hymn_number": row.get::<_, i64>(0)?,
                "title": row.get::<_, String>(1)?,
                "author": row.get::<_, Option<String>>(2)?,
                "composer": row.get::<_, Option<String>>(3)?,
                "first_line": row.get::<_, Option<String>>(4)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(hymns))
}

#[tauri::command]
pub fn get_hymn(db: State<DbState>, id: i64) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;

    // Single query to get hymn data and internal id
    let (hymn_id, mut hymn) = conn
        .query_row(
            "SELECT id, hymn_number, title, author, composer, first_line FROM hymns WHERE hymn_number = ?1",
            [id],
            |row| {
                let internal_id = row.get::<_, i64>(0)?;
                let data = json!({
                    "id": internal_id,
                    "hymn_number": row.get::<_, i64>(1)?,
                    "title": row.get::<_, String>(2)?,
                    "author": row.get::<_, Option<String>>(3)?,
                    "composer": row.get::<_, Option<String>>(4)?,
                    "first_line": row.get::<_, Option<String>>(5)?,
                });
                Ok((internal_id, data))
            },
        )
        .map_err(|e| e.to_string())?;

    let mut stmt = conn
        .prepare(
            "SELECT verse_number, verse_type, text FROM hymn_verses WHERE hymn_id = ?1 ORDER BY verse_number",
        )
        .map_err(|e| e.to_string())?;

    let verses: Vec<Value> = stmt
        .query_map([hymn_id], |row| {
            Ok(json!({
                "verse_number": row.get::<_, i64>(0)?,
                "verse_type": row.get::<_, String>(1)?,
                "text": row.get::<_, String>(2)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    hymn["verses"] = json!(verses);
    Ok(hymn)
}

#[tauri::command]
pub fn get_related_talks(db: State<DbState>, book: String, chapter: i64) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT DISTINCT t.id, t.speaker, t.title, t.date, t.conference, t.url, t.summary
             FROM talks t
             JOIN talk_scripture_refs r ON t.id = r.talk_id
             WHERE r.book_title = ?1 AND r.chapter = ?2
             ORDER BY t.date DESC",
        )
        .map_err(|e| e.to_string())?;

    let talks: Vec<Value> = stmt
        .query_map(rusqlite::params![&book, chapter], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "speaker": row.get::<_, String>(1)?,
                "title": row.get::<_, String>(2)?,
                "date": row.get::<_, Option<String>>(3)?,
                "conference": row.get::<_, Option<String>>(4)?,
                "url": row.get::<_, Option<String>>(5)?,
                "summary": row.get::<_, Option<String>>(6)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(talks))
}

#[tauri::command]
pub fn search_talks(db: State<DbState>, q: String) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let safe_q = sanitize_fts_query(&q);
    let mut stmt = conn
        .prepare(
            "SELECT t.id, t.speaker, t.title, t.date, t.conference, t.url, t.summary
             FROM talks_fts fts
             JOIN talks t ON fts.rowid = t.id
             WHERE talks_fts MATCH ?1
             ORDER BY rank
             LIMIT 50",
        )
        .map_err(|e| e.to_string())?;

    let talks: Vec<Value> = stmt
        .query_map([&safe_q as &str], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "speaker": row.get::<_, String>(1)?,
                "title": row.get::<_, String>(2)?,
                "date": row.get::<_, Option<String>>(3)?,
                "conference": row.get::<_, Option<String>>(4)?,
                "url": row.get::<_, Option<String>>(5)?,
                "summary": row.get::<_, Option<String>>(6)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(talks))
}

#[tauri::command]
pub fn get_volume_stats(db: State<DbState>) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT v.id, v.title, v.abbreviation, v.description,
                    COUNT(DISTINCT b.id) as book_count,
                    COUNT(DISTINCT c.id) as chapter_count,
                    COUNT(DISTINCT vs.id) as verse_count
             FROM volumes v
             LEFT JOIN books b ON b.volume_id = v.id
             LEFT JOIN chapters c ON c.book_id = b.id
             LEFT JOIN verses vs ON vs.chapter_id = c.id
             GROUP BY v.id
             ORDER BY v.id",
        )
        .map_err(|e| e.to_string())?;

    let stats: Vec<Value> = stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "title": row.get::<_, String>(1)?,
                "abbreviation": row.get::<_, String>(2)?,
                "description": row.get::<_, Option<String>>(3)?,
                "book_count": row.get::<_, i64>(4)?,
                "chapter_count": row.get::<_, i64>(5)?,
                "verse_count": row.get::<_, i64>(6)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(stats))
}

// ── Highlight Commands ──

const VALID_HIGHLIGHT_COLORS: &[&str] = &["gold", "rose", "sky", "sage", "lavender"];

#[tauri::command]
pub fn add_highlight(
    db: State<DbState>,
    verse_id: i64,
    color: String,
    start_offset: Option<i64>,
    end_offset: Option<i64>,
    highlighted_text: Option<String>,
) -> Result<Value, String> {
    if !VALID_HIGHLIGHT_COLORS.contains(&color.as_str()) {
        return Err(format!("Invalid highlight color: {}", color));
    }
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO highlights (verse_id, color, start_offset, end_offset, highlighted_text) VALUES (?1, ?2, ?3, ?4, ?5)",
        rusqlite::params![verse_id, &color, start_offset, end_offset, &highlighted_text],
    )
    .map_err(|e| e.to_string())?;
    let id = conn.last_insert_rowid();
    Ok(json!({
        "id": id,
        "verse_id": verse_id,
        "color": color,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "highlighted_text": highlighted_text,
    }))
}

#[tauri::command]
pub fn remove_highlight(db: State<DbState>, id: i64) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    conn.execute("DELETE FROM highlights WHERE id = ?1", [id])
        .map_err(|e| e.to_string())?;
    Ok(json!({"deleted": true}))
}

#[tauri::command]
pub fn get_highlights_for_chapter(
    db: State<DbState>,
    book: String,
    chapter: i64,
) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT h.id, h.verse_id, h.color, h.created_at, h.start_offset, h.end_offset, h.highlighted_text
             FROM highlights h
             JOIN verses v ON h.verse_id = v.id
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             WHERE b.title = ?1 AND c.chapter_number = ?2",
        )
        .map_err(|e| e.to_string())?;

    let highlights: Vec<Value> = stmt
        .query_map(rusqlite::params![&book, chapter], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "verse_id": row.get::<_, i64>(1)?,
                "color": row.get::<_, String>(2)?,
                "created_at": row.get::<_, i64>(3)?,
                "start_offset": row.get::<_, Option<i64>>(4)?,
                "end_offset": row.get::<_, Option<i64>>(5)?,
                "highlighted_text": row.get::<_, Option<String>>(6)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(highlights))
}

// ── Note Commands ──

#[tauri::command]
pub fn add_note(db: State<DbState>, verse_id: i64, text: String) -> Result<Value, String> {
    if text.len() > 50_000 {
        return Err("Note text too long (max 50,000 characters)".to_string());
    }
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO notes (verse_id, text) VALUES (?1, ?2)",
        rusqlite::params![verse_id, &text],
    )
    .map_err(|e| e.to_string())?;
    let id = conn.last_insert_rowid();
    Ok(json!({"id": id, "verse_id": verse_id, "text": text}))
}

#[tauri::command]
pub fn update_note(db: State<DbState>, id: i64, text: String) -> Result<Value, String> {
    if text.len() > 50_000 {
        return Err("Note text too long (max 50,000 characters)".to_string());
    }
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "UPDATE notes SET text = ?1, updated_at = strftime('%s','now') WHERE id = ?2",
        rusqlite::params![&text, id],
    )
    .map_err(|e| e.to_string())?;
    Ok(json!({"id": id, "text": text}))
}

#[tauri::command]
pub fn delete_note(db: State<DbState>, id: i64) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    conn.execute("DELETE FROM notes WHERE id = ?1", [id])
        .map_err(|e| e.to_string())?;
    Ok(json!({"deleted": true}))
}

#[tauri::command]
pub fn get_notes_for_chapter(
    db: State<DbState>,
    book: String,
    chapter: i64,
) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT n.id, n.verse_id, n.text, n.created_at, n.updated_at
             FROM notes n
             JOIN verses v ON n.verse_id = v.id
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             WHERE b.title = ?1 AND c.chapter_number = ?2
             ORDER BY v.verse_number",
        )
        .map_err(|e| e.to_string())?;

    let notes: Vec<Value> = stmt
        .query_map(rusqlite::params![&book, chapter], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "verse_id": row.get::<_, i64>(1)?,
                "text": row.get::<_, String>(2)?,
                "created_at": row.get::<_, i64>(3)?,
                "updated_at": row.get::<_, i64>(4)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(notes))
}

// ── Reading Progress ──

#[tauri::command]
pub fn save_reading_progress(
    db: State<DbState>,
    volume_abbr: String,
    book_title: String,
    chapter: i64,
    last_verse: Option<i64>,
) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO reading_progress (volume_abbr, book_title, chapter, last_verse, last_read)
         VALUES (?1, ?2, ?3, ?4, strftime('%s','now'))
         ON CONFLICT(volume_abbr, book_title, chapter)
         DO UPDATE SET last_verse = ?4, last_read = strftime('%s','now')",
        rusqlite::params![&volume_abbr, &book_title, chapter, last_verse],
    )
    .map_err(|e| e.to_string())?;
    Ok(json!({"saved": true}))
}

#[tauri::command]
pub fn get_reading_progress(db: State<DbState>) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT id, volume_abbr, book_title, chapter, last_verse, last_read
             FROM reading_progress ORDER BY last_read DESC LIMIT 20",
        )
        .map_err(|e| e.to_string())?;

    let progress: Vec<Value> = stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "volume_abbr": row.get::<_, String>(1)?,
                "book_title": row.get::<_, String>(2)?,
                "chapter": row.get::<_, i64>(3)?,
                "last_verse": row.get::<_, Option<i64>>(4)?,
                "last_read": row.get::<_, i64>(5)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(progress))
}

// ── Settings ──

const VALID_SETTING_KEYS: &[&str] = &[
    "fontSize",
    "language",
    "ttsRate",
    "ttsVoice",
    "theme",
    "journeyData",
];

fn validate_setting_key(key: &str) -> Result<(), String> {
    if !VALID_SETTING_KEYS.contains(&key) {
        return Err(format!("Invalid setting key: {}", key));
    }
    Ok(())
}

#[tauri::command]
pub fn get_setting(db: State<DbState>, key: String) -> Result<Value, String> {
    validate_setting_key(&key)?;
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    match conn.query_row("SELECT value FROM settings WHERE key = ?1", [&key], |row| {
        row.get::<_, String>(0)
    }) {
        Ok(val) => Ok(json!(val)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(json!(null)),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
pub fn set_setting(db: State<DbState>, key: String, value: String) -> Result<Value, String> {
    validate_setting_key(&key)?;
    // Global upper bound so a misbehaving renderer can't fill the DB. journeyData
    // (an AI study summary) is the only legitimately large value; cap at 256 KB.
    let max_len = if key == "journeyData" { 256 * 1024 } else { 4096 };
    if value.len() > max_len {
        return Err(format!("Value too large for setting '{}'", key));
    }
    // Validate specific setting values
    match key.as_str() {
        "fontSize" => {
            let size: i32 = value.parse().map_err(|_| "Invalid font size")?;
            if !(10..=48).contains(&size) {
                return Err("Font size must be between 10 and 48".to_string());
            }
        }
        "ttsRate" => {
            let rate: i32 = value.parse().map_err(|_| "Invalid TTS rate")?;
            if !(50..=500).contains(&rate) {
                return Err("TTS rate must be between 50 and 500".to_string());
            }
        }
        "ttsVoice"
            if value.len() > 100
                || !value
                    .chars()
                    .all(|c| c.is_alphanumeric() || " ()-._".contains(c)) =>
        {
            return Err("Invalid voice name".to_string());
        }
        _ => {} // theme, language — free text within the key allowlist
    }
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?1, ?2)
         ON CONFLICT(key) DO UPDATE SET value = ?2",
        rusqlite::params![&key, &value],
    )
    .map_err(|e| e.to_string())?;
    Ok(json!({"key": key, "value": value}))
}

// ── Study View (All Highlights/Notes) ──

#[tauri::command]
pub fn get_all_highlights(
    db: State<DbState>,
    limit: Option<i64>,
    offset: Option<i64>,
) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let limit = limit.unwrap_or(50).clamp(1, 200);
    let offset = offset.unwrap_or(0).max(0);
    let mut stmt = conn
        .prepare(
            "SELECT h.id, h.verse_id, h.color, h.created_at,
                    v.text, v.reference, b.title as book_title,
                    vol.title as volume_title, c.chapter_number, v.verse_number,
                    h.start_offset, h.end_offset, h.highlighted_text
             FROM highlights h
             JOIN verses v ON h.verse_id = v.id
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             JOIN volumes vol ON b.volume_id = vol.id
             ORDER BY h.created_at DESC
             LIMIT ?1 OFFSET ?2",
        )
        .map_err(|e| e.to_string())?;

    let highlights: Vec<Value> = stmt
        .query_map(rusqlite::params![limit, offset], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "verse_id": row.get::<_, i64>(1)?,
                "color": row.get::<_, String>(2)?,
                "created_at": row.get::<_, i64>(3)?,
                "text": row.get::<_, String>(4)?,
                "reference": row.get::<_, Option<String>>(5)?,
                "book_title": row.get::<_, String>(6)?,
                "volume_title": row.get::<_, String>(7)?,
                "chapter_number": row.get::<_, i64>(8)?,
                "verse_number": row.get::<_, i64>(9)?,
                "start_offset": row.get::<_, Option<i64>>(10)?,
                "end_offset": row.get::<_, Option<i64>>(11)?,
                "highlighted_text": row.get::<_, Option<String>>(12)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(highlights))
}

#[tauri::command]
pub fn get_all_notes(
    db: State<DbState>,
    limit: Option<i64>,
    offset: Option<i64>,
) -> Result<Value, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let limit = limit.unwrap_or(50).clamp(1, 200);
    let offset = offset.unwrap_or(0).max(0);
    let mut stmt = conn
        .prepare(
            "SELECT n.id, n.verse_id, n.text, n.created_at, n.updated_at,
                    v.text as verse_text, v.reference, b.title as book_title,
                    vol.title as volume_title, c.chapter_number, v.verse_number
             FROM notes n
             JOIN verses v ON n.verse_id = v.id
             JOIN chapters c ON v.chapter_id = c.id
             JOIN books b ON c.book_id = b.id
             JOIN volumes vol ON b.volume_id = vol.id
             ORDER BY n.updated_at DESC
             LIMIT ?1 OFFSET ?2",
        )
        .map_err(|e| e.to_string())?;

    let notes: Vec<Value> = stmt
        .query_map(rusqlite::params![limit, offset], |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "verse_id": row.get::<_, i64>(1)?,
                "text": row.get::<_, String>(2)?,
                "created_at": row.get::<_, i64>(3)?,
                "updated_at": row.get::<_, i64>(4)?,
                "verse_text": row.get::<_, String>(5)?,
                "reference": row.get::<_, Option<String>>(6)?,
                "book_title": row.get::<_, String>(7)?,
                "volume_title": row.get::<_, String>(8)?,
                "chapter_number": row.get::<_, i64>(9)?,
                "verse_number": row.get::<_, i64>(10)?,
            }))
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;

    Ok(json!(notes))
}
