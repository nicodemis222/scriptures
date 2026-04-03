#!/usr/bin/env python3
"""
export-bundles.py — Export per-volume SQLite bundles and a master bundle.

Creates individual .sqlite files for each volume and a master ZIP with everything.
Output directory: data/bundles/
"""

import sqlite3
import os
import shutil
import zipfile
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'scriptures.db')
BUNDLES_DIR = os.path.join(SCRIPT_DIR, '..', 'data', 'bundles')
MANIFEST_PATH = os.path.join(BUNDLES_DIR, 'manifest.json')


def export_volume(src_conn, volume_id, volume_abbr, volume_title, output_path):
    """Export a single volume to a standalone .sqlite file."""
    if os.path.exists(output_path):
        os.remove(output_path)

    dest = sqlite3.connect(output_path)

    # Create schema
    dest.executescript("""
        CREATE TABLE volumes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            abbreviation TEXT DEFAULT '',
            description TEXT DEFAULT ''
        );
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volume_id INTEGER REFERENCES volumes(id),
            title TEXT NOT NULL,
            abbreviation TEXT DEFAULT '',
            long_title TEXT DEFAULT '',
            num_chapters INTEGER DEFAULT 0,
            book_order INTEGER DEFAULT 0
        );
        CREATE TABLE chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER REFERENCES books(id),
            chapter_number INTEGER NOT NULL,
            num_verses INTEGER DEFAULT 0
        );
        CREATE TABLE verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER REFERENCES chapters(id),
            book_id INTEGER REFERENCES books(id),
            volume_id INTEGER REFERENCES volumes(id),
            verse_number INTEGER NOT NULL,
            text TEXT NOT NULL,
            reference TEXT DEFAULT ''
        );
        CREATE VIRTUAL TABLE scriptures_fts USING fts5(
            text, reference, book_title, volume_title,
            tokenize='porter'
        );
    """)

    # Copy volume
    vol = src_conn.execute(
        "SELECT id, title, abbreviation, description FROM volumes WHERE id = ?",
        (volume_id,)
    ).fetchone()
    if not vol:
        dest.close()
        os.remove(output_path)
        return 0

    dest.execute("INSERT INTO volumes VALUES (?, ?, ?, ?)", vol)

    # Copy books
    books = src_conn.execute(
        "SELECT id, volume_id, title, abbreviation, long_title, num_chapters, book_order FROM books WHERE volume_id = ?",
        (volume_id,)
    ).fetchall()
    dest.executemany("INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?)", books)

    # Copy chapters
    book_ids = [b[0] for b in books]
    if book_ids:
        placeholders = ','.join('?' * len(book_ids))
        chapters = src_conn.execute(
            f"SELECT id, book_id, chapter_number, num_verses FROM chapters WHERE book_id IN ({placeholders})",
            book_ids
        ).fetchall()
        dest.executemany("INSERT INTO chapters VALUES (?, ?, ?, ?)", chapters)

        # Copy verses
        chapter_ids = [c[0] for c in chapters]
        if chapter_ids:
            # Batch in groups of 500 to avoid too many params
            verse_count = 0
            for i in range(0, len(chapter_ids), 500):
                batch = chapter_ids[i:i+500]
                placeholders = ','.join('?' * len(batch))
                verses = src_conn.execute(
                    f"SELECT id, chapter_id, book_id, volume_id, verse_number, text, reference FROM verses WHERE chapter_id IN ({placeholders})",
                    batch
                ).fetchall()
                dest.executemany("INSERT INTO verses VALUES (?, ?, ?, ?, ?, ?, ?)", verses)
                verse_count += len(verses)

            # Build FTS index
            dest.execute("""
                INSERT INTO scriptures_fts(rowid, text, reference, book_title, volume_title)
                SELECT v.id, v.text, v.reference, b.title, vol.title
                FROM verses v
                JOIN books b ON v.book_id = b.id
                JOIN volumes vol ON v.volume_id = vol.id
            """)
        else:
            verse_count = 0
    else:
        verse_count = 0

    dest.commit()
    dest.close()
    return verse_count


def export_hymns(src_conn, output_path):
    """Export hymns to a standalone .sqlite file."""
    if os.path.exists(output_path):
        os.remove(output_path)

    dest = sqlite3.connect(output_path)
    dest.executescript("""
        CREATE TABLE hymns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hymn_number INTEGER,
            title TEXT NOT NULL,
            author TEXT DEFAULT '',
            composer TEXT DEFAULT '',
            first_line TEXT DEFAULT '',
            is_public_domain BOOLEAN DEFAULT 1
        );
        CREATE TABLE hymn_verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hymn_id INTEGER REFERENCES hymns(id),
            verse_number INTEGER NOT NULL,
            verse_type TEXT DEFAULT 'verse',
            text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE hymns_fts USING fts5(
            title, author, first_line, lyrics,
            content='',
            tokenize='porter'
        );
    """)

    hymns = src_conn.execute(
        "SELECT id, hymn_number, title, author, composer, first_line, is_public_domain FROM hymns"
    ).fetchall()
    dest.executemany("INSERT INTO hymns VALUES (?, ?, ?, ?, ?, ?, ?)", hymns)

    hymn_ids = [h[0] for h in hymns]
    if hymn_ids:
        for i in range(0, len(hymn_ids), 500):
            batch = hymn_ids[i:i+500]
            placeholders = ','.join('?' * len(batch))
            verses = src_conn.execute(
                f"SELECT id, hymn_id, verse_number, verse_type, text FROM hymn_verses WHERE hymn_id IN ({placeholders})",
                batch
            ).fetchall()
            dest.executemany("INSERT INTO hymn_verses VALUES (?, ?, ?, ?, ?)", verses)

    dest.commit()
    dest.close()
    return len(hymns)


def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    os.makedirs(BUNDLES_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # Get all volumes
    volumes = conn.execute(
        "SELECT id, title, abbreviation, description FROM volumes ORDER BY id"
    ).fetchall()

    manifest = {"bundles": [], "version": 1}

    print("=== Exporting Scripture Bundles ===\n")

    for vol_id, vol_title, vol_abbr, vol_desc in volumes:
        filename = f"{vol_abbr}.sqlite"
        output_path = os.path.join(BUNDLES_DIR, filename)
        verse_count = export_volume(conn, vol_id, vol_abbr, vol_title, output_path)
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        manifest["bundles"].append({
            "id": vol_abbr,
            "name": vol_title,
            "volume_id": vol_id,
            "filename": filename,
            "size_bytes": file_size,
            "verse_count": verse_count,
            "version": 1
        })
        print(f"  {vol_title} ({vol_abbr}): {verse_count} verses, {file_size:,} bytes")

    # Export hymns
    hymns_path = os.path.join(BUNDLES_DIR, "hymns.sqlite")
    hymn_count = export_hymns(conn, hymns_path)
    hymns_size = os.path.getsize(hymns_path)
    manifest["bundles"].append({
        "id": "hymns",
        "name": "LDS Hymnal",
        "volume_id": None,
        "filename": "hymns.sqlite",
        "size_bytes": hymns_size,
        "verse_count": hymn_count,
        "version": 1
    })
    print(f"  LDS Hymnal (hymns): {hymn_count} hymns, {hymns_size:,} bytes")

    # Write manifest
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written to {MANIFEST_PATH}")

    # Create master ZIP
    zip_path = os.path.join(BUNDLES_DIR, "all-scriptures-bundle.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for bundle in manifest["bundles"]:
            bundle_path = os.path.join(BUNDLES_DIR, bundle["filename"])
            if os.path.exists(bundle_path):
                zf.write(bundle_path, bundle["filename"])
        zf.write(MANIFEST_PATH, "manifest.json")

    zip_size = os.path.getsize(zip_path)
    print(f"\nMaster bundle: {zip_path}")
    print(f"Master bundle size: {zip_size:,} bytes ({zip_size / 1024 / 1024:.1f} MB)")

    # Also copy full DB as the "complete" bundle
    full_path = os.path.join(BUNDLES_DIR, "scriptures-full.sqlite")
    shutil.copy2(DB_PATH, full_path)
    full_size = os.path.getsize(full_path)
    print(f"Full database copy: {full_size:,} bytes ({full_size / 1024 / 1024:.1f} MB)")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
