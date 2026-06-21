use rusqlite::Connection;
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::{AppHandle, Manager};

pub struct DbState {
    pub conn: Mutex<Connection>,
}

/// Search for the bundled scriptures.db in multiple candidate locations.
fn find_bundled_db(app: &AppHandle) -> Option<PathBuf> {
    let resource_dir = app.path().resource_dir().ok()?;

    // Try multiple candidate paths (Tauri bundles with relative path structure)
    let candidates = [
        resource_dir.join("_up_/_up_/data/scriptures.db"),
        resource_dir.join("../../data/scriptures.db"),
        resource_dir.join("data/scriptures.db"),
        resource_dir.join("scriptures.db"),
    ];

    for candidate in &candidates {
        if candidate.exists() {
            let size = fs::metadata(candidate).map(|m| m.len()).unwrap_or(0);
            if size > 1000 {
                // Valid DB (not empty placeholder)
                eprintln!(
                    "[db] Found bundled DB at: {} ({} bytes)",
                    candidate.display(),
                    size
                );
                return Some(candidate.clone());
            }
        }
    }

    // Also try relative to the executable itself
    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            let from_exe = exe_dir.join("../Resources/_up_/_up_/data/scriptures.db");
            if from_exe.exists() {
                eprintln!("[db] Found bundled DB via exe path: {}", from_exe.display());
                return Some(from_exe);
            }
        }
    }

    eprintln!(
        "[db] Could not find bundled scriptures.db. resource_dir={}",
        resource_dir.display()
    );
    None
}

pub fn init_db(app: &AppHandle) -> Result<DbState, Box<dyn std::error::Error>> {
    let app_data = app.path().app_data_dir()?;
    fs::create_dir_all(&app_data)?;
    let db_path = app_data.join("scriptures.db");

    let bundled_path = find_bundled_db(app);

    // Determine if we need to copy the bundled DB
    let needs_copy = if !db_path.exists() {
        eprintln!("[db] No cached DB found, will copy from bundle");
        true
    } else {
        // Check if cached DB is empty or corrupt
        let cached_size = fs::metadata(&db_path).map(|m| m.len()).unwrap_or(0);
        if cached_size < 1000 {
            eprintln!(
                "[db] Cached DB is empty/corrupt ({} bytes), will replace",
                cached_size
            );
            true
        } else if let Some(ref bp) = bundled_path {
            // Check if bundled is newer
            let bundled_mod = fs::metadata(bp).and_then(|m| m.modified()).ok();
            let cached_mod = fs::metadata(&db_path).and_then(|m| m.modified()).ok();
            match (bundled_mod, cached_mod) {
                (Some(b), Some(c)) if b > c => {
                    eprintln!("[db] Bundled DB is newer than cached, will update");
                    true
                }
                _ => false,
            }
        } else {
            false
        }
    };

    if needs_copy {
        match bundled_path {
            Some(ref bp) => {
                // If a prior install's DB exists, preserve the user's data
                // (highlights, notes, etc.) across the content upgrade instead
                // of clobbering it. The bundled DB ships only static scripture
                // content and no user tables, so a naive copy would wipe all
                // highlights/notes/settings — that was a real data-loss bug.
                let had_existing = db_path.exists();
                let preserve_path = app_data.join("scriptures.db.userdata");
                if had_existing {
                    // Keep both a generic backup and a dedicated user-data copy.
                    let backup = app_data.join("scriptures.db.backup");
                    let _ = fs::copy(&db_path, &backup);
                    let _ = fs::copy(&db_path, &preserve_path);
                }

                // Remove stale WAL/SHM so the fresh copy isn't shadowed by an
                // old write-ahead log pointing at the previous file.
                let _ = fs::remove_file(app_data.join("scriptures.db-wal"));
                let _ = fs::remove_file(app_data.join("scriptures.db-shm"));

                fs::copy(bp, &db_path)?;
                eprintln!("[db] Copied bundled DB to {}", db_path.display());

                if had_existing && preserve_path.exists() {
                    // Open the fresh DB, create user tables, then merge prior
                    // user rows back in.
                    let conn = Connection::open(&db_path)?;
                    conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
                    run_migrations(&conn)?;
                    if let Err(e) = restore_user_data(&conn, &preserve_path) {
                        eprintln!("[db] WARNING: failed to restore user data: {}", e);
                    } else {
                        eprintln!("[db] Restored user data from prior install");
                    }
                    drop(conn);
                    let _ = fs::remove_file(&preserve_path);
                }
            }
            None => {
                return Err("Database not found. Please reinstall the application.".into());
            }
        }
    }

    let conn = Connection::open(&db_path)?;
    conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;

    // Verify DB is valid
    let verse_count: i64 = conn
        .query_row("SELECT COUNT(*) FROM verses", [], |r| r.get(0))
        .unwrap_or(0);
    eprintln!("[db] Database opened with {} verses", verse_count);

    if verse_count == 0 {
        // DB is empty despite existing — force re-copy. No user data to
        // preserve here (the DB is empty), so a direct copy is safe.
        drop(conn);
        let _ = fs::remove_file(app_data.join("scriptures.db-wal"));
        let _ = fs::remove_file(app_data.join("scriptures.db-shm"));
        if let Some(ref bp) = find_bundled_db(app) {
            fs::copy(bp, &db_path)?;
            eprintln!("[db] Re-copied bundled DB (was empty)");
        }
        let conn = Connection::open(&db_path)?;
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
        run_migrations(&conn)?;
        return Ok(DbState {
            conn: Mutex::new(conn),
        });
    }

    run_migrations(&conn)?;

    Ok(DbState {
        conn: Mutex::new(conn),
    })
}

/// User-owned tables that must survive a content (bundle) upgrade.
const USER_TABLES: &[&str] = &[
    "highlights",
    "notes",
    "reading_progress",
    "settings",
    "translation_cache",
];

/// Copy user rows from a preserved prior-install DB into the freshly-copied DB.
/// Uses INSERT OR IGNORE so re-runs are safe and conflicting PKs don't error.
fn restore_user_data(conn: &Connection, old_db: &std::path::Path) -> Result<(), Box<dyn std::error::Error>> {
    conn.execute(
        "ATTACH DATABASE ?1 AS olddb",
        [old_db.to_string_lossy().to_string()],
    )?;

    let result = (|| -> Result<(), Box<dyn std::error::Error>> {
        for table in USER_TABLES {
            // Only copy if the old DB actually has this table.
            let exists: i64 = conn
                .query_row(
                    "SELECT COUNT(*) FROM olddb.sqlite_master WHERE type='table' AND name=?1",
                    [table],
                    |r| r.get(0),
                )
                .unwrap_or(0);
            if exists == 0 {
                continue;
            }
            // Intersect columns so a schema change between versions doesn't break
            // the copy: build an explicit shared-column list.
            let cols = shared_columns(conn, table)?;
            if cols.is_empty() {
                continue;
            }
            let col_list = cols.join(", ");
            let sql = format!(
                "INSERT OR IGNORE INTO main.{t} ({c}) SELECT {c} FROM olddb.{t}",
                t = table,
                c = col_list
            );
            if let Err(e) = conn.execute_batch(&sql) {
                eprintln!("[db] user-data restore skipped {}: {}", table, e);
            }
        }
        Ok(())
    })();

    // Always detach, even on error.
    let _ = conn.execute("DETACH DATABASE olddb", []);
    result
}

/// Return the list of columns present in BOTH main.<table> and olddb.<table>.
fn shared_columns(conn: &Connection, table: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let main_cols = table_columns(conn, "main", table)?;
    let old_cols = table_columns(conn, "olddb", table)?;
    Ok(main_cols
        .into_iter()
        .filter(|c| old_cols.contains(c))
        .collect())
}

fn table_columns(conn: &Connection, schema: &str, table: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    // PRAGMA can't be parameterized; schema/table are internal constants here.
    let mut stmt = conn.prepare(&format!("PRAGMA {}.table_info({})", schema, table))?;
    let cols = stmt
        .query_map([], |row| row.get::<_, String>(1))?
        .collect::<Result<Vec<_>, _>>()?;
    Ok(cols)
}

/// Run a single ALTER TABLE ADD COLUMN, treating "duplicate column" as success.
/// Lets migrations be idempotent even if a bundle ships with the column present.
fn add_column_if_missing(conn: &Connection, sql: &str) -> Result<(), Box<dyn std::error::Error>> {
    match conn.execute_batch(sql) {
        Ok(()) => Ok(()),
        Err(rusqlite::Error::SqliteFailure(_, Some(ref msg))) if msg.contains("duplicate column") => Ok(()),
        Err(e) if e.to_string().contains("duplicate column") => Ok(()),
        Err(e) => Err(e.into()),
    }
}

fn run_migrations(conn: &Connection) -> Result<(), Box<dyn std::error::Error>> {
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at INTEGER DEFAULT (strftime('%s','now'))
        );",
    )?;

    let current: i64 = conn
        .query_row(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations",
            [],
            |r| r.get(0),
        )
        .map_err(|e| -> Box<dyn std::error::Error> {
            format!("Failed to read migration version: {}", e).into()
        })?;

    let migrations: &[(i64, &str)] = &[
        (
            1,
            "CREATE TABLE IF NOT EXISTS highlights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verse_id INTEGER NOT NULL,
                color TEXT NOT NULL DEFAULT 'gold',
                created_at INTEGER DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_highlights_verse ON highlights(verse_id);
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verse_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s','now')),
                updated_at INTEGER DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_notes_verse ON notes(verse_id);
            CREATE TABLE IF NOT EXISTS reading_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_abbr TEXT NOT NULL,
                book_title TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                last_verse INTEGER,
                last_read INTEGER DEFAULT (strftime('%s','now')),
                UNIQUE(volume_abbr, book_title, chapter)
            );",
        ),
        (
            2,
            "CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );",
        ),
        (
            3,
            "CREATE TABLE IF NOT EXISTS translation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verse_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                UNIQUE(verse_id, language)
            );",
        ),
        // Migration 4 is special-cased below (idempotent ALTERs).
        (4, ""),
    ];

    for (version, sql) in migrations {
        if *version <= current {
            continue;
        }
        // Wrap each migration + its version stamp in a transaction so a partial
        // failure can't leave the schema half-migrated.
        conn.execute_batch("BEGIN")?;
        let applied = (|| -> Result<(), Box<dyn std::error::Error>> {
            if *version == 4 {
                // Sub-verse highlight columns — idempotent in case a future
                // bundle already ships them.
                add_column_if_missing(conn, "ALTER TABLE highlights ADD COLUMN start_offset INTEGER")?;
                add_column_if_missing(conn, "ALTER TABLE highlights ADD COLUMN end_offset INTEGER")?;
                add_column_if_missing(conn, "ALTER TABLE highlights ADD COLUMN highlighted_text TEXT")?;
            } else {
                conn.execute_batch(sql)?;
            }
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?1)",
                [version],
            )?;
            Ok(())
        })();
        match applied {
            Ok(()) => {
                conn.execute_batch("COMMIT")?;
            }
            Err(e) => {
                let _ = conn.execute_batch("ROLLBACK");
                return Err(e);
            }
        }
    }
    Ok(())
}
