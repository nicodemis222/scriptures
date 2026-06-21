# First-Install UX Plan (clean Mac)

**Goal:** A brand-new user on a clean Mac (no Homebrew, no Xcode CLT, maybe non-admin, maybe offline) installs the DMG and has a fully working app with **zero surprise prompts** and **nothing broken** — even with no Ollama and no AI models.

## Audit findings (parallel agents + verified locally)

On a clean Apple-Silicon Mac with no Xcode Command Line Tools:
- `/usr/bin/python3`, `git`, `clang` are **hardlinks to one CLT shim** (verified: identical inode, 78 links). Invoking `python3` **pops Apple's "install command line developer tools" modal** and does not run Python.
- **No Homebrew**, no compiler. `brew` → command not found.
- `/Applications` is `root:admin` — a standard (non-admin) user can't write it.
- `xcode-select --install` only *opens a dialog*; can't be driven headlessly.
- Ollama isn't present; its CLI symlink needs a one-time admin password; the app is ~550MB and models are GBs.

### What breaks today on a clean Mac
1. **CRITICAL** — `start_piper_on_launch → ensure_piper_venv` runs `python3 -m venv` **on first launch**, popping Apple's CLT modal with no context, then failing. (`tts.rs`)
2. **CRITICAL** — TTS is **Piper-only**; with no python3/CLT, **Read Aloud is completely dead** (no fallback). (`tts.rs read_aloud*`)
3. **HIGH** — offline first launch: pip install of piper-tts/onnxruntime fails → bundled voices are dead weight, Read Aloud broken.
4. **MEDIUM** — AI: without Ollama the assistant is unusable; download size (~4.3 GB) isn't disclosed; install assumes brew/admin/writable `/Applications`.

## Design decisions

### TTS — make Read Aloud frictionless on every Mac
- **macOS `say` is the always-available engine.** Zero deps, offline, present on every Mac. Read Aloud works immediately.
- **Piper is the optional "enhanced neural voices" upgrade.** Used automatically *only if its venv is already set up*; **never bootstrapped by invoking the python3 shim on launch** (kills the surprise modal).
- **Opt-in setup** in Settings: "Set up enhanced voices" detects CLT via `xcode-select -p` (exit code only — never invokes the shim), explains the requirement, and can open Apple's official installer *with context*. Bootstraps the venv from a real python only after explicit consent. Fail-soft messaging.
- `list_voices` returns curated macOS `say` voices when Piper is down, so the voice picker still works.

### AI — bulletproof optional
- Verify **zero breakage** with no Ollama: reading, search, highlights, notes, hymns, and `say`-TTS are all independent of AI.
- **Disclose the ~4.3 GB** download (engine + mistral) in FirstRunSetup and the assistant.
- `install_ollama` **fail-soft**: brew-absent already falls back to direct download; handle non-writable `/Applications` / non-admin with a clear message + link to ollama.com instead of a raw error.
- Talk to Ollama over its **localhost HTTP API** (already do for status/generate); surface `port_conflict` to the UI.

### Sequencing
- Nothing blocks the UI on a dependency (threads already). First launch on a clean Mac: app opens, library + search + highlights + notes + hymns + `say` Read Aloud all work; AI and enhanced voices are clearly-labeled opt-ins. **No modal, no crash, no hang, no silent dead button.**

## Out of scope (documented, not done now)
- Bundling a relocatable python + vendored piper into the .app (would make enhanced voices zero-friction offline but adds ~250 MB and nested-binary notarization complexity). Tracked as a future enhancement; `say` covers the frictionless baseline.
