# Scriptures — Feature Test Plan

**App version:** 0.4.0
**Platform:** macOS (Apple Silicon), Tauri v2 + React 19 + Rust + SQLite/FTS5
**Last updated:** 2026-04-21

This plan verifies every user-facing feature plus the install/upgrade and
AI/TTS infrastructure paths. Each test lists **Pre**, **Steps**, **Expected**,
and a **Pass/Fail** box. Tests marked **[AUTO]** are checkable from the shell
or DB without driving the GUI; **[GUI]** require the running app.

---

## 0. Build & Static Quality Gates  [AUTO]

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 0.1 | TypeScript | `cd frontend && npx tsc -b` | exit 0, no errors |
| 0.2 | ESLint | `cd frontend && npx eslint .` | 0 errors (advisory warnings OK) |
| 0.3 | Rust compile | `cd frontend/src-tauri && cargo check` | exit 0 |
| 0.4 | Clippy | `cargo clippy` | 0 errors, 0 warnings |
| 0.5 | Frontend bundle | `cd frontend && npm run build` | dist/ produced |
| 0.6 | Tauri build | `npx @tauri-apps/cli build` | .app + .dmg produced |
| 0.7 | Codesign valid | `codesign --verify --deep --strict Scriptures.app` | "valid on disk" |
| 0.8 | Notarization | `spctl -a -t open --context context:primary-signature *.dmg` | "accepted / Notarized Developer ID" |

---

## 1. Install / Upgrade / Data Preservation

### 1.1 Fresh install (no prior app, no `~/.scriptures`)  [GUI]
- **Pre:** `rm -rf /Applications/Scriptures.app ~/.scriptures ~/Library/Application\ Support/com.scriptures.app ~/Library/WebKit/com.scriptures.app`
- **Steps:** Mount DMG, drag to Applications, launch.
- **Expected:** App opens; Tutorial (slide 1/8) shows; after Skip/finish, FirstRunSetup overlay appears; library loads Book of Mormon with chapters.

### 1.2 Upgrade over existing install — **user data preserved**  [AUTO+GUI]
- **Pre:** Existing v0.3.0 install with at least 1 highlight + 1 note + changed settings (font size).
- **Steps:**
  1. Before upgrade, record counts:
     `sqlite3 ~/Library/Application\ Support/com.scriptures.app/scriptures.db "SELECT (SELECT COUNT(*) FROM highlights), (SELECT COUNT(*) FROM notes), (SELECT value FROM settings WHERE key='fontSize');"`
  2. Install v0.4.0 DMG over the existing app; launch.
  3. Re-run the same query.
- **Expected:** highlight/note counts and fontSize **unchanged** after upgrade. (Regression guard for the bundle-copy data-loss bug — `db.rs restore_user_data`.) A `scriptures.db.backup` exists in app-data.

### 1.3 Corrupt/empty cached DB recovery  [AUTO]
- **Pre:** `: > ~/Library/Application\ Support/com.scriptures.app/scriptures.db` (truncate to empty)
- **Steps:** Launch app.
- **Expected:** App detects empty DB, re-copies bundled DB, library has 54,509 verses. No crash.

### 1.4 Migration idempotency  [AUTO]
- **Steps:** `sqlite3 <appdata>/scriptures.db "SELECT version FROM schema_migrations ORDER BY version;"`
- **Expected:** rows 1,2,3,4 present; relaunching app does not error or duplicate. ALTER columns `start_offset,end_offset,highlighted_text` exist on `highlights`.

---

## 2. Scripture Navigation  [GUI]

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 2.1 | Volume tabs | Click each of 9 tabs (BoM, Bible, D&C, PGP, Coptic, DSS, Russian, Ancient Witnesses, Hymns) | Each loads its book list |
| 2.2 | Tab reorder | Drag a tab to a new position; relaunch | Order persists (localStorage `tabOrder`) |
| 2.3 | Book → chapters | Select multi-chapter book | Chapter grid shows correct count |
| 2.4 | Chapter → verses | Select a chapter | Verses render with verse numbers |
| 2.5 | Single-chapter book | Select Enos/Jarom | Opens directly to verses |
| 2.6 | D&C sections | Select Section 76 | Loads section 76 verses |
| 2.7 | Next/Prev chapter | In verse view use nav | Loads adjacent chapter; "Chapter X of Y" correct |
| 2.8 | Next/Prev book | At chapter bounds | Crosses into adjacent book |

---

## 3. Search (FTS5)  [AUTO+GUI]

| # | Test | Query | Expected |
|---|------|-------|----------|
| 3.1 | Single term | `faith` | Many results (~902 verses in DB) |
| 3.2 | Multi-term AND | `faith hope` | Verses containing **both** words any order (~41), not just exact phrase |
| 3.3 | No false phrase-lock | `faith hope` | Strictly more than exact-adjacency (`"faith hope"` ≈ 9) |
| 3.4 | Injection neutralized | `faith OR 1=1` | Treated as literal tokens; no SQL/FTS error, bounded results |
| 3.5 | Apostrophe | `God's` | Returns results, no error |
| 3.6 | Empty/punctuation only | `!!!` or `   ` | No results, no crash |
| 3.7 | Cross-volume | search term present in multiple volumes | Results span volumes; current tab prioritized |
| 3.8 | Result navigation | Click a result | Opens that chapter at the verse |

**[AUTO] FTS semantics** verified directly:
`sqlite3 data/scriptures.db "SELECT COUNT(*) FROM scriptures_fts WHERE scriptures_fts MATCH '\"faith\" AND \"hope\"';"`

---

## 4. Highlights  [GUI]

| # | Test | Expected |
|---|------|----------|
| 4.1 | Select sub-verse text → highlight | Highlight appears in chosen color |
| 4.2 | 5 colors | gold/rose/sky/sage/lavender all apply |
| 4.3 | Remove highlight | Highlight cleared |
| 4.4 | Persistence | Relaunch → highlight still present |
| 4.5 | Multiple per verse | Two highlights on one verse coexist |
| 4.6 | Chapter switch isolation | Highlights from chapter A do not bleed into chapter B (regression guard) |

---

## 5. Notes  [GUI]

| # | Test | Expected |
|---|------|----------|
| 5.1 | Add note to verse | Note saved, quill icon shows |
| 5.2 | Edit note | Updated text persists |
| 5.3 | Delete note | Removed |
| 5.4 | Persistence | Relaunch → note present |
| 5.5 | Long note (≤50k chars) | Accepted; >50k rejected gracefully |

---

## 6. Hymns  [GUI]
- 6.1 Hymns tab lists hymns. 6.2 Select hymn → verses + chorus render. 6.3 Back returns to list. 6.4 Hymn search returns matches.

## 7. My Study  [GUI]
- 7.1 Opens aggregated highlights + notes. 7.2 Click an entry → navigates to that chapter. 7.3 Empty state when no data.

---

## 8. AI Scripture Assistant  [GUI] — **focus area**

| # | State | Steps | Expected |
|---|-------|-------|----------|
| 8.1 | Engine not installed | Open Assistant with Ollama absent | Shows **"Install AI Engine + Mistral 7B"**; clicking runs install→start→download with progress |
| 8.2 | Engine installed, not running | Ollama installed but stopped | Shows **"Start AI Engine"**; click starts it |
| 8.3 | **Running, model missing** | Ollama running but no `mistral` (e.g. setup skipped / interrupted) | Shows **"Download Mistral 7B (~4.1 GB)"** button — NOT a dead-end "Start" button (headline bug fix). Click → progress bar → chat unlocks |
| 8.4 | Ready | Engine + mistral present | Chat UI shows; "Powered by local Mistral 7B" |
| 8.5 | Ask question | Type a scripture question | Streams a relevant answer citing verses |
| 8.6 | Explain this chapter | Quick action in verse view | Returns chapter explanation |
| 8.7 | Find related passages | Quick action | Returns cross-canon connections |
| 8.8 | Engine unreachable mid-chat | Stop Ollama then ask | Friendly "Could not reach the AI engine" error, no crash |
| 8.9 | Model fixed | Inspect requests | Only `mistral:7b` is ever requested (no model dropdown anywhere) |

**[AUTO]** Confirm hardcoded model: `grep -n "AI_MODEL\|mistral" frontend/src-tauri/src/ai.rs` → all generate/explain/translate use `AI_MODEL = "mistral:7b"`.

---

## 9. First-Run Setup overlay  [GUI] — **focus area**

| # | Test | Expected |
|---|------|----------|
| 9.1 | Fresh launch | Overlay after tutorial; 3 status rows (Engine / Running / Mistral) |
| 9.2 | All present | If engine+model already there → "Everything is ready!" + "Begin Scripture Study" |
| 9.3 | Set Up button | Runs install→start→download sequentially with live % |
| 9.4 | Skip for Now | Closes overlay; app usable; setup deferred |
| 9.5 | **Skip mid-download** | Click "Continue in Background" while pull streaming | No React unmount errors/crash; download continues server-side (mounted-ref guard) |
| 9.6 | Persistence | After completing/skipping, relaunch | Overlay does NOT reappear (localStorage `setup_completed`) |
| 9.7 | Resume model later | Skip at first run, later open Assistant | Test 8.3 path offers the download |

---

## 10. My Journey (RAG)  [GUI]

| # | Test | Expected |
|---|------|----------|
| 10.1 | Generate with data | With highlights/notes present | Produces Study Summary, Themes, Growth, Reading Path, Weekly Goal |
| 10.2 | Markdown render | — | `##` headings render as styled headings, **bold** renders bold — NO literal `##` leaking |
| 10.3 | Reference links | Click a "1 Nephi 3" suggestion | Navigates correctly (leading-ordinal book names parsed) |
| 10.4 | Empty state | No highlights/notes | Prompts user to start highlighting |
| 10.5 | Error preserves prior | Engine down during refresh | Shows error without destroying a previously generated journey |
| 10.6 | Uses mistral only | — | Request uses `mistral:7b` |

---

## 11. Translation  [GUI]

| # | Test | Expected |
|---|------|----------|
| 11.1 | Translate chapter | Pick Spanish | Verses show Spanish under each |
| 11.2 | Cache | Re-select same language | Instant (from `translation_cache`) |
| 11.3 | Back to English | Select English (empty value) | Clears translation immediately — no doomed translate-to-English round trip |
| 11.4 | All 10 languages | Spot-check FR/DE/ZH/RU/AR | Each returns translated text |
| 11.5 | Engine down | — | Graceful failure, reverts language |

---

## 12. Read Aloud (Piper TTS)  [GUI]

| # | Test | Expected |
|---|------|----------|
| 12.1 | First launch venv bootstrap | Fresh `~/.scriptures` | "Setting up voice engine" banner; completes; voices populate |
| 12.2 | Play | Press play in verse view | Audio plays verse-by-verse |
| 12.3 | Pause/Resume | — | Audio pauses and resumes at same verse |
| 12.4 | Skip fwd/back | — | Jumps verses |
| 12.5 | Stop | — | Audio stops; player hides |
| 12.6 | Voice selection | 4 voices (lessac/cori/amy/joe) | Switching voice changes audio |
| 12.7 | Chapter change stops audio | Navigate away mid-play | Audio stops cleanly |
| 12.8 | App exit cleanup | Quit while playing | No orphaned `afplay`/piper after exit (`pgrep afplay` empty) |

---

## 13. Port Deconfliction  [AUTO+GUI] — **focus area**

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 13.1 | Piper default port free | Normal launch | Piper binds 8095; `/health` returns `engine: piper` |
| 13.2 | **Piper port occupied by stranger** | `python3 -m http.server 8095` then launch app | App does NOT kill the stranger; Piper hops to 8096+ ; TTS still works. Stranger still running afterward. |
| 13.3 | Reuse our own Piper | Relaunch app while prior Piper alive on 8095 | Reuses it (no second server, no kill) |
| 13.4 | Ollama already running | Ollama serving for another app | App reuses it; does not spawn a second `ollama serve` |
| 13.5 | **Ollama port occupied by stranger** | Bind 11434 with a non-Ollama listener | `check_ollama_installed` reports `port_conflict: true`; Start shows clear "port in use" error, no infinite retry |
| 13.6 | Exit does not nuke port | Quit app | App only kills its own afplay/piper child; does NOT `lsof -ti:8095 | kill` arbitrary processes |

**[AUTO]** `grep -n "lsof -ti" frontend/src-tauri/src/*.rs` → no unconditional port-kill remains.

---

## 14. Settings  [GUI]

| # | Test | Expected |
|---|------|----------|
| 14.1 | Theme light/dark | Toggle | Applies immediately, persists |
| 14.2 | **Theme: System** | Select System | Follows OS appearance; flips live when OS theme changes |
| 14.3 | Font size slider | Adjust | Verse text resizes, persists |
| 14.4 | TTS speed | Adjust | Reading rate changes |
| 14.5 | No model selector | — | AI section shows fixed "Mistral 7B" note; no model input field |
| 14.6 | Version | — | Shows v0.4.0 |
| 14.7 | View Tutorial | Click | Re-opens tutorial |

---

## 15. Tutorial  [GUI]
- 15.1 8 slides navigable. 15.2 Skip closes. 15.3 "AI Assistant — powered by local Mistral 7B" copy. 15.4 Re-openable from Settings.

---

## 16. Security Hardening  [AUTO]

| # | Test | Expected |
|---|------|----------|
| 16.1 | Piper body cap | `curl -X POST 127.0.0.1:<port>/synthesize -H 'Content-Length: 99999999' ...` | 413 Request body too large |
| 16.2 | Piper text cap | POST text > 5000 chars | Truncated to 5000, still 200 |
| 16.3 | Piper voice traversal | POST `{"voice":"../../etc/passwd"}` | 400 Invalid voice id |
| 16.4 | Piper Host check | POST with `Host: evil.com` | 403 Forbidden host |
| 16.5 | Piper no wildcard CORS | OPTIONS request | No `Access-Control-Allow-Origin: *` header |
| 16.6 | Piper threaded | Two slow concurrent requests | Both served (no head-of-line block) |
| 16.7 | shell open restricted | — | `tauri.conf.json plugins.shell.open = "^https?://"`; non-http URLs rejected |
| 16.8 | CSP tightened | — | `object-src 'none'; base-uri 'none'; frame-ancestors 'none'` present |
| 16.9 | Ollama install archive validation | — | install script rejects non-zip downloads before extracting |
| 16.10 | Settings size cap | set a >256KB journeyData | rejected "Value too large" |

---

## 17. Regression Sweep (post-fix)  [GUI]
Run a 5-minute end-to-end: open app → navigate BoM 1 Nephi 3 → highlight a phrase → add a note → search "faith hope" → open a result → translate to Spanish → play Read Aloud → open AI Assistant (download model if needed) → ask a question → generate My Journey → toggle dark/system theme → quit. Confirm no console errors, no orphan processes, no crashes.
