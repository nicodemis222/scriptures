#!/usr/bin/env python3
"""Import Dead Sea Scrolls from archive.org OCR text into ARK scriptures DB."""

import os
import re
import sqlite3
import sys

DB = os.path.join(os.path.dirname(__file__), "..", "data", "scriptures", "scriptures.db")
DSS_TEXT = "/tmp/dss-text.txt"

# Major scrolls to extract with their approximate line ranges and known section headers
SCROLLS = [
    {
        "title": "Community Rule",
        "abbr": "1QS",
        "start_pattern": r"The Community Rule",
        "end_pattern": r"Community Rule manuscripts from Cave 4|Entry into the Covenant",
        "order": 1,
    },
    {
        "title": "Damascus Document",
        "abbr": "CD",
        "start_pattern": r"The Damascus Document",
        "end_pattern": r"Damascus Document manuscripts from Cave 4|The Messianic Rule",
        "order": 2,
    },
    {
        "title": "War Scroll",
        "abbr": "1QM",
        "start_pattern": r"The War Scroll -",
        "end_pattern": r"The War Scroll from Cave 4|The Temple Scroll",
        "order": 3,
    },
    {
        "title": "Temple Scroll",
        "abbr": "11QT",
        "start_pattern": r"The Temple Scroll -",
        "end_pattern": r"Miscellaneous|MMT|Copper Scroll|The Wicked",
        "order": 4,
    },
    {
        "title": "Thanksgiving Hymns",
        "abbr": "1QH",
        "start_pattern": r"Thanksgiving Hymns|THE THANKSGIVING HYMNS|Hymns|HYMNS",
        "end_pattern": r"Apocryphal Psalms|Songs for|Blessings|LITURGICAL",
        "order": 5,
    },
    {
        "title": "Copper Scroll",
        "abbr": "3Q15",
        "start_pattern": r"The Copper Scroll",
        "end_pattern": r"Miscellan|The Wicked|An Annalistic",
        "order": 6,
    },
]


def main():
    if not os.path.exists(DSS_TEXT):
        print(f"DSS text file not found at {DSS_TEXT}")
        print("Run: curl the archive.org URL first")
        sys.exit(1)

    with open(DSS_TEXT, "r", errors="replace") as f:
        full_text = f.read()

    lines = full_text.split("\n")
    print(f"Loaded {len(lines)} lines from DSS text")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")

    # Get or verify DSS volume
    row = conn.execute("SELECT id FROM volumes WHERE abbreviation='dss'").fetchone()
    if not row:
        conn.execute("INSERT INTO volumes(title, abbreviation) VALUES('Dead Sea Scrolls', 'dss')")
        conn.commit()
    vol_id = conn.execute("SELECT id FROM volumes WHERE abbreviation='dss'").fetchone()[0]

    total_verses = 0

    for scroll in SCROLLS:
        print(f"\n=== {scroll['title']} ({scroll['abbr']}) ===")

        # Find the scroll's text block
        start_idx = None
        end_idx = len(lines)

        for i, line in enumerate(lines):
            if start_idx is None and re.search(scroll["start_pattern"], line, re.IGNORECASE):
                # Skip the header line, start from next paragraph
                start_idx = i + 1
            elif start_idx is not None and i > start_idx + 10 and re.search(scroll["end_pattern"], line, re.IGNORECASE):
                end_idx = i
                break

        if start_idx is None:
            print(f"    Could not find start pattern: {scroll['start_pattern']}")
            continue

        # Extract text block
        block_lines = lines[start_idx:min(end_idx, start_idx + 2000)]
        block_text = "\n".join(block_lines)

        # Skip introduction/commentary paragraphs (usually first few before actual text)
        # Look for Roman numeral sections (I, II, III...) or column markers (Col.)
        paragraphs = re.split(r"\n\s*\n", block_text)

        # Create book
        book_row = conn.execute("SELECT id FROM books WHERE abbreviation=? AND volume_id=?",
                                (scroll["abbr"], vol_id)).fetchone()
        if book_row:
            book_id = book_row[0]
        else:
            cur = conn.execute(
                "INSERT INTO books(title, abbreviation, long_title, num_chapters, book_order, volume_id) VALUES(?,?,?,?,?,?)",
                (scroll["title"], scroll["abbr"], scroll["title"], 1, scroll["order"], vol_id),
            )
            conn.commit()
            book_id = cur.lastrowid

        # Parse into sections/chapters and verses
        chapter_num = 1
        verse_num = 0
        scroll_total = 0

        for para in paragraphs:
            text = para.strip()
            if len(text) < 15:
                continue

            # Check for section/column markers
            section_match = re.match(
                r"^(?:Col(?:umn)?\.?\s*)?([IVXLC]+(?:\s|$)|\d+(?:\s|$)|[A-Z]\.\s)",
                text,
            )
            if section_match:
                chapter_num += 1
                verse_num = 0

            # Skip OCR artifacts, page numbers, footnotes
            if re.match(r"^\d+$", text.strip()):
                continue
            if "Penguin" in text or "copyright" in text.lower() or "ISBN" in text:
                continue
            if len(text) < 20:
                continue

            # Get or create chapter
            chap_row = conn.execute(
                "SELECT id FROM chapters WHERE book_id=? AND chapter_number=?",
                (book_id, chapter_num),
            ).fetchone()
            if chap_row:
                chapter_id = chap_row[0]
            else:
                cur = conn.execute(
                    "INSERT INTO chapters(chapter_number, book_id) VALUES(?,?)",
                    (chapter_num, book_id),
                )
                conn.commit()
                chapter_id = cur.lastrowid

            # Split paragraph into verse-sized chunks (2-4 sentences each)
            sentences = re.split(r"(?<=[.!?])\s+", text)
            chunk = []
            for sent in sentences:
                chunk.append(sent.strip())
                if len(" ".join(chunk)) > 100 or sent.endswith((".", "!", "?")):
                    verse_text = " ".join(chunk).strip()
                    if len(verse_text) > 15:
                        verse_num += 1
                        ref = f"{scroll['abbr']} {chapter_num}:{verse_num}"

                        existing = conn.execute(
                            "SELECT id FROM verses WHERE reference=? AND volume_id=?",
                            (ref, vol_id),
                        ).fetchone()
                        if not existing:
                            conn.execute(
                                "INSERT INTO verses(text, verse_number, reference, book_id, chapter_id, volume_id) VALUES(?,?,?,?,?,?)",
                                (verse_text, verse_num, ref, book_id, chapter_id, vol_id),
                            )
                            scroll_total += 1
                    chunk = []

            # Flush remaining
            if chunk:
                verse_text = " ".join(chunk).strip()
                if len(verse_text) > 15:
                    verse_num += 1
                    ref = f"{scroll['abbr']} {chapter_num}:{verse_num}"
                    existing = conn.execute(
                        "SELECT id FROM verses WHERE reference=? AND volume_id=?",
                        (ref, vol_id),
                    ).fetchone()
                    if not existing:
                        conn.execute(
                            "INSERT INTO verses(text, verse_number, reference, book_id, chapter_id, volume_id) VALUES(?,?,?,?,?,?)",
                            (verse_text, verse_num, ref, book_id, chapter_id, vol_id),
                        )
                        scroll_total += 1

        conn.commit()
        print(f"    {scroll_total} verses, {chapter_num} sections")
        total_verses += scroll_total

        # Update chapter count
        conn.execute("UPDATE books SET num_chapters=? WHERE id=?", (chapter_num, book_id))
        conn.commit()

    # Rebuild FTS
    print("\n=== Rebuilding FTS ===")
    try:
        conn.execute("DELETE FROM scriptures_fts")
        conn.execute("INSERT INTO scriptures_fts(rowid, text) SELECT rowid, text FROM verses")
        conn.commit()
        fts_count = conn.execute("SELECT COUNT(*) FROM scriptures_fts").fetchone()[0]
        print(f"    FTS rebuilt: {fts_count} entries")
    except Exception as e:
        print(f"    FTS error: {e}")

    # Summary
    dss_total = conn.execute(
        "SELECT COUNT(*) FROM verses WHERE volume_id=?", (vol_id,)
    ).fetchone()[0]
    print(f"\n=== Summary ===")
    print(f"    New verses added: {total_verses}")
    print(f"    Total DSS verses: {dss_total}")

    conn.close()


if __name__ == "__main__":
    main()
