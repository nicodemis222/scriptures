# Scriptures App — Project Context

**Last Updated**: 2026-04-03
**Location**: `/Users/matthewjohnson/Projects/scriptures/`
**Repo**: Private (not on GitHub yet)

---

## What This Is

A standalone Tauri v2 desktop app for studying sacred texts across 9 scriptural traditions. Built with React 19 + TypeScript frontend and Rust backend with SQLite (FTS5).

## Architecture

```
scriptures/
  frontend/                 # Tauri + Vite + React + TypeScript
    src/
      App.tsx               # Main coordinator (view modes, state, routing)
      main.tsx              # Entry point + ErrorBoundary
      components/
        VolumeNav.tsx       # Draggable tab bar (9 volumes)
        BookList.tsx        # Sidebar book list with chapter indicator
        ChapterGrid.tsx     # Chapter number grid
        VerseDisplay.tsx    # Main verse reader (highlights, notes, translation, TTS)
        VerseToolbar.tsx    # Floating highlight/note toolbar on verse selection
        NoteEditor.tsx      # Inline note textarea
        SearchBar.tsx       # Global cross-volume search
        HymnViewer.tsx      # Hymn display with verses/chorus
        RelatedContent.tsx  # Prophet talks linked to chapters (opens in browser via shell:open)
        ReadAloudControls.tsx # Sticky floating TTS player bar (verse-by-verse, pause/resume)
        StudyView.tsx       # My Study — all highlights & notes
        SettingsPanel.tsx   # Theme, font size, language, TTS rate, AI model
        AIAssistant.tsx     # Right-side chat panel + OllamaSetup with install button
        MyJourney.tsx       # RAG-powered personal study summary
        Tutorial.tsx        # 8-slide onboarding walkthrough
        Toast.tsx           # Toast notification system
        Icons.tsx           # 26 SVG sacred icons
      hooks/useScriptures.ts # All Tauri invoke() wrappers (40+ functions)
      types/scriptures.ts    # All TypeScript interfaces
      data/constants.ts      # Volume tabs, fallback data, default tab order
      styles/index.css       # Complete sacred theme (~2000 lines)
        # Gold/purple/teal palette, EB Garamond, Cormorant Garamond, Inter
        # Dark mode, illuminated manuscript frame, ornamental accents
        # Sticky TTS player, responsive breakpoints
    src-tauri/
      src/
        main.rs             # Tauri entry + 34 registered commands
        db.rs               # SQLite init, migration system (4 migrations), auto-update from bundle
        commands.rs          # 26 scripture/highlight/note/settings commands
        bundles.rs           # Asset bundle manifest + volume stats
        tts.rs               # TTS: VibeVoice HTTP (primary) + system say (fallback)
                             # Voice listing, Ollama install/start/pull commands
        ai.rs                # Ollama RAG: ai_query, ai_explain, translate_chapter
                             # FTS5-based retrieval, translation cache
      Cargo.toml            # tauri 2, rusqlite (bundled), serde, serde_json, tauri-plugin-shell
      tauri.conf.json       # 1200x800, CSP, bundle resources
      capabilities/default.json  # core:default + shell:allow-open
  data/
    scriptures.db           # Main database (~30MB, 54,500+ verses)
    scriptures.db.backup-*  # Pre-fix backups
    bundles/                # Per-volume .sqlite exports + manifest.json + master ZIP
  scripts/
    build-scriptures-db.py  # Original DB builder
    expand-scriptures-db.py # Coptic/DSS/Russian content (130KB)
    import-talks.py         # 53 prophet talks with 298 scripture cross-refs
    import-dss.py           # Dead Sea Scrolls from archive.org
    complete-content.py     # Content gap filler v1
    complete-content-v2.py  # Content gap filler v2
    complete-maccabees.py   # 1-2 Maccabees full text
    complete-maccabees-v2.py # Via JSON data files
    fix-database.py         # Dedup, book_order, orphan cleanup
    fix-dss-content.py      # DSS OCR garbage removal
    fix-dss-final.py        # Community Rule + Damascus Document replacement
    add-ancient-witnesses.py # Ancient Witnesses volume
    export-bundles.py       # Per-volume .sqlite export + master ZIP
    verse_data/             # JSON verse data for Maccabees
  services/
    vibevoice-tts/
      server.py             # VibeVoice HTTP server (port 8095, from ARK)
      voices/               # .pt voice preset files (9 English + multilingual)
  ui/
    ScripturesTab.tsx       # Original ARK component (reference only)
  README.md
```

## Database: 54,500+ Verses Across 9 Volumes

| Volume | ID | Abbr | Books | Verses |
|--------|-----|------|-------|--------|
| Old Testament | 1 | ot | 39 | 23,147 |
| New Testament | 2 | nt | 27 | 7,953 |
| Book of Mormon | 3 | bom | 15 | 6,604 |
| Doctrine & Covenants | 4 | dc | 1 (138 sections) | 3,654 |
| Pearl of Great Price | 5 | pgp | 5 | 635 |
| Coptic Bible | 200 | coptic | 17 | ~5,300 |
| Dead Sea Scrolls | 300 | dss | 13 | ~2,000 |
| Russian Orthodox | 400 | russian | 14 | ~5,200 |
| Ancient Witnesses | 500 | aw | 13 | ~73 |

Plus: 317 hymns, 53 prophet talks (298 cross-refs)

## Database Migrations (db.rs)

1. highlights, notes, reading_progress tables
2. settings table
3. translation_cache table
4. ALTER highlights ADD start_offset, end_offset, highlighted_text (sub-verse highlighting)

## Key Features

- **9 scripture volumes** with drag-to-reorder tabs (persisted in localStorage)
- **Full-text search** (FTS5) across ALL volumes simultaneously, prioritizing current tab
- **Sub-verse highlighting** — select any word/sentence, 5 colors (gold/rose/sky/sage/lavender)
- **Inline notes** on any verse with quill icon
- **Continuous reading** — Next/Previous Chapter + Next/Previous Book navigation
- **Sticky floating TTS player** — verse-by-verse playback, pause/resume, skip, voice selection
- **VibeVoice neural TTS** (primary, port 8095) with system `say` fallback
- **AI Scripture Assistant** — Ollama-powered RAG with auto-model detection, model selector
- **Ollama auto-install** — Install + Start + Pull model buttons in AI panel
- **Multi-language translation** — 10 languages via Ollama, cached in DB
- **My Journey** — RAG-powered personal study summary from highlights/notes
- **Related prophet talks** — cross-referenced below each chapter, opens in system browser
- **Settings** — theme (light/dark), font size, TTS rate/voice, AI model, tutorial replay
- **Tutorial** — 8-slide onboarding with skip/revisit
- **Toast notifications** — feedback on all user actions
- **Dark mode** with higher-opacity highlights
- **Illuminated manuscript frame** — gold gradient border with corner ornaments
- **Ornamental accents** — gold dividers, drop caps, celestial stars on cards

## Deployment

### Code Signing
- Identity: `Developer ID Application: Matthew Johnson (DCGN5QTCKT)`
- Notarization: `xcrun notarytool submit --keychain-profile "notary" --wait`
- Stapling: `xcrun stapler staple`

### Distribution
- S3: `s3://ark-data-bundles/Scriptures_0.1.0_aarch64.dmg`
- Public URL: `https://ark-data-bundles.s3.us-west-2.amazonaws.com/Scriptures_0.1.0_aarch64.dmg`
- Website: `https://humandividendprotocol.com/scriptures.html`

### Build Pipeline
```bash
cd frontend
rm -f ~/Library/Application\ Support/com.scriptures.app/scriptures.db  # flush cache
cargo tauri build
codesign --deep --force --options runtime --sign "Developer ID Application: Matthew Johnson (DCGN5QTCKT)" src-tauri/target/release/bundle/macos/Scriptures.app
hdiutil create -volname "Scriptures" -srcfolder src-tauri/target/release/bundle/macos/Scriptures.app -ov -format UDZO /tmp/scriptures_signed.dmg
mv /tmp/scriptures_signed.dmg src-tauri/target/release/bundle/dmg/Scriptures_0.1.0_aarch64.dmg
xcrun notarytool submit src-tauri/target/release/bundle/dmg/Scriptures_0.1.0_aarch64.dmg --keychain-profile "notary" --wait
xcrun stapler staple src-tauri/target/release/bundle/dmg/Scriptures_0.1.0_aarch64.dmg
aws s3 cp src-tauri/target/release/bundle/dmg/Scriptures_0.1.0_aarch64.dmg s3://ark-data-bundles/
```

### Website Deploy
```bash
rsync -avz /Users/matthewjohnson/Projects/HDP/landing/ ubuntu@34.216.115.167:~/landing-deploy/ -e "ssh -i ~/.ssh/hdp_lightsail"
ssh -i ~/.ssh/hdp_lightsail ubuntu@34.216.115.167 "sudo cp -r ~/landing-deploy/* /var/www/humandividendprotocol.com/"
```

## TTS Architecture

**Primary**: VibeVoice-Realtime-0.5B (Microsoft neural TTS)
- Server: `services/vibevoice-tts/server.py` on port 8095
- Voices: 9 English + 3 multilingual (.pt presets)
- Synthesis: POST /synthesize → WAV → afplay
- Quality: Natural, expressive (~200ms first chunk)

**Fallback**: macOS `say` command (system TTS)
- Instant start (~10ms)
- Voice selection from system voices
- Text piped via stdin (avoids ARG_MAX)

**Frontend**: Sticky floating player bar at bottom
- Verse-by-verse playback with auto-advance
- Pause/resume from current verse
- Skip forward/back between verses
- Progress bar (verse X of Y)
- Voice dropdown (VibeVoice + system voices)

## AI Architecture

**Engine**: Ollama (local LLM)
- Auto-detect installed models (filters embedding-only)
- Default: llama3.2:latest
- Model selector in AI panel
- Auto-install button (brew install ollama → ollama pull llama3.2)

**RAG Pipeline** (ai.rs):
1. User question → extract keywords
2. FTS5 search → top 10 relevant verses
3. If chapter context: include current chapter verses
4. Augmented prompt → Ollama generate
5. Response with scripture citations

**Translation** (ai.rs):
1. User selects language → translate_chapter called
2. Check translation_cache (single IN query, not N+1)
3. Cache miss → batch 20 verses → Ollama translate prompt
4. Parse [N] prefixed lines back to verse IDs
5. Cache results → return translations
6. 10 validated languages: Spanish, French, Portuguese, German, Italian, Chinese, Korean, Japanese, Russian, Arabic

## Security Measures Applied

- SQL: All queries parameterized (no string concatenation)
- FTS5: `sanitize_fts_query()` wraps in quotes, caps at 500 chars (UTF-8 safe)
- TTS voice: Validated (alphanumeric + spaces/hyphens, no `..`, max 100 chars)
- TTS text: Sanitized (no control chars), capped at 50,000 chars, piped via stdin
- Settings: Key allowlist (6 keys), value validation per key (fontSize 10-48, ttsRate 50-500, aiModel regex, ttsVoice regex)
- Highlights: Color allowlist (5 colors)
- Notes: Max 50,000 chars
- Translation: Language allowlist (10 languages)
- AI model: Validated (alphanumeric + `:.-_`, max 64 chars)
- URLs: `shell:allow-open` permission, HTTP/HTTPS regex check before opening
- DB path: Multi-candidate search with size validation, auto-recovery from empty DB
- Errors: Internal paths logged to stderr only, generic messages to frontend
- Windows TTS: Uses -File script (not -Command string injection)
- Mutex: Released before blocking IO (child.wait, curl)

## Review History

All reviews passed from everything-claude-code agents:
- TypeScript Reviewer: WARNING → fixed (Toast ID bug, floating promises)
- Rust Reviewer: CRITICAL → fixed (voice injection, PowerShell injection, mutex deadlock, UTF-8 panic)
- Security Reviewer: CRITICAL → fixed (voice validation, language allowlist, note length, settings validation)

## Known Limitations

- Ollama required for AI/translation features (not bundled, user must install)
- VibeVoice server must be started separately (not auto-launched by app yet)
- Single Mutex<Connection> for DB (sufficient for desktop, would need pool for server)
- `curl` used for Ollama/VibeVoice calls (could be replaced with reqwest for native HTTP)
- No cloud sync — all data is local only
- macOS only for TTS voice selection (Linux/Windows have limited voice options)
