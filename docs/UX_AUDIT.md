# Scriptures — Brutal UX & Completeness Audit (2026-06-22)

Reviewed against the professional bar: YouVersion, Logos, Olive Tree, Blue Letter
Bible, Accordance, e-Sword. Six independent expert critics + live DB/code evidence.

## Scorecard (vs a professional Bible-app bar)

| Dimension | Score |
|-----------|-------|
| Reading experience & verse interaction | 4/10 |
| Navigation & findability | 4/10 |
| Study depth & AI assistant | 4/10 |
| Personal features & retention | 3/10 |
| Onboarding, polish, dead UI | 7/10 |
| Completeness vs professional apps | 5/10 |

**Honest verdict:** a beautiful, genuinely novel niche tool (multi-canon, fully
offline, local-AI) undercut by missing daily-use table stakes and a few
embarrassing data/UI defects. The bones are good; the everyday gestures are absent.

## What's genuinely good (don't lose this)
- Local RAG AI assistant that actually cites context — nothing mainstream does this offline.
- Nine canons including Dead Sea Scrolls, Coptic, Russian Orthodox, Ancient Witnesses — unique.
- Fully offline, no account, bundled 54k-verse DB; one of the best onboarding flows in its class.
- Tasteful illuminated-manuscript reading typography; sub-verse 5-color highlighting.

## P0 — broken or table-stakes-missing (fixing this round)
1. **Editorial braces bleed into 62% of the OT.** 17,366 verses render literal
   `{it was}` / `{Heb. soul}` / `{moving: or, creeping}`. Genesis 1:4 shows
   "{the light from...: Heb. between the light and between the darkness}". Looks broken.
2. **No copy / no share of a verse.** The selection toolbar has highlight+note only.
   Every Bible app's #1 verse gesture is missing. (0 clipboard calls in the codebase.)
3. **`reference` column empty for 100% of the core canon** (42,030 verses). Breaks
   AI citations (the model gets a blank label so it literally can't cite KJV/BoM/D&C),
   search-result labels, and any go-to-reference.
4. **No go-to-reference.** Typing "Alma 32" or "John 3:16" returns ZERO (FTS treats
   it as keywords). The single most important study gesture is impossible.
5. **"Verse Explain" is advertised but unreachable.** `ai_explain` + `aiExplain()`
   exist; no UI calls them. False advertising in tutorial + settings.
6. **Dead UI.** Two permanently-disabled header buttons (one tooltipped "coming soon"
   for translation, which already ships); the whole AssetManager view is built but
   unreachable; tutorial promises "bookmarks" that don't exist.

## P1 — high-value (this round where achievable)
7. Search result drops you on an orphaned single verse — no chapter context.
8. No reading-progress / "Continue reading" / recents — backend exists, never called.
9. No verse-of-the-day or any daily engagement hook.
10. "My Study" is read-only — can't delete a highlight or edit/delete a note there.
11. No scroll-position memory; every nav resets to top.
12. No chapter picker — Alma 1 → Alma 32 is "Next Chapter" ×31.

## Bigger lifts — documented, deferred (need content/licensing or large effort)
- Cross-references & footnotes (need a dataset, e.g. public-domain Treasury of
  Scripture Knowledge for KJV; LDS footnote apparatus is copyrighted).
- Strong's numbers / interlinear / lexicon (licensed or huge).
- Reading plans / devotionals; cloud sync; parallel-translation columns (achievable
  later — the DB supports the join).
- Thin content: "Ancient Witnesses" is 73 verses of excerpts; DSS is 895. Honest
  labeling or expansion needed.

## This round's execution plan (impact-to-effort ordered)
**Batch A (DB, foundational):** strip braces + rebuild FTS; populate `reference`
for all 54k verses.
**Batch B (verse gestures):** Copy + Share in the verse toolbar.
**Batch C (navigation):** go-to-reference parser in the search bar; search result
opens the full chapter scrolled+flashed to the verse; chapter jump within a book.
**Batch D (reachability/honesty):** wire "Verse Explain"; remove dead header
buttons; reachable Scripture Library; fix tutorial over-promises.
**Batch E (retention):** wire reading-progress → "Continue reading" + recents;
verse-of-the-day on the welcome screen; "My Study" delete/edit management.
**Verifier:** `scripts/verify-ux-journeys.sh` asserts each of the above end-to-end.
