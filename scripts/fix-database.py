#!/usr/bin/env python3
"""
Fix all data quality issues in scriptures.db.

1. Fix Pearl of Great Price book_order
2. Remove orphaned D&C 89 record
3. Deduplicate Coptic books (volume_id=200)
4. Deduplicate DSS books (volume_id=300)
5. Deduplicate Russian Orthodox books (volume_id=400)
6. Resequence book_order for all volumes
7. Rebuild FTS index
8. Verify fixes
"""

import sqlite3
import shutil
import os
from datetime import datetime

DB_PATH = "/Users/matthewjohnson/Projects/scriptures/data/scriptures.db"
BACKUP_PATH = DB_PATH + f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def query_all(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


def print_table(rows, headers=None):
    if not rows:
        print("  (no rows)")
        return
    if headers:
        print("  " + " | ".join(str(h).ljust(12) for h in headers))
        print("  " + "-+-".join("-" * 12 for _ in headers))
    for row in rows:
        print("  " + " | ".join(str(v).ljust(12) for v in row))


def get_verse_count(cur):
    return query_all(cur, "SELECT COUNT(*) FROM verses")[0][0]


def get_book_count(cur):
    return query_all(cur, "SELECT COUNT(*) FROM books")[0][0]


def main():
    # --- Backup ---
    print_section("BACKUP")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"  Backup created: {BACKUP_PATH}")
    print(f"  Size: {os.path.getsize(BACKUP_PATH):,} bytes")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- Before stats ---
    print_section("BEFORE STATISTICS")
    total_verses_before = get_verse_count(cur)
    total_books_before = get_book_count(cur)
    print(f"  Total verses: {total_verses_before}")
    print(f"  Total books:  {total_books_before}")

    # Books with book_order=0
    zero_order = query_all(cur, """
        SELECT b.id, b.title, v.title as volume, b.book_order
        FROM books b JOIN volumes v ON b.volume_id=v.id
        WHERE b.book_order=0 ORDER BY v.title, b.title
    """)
    print(f"\n  Books with book_order=0: {len(zero_order)}")
    for row in zero_order:
        print(f"    [{row[0]}] {row[1]} ({row[2]}) order={row[3]}")

    # Duplicate titles within volumes
    dupes = query_all(cur, """
        SELECT b.volume_id, v.title, b.title, COUNT(*) as cnt
        FROM books b JOIN volumes v ON b.volume_id=v.id
        GROUP BY b.volume_id, b.title HAVING cnt > 1
        ORDER BY b.volume_id, b.title
    """)
    print(f"\n  Duplicate book titles within volumes: {len(dupes)}")
    for row in dupes:
        print(f"    Volume {row[0]} ({row[1]}): '{row[2]}' x{row[3]}")

    verses_deleted = 0
    chapters_deleted = 0
    books_deleted = 0

    # =========================================================
    # FIX 1: Pearl of Great Price book_order
    # =========================================================
    print_section("FIX 1: Pearl of Great Price book_order")

    pgp_books = query_all(cur, "SELECT id, title, book_order FROM books WHERE volume_id=5 ORDER BY id")
    print("  Before:")
    print_table(pgp_books, ["id", "title", "order"])

    # Canonical order: Moses=1, Abraham=2, JS-Matthew=3, JS-History=4, Articles of Faith=5
    pgp_order = {
        "Moses": 1,
        "Abraham": 2,
    }
    # The others have special characters - match by pattern
    for book_id, title, order in pgp_books:
        if "Matthew" in title:
            pgp_order[title] = 3
        elif "History" in title:
            pgp_order[title] = 4
        elif "Articles" in title:
            pgp_order[title] = 5

    for book_id, title, order in pgp_books:
        new_order = pgp_order.get(title)
        if new_order and new_order != order:
            cur.execute("UPDATE books SET book_order=? WHERE id=?", (new_order, book_id))
            print(f"  Updated '{title}' (id={book_id}): order {order} -> {new_order}")

    pgp_books_after = query_all(cur, "SELECT id, title, book_order FROM books WHERE volume_id=5 ORDER BY book_order")
    print("  After:")
    print_table(pgp_books_after, ["id", "title", "order"])

    # =========================================================
    # FIX 2: Remove orphaned D&C 89
    # =========================================================
    print_section("FIX 2: Remove orphaned D&C 89")

    dc_books = query_all(cur, "SELECT id, title, book_order, num_chapters FROM books WHERE volume_id=4 ORDER BY book_order")
    print("  D&C books before:")
    print_table(dc_books, ["id", "title", "order", "chapters"])

    # Find and verify the orphan
    orphan = query_all(cur, """
        SELECT b.id, b.title,
            (SELECT COUNT(*) FROM chapters WHERE book_id=b.id) as ch,
            (SELECT COUNT(*) FROM verses WHERE book_id=b.id) as v
        FROM books b WHERE volume_id=4 AND title='D&C 89'
    """)
    if orphan:
        oid, otitle, och, ov = orphan[0]
        print(f"  Orphan found: id={oid}, title='{otitle}', chapters={och}, verses={ov}")
        if och == 0 and ov == 0:
            cur.execute("DELETE FROM books WHERE id=?", (oid,))
            books_deleted += 1
            print(f"  Deleted orphan book id={oid}")
        else:
            print(f"  WARNING: Orphan has content, skipping delete!")

    # =========================================================
    # FIX 3: Deduplicate Coptic books (volume_id=200)
    # =========================================================
    print_section("FIX 3: Deduplicate Coptic books (volume_id=200)")

    coptic_books = query_all(cur, """
        SELECT id, title, book_order, num_chapters,
            (SELECT COUNT(*) FROM chapters WHERE book_id=b.id) as ch_count,
            (SELECT COUNT(*) FROM verses WHERE book_id=b.id) as v_count
        FROM books b WHERE volume_id=200 ORDER BY title, book_order
    """)
    print("  All Coptic books:")
    print_table(coptic_books, ["id", "title", "order", "num_ch", "ch_ct", "v_ct"])

    # Stubs that are duplicates of main entries (same or similar title, book_order=0):
    # 4097(Tobit,0v) -> dup of 2007(Tobit)
    # 4098(Judith,0v) -> dup of 2008(Judith)
    # 4099(Wisdom of Solomon,0v) -> dup of 2010(Wisdom of Solomon)
    # 4100(Sirach (Ecclesiasticus),4v) -> dup of 2006(Sirach) -- verses are duplicates
    # 4101(Baruch,0v) -> dup of 2009(Baruch)

    coptic_stubs_to_delete = [4097, 4098, 4099, 4100, 4101]

    for stub_id in coptic_stubs_to_delete:
        stub_info = query_all(cur, """
            SELECT id, title,
                (SELECT COUNT(*) FROM verses WHERE book_id=?) as v_count
            FROM books WHERE id=?
        """, (stub_id, stub_id))
        if not stub_info:
            continue
        _, title, v_count = stub_info[0]

        # Delete verses, chapters, then book
        if v_count > 0:
            v_del = cur.execute("DELETE FROM verses WHERE book_id=?", (stub_id,)).rowcount
            verses_deleted += v_del
            print(f"  Deleted {v_del} duplicate verses from stub '{title}' (id={stub_id})")

        ch_del = cur.execute("DELETE FROM chapters WHERE book_id=?", (stub_id,)).rowcount
        chapters_deleted += ch_del

        cur.execute("DELETE FROM books WHERE id=?", (stub_id,))
        books_deleted += 1
        print(f"  Deleted stub book '{title}' (id={stub_id})")

    # Stubs that are standalone (no main entry): 4102(1 Maccabees), 4103(2 Maccabees), 4104(3 Maccabees), 4105(Letter of Jeremiah)
    # These stay - they just need proper book_order (handled in Fix 6)
    print("  Keeping standalone Coptic books: 1 Maccabees, 2 Maccabees, 3 Maccabees, Letter of Jeremiah")

    # =========================================================
    # FIX 4: Deduplicate DSS books (volume_id=300)
    # =========================================================
    print_section("FIX 4: Deduplicate DSS books (volume_id=300)")

    dss_books = query_all(cur, """
        SELECT id, title, book_order,
            (SELECT COUNT(*) FROM verses WHERE book_id=b.id) as v_count
        FROM books b WHERE volume_id=300 ORDER BY title, book_order
    """)
    print("  All DSS books:")
    print_table(dss_books, ["id", "title", "order", "verses"])

    # DSS stubs (parenthetical names, book_order=0):
    # 4106 Community Rule (1QS) -> 3001 Community Rule
    # 4107 War Scroll (1QM) -> 3002 War Scroll
    # 4108 Thanksgiving Hymns (1QH) -> 3003 Thanksgiving Hymns
    # 4109 Temple Scroll (11QT) -> 3004 Temple Scroll
    # 4110 Habakkuk Commentary (1QpHab) -> 3005 Habakkuk Commentary
    # 4111 Damascus Document (CD) -> 3007 Damascus Document
    # 4112 Copper Scroll (3Q15) -> 3009 Copper Scroll
    # 4113 Isaiah Scroll (1QIsa) -> 3010 Isaiah Scroll

    dss_stubs_to_delete = [4106, 4107, 4108, 4109, 4110, 4111, 4112, 4113]

    for stub_id in dss_stubs_to_delete:
        stub_info = query_all(cur, """
            SELECT id, title,
                (SELECT COUNT(*) FROM verses WHERE book_id=?) as v_count
            FROM books WHERE id=?
        """, (stub_id, stub_id))
        if not stub_info:
            continue
        _, title, v_count = stub_info[0]

        # The stub verses are at overlapping chapter numbers with the main entry
        # but contain different (translated) content. The main entries have far more
        # content overall. Delete the stub verses since they overlap chapter-wise.
        if v_count > 0:
            v_del = cur.execute("DELETE FROM verses WHERE book_id=?", (stub_id,)).rowcount
            verses_deleted += v_del
            print(f"  Deleted {v_del} stub verses from '{title}' (id={stub_id})")

        ch_del = cur.execute("DELETE FROM chapters WHERE book_id=?", (stub_id,)).rowcount
        chapters_deleted += ch_del

        cur.execute("DELETE FROM books WHERE id=?", (stub_id,))
        books_deleted += 1
        print(f"  Deleted stub book '{title}' (id={stub_id})")

    # =========================================================
    # FIX 5: Deduplicate Russian Orthodox books (volume_id=400)
    # =========================================================
    print_section("FIX 5: Deduplicate Russian Orthodox books (volume_id=400)")

    ro_books = query_all(cur, """
        SELECT id, title, book_order,
            (SELECT COUNT(*) FROM verses WHERE book_id=b.id) as v_count
        FROM books b WHERE volume_id=400 ORDER BY title, book_order
    """)
    print("  All Russian Orthodox books:")
    print_table(ro_books, ["id", "title", "order", "verses"])

    # Stubs (book_order=0, all empty):
    # 4114(1 Esdras) -> 4001(1 Esdras)
    # 4115(2 Esdras) -> 4002(2 Esdras)
    # 4116(3 Maccabees) -> 4011(3 Maccabees)
    # 4117(Prayer of Manasseh) -> 4013(Prayer of Manasseh)
    # 4118(Psalm 151) -> 4014(Psalm 151)

    ro_stubs_to_delete = [4114, 4115, 4116, 4117, 4118]

    for stub_id in ro_stubs_to_delete:
        stub_info = query_all(cur, "SELECT id, title FROM books WHERE id=?", (stub_id,))
        if not stub_info:
            continue
        _, title = stub_info[0]

        # All are empty, just delete
        ch_del = cur.execute("DELETE FROM chapters WHERE book_id=?", (stub_id,)).rowcount
        chapters_deleted += ch_del
        cur.execute("DELETE FROM books WHERE id=?", (stub_id,))
        books_deleted += 1
        print(f"  Deleted empty stub book '{title}' (id={stub_id})")

    # =========================================================
    # FIX 6: Resequence book_order for all volumes
    # =========================================================
    print_section("FIX 6: Resequence book_order for all volumes")

    volumes = query_all(cur, "SELECT id, title FROM volumes ORDER BY id")
    for vol_id, vol_title in volumes:
        books = query_all(cur, """
            SELECT id, title, book_order FROM books
            WHERE volume_id=? ORDER BY book_order, id
        """, (vol_id,))
        if not books:
            continue

        needs_fix = any(b[2] == 0 for b in books)
        sequential = all(books[i][2] == i + 1 for i in range(len(books)))

        if needs_fix or not sequential:
            print(f"\n  Volume {vol_id} ({vol_title}): resequencing {len(books)} books")
            for i, (book_id, title, old_order) in enumerate(books, 1):
                if old_order != i:
                    cur.execute("UPDATE books SET book_order=? WHERE id=?", (i, book_id))
                    print(f"    '{title}' (id={book_id}): {old_order} -> {i}")

    # =========================================================
    # FIX 7: Rebuild FTS index
    # =========================================================
    print_section("FIX 7: Rebuild FTS index")

    # The FTS table has content columns (scriptures_fts_content exists), so it's a content-based FTS5
    fts_before = query_all(cur, "SELECT COUNT(*) FROM scriptures_fts")[0][0]
    print(f"  FTS rows before rebuild: {fts_before}")

    cur.execute("DELETE FROM scriptures_fts")
    cur.execute("""
        INSERT INTO scriptures_fts(rowid, text, reference, book_title, volume_title)
        SELECT v.id, v.text, v.reference, b.title, vol.title
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        JOIN volumes vol ON b.volume_id = vol.id
    """)

    fts_after = query_all(cur, "SELECT COUNT(*) FROM scriptures_fts")[0][0]
    print(f"  FTS rows after rebuild:  {fts_after}")

    # =========================================================
    # COMMIT
    # =========================================================
    conn.commit()
    print_section("CHANGES COMMITTED")
    print(f"  Books deleted:    {books_deleted}")
    print(f"  Chapters deleted: {chapters_deleted}")
    print(f"  Verses deleted:   {verses_deleted}")

    # =========================================================
    # FIX 8: Verify
    # =========================================================
    print_section("VERIFICATION")

    total_verses_after = get_verse_count(cur)
    total_books_after = get_book_count(cur)
    print(f"  Total verses: {total_verses_before} -> {total_verses_after} (diff: {total_verses_after - total_verses_before})")
    print(f"  Total books:  {total_books_before} -> {total_books_after} (diff: {total_books_after - total_books_before})")
    print(f"  Verses deleted should equal diff: {verses_deleted} == {total_verses_before - total_verses_after}: {verses_deleted == total_verses_before - total_verses_after}")

    # Check no duplicate titles
    dupes_after = query_all(cur, """
        SELECT b.volume_id, v.title, b.title, COUNT(*) as cnt
        FROM books b JOIN volumes v ON b.volume_id=v.id
        GROUP BY b.volume_id, b.title HAVING cnt > 1
    """)
    print(f"\n  Duplicate book titles remaining: {len(dupes_after)}")
    if dupes_after:
        for row in dupes_after:
            print(f"    Volume {row[0]} ({row[1]}): '{row[2]}' x{row[3]}")

    # Check no book_order=0
    zero_after = query_all(cur, "SELECT id, title, volume_id, book_order FROM books WHERE book_order=0")
    print(f"  Books with book_order=0 remaining: {len(zero_after)}")
    if zero_after:
        for row in zero_after:
            print(f"    [{row[0]}] {row[1]} (vol={row[2]}) order={row[3]}")

    # FTS row count matches verse count
    fts_count = query_all(cur, "SELECT COUNT(*) FROM scriptures_fts")[0][0]
    print(f"\n  FTS index rows: {fts_count}")
    print(f"  Verse count:    {total_verses_after}")
    print(f"  FTS matches verses: {fts_count == total_verses_after}")

    # Show final book list per volume
    print_section("FINAL BOOK LIST BY VOLUME")
    for vol_id, vol_title in volumes:
        books = query_all(cur, """
            SELECT book_order, title,
                (SELECT COUNT(*) FROM verses WHERE book_id=b.id) as v_count
            FROM books b WHERE volume_id=?
            ORDER BY book_order
        """, (vol_id,))
        if books:
            print(f"\n  Volume {vol_id}: {vol_title} ({len(books)} books)")
            for order, title, v_count in books:
                print(f"    {order:3d}. {title} ({v_count} verses)")

    conn.close()
    print_section("DONE")


if __name__ == "__main__":
    main()
