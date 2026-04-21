# Scriptures — Sacred Scripture Study App

**Last Updated**: 2026-04-06
**Version**: 0.2.0

## Overview
Offline-first desktop app for studying sacred texts across 9 scriptural traditions. Built with Tauri v2 + React 19 + TypeScript + Rust + SQLite/FTS5.

**Repo**: https://github.com/nicodemis222/scriptures (public)
**Website**: humandividendprotocol.com/scriptures.html
**DMG**: s3://ark-data-bundles/Scriptures_0.2.0_aarch64.dmg (335 MB, signed + notarized)
**Windows**: s3://ark-data-bundles/Scriptures_0.1.0_x64-setup.exe (GitHub Actions build)

## Architecture

```
frontend/
  src/
    App.tsx                    # Main coordinator: 10 view modes, dark mode, tab reorder
    components/
      AIAssistant.tsx          # Scripture Assistant (Qwen 2.5 via Ollama, RAG)
      MyJourney.tsx            # AI study summary from highlights/notes
      ReadAloudControls.tsx    # TTS player: 4 Piper voices, play/pause/stop
      VerseDisplay.tsx         # Sub-verse highlighting, notes, translation, chapter nav
      SettingsPanel.tsx        # Font size, theme, language, TTS rate
      Tutorial.tsx             # First-run tutorial overlay
    hooks/
      useScriptures.ts         # All Tauri invoke wrappers (40+ commands)
    types/
      scriptures.ts            # TypeScript interfaces
    styles/
      index.css                # ~2500 lines sacred theme CSS (illuminated manuscript)
  src-tauri/
    src/
      main.rs                  # Tauri entry: setup, cache cleanup on upgrade, exit handler
      tts.rs                   # Piper TTS: synthesis, playback, voice management
      ai.rs                    # Qwen AI: RAG query, explain, translate, Ollama management
      commands.rs              # 26 scripture/highlight/note/settings commands
      db.rs                    # SQLite init, migrations, empty DB recovery
      bundles.rs               # Data bundle management
    Cargo.toml                 # Dependencies: tauri 2, rusqlite, serde_json, libc
    tauri.conf.json            # Bundle ID: com.scriptures.app, v0.2.0
services/
  piper-tts/
    server.py                  # Piper HTTP server (port 8095): /synthesize, /health, /voices
    models/                    # 4 ONNX voice models (~354 MB total)
data/
  scriptures.db                # SQLite DB: 54,500+ verses, FTS5 index, 9 volumes
```

## 9 Scripture Volumes
Book of Mormon, Holy Bible (KJV), Doctrine & Covenants, Pearl of Great Price, Coptic Bible, Dead Sea Scrolls, Russian Orthodox, Ancient Witnesses, Hymns (317)

## AI System (Qwen 2.5 via Ollama)

### Scripture Assistant (`ai.rs: ai_query`)
RAG with 4-tier retrieval, prioritizing current reading context:
1. **Tier 1**: Current chapter (up to 20 verses)
2. **Tier 2**: Same book, other chapters via FTS5 (up to 8)
3. **Tier 3**: Same volume, other books via FTS5 (up to 6)
4. **Tier 4**: All other volumes globally via FTS5 (up to 6)

System prompt names all 9 volumes and encourages cross-canon connections.
Default model: `qwen2.5:latest`. User can select any installed Ollama model.

### Verse Explain (`ai.rs: ai_explain`)
- Fetches target verse + 2 surrounding verses
- Cross-reference search: 5 related passages from any volume via FTS5
- Prompt asks for historical context, daily application, cross-canon connections

### My Journey (`MyJourney.tsx`)
- Fetches up to 500 highlights + 500 notes
- Analyzes study patterns: top books, color focus areas, themes
- Passes most-studied book as `context_book` for RAG tier 2-4 activation
- Generates: Study Summary, Themes, Growth Assessment, Reading Path, Weekly Goal

### Translation (`ai.rs: translate_chapter`)
- 10 languages: Spanish, French, Portuguese, German, Italian, Chinese, Korean, Japanese, Russian, Arabic
- Batch translation (up to 20 verses per Ollama call)
- Cached in `translation_cache` table (INSERT OR REPLACE)
- DB lock released before Ollama call

### Ollama Management (`ai.rs`)
- `check_ollama_installed`: checks binary + running status
- `install_ollama`: brew install or curl script
- `start_ollama`: spawns `ollama serve`
- `pull_ollama_model`: downloads model with validation
- Frontend: AIEngineSetup component with Install/Start/Download buttons
- All user-facing text says "AI engine" / "Qwen" (not "Ollama")

## TTS System (Piper)

### Architecture
- **Server**: Python HTTP server (`services/piper-tts/server.py`) on port 8095
- **Engine**: piper-tts Python package in venv at `~/.scriptures/piper-env/`
- **Models**: 4 ONNX voices bundled in .app Resources:
  - `en_US-lessac-high` (default, highest quality)
  - `en_GB-cori-high` (British)
  - `en_US-amy-medium`
  - `en_US-joe-medium` (male)
- **Synthesis**: ~200-700ms per sentence via direct Command API (no shell scripts)
- **Playback**: Background thread with AtomicBool flags for pause/cancel
- **Voice validation**: `is_valid_voice_id()` — alphanumeric + hyphen + underscore only

### Startup Flow
1. `main.rs: setup()` calls `start_piper_on_launch()` — starts server in background
2. Frontend `ReadAloudControls` retries `listVoices()` every 3s for 30s
3. Voice dropdown populates once server responds to `/voices`
4. `read_aloud` auto-starts server if not running (fallback)

### Process Management
- `play_sentences()` runs on `std::thread::spawn` (non-blocking)
- Pause: sets `AtomicBool` flag + SIGSTOP on current afplay
- Resume: clears flag + SIGCONT
- Stop: sets cancelled flag + SIGKILL + pkill orphaned afplay
- App exit: `RunEvent::Exit` handler kills all processes + cleanup

## Security
- No shell script generation (eliminated command injection vectors)
- Voice IDs validated with strict allowlist
- FTS5 queries sanitized via `sanitize_fts_query()` (phrase-wrapped)
- Model names validated: alphanumeric + `.:_-`, max 64 chars
- Settings key allowlist with per-key value validation
- Highlight colors restricted to 5-color allowlist
- Note text capped at 50,000 chars
- DB lock released before all blocking Ollama calls
- PID bounds check before i32 cast for signal calls

## Build & Deploy Pipeline

### macOS DMG
```bash
npx @tauri-apps/cli build
# Bundle Piper into .app/Contents/Resources/piper/
codesign --deep --force --options runtime --sign "Developer ID Application: Matthew Johnson (DCGN5QTCKT)" Scriptures.app
hdiutil create -volname "ScripturesApp" -srcfolder staging/ -format UDZO Scriptures_0.2.0_aarch64.dmg
codesign --force --sign "Developer ID Application: ..." *.dmg
xcrun notarytool submit *.dmg --keychain-profile "notary" --wait
xcrun stapler staple *.dmg
aws s3 cp *.dmg s3://ark-data-bundles/
```

### Website Deploy
```bash
rsync -azP -e "ssh -i ~/.ssh/hdp_lightsail" scriptures.html ubuntu@34.216.115.167:~/landing-deploy/
ssh -i ~/.ssh/hdp_lightsail ubuntu@34.216.115.167 "sudo cp ~/landing-deploy/scriptures.html /var/www/humandividendprotocol.com/"
```

### Windows/Linux
GitHub Actions workflow: `.github/workflows/build.yml` (workflow_dispatch trigger)
Builds on windows-latest and ubuntu-22.04 runners.
Trigger: `gh workflow run build.yml`

## Version Upgrade System
`main.rs: clear_caches_on_upgrade()` runs before Tauri init:
- Reads `~/.scriptures/last_version`
- If version changed: clears WebKit caches, Application Support webview data, TTS temp files, kills stale processes, resets LaunchServices
- Writes current version to `~/.scriptures/last_version`

## Clean Install on Another Mac
```bash
pkill -f Scriptures 2>/dev/null
rm -rf /Applications/Scriptures.app
rm -rf ~/Library/WebKit/com.scriptures.app
rm -rf ~/Library/Caches/com.scriptures.app
rm -rf ~/Library/Application\ Support/com.scriptures.app/EBWebView
rm -rf ~/.scriptures/last_version
# Then install fresh DMG
```

## Database
- SQLite with FTS5 (bundled via rusqlite)
- `scriptures_fts` table indexes: text, reference, book_title, volume_title (all 9 volumes)
- 4 migrations: highlights/notes, settings, translation_cache, sub-verse highlight offsets
- Auto-update from bundled DB when newer version detected
- App Support path: `~/Library/Application Support/com.scriptures.app/scriptures.db`

## Key Dependencies
- **Rust**: tauri 2, rusqlite (bundled), serde_json, libc
- **Frontend**: React 19, TypeScript, Vite 8
- **TTS**: piper-tts (Python, via venv), 4 ONNX voice models
- **AI**: Ollama (user-installed), Qwen 2.5 model
- **Build**: @tauri-apps/cli
- **CI**: GitHub Actions (macOS/Windows/Linux)
- **Signing**: Developer ID Application: Matthew Johnson (DCGN5QTCKT)
- **Notarization**: keychain profile "notary"

## History
- v0.1.0: Initial release with VibeVoice TTS, llama3.2 AI
- v0.2.0: Piper TTS (4 voices), Qwen 2.5 AI, cross-canon RAG, security hardening, cache cleanup on upgrade, all Ollama UI references removed
