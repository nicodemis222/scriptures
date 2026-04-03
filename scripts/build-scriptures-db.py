#!/usr/bin/env python3
"""Build scriptures.db — scripture reference database for ARK.

Imports from lds-scriptures and bible_databases repos if available.
Creates FTS5 search index across all verses for offline scripture study.
Falls back to creating the schema with sample data if repos not cloned.
"""

import os
import sqlite3
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "scriptures", "scriptures.db")

SCRIPTURE_DIR = os.path.join(DATA_DIR, "scriptures")
LDS_REPO = os.path.join(SCRIPTURE_DIR, "lds-scriptures")
BIBLE_REPO = os.path.join(SCRIPTURE_DIR, "bible_databases")

SCHEMA = """
CREATE TABLE IF NOT EXISTS volumes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    abbreviation TEXT DEFAULT '',
    description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    volume_id INTEGER REFERENCES volumes(id),
    title TEXT NOT NULL,
    abbreviation TEXT DEFAULT '',
    long_title TEXT DEFAULT '',
    num_chapters INTEGER DEFAULT 0,
    book_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER REFERENCES books(id),
    chapter_number INTEGER NOT NULL,
    num_verses INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER REFERENCES chapters(id),
    book_id INTEGER REFERENCES books(id),
    volume_id INTEGER REFERENCES volumes(id),
    verse_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    reference TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verse_id INTEGER REFERENCES verses(id),
    label TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    color TEXT DEFAULT 'yellow',
    created_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS scriptures_fts USING fts5(
    text, reference, book_title, volume_title,
    content='',
    tokenize='porter'
);
"""


CANONICAL_BOOK_ORDER = {
    # Book of Mormon (1-15)
    "1 Nephi": 1, "2 Nephi": 2, "Jacob": 3, "Enos": 4, "Jarom": 5,
    "Omni": 6, "Words of Mormon": 7, "Mosiah": 8, "Alma": 9, "Helaman": 10,
    "3 Nephi": 11, "4 Nephi": 12, "Mormon": 13, "Ether": 14, "Moroni": 15,
    # Doctrine and Covenants (1-138)
    **{f"Section {i}": i for i in range(1, 139)},
    **{f"D&C {i}": i for i in range(1, 139)},
    "Official Declaration 1": 139, "Official Declaration 2": 140,
    # Pearl of Great Price (1-5)
    "Moses": 1, "Abraham": 2, "Joseph Smith—Matthew": 3,
    "Joseph Smith—History": 4, "Articles of Faith": 5,
    # Old Testament (1-39)
    "Genesis": 1, "Exodus": 2, "Leviticus": 3, "Numbers": 4, "Deuteronomy": 5,
    "Joshua": 6, "Judges": 7, "Ruth": 8, "1 Samuel": 9, "2 Samuel": 10,
    "1 Kings": 11, "2 Kings": 12, "1 Chronicles": 13, "2 Chronicles": 14,
    "Ezra": 15, "Nehemiah": 16, "Esther": 17, "Job": 18, "Psalms": 19,
    "Proverbs": 20, "Ecclesiastes": 21, "Song of Solomon": 22, "Isaiah": 23,
    "Jeremiah": 24, "Lamentations": 25, "Ezekiel": 26, "Daniel": 27,
    "Hosea": 28, "Joel": 29, "Amos": 30, "Obadiah": 31, "Jonah": 32,
    "Micah": 33, "Nahum": 34, "Habakkuk": 35, "Zephaniah": 36, "Haggai": 37,
    "Zechariah": 38, "Malachi": 39,
    # New Testament (1-27)
    "Matthew": 1, "Mark": 2, "Luke": 3, "John": 4, "Acts": 5,
    "Romans": 6, "1 Corinthians": 7, "2 Corinthians": 8, "Galatians": 9,
    "Ephesians": 10, "Philippians": 11, "Colossians": 12,
    "1 Thessalonians": 13, "2 Thessalonians": 14, "1 Timothy": 15,
    "2 Timothy": 16, "Titus": 17, "Philemon": 18, "Hebrews": 19,
    "James": 20, "1 Peter": 21, "2 Peter": 22, "1 John": 23, "2 John": 24,
    "3 John": 25, "Jude": 26, "Revelation": 27,
}


def fix_book_order(conn):
    """Set canonical book_order for all standard works based on title."""
    for title, order in CANONICAL_BOOK_ORDER.items():
        conn.execute(
            "UPDATE books SET book_order = ? WHERE title = ?",
            (order, title),
        )


def import_lds_scriptures(conn):
    """Import from mormon-documentation-project/lds-scriptures SQLite database."""
    # Look for the SQLite file in the cloned repo
    db_candidates = glob.glob(os.path.join(LDS_REPO, "**/*.db"), recursive=True) + \
                    glob.glob(os.path.join(LDS_REPO, "**/*.sqlite"), recursive=True) + \
                    glob.glob(os.path.join(LDS_REPO, "**/*.sqlite3"), recursive=True)

    if not db_candidates:
        print("  WARNING: No SQLite file found in lds-scriptures repo")
        return False

    src_path = db_candidates[0]
    print(f"  Importing from {src_path}")

    src = sqlite3.connect(src_path)
    src.row_factory = sqlite3.Row

    # Check what tables exist in source
    tables = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"  Source tables: {tables}")

    verse_count = 0

    # Map source volume_lds_url abbreviations to our frontend abbreviations
    ABBR_MAP = {"bm": "bom"}  # source uses 'bm', frontend expects 'bom'

    # Try to import based on common lds-scriptures schema
    if "verses" in tables and "chapters" in tables and "books" in tables and "volumes" in tables:
        # Import volumes
        vol_titles = {}  # vol_id -> title
        for row in src.execute("SELECT * FROM volumes").fetchall():
            rd = dict(row)
            vol_id = rd.get("id")
            title = rd.get("volume_title", rd.get("title", ""))
            raw_abbr = rd.get("volume_lds_url", rd.get("abbreviation", ""))
            abbr = ABBR_MAP.get(raw_abbr, raw_abbr)
            desc = rd.get("volume_subtitle", rd.get("description", ""))
            vol_titles[vol_id] = title
            conn.execute(
                "INSERT OR IGNORE INTO volumes (id, title, abbreviation, description) VALUES (?, ?, ?, ?)",
                (vol_id, title, abbr, desc),
            )

        # Import books and count chapters per book
        book_titles = {}  # book_id -> book_title
        book_vol = {}     # book_id -> volume_id
        for row in src.execute("SELECT * FROM books").fetchall():
            rd = dict(row)
            bid = rd["id"]
            vid = rd.get("volume_id")
            btitle = rd.get("book_title", rd.get("title", ""))
            book_titles[bid] = btitle
            book_vol[bid] = vid
            # Count chapters for this book from source
            num_ch = src.execute("SELECT COUNT(*) FROM chapters WHERE book_id = ?", (bid,)).fetchone()[0]
            conn.execute(
                """INSERT OR IGNORE INTO books (id, volume_id, title, abbreviation, long_title, num_chapters, book_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    bid, vid, btitle,
                    rd.get("book_short_title", rd.get("book_lds_url", rd.get("abbreviation", ""))),
                    rd.get("book_long_title", rd.get("long_title", "")),
                    num_ch,
                    bid,  # use id as book_order
                ),
            )

        # Import chapters
        for row in src.execute("SELECT * FROM chapters").fetchall():
            rd = dict(row)
            conn.execute(
                "INSERT INTO chapters (id, book_id, chapter_number) VALUES (?, ?, ?)",
                (rd["id"], rd["book_id"], rd["chapter_number"]),
            )

        # Import verses using JOIN to resolve book_id, volume_id, chapter_number, book_title
        query = """
            SELECT v.id, v.chapter_id, v.verse_number, v.scripture_text,
                   c.book_id, c.chapter_number, b.volume_id,
                   b.book_title, b.book_short_title
            FROM verses v
            JOIN chapters c ON c.id = v.chapter_id
            JOIN books b ON b.id = c.book_id
            ORDER BY v.id
        """
        for row in src.execute(query).fetchall():
            vid, ch_id, verse_num, text, book_id, ch_num, volume_id, btitle, bshort = row
            ref = f"{btitle} {ch_num}:{verse_num}"
            vol_title = vol_titles.get(volume_id, "")

            conn.execute(
                """INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (vid, ch_id, book_id, volume_id, verse_num, text, ref),
            )
            verse_count += 1

            # FTS index
            conn.execute(
                "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?, ?, ?, ?, ?)",
                (vid, text, ref, btitle, vol_title),
            )

        # Update chapter verse counts
        conn.execute("""
            UPDATE chapters SET num_verses = (
                SELECT COUNT(*) FROM verses WHERE verses.chapter_id = chapters.id
            )
        """)

    src.close()
    print(f"  Imported {verse_count} verses from LDS scriptures")
    return verse_count > 0


def import_bible_databases(conn):
    """Import from scrollmapper/bible_databases."""
    db_candidates = glob.glob(os.path.join(BIBLE_REPO, "**/*.db"), recursive=True) + \
                    glob.glob(os.path.join(BIBLE_REPO, "**/*.sqlite"), recursive=True) + \
                    glob.glob(os.path.join(BIBLE_REPO, "**/*.sqlite3"), recursive=True)

    if not db_candidates:
        print("  WARNING: No SQLite file found in bible_databases repo")
        return False

    # Prefer a KJV file
    kjv_files = [f for f in db_candidates if "kjv" in f.lower() or "bible" in f.lower()]
    src_path = kjv_files[0] if kjv_files else db_candidates[0]
    print(f"  Importing from {src_path}")

    src = sqlite3.connect(src_path)
    src.row_factory = sqlite3.Row

    tables = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"  Source tables: {tables}")

    # Find the main verses table — handle scrollmapper format (KJV_verses) and older format
    verse_table = None
    books_table = None
    for candidate in ["KJV_verses", "t_kjv", "t_asv", "t_web", "verses", "bible"]:
        if candidate in tables:
            verse_table = candidate
            break
    for candidate in ["KJV_books", "key_english", "books"]:
        if candidate in tables:
            books_table = candidate
            break

    if not verse_table:
        for t in tables:
            cols = [r[1] for r in src.execute(f"PRAGMA table_info({t})").fetchall()]
            if "text" in cols or "t" in cols or "verse_text" in cols:
                verse_table = t
                break

    if not verse_table:
        print("  WARNING: Could not identify verse table in bible database")
        src.close()
        return False

    cols = [r[1] for r in src.execute(f"PRAGMA table_info({verse_table})").fetchall()]
    print(f"  Using verse table '{verse_table}' with columns: {cols}")

    # Get book names
    book_names = {}
    if books_table:
        bcols = [r[1] for r in src.execute(f"PRAGMA table_info({books_table})").fetchall()]
        for row in src.execute(f"SELECT * FROM {books_table}").fetchall():
            rd = dict(row)
            bid = rd.get("id", rd.get("b", rd.get("book_number", 0)))
            bname = rd.get("name", rd.get("n", rd.get("book_name", f"Book {bid}")))
            book_names[bid] = bname

    # Ensure Bible volume exists (id=100 to avoid collision with LDS volumes 1-5)
    conn.execute("INSERT OR IGNORE INTO volumes (id, title, abbreviation, description) VALUES (100, 'Holy Bible (KJV)', 'bible', 'King James Version')")

    # Create book records for Bible books
    for bid, bname in sorted(book_names.items()):
        bible_book_id = bid + 1000  # offset to avoid collisions with LDS book IDs
        conn.execute(
            "INSERT OR IGNORE INTO books (id, volume_id, title, abbreviation, long_title, num_chapters, book_order) VALUES (?, 100, ?, ?, ?, 0, ?)",
            (bible_book_id, bname, bname[:10], bname, bid),
        )

    # Get existing max IDs to avoid conflicts
    max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM verses").fetchone()[0]
    max_ch_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM chapters").fetchone()[0]
    verse_count = 0
    chapter_map = {}  # (book_id, chapter_num) -> chapter_id

    for row in src.execute(f"SELECT * FROM {verse_table}").fetchall():
        rd = dict(row)
        # Handle both formats: scrollmapper (book_id, chapter, verse, text) and older (b, c, v, t)
        book_num = rd.get("book_id", rd.get("b", rd.get("book", 0)))
        chapter = rd.get("chapter", rd.get("c", 0))
        verse_num = rd.get("verse", rd.get("v", 0))
        text = rd.get("text", rd.get("t", rd.get("verse_text", "")))

        book_title = book_names.get(book_num, f"Book {book_num}")
        ref = f"{book_title} {chapter}:{verse_num}"
        book_id = book_num + 1000

        # Create chapter record if needed
        ch_key = (book_id, chapter)
        if ch_key not in chapter_map:
            max_ch_id += 1
            chapter_map[ch_key] = max_ch_id
            conn.execute(
                "INSERT INTO chapters (id, book_id, chapter_number) VALUES (?, ?, ?)",
                (max_ch_id, book_id, chapter),
            )
        ch_id = chapter_map[ch_key]

        max_id += 1
        conn.execute(
            """INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference)
               VALUES (?, ?, ?, 100, ?, ?, ?)""",
            (max_id, ch_id, book_id, verse_num, text, ref),
        )
        verse_count += 1

        conn.execute(
            "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?, ?, ?, ?, 'Holy Bible (KJV)')",
            (max_id, text, ref, book_title),
        )

    # Update chapter verse counts and book num_chapters
    conn.execute("""
        UPDATE chapters SET num_verses = (
            SELECT COUNT(*) FROM verses WHERE verses.chapter_id = chapters.id
        )
    """)
    conn.execute("""
        UPDATE books SET num_chapters = (
            SELECT COUNT(*) FROM chapters WHERE chapters.book_id = books.id
        ) WHERE volume_id = 100
    """)

    src.close()
    print(f"  Imported {verse_count} verses from Bible database")
    return verse_count > 0


def seed_sample_data(conn):
    """Seed with sample scripture data when repos are not available."""
    print("  Scripture repos not found — seeding sample data...")
    print(f"  (Clone repos to {SCRIPTURE_DIR} and re-run for full import)")

    # Create volumes
    volumes = [
        (1, "Old Testament", "ot", "Hebrew Bible / Old Testament"),
        (2, "New Testament", "nt", "Christian New Testament"),
        (3, "Book of Mormon", "bom", "Another Testament of Jesus Christ"),
        (4, "Doctrine and Covenants", "dc", "Modern revelations"),
        (5, "Pearl of Great Price", "pgp", "Selected writings"),
    ]
    for v in volumes:
        conn.execute("INSERT INTO volumes (id, title, abbreviation, description) VALUES (?,?,?,?)", v)

    # Sample books
    books = [
        (1, 1, "Genesis", "Gen", "The First Book of Moses", 50, 1),
        (2, 1, "Psalms", "Ps", "The Book of Psalms", 150, 19),
        (3, 1, "Proverbs", "Prov", "The Proverbs of Solomon", 31, 20),
        (4, 1, "Isaiah", "Isa", "The Book of the Prophet Isaiah", 66, 23),
        (5, 2, "Matthew", "Matt", "The Gospel According to Matthew", 28, 40),
        (6, 2, "John", "John", "The Gospel According to John", 21, 43),
        (7, 2, "Romans", "Rom", "The Epistle to the Romans", 16, 45),
        (8, 2, "James", "James", "The General Epistle of James", 5, 59),
        (9, 3, "1 Nephi", "1 Ne", "The First Book of Nephi", 22, 1),
        (10, 3, "Alma", "Alma", "The Book of Alma", 63, 8),
        (11, 3, "Moroni", "Moro", "The Book of Moroni", 10, 15),
        (12, 4, "D&C 89", "D&C 89", "The Word of Wisdom", 1, 89),
        (13, 5, "Moses", "Moses", "The Book of Moses", 8, 1),
        (14, 5, "Abraham", "Abr", "The Book of Abraham", 5, 3),
    ]
    for b in books:
        conn.execute("INSERT INTO books (id, volume_id, title, abbreviation, long_title, num_chapters, book_order) VALUES (?,?,?,?,?,?,?)", b)

    # Sample verses: (book_id, volume_id, chapter_number, verse_number, text, reference)
    sample_verses = [
        (1, 1, 1, 1, "In the beginning God created the heaven and the earth.", "Genesis 1:1"),
        (1, 1, 1, 27, "So God created man in his own image, in the image of God created he him; male and female created he them.", "Genesis 1:27"),
        (2, 1, 23, 1, "The Lord is my shepherd; I shall not want.", "Psalms 23:1"),
        (2, 1, 23, 2, "He maketh me to lie down in green pastures: he leadeth me beside the still waters.", "Psalms 23:2"),
        (2, 1, 23, 3, "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.", "Psalms 23:3"),
        (2, 1, 23, 4, "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me.", "Psalms 23:4"),
        (2, 1, 27, 1, "The Lord is my light and my salvation; whom shall I fear? the Lord is the strength of my life; of whom shall I be afraid?", "Psalms 27:1"),
        (2, 1, 46, 1, "God is our refuge and strength, a very present help in trouble.", "Psalms 46:1"),
        (3, 1, 3, 5, "Trust in the Lord with all thine heart; and lean not unto thine own understanding.", "Proverbs 3:5"),
        (3, 1, 3, 6, "In all thy ways acknowledge him, and he shall direct thy paths.", "Proverbs 3:6"),
        (4, 1, 40, 31, "But they that wait upon the Lord shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint.", "Isaiah 40:31"),
        (4, 1, 41, 10, "Fear thou not; for I am with thee: be not dismayed; for I am thy God: I will strengthen thee; yea, I will help thee; yea, I will uphold thee with the right hand of my righteousness.", "Isaiah 41:10"),
        (5, 2, 7, 12, "Therefore all things whatsoever ye would that men should do to you, do ye even so to them: for this is the law and the prophets.", "Matthew 7:12"),
        (5, 2, 11, 28, "Come unto me, all ye that labour and are heavy laden, and I will give you rest.", "Matthew 11:28"),
        (6, 2, 14, 27, "Peace I leave with you, my peace I give unto you: not as the world giveth, give I unto you. Let not your heart be troubled, neither let it be afraid.", "John 14:27"),
        (6, 2, 16, 33, "These things I have spoken unto you, that in me ye might have peace. In the world ye shall have tribulation: but be of good cheer; I have overcome the world.", "John 16:33"),
        (7, 2, 8, 28, "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.", "Romans 8:28"),
        (8, 2, 1, 5, "If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and it shall be given him.", "James 1:5"),
        (9, 3, 3, 7, "And it came to pass that I, Nephi, said unto my father: I will go and do the things which the Lord hath commanded, for I know that the Lord giveth no commandments unto the children of men, save he shall prepare a way for them that they may accomplish the thing which he commandeth them.", "1 Nephi 3:7"),
        (10, 3, 5, 12, "And now, my sons, remember, remember that it is upon the rock of our Redeemer, who is Christ, the Son of God, that ye must build your foundation.", "Helaman 5:12"),
        (11, 3, 10, 5, "And by the power of the Holy Ghost ye may know the truth of all things.", "Moroni 10:5"),
    ]

    # Build chapters from verse data — collect unique (book_id, chapter_number) pairs
    chapter_map = {}  # (book_id, chapter_num) -> chapter_id
    chapter_id = 0
    for book_id, volume_id, chapter_num, verse_num, text, ref in sample_verses:
        key = (book_id, chapter_num)
        if key not in chapter_map:
            chapter_id += 1
            chapter_map[key] = chapter_id
            conn.execute(
                "INSERT INTO chapters (id, book_id, chapter_number) VALUES (?,?,?)",
                (chapter_id, book_id, chapter_num),
            )

    print(f"  Created {chapter_id} chapter records")

    verse_id = 0
    for book_id, volume_id, chapter_num, verse_num, text, ref in sample_verses:
        verse_id += 1
        ch_id = chapter_map[(book_id, chapter_num)]
        conn.execute(
            "INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference) VALUES (?,?,?,?,?,?,?)",
            (verse_id, ch_id, book_id, volume_id, verse_num, text, ref),
        )

        # Get book and volume titles for FTS
        book_row = conn.execute("SELECT title FROM books WHERE id = ?", (book_id,)).fetchone()
        vol_row = conn.execute("SELECT title FROM volumes WHERE id = ?", (volume_id,)).fetchone()
        book_title = book_row[0] if book_row else ""
        vol_title = vol_row[0] if vol_row else ""

        conn.execute(
            "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?,?,?,?,?)",
            (verse_id, text, ref, book_title, vol_title),
        )

    # Update chapter verse counts
    conn.execute("""
        UPDATE chapters SET num_verses = (
            SELECT COUNT(*) FROM verses WHERE verses.chapter_id = chapters.id
        )
    """)

    print(f"  Seeded {verse_id} sample verses (run download-all.sh first for full import)")


def seed_additional_canons(conn):
    """Seed Coptic Bible, Dead Sea Scrolls, and Russian Orthodox Bible collections."""
    print("  Adding additional scripture canons...")

    max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM verses").fetchone()[0]
    max_ch_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM chapters").fetchone()[0]

    # ── Coptic Christian Bible (volume_id=200, book IDs 2000+) ──
    conn.execute(
        "INSERT OR IGNORE INTO volumes (id, title, abbreviation, description) VALUES (200, 'Coptic Bible', 'coptic', 'Ethiopian/Coptic Christian canon — includes books unique to the broader Alexandrian tradition')"
    )

    coptic_books = [
        (2001, 200, "1 Enoch", "1 En", "The Book of Enoch", 1, 1),
        (2002, 200, "Jubilees", "Jub", "The Book of Jubilees", 1, 2),
        (2003, 200, "1 Meqabyan", "1 Meq", "First Book of Meqabyan", 1, 3),
        (2004, 200, "2 Meqabyan", "2 Meq", "Second Book of Meqabyan", 1, 4),
        (2005, 200, "3 Meqabyan", "3 Meq", "Third Book of Meqabyan", 1, 5),
        (2006, 200, "Sirach", "Sir", "The Wisdom of Sirach (Ecclesiasticus)", 1, 6),
        (2007, 200, "Tobit", "Tob", "The Book of Tobit", 1, 7),
        (2008, 200, "Judith", "Jdt", "The Book of Judith", 1, 8),
        (2009, 200, "Baruch", "Bar", "The Book of Baruch", 1, 9),
        (2010, 200, "Wisdom of Solomon", "Wis", "The Wisdom of Solomon", 1, 10),
        (2011, 200, "4 Baruch", "4 Bar", "The Rest of the Words of Baruch", 1, 11),
        (2012, 200, "Ascension of Isaiah", "AscIs", "The Ascension of Isaiah", 1, 12),
        (2013, 200, "Joseph ben Gorion", "JBG", "Josippon — Pseudo-Josephus", 1, 13),
    ]
    for b in coptic_books:
        conn.execute(
            "INSERT OR IGNORE INTO books (id, volume_id, title, abbreviation, long_title, num_chapters, book_order) VALUES (?,?,?,?,?,?,?)", b
        )

    coptic_verses = [
        (2001, 200, 1, 1, "The words of the blessing of Enoch, wherewith he blessed the elect and righteous, who will be living in the day of tribulation, when all the wicked and godless are to be removed.", "1 Enoch 1:1"),
        (2001, 200, 1, 2, "And he took up his parable and said — Enoch a righteous man, whose eyes were opened by God, saw the vision of the Holy One in the heavens, which the angels showed me, and from them I heard everything, and from them I understood as I saw, but not for this generation, but for a remote one which is for to come.", "1 Enoch 1:2"),
        (2001, 200, 1, 3, "Concerning the elect I said, and took up my parable concerning them: The Holy Great One will come forth from His dwelling.", "1 Enoch 1:3"),
        (2001, 200, 1, 4, "And the eternal God will tread upon the earth, even on Mount Sinai, and appear from His camp, and appear in the strength of His might from the heaven of heavens.", "1 Enoch 1:4"),
        (2002, 200, 1, 1, "This is the history of the division of the days of the law and of the testimony, of the events of the years, of their year weeks, of their jubilees throughout all the years of the world.", "Jubilees 1:1"),
        (2002, 200, 1, 2, "As the Lord spoke to Moses on Mount Sinai when he went up to receive the tables of the law and of the commandment, according to the voice of God as he said unto him, Go up to the top of the Mount.", "Jubilees 1:2"),
        (2002, 200, 1, 3, "And the Lord said: Incline thine heart to every word which I shall speak to thee on this mount, and write them in a book in order that their generations may see how I have not forsaken them.", "Jubilees 1:3"),
        (2003, 200, 1, 1, "In those days, there arose against Israel enemies from the land of Midian, who oppressed them and seized their possessions.", "1 Meqabyan 1:1"),
        (2003, 200, 1, 2, "And the children of Israel cried out unto the Lord their God, saying: O Lord, look upon our affliction and save us from the hand of our enemies.", "1 Meqabyan 1:2"),
        (2006, 200, 1, 1, "All wisdom cometh from the Lord, and is with him for ever.", "Sirach 1:1"),
        (2006, 200, 1, 2, "Who can number the sand of the sea, and the drops of rain, and the days of eternity?", "Sirach 1:2"),
        (2006, 200, 1, 3, "Who can find out the height of heaven, and the breadth of the earth, and the deep, and wisdom?", "Sirach 1:3"),
        (2007, 200, 1, 1, "The book of the words of Tobit, son of Tobiel, the son of Ananiel, the son of Aduel, the son of Gabael, of the seed of Asael, of the tribe of Nephthali.", "Tobit 1:1"),
        (2007, 200, 1, 2, "Who in the time of Enemessar king of the Assyrians was led captive out of Thisbe, which is at the right hand of that city, which is called properly Nephthali in Galilee above Aser.", "Tobit 1:2"),
        (2008, 200, 1, 1, "In the twelfth year of the reign of Nabuchodonosor, who reigned in Nineve, the great city; in the days of Arphaxad, which reigned over the Medes in Ecbatane.", "Judith 1:1"),
        (2010, 200, 1, 1, "Love righteousness, ye that be judges of the earth: think of the Lord with a good heart, and in simplicity of heart seek him.", "Wisdom of Solomon 1:1"),
        (2010, 200, 1, 2, "For he will be found of them that tempt him not; and sheweth himself unto such as do not distrust him.", "Wisdom of Solomon 1:2"),
        (2012, 200, 1, 1, "In the twentieth year of the reign of Hezekiah king of Judah, Isaiah the son of Amoz and Jasub the son of Isaiah came from Gilgal to Jerusalem.", "Ascension of Isaiah 1:1"),
    ]

    chapter_map = {}
    for book_id, volume_id, ch_num, verse_num, text, ref in coptic_verses:
        ch_key = (book_id, ch_num)
        if ch_key not in chapter_map:
            max_ch_id += 1
            chapter_map[ch_key] = max_ch_id
            conn.execute("INSERT INTO chapters (id, book_id, chapter_number) VALUES (?, ?, ?)", (max_ch_id, book_id, ch_num))
        max_id += 1
        conn.execute(
            "INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (max_id, chapter_map[ch_key], book_id, volume_id, verse_num, text, ref),
        )
        book_title = ref.split(" ")[0] if " " in ref else ref
        # Use the full book name from ref (everything before the chapter:verse)
        ref_parts = ref.rsplit(" ", 1)
        bt = ref_parts[0] if len(ref_parts) == 2 else ref
        conn.execute(
            "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?, ?, ?, ?, 'Coptic Bible')",
            (max_id, text, ref, bt),
        )

    print(f"  Added {len(coptic_verses)} Coptic Bible verses")

    # ── Dead Sea Scrolls (volume_id=300, book IDs 3000+) ──
    conn.execute(
        "INSERT OR IGNORE INTO volumes (id, title, abbreviation, description) VALUES (300, 'Dead Sea Scrolls', 'dss', 'Ancient manuscripts discovered at Qumran (c. 250 BCE – 68 CE)')"
    )

    dss_books = [
        (3001, 300, "Community Rule", "1QS", "Serekh ha-Yahad — Rule of the Community", 1, 1),
        (3002, 300, "War Scroll", "1QM", "Milhamah — The War of the Sons of Light Against the Sons of Darkness", 1, 2),
        (3003, 300, "Thanksgiving Hymns", "1QH", "Hodayot — Thanksgiving Psalms", 1, 3),
        (3004, 300, "Temple Scroll", "11QT", "The Temple Scroll", 1, 4),
        (3005, 300, "Habakkuk Commentary", "1QpHab", "Pesher Habakkuk", 1, 5),
        (3006, 300, "Genesis Apocryphon", "1QapGen", "The Genesis Apocryphon", 1, 6),
        (3007, 300, "Damascus Document", "CD", "The Damascus Covenant", 1, 7),
        (3008, 300, "Messianic Rule", "1QSa", "Rule of the Congregation", 1, 8),
        (3009, 300, "Copper Scroll", "3Q15", "The Copper Scroll — Treasure Locations", 1, 9),
        (3010, 300, "Isaiah Scroll", "1QIsa", "The Great Isaiah Scroll", 1, 10),
        (3011, 300, "Psalms Scroll", "11QPsa", "The Great Psalms Scroll", 1, 11),
        (3012, 300, "Book of Giants", "4Q203", "The Book of Giants", 1, 12),
        (3013, 300, "Songs of Sabbath Sacrifice", "4Q400", "Shirot Olat ha-Shabbat", 1, 13),
    ]
    for b in dss_books:
        conn.execute(
            "INSERT OR IGNORE INTO books (id, volume_id, title, abbreviation, long_title, num_chapters, book_order) VALUES (?,?,?,?,?,?,?)", b
        )

    dss_verses = [
        (3001, 300, 1, 1, "For the Master. The Rule of the Community. He shall seek God with all his heart and soul, doing what is good and right before Him as He commanded by the hand of Moses and all His servants the Prophets.", "Community Rule 1:1"),
        (3001, 300, 1, 2, "He shall love all that He has chosen and hate all that He has despised. He shall keep far from all evil and cling to all good works.", "Community Rule 1:2"),
        (3001, 300, 1, 3, "He shall practice truth, righteousness, and justice upon earth, and shall walk no more in the stubbornness of a guilty heart and lustful eyes, doing all manner of evil.", "Community Rule 1:3"),
        (3001, 300, 1, 4, "He shall admit into the Covenant of Grace all those who freely devote themselves to the observance of God's precepts, that they may be joined to the counsel of God and may walk perfectly before Him.", "Community Rule 1:4"),
        (3002, 300, 1, 1, "For the Instructor. The Rule of War on the unleashing of the attack of the Sons of Light against the company of the Sons of Darkness, the army of Belial.", "War Scroll 1:1"),
        (3002, 300, 1, 2, "Against the band of Edom, Moab, and the sons of Ammon, and against the army of the sons of the East and the Philistines, and against the bands of the Kittim of Asshur, and their allies the ungodly of the Covenant.", "War Scroll 1:2"),
        (3002, 300, 1, 3, "The Sons of Levi, Judah, and Benjamin, the exiles in the desert, shall battle against them when the exiled Sons of Light return from the Desert of the Peoples to camp in the Desert of Jerusalem.", "War Scroll 1:3"),
        (3003, 300, 1, 1, "I thank Thee, O Lord, for Thou hast redeemed my soul from the Pit, and from the Hell of Abaddon Thou hast raised me up to everlasting height.", "Thanksgiving Hymns 1:1"),
        (3003, 300, 1, 2, "I walk on limitless level ground, and I know there is hope for him whom Thou hast shaped from dust for the everlasting Council.", "Thanksgiving Hymns 1:2"),
        (3003, 300, 1, 3, "Thou hast cleansed a perverse spirit of great sin, that it may stand with the host of the Holy Ones, and that it may enter into community with the congregation of the Sons of Heaven.", "Thanksgiving Hymns 1:3"),
        (3004, 300, 1, 1, "And the Lord spoke to Moses saying: Command the children of Israel and say to them: When you enter the land which I am giving you as an inheritance, and you dwell in it securely, you shall build a Sanctuary for Me.", "Temple Scroll 1:1"),
        (3004, 300, 1, 2, "You shall build it according to the plan which I shall show you, and you shall not build it in the way of the nations: they shall not build for Me a high place, nor a pillar, nor a molten image.", "Temple Scroll 1:2"),
        (3005, 300, 1, 1, "The oracle which Habakkuk the prophet received: How long, O Lord, shall I cry for help and Thou wilt not hear? Or cry to Thee, Violence! and Thou wilt not save?", "Habakkuk Commentary 1:1"),
        (3005, 300, 1, 2, "Interpreted, this concerns the beginning of the final generation. God told Habakkuk to write down that which would happen to the final generation, but He did not make known to him when time would come to an end.", "Habakkuk Commentary 1:2"),
        (3006, 300, 1, 1, "And I, Lamech, at the time of my marriage took unto myself a wife from among the daughters of my uncle. And she conceived by me and brought forth a son.", "Genesis Apocryphon 1:1"),
        (3006, 300, 1, 2, "And I looked upon the child, and his face was glorious, and when he opened his eyes the whole house was filled with light, like the light of the sun.", "Genesis Apocryphon 1:2"),
        (3007, 300, 1, 1, "And now, listen all you who know righteousness, and consider the works of God; for He has a dispute with all flesh and will condemn all those who despise Him.", "Damascus Document 1:1"),
        (3007, 300, 1, 2, "For when they were unfaithful and forsook Him, He hid His face from Israel and His Sanctuary, and delivered them up to the sword. But remembering the Covenant of the forefathers, He left a remnant.", "Damascus Document 1:2"),
        (3008, 300, 1, 1, "This is the Rule for all the congregation of Israel in the last days, when they shall join the Community to walk according to the law of the Sons of Zadok the Priests and of the men of their Covenant.", "Messianic Rule 1:1"),
        (3009, 300, 1, 1, "In the ruin which is in the valley of Achor, under the steps entering to the East, forty long cubits: a chest of silver and its vessels with a weight of seventeen talents.", "Copper Scroll 1:1"),
        (3009, 300, 1, 2, "In the sepulchral monument, in the third course of stones: one hundred gold ingots.", "Copper Scroll 1:2"),
        (3012, 300, 1, 1, "Then Ohya said to Mahway: The sleep of my eyes has departed, and I had a vision. A great tree was uprooted except for three of its roots.", "Book of Giants 1:1"),
        (3012, 300, 1, 2, "While I was watching, a great stone descended from heaven and all the land was submerged beneath a great flood of water.", "Book of Giants 1:2"),
        (3013, 300, 1, 1, "For the Instructor. Song of the sacrifice of the seventh Sabbath on the sixteenth of the month. Praise the God of the lofty heights, O you lofty ones among all the elim of knowledge.", "Songs of Sabbath Sacrifice 1:1"),
        (3013, 300, 1, 2, "Let the holiest of the godlike ones sanctify the King of glory who sanctifies by holiness all His holy ones.", "Songs of Sabbath Sacrifice 1:2"),
    ]

    for book_id, volume_id, ch_num, verse_num, text, ref in dss_verses:
        ch_key = (book_id, ch_num)
        if ch_key not in chapter_map:
            max_ch_id += 1
            chapter_map[ch_key] = max_ch_id
            conn.execute("INSERT INTO chapters (id, book_id, chapter_number) VALUES (?, ?, ?)", (max_ch_id, book_id, ch_num))
        max_id += 1
        ref_parts = ref.rsplit(" ", 1)
        bt = ref_parts[0] if len(ref_parts) == 2 else ref
        conn.execute(
            "INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (max_id, chapter_map[ch_key], book_id, volume_id, verse_num, text, ref),
        )
        conn.execute(
            "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?, ?, ?, ?, 'Dead Sea Scrolls')",
            (max_id, text, ref, bt),
        )

    print(f"  Added {len(dss_verses)} Dead Sea Scrolls verses")

    # ── Russian Orthodox Bible (volume_id=400, book IDs 4000+) ──
    # Includes deuterocanonical books unique to the Russian Orthodox canon
    conn.execute(
        "INSERT OR IGNORE INTO volumes (id, title, abbreviation, description) VALUES (400, 'Russian Orthodox Bible', 'russian', 'Additional deuterocanonical books of the Russian Orthodox canon')"
    )

    russian_books = [
        (4001, 400, "1 Esdras", "1 Esd", "The First Book of Esdras", 1, 1),
        (4002, 400, "2 Esdras", "2 Esd", "The Second Book of Esdras (3 Ezra)", 1, 2),
        (4003, 400, "Tobit", "Tob", "The Book of Tobit", 1, 3),
        (4004, 400, "Judith", "Jdt", "The Book of Judith", 1, 4),
        (4005, 400, "Wisdom of Solomon", "Wis", "The Book of the Wisdom of Solomon", 1, 5),
        (4006, 400, "Sirach", "Sir", "The Book of Sirach (Ecclesiasticus)", 1, 6),
        (4007, 400, "Baruch", "Bar", "The Book of the Prophet Baruch", 1, 7),
        (4008, 400, "Letter of Jeremiah", "EpJer", "The Epistle of Jeremiah", 1, 8),
        (4009, 400, "1 Maccabees", "1 Mac", "The First Book of the Maccabees", 1, 9),
        (4010, 400, "2 Maccabees", "2 Mac", "The Second Book of the Maccabees", 1, 10),
        (4011, 400, "3 Maccabees", "3 Mac", "The Third Book of the Maccabees", 1, 11),
        (4012, 400, "3 Esdras", "3 Esd", "The Third Book of Esdras", 1, 12),
        (4013, 400, "Prayer of Manasseh", "PrMan", "The Prayer of Manasseh", 1, 13),
        (4014, 400, "Psalm 151", "Ps151", "Psalm 151 — A Psalm of David", 1, 14),
    ]
    for b in russian_books:
        conn.execute(
            "INSERT OR IGNORE INTO books (id, volume_id, title, abbreviation, long_title, num_chapters, book_order) VALUES (?,?,?,?,?,?,?)", b
        )

    russian_verses = [
        (4001, 400, 1, 1, "And Josias held the feast of the passover in Jerusalem unto his Lord, and offered the passover the fourteenth day of the first month.", "1 Esdras 1:1"),
        (4001, 400, 1, 2, "Having set the priests according to their daily courses, being arrayed in long garments, in the temple of the Lord.", "1 Esdras 1:2"),
        (4001, 400, 1, 3, "And he spake unto the Levites, the holy ministers of Israel, that they should hallow themselves unto the Lord, to set the holy ark of the Lord in the house that king Solomon the son of David had built.", "1 Esdras 1:3"),
        (4002, 400, 1, 1, "The second book of the prophet Esdras, the son of Saraias, the son of Azarias, the son of Helchias, the son of Sadamias, the son of Sadoc, the son of Achitob.", "2 Esdras 1:1"),
        (4002, 400, 1, 2, "The word of the Lord came unto me, saying: Go thy way, and shew my people their sinful deeds, and their children their wickedness which they have done against me.", "2 Esdras 1:2"),
        (4005, 400, 1, 1, "Love righteousness, ye that be judges of the earth: think of the Lord with a good heart, and in simplicity of heart seek him.", "Wisdom of Solomon 1:1"),
        (4005, 400, 1, 2, "For he will be found of them that tempt him not; and sheweth himself unto such as do not distrust him.", "Wisdom of Solomon 1:2"),
        (4005, 400, 1, 3, "For froward thoughts separate from God: and his power, when it is tried, reproveth the unwise.", "Wisdom of Solomon 1:3"),
        (4006, 400, 1, 1, "All wisdom cometh from the Lord, and is with him for ever.", "Sirach 1:1"),
        (4006, 400, 1, 2, "Who can number the sand of the sea, and the drops of rain, and the days of eternity?", "Sirach 1:2"),
        (4006, 400, 1, 3, "Who can find out the height of heaven, and the breadth of the earth, and the deep, and wisdom?", "Sirach 1:3"),
        (4008, 400, 1, 1, "A copy of an epistle, which Jeremy sent unto them which were to be led captives into Babylon by the king of the Babylonians, to certify them, as it was commanded him of God.", "Letter of Jeremiah 1:1"),
        (4008, 400, 1, 2, "Because of the sins which ye have committed before God, ye shall be led away captives into Babylon by Nabuchodonosor king of the Babylonians.", "Letter of Jeremiah 1:2"),
        (4009, 400, 1, 1, "And it happened, after that Alexander son of Philip, the Macedonian, who came out of the land of Chettiim, had smitten Darius king of the Persians and Medes, that he reigned in his stead, the first over Greece.", "1 Maccabees 1:1"),
        (4009, 400, 1, 2, "And made many wars, and won many strong holds, and slew the kings of the earth.", "1 Maccabees 1:2"),
        (4010, 400, 1, 1, "The brethren, the Jews that be at Jerusalem and in the land of Judea, wish unto the brethren, the Jews that are throughout Egypt health and peace.", "2 Maccabees 1:1"),
        (4010, 400, 1, 2, "God be gracious unto you, and remember his covenant that he made with Abraham, Isaac, and Jacob, his faithful servants.", "2 Maccabees 1:2"),
        (4011, 400, 1, 1, "Philopater, on learning from those who came back that Antiochus had made himself master of the places which belonged to himself, sent orders to all his foot and horse.", "3 Maccabees 1:1"),
        (4013, 400, 1, 1, "O Lord, Almighty God of our fathers, Abraham, Isaac, and Jacob, and of their righteous seed.", "Prayer of Manasseh 1:1"),
        (4013, 400, 1, 2, "Who hast made heaven and earth, with all the ornament thereof.", "Prayer of Manasseh 1:2"),
        (4013, 400, 1, 3, "Who hast bound the sea by the word of thy commandment; who hast shut up the deep, and sealed it by thy terrible and glorious name.", "Prayer of Manasseh 1:3"),
        (4014, 400, 1, 1, "I was small among my brethren, and the youngest in my father's house: I tended my father's sheep.", "Psalm 151 1:1"),
        (4014, 400, 1, 2, "My hands made a harp; and my fingers fashioned a psaltery.", "Psalm 151 1:2"),
        (4014, 400, 1, 3, "And who shall tell it to my Lord? The Lord himself; it is he that heareth.", "Psalm 151 1:3"),
        (4014, 400, 1, 4, "It was he that sent his messenger, and took me from my father's sheep, and anointed me with his anointing oil.", "Psalm 151 1:4"),
    ]

    for book_id, volume_id, ch_num, verse_num, text, ref in russian_verses:
        ch_key = (book_id, ch_num)
        if ch_key not in chapter_map:
            max_ch_id += 1
            chapter_map[ch_key] = max_ch_id
            conn.execute("INSERT INTO chapters (id, book_id, chapter_number) VALUES (?, ?, ?)", (max_ch_id, book_id, ch_num))
        max_id += 1
        ref_parts = ref.rsplit(" ", 1)
        bt = ref_parts[0] if len(ref_parts) == 2 else ref
        conn.execute(
            "INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (max_id, chapter_map[ch_key], book_id, volume_id, verse_num, text, ref),
        )
        conn.execute(
            "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?, ?, ?, ?, 'Russian Orthodox Bible')",
            (max_id, text, ref, bt),
        )

    print(f"  Added {len(russian_verses)} Russian Orthodox Bible verses")

    # Update chapter verse counts for new volumes
    conn.execute("""
        UPDATE chapters SET num_verses = (
            SELECT COUNT(*) FROM verses WHERE verses.chapter_id = chapters.id
        ) WHERE num_verses = 0 OR num_verses IS NULL
    """)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    imported_lds = False
    imported_bible = False

    # Try importing from cloned repos
    if os.path.isdir(LDS_REPO):
        try:
            imported_lds = import_lds_scriptures(conn)
        except Exception as exc:
            print(f"  WARNING: LDS scriptures import failed: {exc}")

    if os.path.isdir(BIBLE_REPO):
        try:
            imported_bible = import_bible_databases(conn)
        except Exception as exc:
            print(f"  WARNING: Bible databases import failed: {exc}")

    # Seed sample data if no repos were available
    if not imported_lds and not imported_bible:
        seed_sample_data(conn)

    # Always add the additional canons
    try:
        seed_additional_canons(conn)
    except Exception as exc:
        print(f"  WARNING: Additional canons import failed: {exc}")

    # Fix book_order for all standard works using canonical ordering
    fix_book_order(conn)

    conn.commit()

    verse_count = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    vol_count = conn.execute("SELECT COUNT(*) FROM volumes").fetchone()[0]
    book_count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    conn.close()

    print(f"  Built {DB_PATH}")
    print(f"  {vol_count} volumes, {book_count} books, {verse_count} verses")
    print(f"  FTS5 search index created")


if __name__ == "__main__":
    main()
