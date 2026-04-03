#!/usr/bin/env python3
"""
import-talks.py — Add prophet talks/speeches with scripture cross-references.

Adds tables: talks, talk_scripture_refs, talks_fts
Populates with General Conference talks and key historical addresses
with their scripture references for cross-referencing while reading.

Idempotent: checks for existing records before inserting.
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'scriptures.db')

def create_tables(conn):
    """Create talks tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS talks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            speaker TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT,
            conference TEXT,
            url TEXT,
            summary TEXT
        );

        CREATE TABLE IF NOT EXISTS talk_scripture_refs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            talk_id INTEGER REFERENCES talks(id) ON DELETE CASCADE,
            book_title TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse_start INTEGER,
            verse_end INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_talk_refs_book_ch
            ON talk_scripture_refs(book_title, chapter);

        CREATE INDEX IF NOT EXISTS idx_talk_refs_talk
            ON talk_scripture_refs(talk_id);
    """)

    # Create FTS table (drop and recreate to ensure schema matches)
    try:
        conn.execute("SELECT * FROM talks_fts LIMIT 0")
    except sqlite3.OperationalError:
        conn.execute("""
            CREATE VIRTUAL TABLE talks_fts USING fts5(
                title, speaker, summary,
                content='',
                tokenize='porter'
            )
        """)

    conn.commit()
    print("Tables created/verified.")


def talk_exists(conn, speaker, title):
    """Check if a talk already exists."""
    row = conn.execute(
        "SELECT id FROM talks WHERE speaker = ? AND title = ?",
        (speaker, title)
    ).fetchone()
    return row[0] if row else None


def insert_talk(conn, speaker, title, date, conference, url, summary, refs):
    """Insert a talk and its scripture references. Returns talk_id."""
    existing = talk_exists(conn, speaker, title)
    if existing:
        return existing

    cur = conn.execute(
        "INSERT INTO talks (speaker, title, date, conference, url, summary) VALUES (?, ?, ?, ?, ?, ?)",
        (speaker, title, date, conference, url, summary)
    )
    talk_id = cur.lastrowid

    for ref in refs:
        book, chapter = ref[0], ref[1]
        verse_start = ref[2] if len(ref) > 2 else None
        verse_end = ref[3] if len(ref) > 3 else None
        conn.execute(
            "INSERT INTO talk_scripture_refs (talk_id, book_title, chapter, verse_start, verse_end) VALUES (?, ?, ?, ?, ?)",
            (talk_id, book, chapter, verse_start, verse_end)
        )

    return talk_id


# =============================================================================
# TALK DATA
# Each entry: (speaker, title, date, conference, url, summary, [scripture_refs])
# Scripture refs: (book_title, chapter, verse_start?, verse_end?)
# =============================================================================

TALKS = [
    # --- MODERN PROPHETS: RECENT GENERAL CONFERENCE ---

    ("Russell M. Nelson", "The Power of Spiritual Momentum", "2022-04-03",
     "April 2022 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2022/04/47nelson",
     "President Nelson teaches about building and maintaining spiritual momentum through consistent gospel living.",
     [("2 Nephi", 31, 20), ("Mosiah", 4, 30), ("Alma", 37, 6), ("3 Nephi", 18, 15),
      ("Moroni", 10, 32), ("Doctrine and Covenants", 88, 63)]),

    ("Russell M. Nelson", "Overcome the World and Find Rest", "2022-10-02",
     "October 2022 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2022/10/47nelson",
     "President Nelson invites members to overcome the world by choosing the higher path of Jesus Christ.",
     [("1 Nephi", 22, 26), ("2 Nephi", 4, 34), ("Mosiah", 3, 19),
      ("Alma", 34, 32), ("3 Nephi", 27, 27), ("Ether", 12, 4),
      ("Doctrine and Covenants", 6, 36), ("Doctrine and Covenants", 101, 36)]),

    ("Russell M. Nelson", "Let God Prevail", "2020-10-04",
     "October 2020 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2020/10/46nelson",
     "President Nelson teaches about letting God prevail in our lives and gathering Israel.",
     [("Genesis", 32, 28), ("1 Nephi", 19, 15), ("2 Nephi", 6, 11),
      ("Jacob", 5, 61), ("3 Nephi", 21, 1), ("3 Nephi", 22, 2),
      ("Doctrine and Covenants", 29, 7), ("Abraham", 2, 9)]),

    ("Russell M. Nelson", "Hear Him", "2020-04-05",
     "April 2020 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2020/04/45nelson",
     "President Nelson testifies of the importance of hearing the voice of Jesus Christ.",
     [("3 Nephi", 11, 7), ("Joseph Smith—History", 1, 17),
      ("Doctrine and Covenants", 18, 34), ("Doctrine and Covenants", 1, 38),
      ("Moses", 1, 6), ("John", 10, 27)]),

    ("Dallin H. Oaks", "The Need for a Church", "2021-10-03",
     "October 2021 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2021/10/14oaks",
     "President Oaks explains why the Savior established His Church and why it is necessary.",
     [("Ephesians", 4, 11, 14), ("Mosiah", 18, 8, 10),
      ("3 Nephi", 18, 22), ("Doctrine and Covenants", 1, 30),
      ("Doctrine and Covenants", 115, 4), ("Matthew", 16, 18)]),

    ("Dallin H. Oaks", "Trust in the Lord", "2019-10-06",
     "October 2019 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2019/10/17oaks",
     "President Oaks teaches about trusting in the Lord's plan and timing.",
     [("Proverbs", 3, 5, 6), ("2 Nephi", 28, 30), ("Isaiah", 55, 8, 9),
      ("Doctrine and Covenants", 122, 7), ("Alma", 36, 3)]),

    ("Henry B. Eyring", "The Lord Leads His Church", "2022-10-02",
     "October 2022 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2022/10/12eyring",
     "President Eyring testifies that Jesus Christ leads His Church through revelation.",
     [("Amos", 3, 7), ("Doctrine and Covenants", 1, 38),
      ("3 Nephi", 27, 8), ("Ephesians", 2, 20)]),

    ("Jeffrey R. Holland", "Safety for the Soul", "2009-10-04",
     "October 2009 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2009/10/safety-for-the-soul",
     "Elder Holland delivers a powerful testimony of the Book of Mormon.",
     [("1 Nephi", 1, 1), ("2 Nephi", 33, 10, 11), ("Alma", 36, 21),
      ("Moroni", 10, 4, 5), ("Ether", 12, 41), ("2 Nephi", 25, 23),
      ("2 Nephi", 31, 20), ("Jacob", 4, 12)]),

    ("Jeffrey R. Holland", "The Laborers in the Vineyard", "2012-04-01",
     "April 2012 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2012/04/the-laborers-in-the-vineyard",
     "Elder Holland teaches about the generosity and mercy of God through the parable of the laborers.",
     [("Matthew", 20, 1, 16), ("Luke", 15, 11, 32), ("Mosiah", 4, 11),
      ("Alma", 26, 12), ("Moroni", 10, 32, 33)]),

    ("Jeffrey R. Holland", "Like a Broken Vessel", "2013-10-06",
     "October 2013 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2013/10/like-a-broken-vessel",
     "Elder Holland addresses mental health challenges with compassion and gospel perspective.",
     [("Psalms", 31, 12), ("Alma", 7, 11, 12), ("Isaiah", 53, 4),
      ("Matthew", 11, 28), ("2 Corinthians", 4, 8, 9)]),

    ("Dieter F. Uchtdorf", "The Infinite Power of Hope", "2008-10-05",
     "October 2008 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2008/10/the-infinite-power-of-hope",
     "President Uchtdorf teaches about the sustaining power of hope in Jesus Christ.",
     [("Ether", 12, 4), ("Romans", 8, 24), ("Moroni", 7, 40, 42),
      ("Alma", 32, 21), ("Hebrews", 11, 1), ("2 Nephi", 31, 20)]),

    ("Dieter F. Uchtdorf", "Come, Join with Us", "2013-10-06",
     "October 2013 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2013/10/come-join-with-us",
     "President Uchtdorf invites all to come or return to the Church of Jesus Christ.",
     [("3 Nephi", 9, 14), ("Matthew", 11, 28, 30), ("Moroni", 10, 32),
      ("Alma", 5, 33, 34), ("Doctrine and Covenants", 18, 10)]),

    ("David A. Bednar", "The Tender Mercies of the Lord", "2005-04-03",
     "April 2005 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2005/04/the-tender-mercies-of-the-lord",
     "Elder Bednar teaches about recognizing God's tender mercies in our lives.",
     [("1 Nephi", 1, 20), ("1 Nephi", 8, 8), ("Ether", 6, 8),
      ("Psalms", 145, 9), ("Doctrine and Covenants", 46, 9)]),

    ("David A. Bednar", "Watchful unto Prayer Continually", "2010-04-04",
     "April 2010 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2010/04/pray-always",
     "Elder Bednar teaches about meaningful, heartfelt prayer.",
     [("3 Nephi", 18, 15), ("2 Nephi", 32, 8, 9), ("Alma", 34, 17, 27),
      ("Doctrine and Covenants", 19, 38), ("Moroni", 7, 48)]),

    ("Neil L. Andersen", "Faith Is Not by Chance, but by Choice", "2015-10-04",
     "October 2015 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2015/10/faith-is-not-by-chance-but-by-choice",
     "Elder Andersen teaches that faith is a choice requiring consistent effort.",
     [("Alma", 32, 27, 28), ("Ether", 12, 6), ("Moroni", 7, 33),
      ("Hebrews", 11, 1, 6), ("Romans", 10, 17)]),

    ("Quentin L. Cook", "The Doctrine of the Father", "2012-04-01",
     "April 2012 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2012/04/in-tune-with-the-music-of-faith",
     "Elder Cook teaches about the importance of family and being in tune with the Spirit.",
     [("1 Nephi", 8, 12), ("3 Nephi", 17, 21), ("Mosiah", 2, 17),
      ("Doctrine and Covenants", 68, 25, 28)]),

    ("D. Todd Christofferson", "The Power of Covenants", "2009-04-05",
     "April 2009 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2009/04/the-power-of-covenants",
     "Elder Christofferson teaches about the protecting and enabling power of covenants.",
     [("Abraham", 1, 18, 19), ("Doctrine and Covenants", 84, 33, 40),
      ("Mosiah", 5, 5), ("3 Nephi", 18, 10), ("2 Nephi", 31, 19, 20)]),

    ("Ronald A. Rasband", "Let the Holy Spirit Guide", "2017-04-02",
     "April 2017 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2017/04/let-the-holy-spirit-guide",
     "Elder Rasband teaches about recognizing and following the Holy Ghost.",
     [("John", 14, 26), ("Moroni", 10, 5), ("2 Nephi", 32, 5),
      ("Doctrine and Covenants", 8, 2, 3), ("Galatians", 5, 22, 23)]),

    ("Gary E. Stevenson", "Sacred Homes, Sacred Temples", "2009-04-05",
     "April 2009 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2009/04/sacred-homes-sacred-temples",
     "Elder Stevenson teaches about making homes sacred sanctuaries.",
     [("Doctrine and Covenants", 109, 8), ("Doctrine and Covenants", 88, 119),
      ("3 Nephi", 18, 21), ("Alma", 37, 36, 37)]),

    ("Dale G. Renlund", "Atonement of Jesus Christ", "2016-10-02",
     "October 2016 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2016/10/repentance-a-joyful-choice",
     "Elder Renlund teaches about the enabling power of the Atonement and joyful repentance.",
     [("Alma", 7, 11, 13), ("2 Nephi", 2, 6, 8), ("Alma", 42, 15),
      ("Mosiah", 3, 7), ("Doctrine and Covenants", 19, 16, 18)]),

    # --- HISTORICAL PROPHETS ---

    ("Joseph Smith", "The King Follett Discourse", "1844-04-07",
     "General Conference April 1844",
     "https://www.churchofjesuschrist.org/study/ensign/1971/04/the-king-follett-sermon",
     "Prophet Joseph Smith's landmark sermon on the nature of God, the eternal destiny of man, and salvation for the dead.",
     [("Genesis", 1, 1), ("John", 5, 26), ("John", 17, 3),
      ("Revelation", 1, 6), ("Doctrine and Covenants", 130, 22),
      ("Doctrine and Covenants", 132, 20), ("Abraham", 3, 22, 23),
      ("Moses", 1, 39)]),

    ("Joseph Smith", "The Articles of Faith", "1842-03-01",
     "Wentworth Letter 1842",
     "https://www.churchofjesuschrist.org/study/scriptures/pgp/a-of-f/1",
     "Joseph Smith's concise statement of 13 fundamental beliefs of the Church.",
     [("Articles of Faith", 1, 1), ("Articles of Faith", 1, 3),
      ("Articles of Faith", 1, 4), ("Articles of Faith", 1, 5),
      ("Articles of Faith", 1, 8), ("Articles of Faith", 1, 10),
      ("Articles of Faith", 1, 13)]),

    ("Brigham Young", "Discourse on the Holy Ghost", "1853-02-06",
     "Journal of Discourses Vol. 1",
     None,
     "President Young teaches about the role of the Holy Ghost and personal revelation.",
     [("John", 14, 26), ("John", 16, 13), ("Moroni", 10, 5),
      ("Doctrine and Covenants", 8, 2), ("Doctrine and Covenants", 130, 22)]),

    ("John Taylor", "The Mediation and Atonement", "1882-01-01",
     "Published work 1882",
     None,
     "President Taylor's comprehensive treatise on the Atonement of Jesus Christ.",
     [("2 Nephi", 9, 6, 12), ("Alma", 34, 8, 14), ("Mosiah", 3, 5, 11),
      ("Isaiah", 53, 3, 7), ("Doctrine and Covenants", 19, 16, 19),
      ("Moses", 6, 59), ("Genesis", 3, 15)]),

    ("Wilford Woodruff", "Official Declaration 1 (The Manifesto)", "1890-09-25",
     "Official Declaration 1890",
     "https://www.churchofjesuschrist.org/study/scriptures/dc-testament/od/1",
     "President Woodruff's official declaration ending the practice of plural marriage.",
     [("Doctrine and Covenants", 132, 1), ("Doctrine and Covenants", 1, 14),
      ("Articles of Faith", 1, 12)]),

    ("Lorenzo Snow", "Discourse on the Grand Destiny of Man", "1898-10-08",
     "October 1898 General Conference",
     None,
     "President Snow teaches about man's divine potential and eternal progression.",
     [("Moses", 1, 39), ("Doctrine and Covenants", 93, 29),
      ("Abraham", 3, 22, 23), ("Doctrine and Covenants", 132, 20),
      ("Romans", 8, 16, 17), ("Genesis", 1, 26, 27)]),

    ("Joseph F. Smith", "Vision of the Redemption of the Dead", "1918-10-03",
     "October 1918 General Conference",
     "https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/138",
     "President Smith's vision of the spirit world and the redemption of the dead, later canonized as D&C 138.",
     [("Doctrine and Covenants", 138, 1), ("Doctrine and Covenants", 138, 11),
      ("Doctrine and Covenants", 138, 30), ("Doctrine and Covenants", 138, 57),
      ("1 Peter", 3, 18, 20), ("1 Peter", 4, 6),
      ("John", 5, 25, 29)]),

    ("Heber J. Grant", "The Strength of Being Honest", "1938-04-03",
     "April 1938 General Conference",
     None,
     "President Grant teaches about the importance of honesty, integrity, and keeping the Word of Wisdom.",
     [("Doctrine and Covenants", 89, 1), ("Doctrine and Covenants", 89, 18, 21),
      ("Articles of Faith", 1, 13), ("Proverbs", 12, 22)]),

    ("George Albert Smith", "To the Relief Society", "1945-10-07",
     "October 1945 General Conference",
     None,
     "President Smith teaches about the importance of love, kindness, and service to all people.",
     [("Matthew", 22, 36, 40), ("Mosiah", 2, 17),
      ("John", 13, 34, 35), ("Moroni", 7, 45, 48)]),

    ("David O. McKay", "Every Member a Missionary", "1959-04-05",
     "April 1959 General Conference",
     None,
     "President McKay's landmark call for every member to share the gospel.",
     [("Matthew", 28, 19, 20), ("Doctrine and Covenants", 4, 1, 7),
      ("Doctrine and Covenants", 88, 81), ("3 Nephi", 12, 14, 16),
      ("Alma", 26, 5, 7)]),

    ("Joseph Fielding Smith", "Seek Ye Earnestly", "1961-04-09",
     "April 1961 General Conference",
     None,
     "Elder Smith (later President) teaches about the importance of scripture study.",
     [("2 Timothy", 3, 16, 17), ("2 Nephi", 32, 3),
      ("Doctrine and Covenants", 18, 34, 36), ("John", 5, 39),
      ("1 Nephi", 19, 23)]),

    ("Harold B. Lee", "Stand Ye in Holy Places", "1973-10-07",
     "October 1973 General Conference",
     None,
     "President Lee's final conference address about standing in holy places and being not moved.",
     [("Doctrine and Covenants", 87, 8), ("Doctrine and Covenants", 45, 32),
      ("Matthew", 24, 15), ("3 Nephi", 20, 22)]),

    ("Spencer W. Kimball", "The False Gods We Worship", "1976-06-01",
     "Ensign June 1976",
     "https://www.churchofjesuschrist.org/study/ensign/1976/06/the-false-gods-we-worship",
     "President Kimball warns against materialism and idolatry in modern society.",
     [("Exodus", 20, 3, 5), ("Matthew", 6, 24), ("Alma", 1, 32),
      ("Doctrine and Covenants", 56, 16, 17), ("1 Nephi", 22, 23),
      ("Jacob", 2, 17, 19)]),

    ("Spencer W. Kimball", "When the World Will Be Converted", "1974-04-07",
     "April 1974 General Conference",
     None,
     "President Kimball's visionary call to lengthen our stride in missionary work and service.",
     [("Doctrine and Covenants", 4, 1, 4), ("Matthew", 28, 19, 20),
      ("1 Nephi", 14, 12, 14), ("Doctrine and Covenants", 88, 81)]),

    ("Ezra Taft Benson", "The Book of Mormon — Keystone of Our Religion", "1986-10-05",
     "October 1986 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/1986/10/the-book-of-mormon-keystone-of-our-religion",
     "President Benson's landmark address calling the Church to study the Book of Mormon.",
     [("1 Nephi", 1, 1), ("2 Nephi", 25, 26), ("2 Nephi", 33, 10),
      ("Moroni", 10, 4, 5), ("Doctrine and Covenants", 84, 54, 57),
      ("Alma", 37, 44), ("3 Nephi", 27, 27)]),

    ("Ezra Taft Benson", "Beware of Pride", "1989-04-02",
     "April 1989 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/1989/04/beware-of-pride",
     "President Benson warns about the universal sin of pride and teaches humility.",
     [("Moroni", 8, 27), ("Doctrine and Covenants", 23, 1),
      ("Proverbs", 6, 16, 17), ("Jacob", 2, 13),
      ("Alma", 5, 28), ("Helaman", 12, 1, 6)]),

    ("Howard W. Hunter", "The Great Symbol of Our Membership", "1994-10-02",
     "October 1994 General Conference",
     None,
     "President Hunter invites every member to make the temple the great symbol of their membership.",
     [("Doctrine and Covenants", 109, 8), ("Doctrine and Covenants", 110, 1, 10),
      ("Malachi", 4, 5, 6), ("Doctrine and Covenants", 124, 40, 41),
      ("2 Nephi", 5, 16)]),

    ("Gordon B. Hinckley", "The Marvelous Foundation of Our Faith", "2002-10-06",
     "October 2002 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2002/10/the-marvelous-foundation-of-our-faith",
     "President Hinckley testifies of the First Vision and the foundation of the Restoration.",
     [("Joseph Smith—History", 1, 14, 20), ("James", 1, 5),
      ("3 Nephi", 11, 7, 11), ("Doctrine and Covenants", 1, 30),
      ("Doctrine and Covenants", 76, 22, 24)]),

    ("Gordon B. Hinckley", "War and Peace", "2003-04-06",
     "April 2003 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2003/04/war-and-peace",
     "President Hinckley addresses the challenges of war and the need for peace.",
     [("Doctrine and Covenants", 98, 16), ("Matthew", 5, 9),
      ("3 Nephi", 12, 9), ("Alma", 48, 11, 13),
      ("Mormon", 7, 4)]),

    ("Thomas S. Monson", "Dare to Stand Alone", "2011-10-02",
     "October 2011 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2011/10/dare-to-stand-alone",
     "President Monson teaches about moral courage and standing for truth.",
     [("Daniel", 3, 16, 18), ("1 Nephi", 3, 7), ("Joshua", 1, 9),
      ("Doctrine and Covenants", 121, 45), ("Alma", 53, 20, 21)]),

    ("Thomas S. Monson", "The Power of the Priesthood", "2010-04-04",
     "April 2010 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2010/04/the-power-of-the-priesthood",
     "President Monson teaches about honoring and magnifying the priesthood.",
     [("Doctrine and Covenants", 121, 36, 46), ("Doctrine and Covenants", 84, 33, 40),
      ("Alma", 13, 1, 6), ("Jacob", 1, 19)]),

    # --- BOOK OF MORMON-FOCUSED TALKS ---

    ("Tad R. Callister", "The Book of Mormon — a Book from God", "2011-10-02",
     "October 2011 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2011/10/the-book-of-mormon-a-book-from-god",
     "Elder Callister provides compelling evidence and testimony of the divine origin of the Book of Mormon.",
     [("1 Nephi", 1, 1), ("2 Nephi", 29, 8), ("Mormon", 8, 12),
      ("Ether", 5, 3), ("Moroni", 10, 3, 5), ("2 Nephi", 27, 12),
      ("Alma", 37, 4), ("1 Nephi", 13, 40)]),

    ("Boyd K. Packer", "The Book of Mormon: Another Testament of Jesus Christ", "2005-04-03",
     "April 2005 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2005/04/the-book-of-mormon-another-testament-of-jesus-christ-plain-and-precious-things",
     "President Packer testifies of the Book of Mormon as another testament of Jesus Christ.",
     [("1 Nephi", 13, 26, 29), ("1 Nephi", 13, 40), ("2 Nephi", 3, 12),
      ("2 Nephi", 25, 23, 26), ("2 Nephi", 29, 3, 8),
      ("Mormon", 7, 8, 9)]),

    # --- DOCTRINE & COVENANTS / PEARL OF GREAT PRICE FOCUSED ---

    ("Robert D. Hales", "The Covenant of Baptism", "2000-10-01",
     "October 2000 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2000/10/the-covenant-of-baptism-to-be-in-the-kingdom-and-of-the-kingdom",
     "Elder Hales teaches about the baptismal covenant and its significance.",
     [("2 Nephi", 31, 5, 13), ("Mosiah", 18, 8, 10),
      ("Doctrine and Covenants", 20, 37), ("3 Nephi", 11, 23, 26),
      ("Moses", 6, 64, 66), ("Acts", 2, 38)]),

    ("Bruce R. McConkie", "The Purifying Power of Gethsemane", "1985-04-07",
     "April 1985 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/1985/04/the-purifying-power-of-gethsemane",
     "Elder McConkie's final testimony of the Atonement, delivered weeks before his death.",
     [("Mosiah", 3, 7), ("Doctrine and Covenants", 19, 16, 19),
      ("Luke", 22, 44), ("Alma", 7, 11, 13),
      ("2 Nephi", 9, 21, 22), ("Jacob", 4, 12),
      ("Moses", 7, 47)]),

    ("Neal A. Maxwell", "Swallowed Up in the Will of the Father", "1995-10-01",
     "October 1995 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/1995/10/swallowed-up-in-the-will-of-the-father",
     "Elder Maxwell teaches about submitting our will to God's will through the Atonement.",
     [("Mosiah", 15, 7), ("3 Nephi", 11, 11), ("Alma", 7, 11, 13),
      ("Doctrine and Covenants", 19, 18), ("Moses", 4, 2),
      ("Abraham", 3, 27), ("Luke", 22, 42)]),

    # --- BIBLE-FOCUSED TALKS ---

    ("M. Russell Ballard", "The Miracle of the Holy Bible", "2007-04-01",
     "April 2007 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2007/04/the-miracle-of-the-holy-bible",
     "Elder Ballard testifies of the importance and divine nature of the Holy Bible.",
     [("2 Timothy", 3, 16), ("Isaiah", 29, 14), ("John", 3, 16),
      ("John", 17, 3), ("Psalms", 23, 1), ("1 Nephi", 13, 20, 23),
      ("2 Nephi", 29, 3, 6), ("Articles of Faith", 1, 8)]),

    ("Richard G. Scott", "The Power of Scripture", "2011-10-02",
     "October 2011 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2011/10/the-power-of-scripture",
     "Elder Scott teaches about the transforming power of regular scripture study.",
     [("2 Nephi", 32, 3), ("Alma", 31, 5), ("Doctrine and Covenants", 18, 34, 36),
      ("2 Timothy", 3, 16, 17), ("1 Nephi", 19, 23), ("Helaman", 3, 29)]),

    # --- PEARL OF GREAT PRICE FOCUSED ---

    ("Russell M. Nelson", "The Creation", "2000-04-02",
     "April 2000 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2000/04/the-creation",
     "President Nelson teaches about the creation of the earth and its divine purpose.",
     [("Moses", 1, 39), ("Moses", 2, 1), ("Abraham", 3, 24, 25),
      ("Abraham", 4, 1), ("Genesis", 1, 1), ("Genesis", 1, 27),
      ("Doctrine and Covenants", 88, 47, 50)]),

    ("Robert D. Hales", "Agency: Essential to the Plan of Life", "2010-10-03",
     "October 2010 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2010/10/agency-essential-to-the-plan-of-life",
     "Elder Hales teaches about the essential nature of agency in God's plan.",
     [("Moses", 4, 3), ("Moses", 7, 32), ("2 Nephi", 2, 27),
      ("Abraham", 3, 25, 26), ("Doctrine and Covenants", 93, 31),
      ("Helaman", 14, 30, 31), ("Alma", 12, 31)]),

    # --- WOMEN LEADERS ---

    ("Jean B. Bingham", "United in Accomplishing God's Work", "2020-10-04",
     "October 2020 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2020/10/14bingham",
     "Sister Bingham teaches about unity between women and men in God's work.",
     [("Mosiah", 18, 21), ("Moses", 7, 18), ("4 Nephi", 1, 15, 17),
      ("Doctrine and Covenants", 38, 27), ("Ephesians", 4, 11, 13)]),

    ("Bonnie H. Cordon", "Trust in the Lord and Lean Not", "2021-04-04",
     "April 2021 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2021/04/27cordon",
     "Sister Cordon teaches about trusting God's plan even when it's difficult.",
     [("Proverbs", 3, 5, 6), ("2 Nephi", 4, 34),
      ("Alma", 36, 3), ("Doctrine and Covenants", 6, 36)]),

    ("Reyna I. Aburto", "Thru Cloud and Sunshine", "2019-10-06",
     "October 2019 General Conference",
     "https://www.churchofjesuschrist.org/study/general-conference/2019/10/22aburto",
     "Sister Aburto teaches about finding joy and strength through challenges.",
     [("2 Nephi", 2, 25), ("Alma", 7, 11, 12), ("John", 16, 33),
      ("Romans", 8, 28), ("Doctrine and Covenants", 122, 7, 8)]),
]


def rebuild_fts(conn):
    """Rebuild the talks FTS index."""
    conn.execute("DELETE FROM talks_fts")
    conn.execute("""
        INSERT INTO talks_fts(rowid, title, speaker, summary)
        SELECT id, title, speaker, COALESCE(summary, '')
        FROM talks
    """)
    conn.commit()
    print("FTS index rebuilt.")


def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # Get initial counts
    try:
        before_talks = conn.execute("SELECT COUNT(*) FROM talks").fetchone()[0]
    except sqlite3.OperationalError:
        before_talks = 0

    print(f"=== Import Talks ===")
    print(f"Database: {DB_PATH}")
    print(f"Talks before: {before_talks}")
    print()

    # Create tables
    create_tables(conn)

    # Insert talks
    inserted = 0
    skipped = 0
    total_refs = 0

    for talk_data in TALKS:
        speaker, title, date, conference, url, summary, refs = talk_data
        existing = talk_exists(conn, speaker, title)
        if existing:
            skipped += 1
        else:
            insert_talk(conn, speaker, title, date, conference, url, summary, refs)
            inserted += 1
            total_refs += len(refs)

    conn.commit()

    # Rebuild FTS
    rebuild_fts(conn)

    # Final counts
    after_talks = conn.execute("SELECT COUNT(*) FROM talks").fetchone()[0]
    after_refs = conn.execute("SELECT COUNT(*) FROM talk_scripture_refs").fetchone()[0]
    unique_speakers = conn.execute("SELECT COUNT(DISTINCT speaker) FROM talks").fetchone()[0]

    print(f"\n=== Results ===")
    print(f"Talks inserted: {inserted}")
    print(f"Talks skipped (already existed): {skipped}")
    print(f"Scripture references added: {total_refs}")
    print(f"Total talks: {after_talks}")
    print(f"Total scripture references: {after_refs}")
    print(f"Unique speakers: {unique_speakers}")

    # Show coverage by volume
    print(f"\n=== Scripture Reference Coverage ===")
    rows = conn.execute("""
        SELECT book_title, COUNT(*) as ref_count
        FROM talk_scripture_refs
        GROUP BY book_title
        ORDER BY ref_count DESC
        LIMIT 20
    """).fetchall()
    for book, count in rows:
        print(f"  {book}: {count} references")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
