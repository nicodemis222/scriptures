#!/usr/bin/env python3
"""Import public domain scriptures from sacred-texts.com into ARK's scriptures DB."""

import os
import re
import sqlite3
import sys

try:
    import requests
    from bs4 import BeautifulSoup, FeatureNotFound
except ImportError:
    os.system(f"{sys.executable} -m pip install requests beautifulsoup4 lxml")
    import requests
    from bs4 import BeautifulSoup, FeatureNotFound

# Use lxml if available (handles malformed HTML better), fallback to html.parser
try:
    BeautifulSoup("<p>test</p>", "lxml")
    PARSER = "lxml"
except (FeatureNotFound, Exception):
    PARSER = "html.parser"

DB = os.path.join(os.path.dirname(__file__), "..", "data", "scriptures", "scriptures.db")
conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")

HEADERS = {"User-Agent": "ARK-Scriptures-Importer/1.0"}


def get_or_create_volume(abbr, title):
    row = conn.execute("SELECT id FROM volumes WHERE abbreviation=?", (abbr,)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO volumes(title, abbreviation) VALUES(?,?)", (title, abbr))
    conn.commit()
    return cur.lastrowid


def get_or_create_book(title, abbr, volume_id, num_chapters=1, book_order=1):
    row = conn.execute("SELECT id FROM books WHERE title=? AND volume_id=?", (title, volume_id)).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO books(title, abbreviation, long_title, num_chapters, book_order, volume_id) VALUES(?,?,?,?,?,?)",
        (title, abbr, title, num_chapters, book_order, volume_id),
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_chapter(book_id, chapter_num):
    row = conn.execute("SELECT id FROM chapters WHERE book_id=? AND chapter_number=?", (book_id, chapter_num)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO chapters(chapter_number, book_id) VALUES(?,?)", (chapter_num, book_id))
    conn.commit()
    return cur.lastrowid


def insert_verse(text, verse_num, reference, book_id, chapter_id, volume_id):
    existing = conn.execute("SELECT id FROM verses WHERE reference=? AND volume_id=?", (reference, volume_id)).fetchone()
    if existing:
        return
    conn.execute(
        "INSERT INTO verses(text, verse_number, reference, book_id, chapter_id, volume_id) VALUES(?,?,?,?,?,?)",
        (text.strip(), verse_num, reference, book_id, chapter_id, volume_id),
    )


def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    SKIP: {url} ({e})")
        return None


# ── Book of Enoch (R.H. Charles 1917) ──────────────────────────────────────

def import_enoch():
    print("=== Book of Enoch (1 Enoch) ===")
    vol_id = get_or_create_volume("coptic", "Coptic Bible")
    book_id = get_or_create_book("1 Enoch", "1en", vol_id, num_chapters=108, book_order=10)
    total = 0

    # sacred-texts.com Book of Enoch: boe002.htm through boe108.htm (approx)
    for page_num in range(2, 112):
        url = f"https://www.sacred-texts.com/bib/boe/boe{page_num:03d}.htm"
        html = fetch_page(url)
        if not html:
            continue

        soup = BeautifulSoup(html, PARSER)
        # Try to find chapter number from title or h tags
        title_tag = soup.find("title")
        title_text = title_tag.get_text() if title_tag else ""

        chap_match = re.search(r"Chapter\s+(\w+)", title_text, re.IGNORECASE)
        if not chap_match:
            # Try Roman numerals or just use page number
            chap_match = re.search(r"(\d+)", title_text)

        chap_num = int(chap_match.group(1)) if chap_match and chap_match.group(1).isdigit() else page_num - 1
        if chap_num < 1 or chap_num > 108:
            continue

        chapter_id = get_or_create_chapter(book_id, chap_num)

        # Extract paragraph text
        paragraphs = soup.find_all("p")
        verse_num = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 10 or "sacred-texts" in text.lower():
                continue
            # Split on verse numbers if present (e.g., "1. And ..." or numbered)
            verse_parts = re.split(r"(?:^|\s)(\d+)\.\s", text)
            if len(verse_parts) > 2:
                for i in range(1, len(verse_parts), 2):
                    vn = int(verse_parts[i])
                    vt = verse_parts[i + 1].strip() if i + 1 < len(verse_parts) else ""
                    if vt and len(vt) > 5:
                        ref = f"1 Enoch {chap_num}:{vn}"
                        insert_verse(vt, vn, ref, book_id, chapter_id, vol_id)
                        total += 1
            else:
                verse_num += 1
                ref = f"1 Enoch {chap_num}:{verse_num}"
                insert_verse(text, verse_num, ref, book_id, chapter_id, vol_id)
                total += 1

    conn.commit()
    print(f"    Imported {total} verses")
    return total


# ── Book of Jubilees ───────────────────────────────────────────────────────

def import_jubilees():
    print("=== Book of Jubilees ===")
    vol_id = get_or_create_volume("coptic", "Coptic Bible")
    book_id = get_or_create_book("Jubilees", "jub", vol_id, num_chapters=50, book_order=11)
    total = 0

    for page_num in range(2, 55):
        url = f"https://www.sacred-texts.com/bib/jub/jub{page_num:02d}.htm"
        html = fetch_page(url)
        if not html:
            continue

        soup = BeautifulSoup(html, PARSER)
        title_tag = soup.find("title")
        title_text = title_tag.get_text() if title_tag else ""
        chap_match = re.search(r"Chapter\s+(\w+)", title_text, re.IGNORECASE)
        if not chap_match:
            chap_match = re.search(r"(\d+)", title_text)
        chap_num = int(chap_match.group(1)) if chap_match and chap_match.group(1).isdigit() else page_num - 1
        if chap_num < 1:
            continue

        chapter_id = get_or_create_chapter(book_id, chap_num)
        paragraphs = soup.find_all("p")
        verse_num = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 10 or "sacred-texts" in text.lower() or "chapter" in text.lower()[:20]:
                continue
            verse_num += 1
            ref = f"Jubilees {chap_num}:{verse_num}"
            insert_verse(text, verse_num, ref, book_id, chapter_id, vol_id)
            total += 1

    conn.commit()
    print(f"    Imported {total} verses")
    return total


# ── Wisdom of Solomon ──────────────────────────────────────────────────────

def import_wisdom():
    print("=== Wisdom of Solomon ===")
    vol_id = get_or_create_volume("coptic", "Coptic Bible")
    book_id = get_or_create_book("Wisdom of Solomon", "wis", vol_id, num_chapters=19, book_order=12)
    total = 0

    # Try sacred-texts apocrypha section
    for chap in range(1, 20):
        url = f"https://www.sacred-texts.com/bib/apo/wis{chap:03d}.htm"
        html = fetch_page(url)
        if not html:
            continue

        soup = BeautifulSoup(html, PARSER)
        chapter_id = get_or_create_chapter(book_id, chap)
        paragraphs = soup.find_all("p")
        verse_num = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 10:
                continue
            # Look for verse numbering
            parts = re.split(r"(\d+):(\d+)", text)
            if len(parts) > 1:
                continue  # Skip reference lines
            verse_num += 1
            ref = f"Wisdom {chap}:{verse_num}"
            insert_verse(text, verse_num, ref, book_id, chapter_id, vol_id)
            total += 1

    conn.commit()
    print(f"    Imported {total} verses")
    return total


# ── Sirach (Ecclesiasticus) ────────────────────────────────────────────────

def import_sirach():
    print("=== Sirach (Ecclesiasticus) ===")
    vol_id = get_or_create_volume("coptic", "Coptic Bible")
    book_id = get_or_create_book("Sirach", "sir", vol_id, num_chapters=51, book_order=13)
    total = 0

    for chap in range(1, 52):
        url = f"https://www.sacred-texts.com/bib/apo/sir{chap:03d}.htm"
        html = fetch_page(url)
        if not html:
            continue

        soup = BeautifulSoup(html, PARSER)
        chapter_id = get_or_create_chapter(book_id, chap)
        paragraphs = soup.find_all("p")
        verse_num = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 10:
                continue
            verse_num += 1
            ref = f"Sirach {chap}:{verse_num}"
            insert_verse(text, verse_num, ref, book_id, chapter_id, vol_id)
            total += 1

    conn.commit()
    print(f"    Imported {total} verses")
    return total


# ── 2 Esdras (for Russian Orthodox) ───────────────────────────────────────

def import_2esdras():
    print("=== 2 Esdras ===")
    vol_id = get_or_create_volume("russian", "Russian Orthodox Bible")
    book_id = get_or_create_book("2 Esdras", "2es", vol_id, num_chapters=16, book_order=1)
    total = 0

    for chap in range(1, 17):
        url = f"https://www.sacred-texts.com/bib/apo/es2{chap:03d}.htm"
        html = fetch_page(url)
        if not html:
            continue

        soup = BeautifulSoup(html, PARSER)
        chapter_id = get_or_create_chapter(book_id, chap)
        paragraphs = soup.find_all("p")
        verse_num = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 10:
                continue
            verse_num += 1
            ref = f"2 Esdras {chap}:{verse_num}"
            insert_verse(text, verse_num, ref, book_id, chapter_id, vol_id)
            total += 1

    conn.commit()
    print(f"    Imported {total} verses")
    return total


# ── Rebuild FTS ────────────────────────────────────────────────────────────

def rebuild_fts():
    print("=== Rebuilding FTS index ===")
    try:
        conn.execute("DELETE FROM scriptures_fts")
        conn.execute("INSERT INTO scriptures_fts(rowid, text) SELECT rowid, text FROM verses")
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM scriptures_fts").fetchone()[0]
        print(f"    FTS rebuilt with {count} entries")
    except Exception as e:
        print(f"    FTS rebuild failed: {e}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print(f"Database: {DB}")
    before = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    print(f"Verses before: {before}")
    print()

    totals = {}
    totals["enoch"] = import_enoch()
    totals["jubilees"] = import_jubilees()
    totals["wisdom"] = import_wisdom()
    totals["sirach"] = import_sirach()
    totals["2esdras"] = import_2esdras()

    rebuild_fts()

    after = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    print()
    print(f"=== Summary ===")
    print(f"Verses before: {before}")
    print(f"Verses after:  {after}")
    print(f"Added:         {after - before}")
    for name, count in totals.items():
        print(f"  {name}: {count}")

    conn.close()


if __name__ == "__main__":
    main()
