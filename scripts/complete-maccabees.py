#!/usr/bin/env python3
"""Complete ALL remaining content gaps in Coptic and Russian Orthodox volumes.

Books addressed:
- 1 Maccabees (book_id=4102 Coptic, 4009 Russian) — fill to 16 chapters
- 2 Maccabees (book_id=4103 Coptic, 4010 Russian) — fill to 15 chapters
- Letter of Jeremiah (book_id=4105 Coptic, 4008 Russian) — fill to 72 verses
- 1 Esdras (book_id=4001 Russian) — fill sparse chapters

Idempotent: checks existing content before inserting, never deletes.
Sources: KJV Apocrypha 1611 (public domain).
"""

import os
import sqlite3
import json
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "..", "data", "scriptures.db")
DATA_DIR = os.path.join(SCRIPT_DIR, "verse_data")

VOLUME_TITLES = {200: "Coptic Bible", 400: "Russian Orthodox Bible"}


def load_verse_data(filename):
    """Load verse data from a JSON file in verse_data/."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


def get_or_create_chapter(conn, book_id, chapter_number):
    """Get existing chapter_id or create new chapter record."""
    row = conn.execute(
        "SELECT id FROM chapters WHERE book_id=? AND chapter_number=?",
        (book_id, chapter_number),
    ).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO chapters (book_id, chapter_number, num_verses) VALUES (?, ?, 0)",
        (book_id, chapter_number),
    )
    return cur.lastrowid


def get_existing_verses(conn, chapter_id):
    """Return set of verse_numbers that already exist in a chapter."""
    rows = conn.execute(
        "SELECT verse_number FROM verses WHERE chapter_id=?", (chapter_id,)
    ).fetchall()
    return {r[0] for r in rows}


def insert_verses(conn, book_id, volume_id, chapter_id, chapter_number,
                  verses_dict, book_abbrev):
    """Insert missing verses into a chapter. verses_dict = {verse_num: text}."""
    existing = get_existing_verses(conn, chapter_id)
    inserted = 0
    for vnum_str, text in sorted(verses_dict.items(), key=lambda x: int(x[0])):
        vnum = int(vnum_str)
        if vnum in existing:
            continue
        ref = f"{book_abbrev} {chapter_number}:{vnum}"
        conn.execute(
            "INSERT INTO verses (chapter_id, book_id, volume_id, verse_number, text, reference) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (chapter_id, book_id, volume_id, vnum, text, ref),
        )
        inserted += 1
    return inserted


def update_chapter_verse_count(conn, chapter_id):
    """Update num_verses on chapter to actual count."""
    count = conn.execute(
        "SELECT COUNT(*) FROM verses WHERE chapter_id=?", (chapter_id,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE chapters SET num_verses=? WHERE id=?", (count, chapter_id)
    )
    return count


def update_book_metadata(conn, book_id):
    """Update num_chapters on book."""
    count = conn.execute(
        "SELECT COUNT(*) FROM chapters WHERE book_id=?", (book_id,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE books SET num_chapters=? WHERE id=?", (count, book_id)
    )
    return count


def rebuild_fts(conn):
    """Rebuild the scriptures_fts index."""
    print("\nRebuilding FTS index...")
    conn.execute("DELETE FROM scriptures_fts;")
    conn.execute("""
        INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title)
        SELECT v.id, v.text, v.reference, b.title, vol.title
        FROM verses v
        JOIN books b ON v.book_id = b.id
        JOIN volumes vol ON v.volume_id = vol.id;
    """)
    print("FTS index rebuilt.")


def print_stats(conn, label, book_ids):
    """Print verse/chapter counts for given books."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    for bid in book_ids:
        row = conn.execute(
            "SELECT title, num_chapters FROM books WHERE id=?", (bid,)
        ).fetchone()
        if not row:
            continue
        title, nch = row
        total_v = conn.execute(
            "SELECT COUNT(*) FROM verses v JOIN chapters c ON v.chapter_id=c.id WHERE c.book_id=?",
            (bid,),
        ).fetchone()[0]
        vol = conn.execute(
            "SELECT vol.title FROM books b JOIN volumes vol ON b.volume_id=vol.id WHERE b.id=?",
            (bid,),
        ).fetchone()[0]
        print(f"  [{vol}] {title}: {nch} chapters, {total_v} verses")


def process_book(conn, book_id, volume_id, book_abbrev, data_file):
    """Process a single book: load data, insert missing verses."""
    data = load_verse_data(data_file)
    total_inserted = 0
    for ch_str, verses_dict in sorted(data.items(), key=lambda x: int(x[0])):
        ch_num = int(ch_str)
        chapter_id = get_or_create_chapter(conn, book_id, ch_num)
        inserted = insert_verses(
            conn, book_id, volume_id, chapter_id, ch_num, verses_dict, book_abbrev
        )
        new_count = update_chapter_verse_count(conn, chapter_id)
        if inserted > 0:
            print(f"  {book_abbrev} ch {ch_num}: +{inserted} verses (now {new_count})")
        total_inserted += inserted
    nch = update_book_metadata(conn, book_id)
    print(f"  {book_abbrev} (book_id={book_id}): {nch} chapters, +{total_inserted} verses total")
    return total_inserted


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")

    all_book_ids = [4102, 4103, 4105, 4009, 4010, 4008, 4001]
    print_stats(conn, "BEFORE", all_book_ids)

    grand_total = 0

    # 1 Maccabees — Coptic (4102, vol 200) and Russian (4009, vol 400)
    print("\n--- 1 Maccabees ---")
    grand_total += process_book(conn, 4102, 200, "1 Maccabees", "1maccabees.json")
    grand_total += process_book(conn, 4009, 400, "1 Maccabees", "1maccabees.json")

    # 2 Maccabees — Coptic (4103, vol 200) and Russian (4010, vol 400)
    print("\n--- 2 Maccabees ---")
    grand_total += process_book(conn, 4103, 200, "2 Maccabees", "2maccabees.json")
    grand_total += process_book(conn, 4010, 400, "2 Maccabees", "2maccabees.json")

    # Letter of Jeremiah — Coptic (4105, vol 200) and Russian (4008, vol 400)
    print("\n--- Letter of Jeremiah ---")
    grand_total += process_book(conn, 4105, 200, "Letter of Jeremiah", "letter_of_jeremiah.json")
    grand_total += process_book(conn, 4008, 400, "Letter of Jeremiah", "letter_of_jeremiah.json")

    # 1 Esdras — Russian only (4001, vol 400)
    print("\n--- 1 Esdras ---")
    grand_total += process_book(conn, 4001, 400, "1 Esdras", "1esdras.json")

    rebuild_fts(conn)

    conn.commit()

    print_stats(conn, "AFTER", all_book_ids)
    print(f"\nGrand total: +{grand_total} verses inserted")
    conn.close()


if __name__ == "__main__":
    main()
