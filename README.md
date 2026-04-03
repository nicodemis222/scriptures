# Scriptures

Offline scripture browser extracted from the ARK project. Staged for future development as a standalone Tauri desktop app.

## Assets

### Database (`data/scriptures.db`)
- **Engine:** SQLite 3 with FTS5 full-text search
- **Content:** 48,589+ verses across 7 volumes, 150 books, 1,931 chapters
- **Volumes:** Old Testament, New Testament, Book of Mormon, Doctrine & Covenants, Pearl of Great Price, Coptic Bible, Dead Sea Scrolls, Russian Orthodox Bible
- **Hymns:** 127+ LDS Hymnal entries with verses
- **Size:** ~28 MB

### Build Scripts (`scripts/`)
- `build-scriptures-db.py` — Creates schema, imports LDS scriptures and Bible from source repos
- `expand-scriptures-db.py` — Adds Coptic Bible, Dead Sea Scrolls, Russian Orthodox (public domain sources)
- `import-scriptures.py` — Scrapes sacred-texts.com for additional Coptic content
- `import-dss.py` — Imports Dead Sea Scrolls from archive.org OCR
- `build-hymns-db.py` — Builds LDS Hymnal database
- `fix-hymns-db.py` — Data maintenance for hymn entries
- `import-hymns.py` — Additional hymn import

### UI Component (`ui/ScripturesTab.tsx`)
- React component from ARK's PipBoy interface
- Multi-volume tabbed browser with book/chapter/verse navigation
- Full-text search across all volumes
- Hymn display with verses and chorus
- Hardcoded fallback data for offline resilience
- Needs adaptation from ARK's PipBoy styling for standalone use

## Rebuilding the Database

```bash
# Requires cloned repos: LDS-scriptures, bible_databases
python3 scripts/build-scriptures-db.py

# Add extended content (Coptic, DSS, Russian Orthodox)
python3 scripts/expand-scriptures-db.py
```

## API Endpoints (from ARK, for reference)

The ARK API provided these endpoints — to be reimplemented in the Tauri app:

- `GET /search?q=&volume=&limit=&offset=` — Full-text search
- `GET /volumes` — List all scripture volumes
- `GET /books?volume=` — List books, optionally filtered by volume
- `GET /chapter?book=&chapter=` — All verses in a chapter
- `GET /verse?book=&chapter=&verse=` — Single verse
- `GET /hymns/list` — List all hymns
- `GET /hymns/search?q=` — Search hymns
- `GET /hymns/{id}` — Get hymn by ID
