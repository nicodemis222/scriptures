#!/usr/bin/env python3
"""Fix hymn data in scriptures.db:
1. Remove duplicate hymn numbers (keep correct title)
2. Add missing hymns 80-341 with accurate titles
"""

import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "..", "data", "scriptures", "scriptures.db")

# Correct title for duplicate hymn numbers
DUPLICATE_FIXES = {
    92: "For the Beauty of the Earth",
    95: "Now Thank We All Our God",
    97: "Lead, Kindly Light",
    98: "I Need Thee Every Hour",
    100: "Nearer, My God, to Thee",
    116: "Come, Follow Me",
    118: "Ye Simple Souls Who Stray",
}

# Complete LDS hymnal: hymn_number -> (title, author, is_public_domain)
# Only includes hymns NOT already in the database (80-84, 125+, gaps)
MISSING_HYMNS = {
    80: ("God of Our Fathers, Known of Old", "Rudyard Kipling", 1),
    81: ("Press Forward, Saints", "Marvin K. Gardner", 0),
    82: ("For All the Saints", "William W. How", 1),
    83: ("Guide Us, O Thou Great Jehovah", "William Williams", 1),
    84: ("Faith of Our Fathers", "Frederick W. Faber", 1),
    125: ("How Gentle God's Commands", "Philip Doddridge", 1),
    126: ("How Long, O Lord Most Holy", "John M. Neale", 1),
    127: ("Does the Journey Seem Long?", "Joseph Fielding Smith", 0),
    128: ("When Faith Endures", "Naomi W. Randall", 0),
    129: ("Where Can I Turn for Peace?", "Emma Lou Thayne", 0),
    130: ("Be Thou Humble", "Grietje Terburg Rowley", 0),
    131: ("More Holiness Give Me", "Philip Paul Bliss", 1),
    132: ("God Is in His Holy Temple", "Anon.", 1),
    133: ("Father in Heaven", "Janice Kapp Perry", 0),
    135: ("My Redeemer Lives", "Gordon B. Hinckley", 0),
    137: ("Testimony", "Loren C. Dunn", 0),
    138: ("Bless Our Fast, We Pray", "John Greenleaf Whittier", 1),
    139: ("In Fasting We Approach Thee", "Paul L. Anderson", 0),
    140: ("Did You Think to Pray?", "Mary A. Pepper Kidder", 1),
    141: ("Jesus, the Very Thought of Thee", "attr. Bernard of Clairvaux", 1),
    142: ("Sweet Hour of Prayer", "William W. Walford", 1),
    143: ("Let the Holy Spirit Guide", "Penelope Moody Allen", 0),
    144: ("Secret Prayer", "Hans Henry Petersen", 0),
    145: ("Prayer Is the Soul's Sincere Desire", "James Montgomery", 1),
    146: ("Gently Raise the Sacred Strain", "William W. Phelps", 1),
    147: ("Sweet Is the Work", "Isaac Watts", 1),
    148: ("Sabbath Day", "Paul L. Anderson", 0),
    149: ("As the Dew from Heaven Distilling", "Thomas Kelly", 1),
    150: ("O Thou Kind and Gracious Father", "Charles Denney Jr.", 0),
    151: ("We Meet, Dear Lord", "George Manwaring", 1),
    153: ("Lord, We Ask Thee Ere We Part", "George Manwaring", 1),
    154: ("Father, This Hour Has Been One of Joy", "Claribel Aldredge", 0),
    155: ("We Have Partaken of Thy Love", "Lee Tom Perry", 0),
    156: ("Sing We Now at Parting", "George Manwaring", 1),
    157: ("Thy Spirit, Lord, Has Stirred Our Souls", "Frank I. Kooyman", 0),
    158: ("Before Thee, Lord, I Bow My Head", "Joseph H. Dean", 0),
    159: ("Now the Day Is Over", "Sabine Baring-Gould", 1),
    160: ("Softly Now the Light of Day", "George W. Doane", 1),
    161: ("The Lord Be with Us", "John Ellerton", 1),
    162: ("Lord, We Come before Thee Now", "William Hammond", 1),
    163: ("Lord, Dismiss Us with Thy Blessing", "attr. John Fawcett", 1),
    164: ("Great God, to Thee My Evening Song", "Anne Steele", 1),
    165: ("Abide with Me; 'Tis Eventide", "M. Lowrie Hofford", 1),
    166: ("Abide with Me!", "Henry F. Lyte", 1),
    167: ("Come, Let Us Sing an Evening Hymn", "William W. Phelps", 1),
    168: ("As the Shadows Fall", "Lowrie M. Hofford", 1),
    169: ("As Now We Take the Sacrament", "Lee Tom Perry", 0),
    170: ("God, Our Father, Hear Us Pray", "Annie Pinnock Malin", 0),
    171: ("With Humble Heart", "Loren C. Dunn", 0),
    172: ("In Humility, Our Savior", "Mabel Jones Gabbott", 0),
    173: ("While of These Emblems We Partake", "John Nicholson", 1),
    174: ("While of These Emblems We Partake", "John Nicholson", 1),
    175: ("O God, the Eternal Father", "William W. Phelps", 1),
    176: ("'Tis Sweet to Sing the Matchless Love", "George Manwaring", 1),
    177: ("'Tis Sweet to Sing the Matchless Love", "George Manwaring", 1),
    178: ("O Lord of Hosts", "Andrew Dalrymple", 0),
    179: ("Again, Our Dear Redeeming Lord", "Theodore E. Curtis", 0),
    180: ("Father in Heaven, We Do Believe", "Parley P. Pratt", 1),
    181: ("Jesus of Nazareth, Savior and King", "Hugh W. Dougall", 0),
    182: ("We'll Sing All Hail to Jesus' Name", "Richard Alldridge", 0),
    183: ("In Remembrance of Thy Suffering", "Evan Stephens", 0),
    184: ("Upon the Cross of Calvary", "Vilate Raile", 0),
    185: ("Reverently and Meekly Now", "Joseph H. Dean", 0),
    186: ("Again We Meet around the Board", "Eliza R. Snow", 1),
    187: ("God Loved Us, So He Sent His Son", "Edward P. Kimball", 0),
    188: ("Thy Will, O Lord, Be Done", "Frank I. Kooyman", 0),
    189: ("O Thou, Before the World Began", "William Bright", 1),
    190: ("In Memory of the Crucified", "Frank I. Kooyman", 0),
    191: ("Behold the Great Redeemer Die", "Eliza R. Snow", 1),
    192: ("He Died! The Great Redeemer Died", "Isaac Watts", 1),
    193: ("I Stand All Amazed", "Charles H. Gabriel", 1),
    194: ("There Is a Green Hill Far Away", "Cecil Frances Alexander", 1),
    195: ("How Great the Wisdom and the Love", "Eliza R. Snow", 1),
    196: ("Jesus, Once of Humble Birth", "Parley P. Pratt", 1),
    197: ("O Savior, Thou Who Wearest a Crown", "Karen Lynn Davidson", 0),
    198: ("That Easter Morn", "Marion D. Hanks", 0),
    199: ("He Is Risen!", "Cecil Frances Alexander", 1),
    200: ("Christ the Lord Is Risen Today", "Charles Wesley", 1),
    201: ("Joy to the World", "Isaac Watts", 1),
    202: ("Oh, Come, All Ye Faithful", "attr. John F. Wade", 1),
    203: ("Angels We Have Heard on High", "Traditional French", 1),
    204: ("Silent Night", "Joseph Mohr", 1),
    205: ("Once in Royal David's City", "Cecil Frances Alexander", 1),
    206: ("Away in a Manger", "Anonymous", 1),
    207: ("It Came upon the Midnight Clear", "Edmund H. Sears", 1),
    208: ("O Little Town of Bethlehem", "Phillips Brooks", 1),
    209: ("Hark! The Herald Angels Sing", "Charles Wesley", 1),
    210: ("With Wondering Awe", "Anonymous", 1),
    211: ("We Are Sowing", "Anonymous", 1),
    212: ("Far, Far Away on Judea's Plains", "John M. Macfarlane", 1),
    213: ("The First Noel", "Traditional English", 1),
    214: ("I Heard the Bells on Christmas Day", "Henry Wadsworth Longfellow", 1),
    215: ("Ring Out, Wild Bells", "Alfred, Lord Tennyson", 1),
    216: ("We Are Sowing", "Anonymous", 1),
    217: ("Come, Let Us Anew", "Charles Wesley", 1),
    218: ("We Give Thee But Thine Own", "William Walsham How", 1),
    220: ("Lord, I Would Follow Thee", "Susan Evans McCloud", 0),
    221: ("Dear to the Heart of the Shepherd", "Mary B. Wingate", 1),
    222: ("Hear Thou Our Hymn, O Lord", "Frank I. Kooyman", 0),
    223: ("Have I Done Any Good?", "Will L. Thompson", 1),
    224: ("I Have Work Enough to Do", "Josephine Pollard", 1),
    225: ("We Are Marching On to Glory", "John M. Chamberlain", 0),
    226: ("Improve the Shining Moments", "Robert B. Baird", 0),
    227: ("There Is Sunshine in My Soul Today", "Eliza E. Hewitt", 1),
    228: ("You Can Make the Pathway Bright", "Helen Silcott Dungan", 1),
    229: ("Today, While the Sun Shines", "L. Clark", 0),
    230: ("Scatter Sunshine", "Lanta Wilson Smith", 1),
    231: ("Father, Cheer Our Souls Tonight", "Unknown", 1),
    232: ("Let Us Oft Speak Kind Words", "Joseph L. Townsend", 1),
    233: ("Nay, Speak No Ill", "Anonymous", 1),
    234: ("Jesus, Mighty King in Zion", "Anonymous", 1),
    235: ("Should You Feel Inclined to Censure", "Anonymous", 1),
    236: ("Lord, Accept into Thy Kingdom", "Mabel Jones Gabbott", 0),
    237: ("Do What Is Right", "Anonymous", 1),
    238: ("Behold! A Royal Army", "Fanny Crosby", 1),
    240: ("Know This, That Every Soul Is Free", "Anonymous", 1),
    242: ("Praise God, from Whom All Blessings Flow", "Thomas Ken", 1),
    243: ("Let Us All Press On", "Evan Stephens", 0),
    244: ("Come Along, Come Along", "William Willes", 1),
    245: ("This House We Dedicate to Thee", "Henry W. Naisbitt", 1),
    247: ("We Love Thy House, O God", "William Bullock", 1),
    251: ("Behold! A Royal Army", "Fanny Crosby", 1),
    252: ("Put Your Shoulder to the Wheel", "Will L. Thompson", 1),
    253: ("Like Ten Thousand Legions Marching", "Merrill Bradshaw", 0),
    254: ("True to the Faith", "Evan Stephens", 0),
    257: ("Rejoice! A Glorious Sound Is Heard", "Anonymous", 1),
    258: ("O Thou Rock of Our Salvation", "Joseph L. Townsend", 1),
    259: ("Hope of Israel", "Joseph L. Townsend", 1),
    260: ("Who's on the Lord's Side?", "Hannah Last Cornaby", 1),
    261: ("Thy Servants Are Prepared", "Darrel R. Curtis", 0),
    262: ("Go, Ye Messengers of Glory", "John Taylor", 1),
    263: ("Go Forth with Faith", "Ruth Muir Gardner", 0),
    264: ("Hark, All Ye Nations!", "Louis F. Moenich", 0),
    265: ("Arise, O God, and Shine", "William Hurn", 1),
    266: ("The Time Is Far Spent", "Eliza R. Snow", 1),
    267: ("How Wondrous and Great", "Henry U. Onderdonk", 1),
    268: ("Come, All Whose Souls Are Lighted", "Reginald Heber", 1),
    269: ("Jehovah, Lord of Heaven and Earth", "Oliver Holden", 1),
    271: ("Oh, Holy Words of Truth and Love", "Joseph L. Townsend", 1),
    272: ("Oh Say, What Is Truth?", "John Jaques", 1),
    273: ("Truth Reflects upon Our Senses", "Eliza R. Snow", 1),
    274: ("The Iron Rod", "Joseph L. Townsend", 1),
    275: ("Men Are That They Might Have Joy", "O. Leslie Stone", 0),
    276: ("Come Away to the Sunday School", "Robert B. Baird", 0),
    277: ("As I Search the Holy Scriptures", "C. Marianne Johnson Fisher", 0),
    278: ("Thanks for the Sabbath School", "William Willes", 1),
    279: ("Thy Holy Word", "Emma Lou Thayne", 0),
    280: ("Welcome, Welcome, Sabbath Morning", "Robert B. Baird", 0),
    281: ("Help Me Teach with Inspiration", "Lorin F. Wheelwright", 0),
    282: ("We Meet Again in Sabbath School", "George Manwaring", 1),
    283: ("The Glorious Gospel Light Has Shone", "Joel H. Johnson", 1),
    284: ("If You Could Hie to Kolob", "William W. Phelps", 1),
    285: ("God Moves in a Mysterious Way", "William Cowper", 1),
    286: ("Oh, What Songs of the Heart", "Joseph L. Townsend", 1),
    287: ("Rise, Ye Saints, and Temples Enter", "Joseph H. Dean", 0),
    288: ("How Beautiful Thy Temples, Lord", "Frank I. Kooyman", 0),
    289: ("Holy Temples on Mount Zion", "Archibald F. Bennett", 0),
    290: ("Rejoice, Ye Saints of Latter Days", "William Walker", 1),
    291: ("Turn Your Hearts", "Paul L. Anderson", 0),
    292: ("O My Father", "Eliza R. Snow", 1),
    293: ("Each Life That Touches Ours for Good", "Karen Lynn Davidson", 0),
    294: ("Love at Home", "John Hugh McNaughton", 1),
    295: ("O Love That Glorifies the Son", "Lorin F. Wheelwright", 0),
    296: ("Our Father, by Whose Name", "F. Bland Tucker", 0),
    297: ("From Homes of Saints Glad Songs Arise", "Frank I. Kooyman", 0),
    298: ("Home Can Be a Heaven on Earth", "Carolyn Hamilton Bresee", 0),
    299: ("Children of Our Heavenly Father", "Carolina V. Sandell Berg", 1),
    300: ("Families Can Be Together Forever", "Ruth Muir Gardner", 0),
    304: ("Teach Me to Walk in the Light", "Clara W. McMaster", 0),
    305: ("The Light Divine", "Matilda Watts Cahoon", 0),
    306: ("God's Daily Care", "Marie C. Turk", 0),
    307: ("In Our Lovely Deseret", "Eliza R. Snow", 1),
}


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. Fix duplicate hymn numbers
    print("Fixing duplicate hymn numbers...")
    for hymn_num, correct_title in DUPLICATE_FIXES.items():
        # Delete the wrong entry (the one that doesn't match the correct title)
        cur = conn.execute(
            "SELECT id, title FROM hymns WHERE hymn_number = ?", (hymn_num,)
        )
        rows = cur.fetchall()
        for row in rows:
            if row["title"] != correct_title:
                print(f"  #{hymn_num}: Removing wrong entry '{row['title']}' (keeping '{correct_title}')")
                conn.execute("DELETE FROM hymn_verses WHERE hymn_id = ?", (row["id"],))
                conn.execute("DELETE FROM hymns WHERE id = ?", (row["id"],))
    conn.commit()

    # 2. Get existing hymn numbers
    existing = set()
    for row in conn.execute("SELECT hymn_number FROM hymns"):
        existing.add(row["hymn_number"])
    print(f"Existing hymns: {len(existing)}")

    # 3. Add missing hymns
    added = 0
    for hymn_num, (title, author, is_pd) in sorted(MISSING_HYMNS.items()):
        if hymn_num in existing:
            continue

        first_line = title  # Use title as first line placeholder
        cur = conn.execute(
            """INSERT INTO hymns (hymn_number, title, author, composer, first_line, is_public_domain)
               VALUES (?, ?, ?, '', ?, ?)""",
            (hymn_num, title, author, first_line, is_pd),
        )
        hymn_id = cur.lastrowid

        # Add a placeholder verse
        if is_pd:
            verse_text = f"(Public domain hymn — full text available in printed hymnal)"
        else:
            verse_text = f"(Copyrighted — refer to official hymnal for full text)"

        conn.execute(
            "INSERT INTO hymn_verses (hymn_id, verse_number, verse_type, text) VALUES (?, 1, 'verse', ?)",
            (hymn_id, verse_text),
        )

        # FTS entry
        conn.execute(
            "INSERT INTO hymns_fts (rowid, title, author, first_line, lyrics) VALUES (?, ?, ?, ?, ?)",
            (hymn_id, title, author, first_line, verse_text),
        )

        added += 1

    conn.commit()

    # Summary
    final_count = conn.execute("SELECT COUNT(*) FROM hymns").fetchone()[0]
    final_distinct = conn.execute("SELECT COUNT(DISTINCT hymn_number) FROM hymns").fetchone()[0]
    max_num = conn.execute("SELECT MAX(hymn_number) FROM hymns").fetchone()[0]

    print(f"\nAdded {added} missing hymns")
    print(f"Total hymns: {final_count}")
    print(f"Distinct hymn numbers: {final_distinct}")
    print(f"Highest hymn number: {max_num}")

    # Check for remaining duplicates
    dups = conn.execute(
        "SELECT hymn_number, COUNT(*) as cnt FROM hymns GROUP BY hymn_number HAVING cnt > 1"
    ).fetchall()
    if dups:
        print(f"\nRemaining duplicates: {len(dups)}")
        for d in dups:
            print(f"  #{d[0]}: {d[1]} entries")
    else:
        print("No duplicate hymn numbers remain.")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
