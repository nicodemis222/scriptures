#!/usr/bin/env bash
#
# verify-ux-journeys.sh — automated UX-journey + content verifier for Scriptures.
#
# Asserts the core reader journeys end-to-end at the layers we can check
# deterministically: the bundled content DB, the Rust command wiring, and the
# frontend wiring. Run after any change touching the reader, search, DB, or
# verse interaction. Exit 0 = all journeys intact; non-zero = a regression.
#
# Usage: scripts/verify-ux-journeys.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="$ROOT/data/scriptures.db"
SRC="$ROOT/frontend/src"
RS="$ROOT/frontend/src-tauri/src"
PASS=0; FAIL=0
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; PASS=$((PASS+1)); }
bad()  { printf "  \033[31m✗ %s\033[0m\n" "$1"; FAIL=$((FAIL+1)); }
q()    { sqlite3 "$DB" "$1" 2>/dev/null; }
sec()  { printf "\n\033[1m%s\033[0m\n" "$1"; }

[ -f "$DB" ] || { echo "DB not found: $DB"; exit 2; }

sec "Journey 1 — Read a clean chapter (no editorial markup)"
braces=$(q "SELECT COUNT(*) FROM verses WHERE text LIKE '%{%' OR text LIKE '%}%';")
[ "$braces" = "0" ] && ok "no editorial braces in any verse" || bad "braces still present in $braces verses"
gen14=$(q "SELECT text FROM verses ve JOIN chapters c ON ve.chapter_id=c.id JOIN books b ON c.book_id=b.id WHERE b.title='Genesis' AND c.chapter_number=1 AND ve.verse_number=4;")
case "$gen14" in *"{"*) bad "Genesis 1:4 still has markup";; *"And God saw the light"*) ok "Genesis 1:4 reads cleanly";; *) bad "Genesis 1:4 missing/odd: $gen14";; esac

sec "Journey 2 — Every verse has a citable reference"
total=$(q "SELECT COUNT(*) FROM verses;")
refs=$(q "SELECT COUNT(*) FROM verses WHERE reference IS NOT NULL AND reference != '';")
[ "$total" = "$refs" ] && ok "all $total verses have a reference" || bad "only $refs/$total verses have a reference"
alma=$(q "SELECT reference FROM verses WHERE reference='Alma 32:21';")
[ "$alma" = "Alma 32:21" ] && ok "reference lookup 'Alma 32:21' resolves" || bad "Alma 32:21 reference missing"

sec "Journey 3 — Search finds verses (FTS)"
fts=$(q "SELECT COUNT(*) FROM scriptures_fts WHERE scriptures_fts MATCH '\"faith\" AND \"hope\"';")
[ "${fts:-0}" -gt 0 ] && ok "multi-term search 'faith AND hope' → $fts hits" || bad "FTS multi-term search broken"
ftscount=$(q "SELECT COUNT(*) FROM scriptures_fts;")
[ "$ftscount" = "$total" ] && ok "FTS index covers all $total verses" || bad "FTS rows ($ftscount) != verses ($total)"

sec "Journey 4 — Go-to-reference jumps to a chapter"
# Mirrors resolve_reference: book prefix-match + chapter existence.
for ref in "Alma|32" "John|3" "1 Nephi|3" "Genesis|1"; do
  bk="${ref%|*}"; ch="${ref#*|}"
  hit=$(q "SELECT COUNT(*) FROM chapters c JOIN books b ON c.book_id=b.id WHERE (LOWER(b.title)=LOWER('$bk') OR LOWER(b.title) LIKE LOWER('$bk')||'%') AND c.chapter_number=$ch;")
  [ "${hit:-0}" -gt 0 ] && ok "'$bk $ch' resolves to a chapter" || bad "'$bk $ch' does not resolve"
done
grep -q "pub fn resolve_reference" "$RS/commands.rs" && ok "resolve_reference command exists" || bad "resolve_reference command missing"
grep -q "commands::resolve_reference" "$RS/main.rs" && ok "resolve_reference registered" || bad "resolve_reference NOT registered"

sec "Journey 5 — Copy & Share a verse"
grep -q "onCopy" "$SRC/components/VerseToolbar.tsx" && grep -q "onShare" "$SRC/components/VerseToolbar.tsx" \
  && ok "verse toolbar exposes Copy + Share" || bad "verse toolbar missing Copy/Share"
grep -q "clipboard.writeText" "$SRC/components/VerseDisplay.tsx" \
  && ok "copy writes to the clipboard" || bad "no clipboard write wired"

sec "Journey 6 — Search result opens in chapter context + flashes"
grep -q "scrollToVerse" "$SRC/components/VerseDisplay.tsx" && grep -q "verse-flash" "$SRC/components/VerseDisplay.tsx" \
  && ok "navigate-to-verse scroll + flash wired" || bad "scroll-to-verse not wired"
grep -q "data-verse-number" "$SRC/components/VerseDisplay.tsx" \
  && ok "verses carry a scroll target (data-verse-number)" || bad "data-verse-number missing"
grep -q "handleStudyNavigate(verse.book_title" "$SRC/App.tsx" \
  && ok "search-result click opens full chapter (not orphan verse)" || bad "search result still shows orphan verse"

sec "Journey 7 — No dead UI"
if grep -qE 'disabled title="(Read Aloud|Language)' "$SRC/App.tsx"; then bad "dead disabled header buttons still present"; else ok "no disabled 'coming soon' header buttons"; fi
grep -q "jump to a reference" "$SRC/components/SearchBar.tsx" \
  && ok "search placeholder advertises go-to-reference" || bad "go-to-reference not discoverable in placeholder"
if grep -q "Notes, bookmarks, and related talks" "$SRC/components/Tutorial.tsx"; then bad "tutorial over-promises bookmarks"; else ok "tutorial copy matches real features"; fi

sec "Journey 9 — Retention: verse of the day + continue reading"
grep -q "pub fn daily_verse" "$RS/commands.rs" && grep -q "commands::daily_verse" "$RS/main.rs" \
  && ok "daily_verse command exists + registered" || bad "daily_verse not wired"
# Every curated daily verse must resolve to a real verse.
missing=0
for r in "John 3:16" "Alma 32:21" "Moroni 10:4" "Isaiah 40:31" "3 Nephi 11:11"; do
  c=$(q "SELECT COUNT(*) FROM verses WHERE reference='$r';"); [ "${c:-0}" = "1" ] || missing=$((missing+1))
done
[ "$missing" = "0" ] && ok "curated verse-of-the-day references all exist" || bad "$missing curated daily verses missing"
grep -q "saveReadingProgress" "$SRC/App.tsx" && ok "reading progress is saved on read" || bad "reading progress never saved (dead infra)"
grep -q "WelcomeHome" "$SRC/App.tsx" && grep -q "getReadingProgress" "$SRC/components/WelcomeHome.tsx" \
  && ok "home screen surfaces continue-reading + daily verse" || bad "welcome home not wired"

sec "Journey 8 — Content completeness (all 9 canons present)"
vols=$(q "SELECT COUNT(DISTINCT v.id) FROM volumes v JOIN books b ON b.volume_id=v.id JOIN chapters c ON c.book_id=b.id JOIN verses ve ON ve.chapter_id=c.id;")
[ "${vols:-0}" -ge 9 ] && ok "$vols volumes have readable content" || bad "only $vols volumes have content (expected ≥9)"
awv=$(q "SELECT COUNT(ve.id) FROM verses ve JOIN volumes v ON ve.volume_id=v.id WHERE v.title='Ancient Witnesses';")
[ "${awv:-0}" -ge 500 ] && ok "Ancient Witnesses has substantive content ($awv verses)" || bad "Ancient Witnesses too thin ($awv verses)"
clem=$(q "SELECT COUNT(*) FROM verses WHERE book_id=(SELECT id FROM books WHERE title='1 Clement');")
[ "${clem:-0}" -gt 100 ] && ok "1 Clement filled ($clem verses)" || bad "1 Clement still thin/empty ($clem)"
empty=$(q "SELECT COUNT(*) FROM books b WHERE (SELECT COUNT(*) FROM verses WHERE book_id=b.id)=0;")
[ "${empty:-0}" = "0" ] && ok "no empty books" || bad "$empty books have zero verses"

printf "\n\033[1mRESULT: %d passed, %d failed\033[0m\n" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
