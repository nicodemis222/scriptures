#!/usr/bin/env python3
"""Import public domain hymn lyrics into ARK scriptures DB."""

import os
import re
import sqlite3
import sys
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    os.system(f"{sys.executable} -m pip install requests beautifulsoup4 lxml")
    import requests
    from bs4 import BeautifulSoup

DB = os.path.join(os.path.dirname(__file__), "..", "data", "scriptures", "scriptures.db")
HEADERS = {"User-Agent": "ARK-Hymns-Importer/1.0"}

# Public domain hymns with hymnary.org text IDs
HYMNS = [
    ("Amazing Grace", "John Newton", "amazing_grace_how_sweet_the_sound"),
    ("How Great Thou Art", "Carl Boberg", "o_lord_my_god_when_i_in_awesome"),
    ("Be Thou My Vision", "Irish hymn", "be_thou_my_vision_o_lord_of_my"),
    ("It Is Well With My Soul", "Horatio Spafford", "when_peace_like_a_river_attendeth"),
    ("Holy Holy Holy", "Reginald Heber", "holy_holy_holy_lord_god_almighty_early"),
    ("A Mighty Fortress Is Our God", "Martin Luther", "a_mighty_fortress_is_our_god_a"),
    ("Abide With Me", "Henry Lyte", "abide_with_me_fast_falls_the_eventide"),
    ("Rock of Ages", "Augustus Toplady", "rock_of_ages_cleft_for_me_let"),
    ("Come Thou Fount", "Robert Robinson", "come_thou_fount_of_every_blessing_tune"),
    ("Great Is Thy Faithfulness", "Thomas Chisholm", "great_is_thy_faithfulness_o_god_my"),
    ("The Old Rugged Cross", "George Bennard", "on_a_hill_far_away_stood_an"),
    ("What a Friend We Have in Jesus", "Joseph Scriven", "what_a_friend_we_have_in_jesus_all"),
    ("Fairest Lord Jesus", "German hymn", "fairest_lord_jesus_ruler_of_all"),
    ("O Come O Come Emmanuel", "Latin hymn", "o_come_o_come_emmanuel_and_ransom"),
    ("Silent Night", "Joseph Mohr", "silent_night_holy_night_all_is_calm"),
    ("Joy to the World", "Isaac Watts", "joy_to_the_world_the_lord_is_come"),
    ("Hark the Herald Angels Sing", "Charles Wesley", "hark_the_herald_angels_sing_glory_to"),
    ("Nearer My God to Thee", "Sarah Adams", "nearer_my_god_to_thee_nearer_to"),
    ("Onward Christian Soldiers", "Sabine Baring-Gould", "onward_christian_soldiers_marching_as"),
    ("All Creatures of Our God and King", "Francis of Assisi", "all_creatures_of_our_god_and_king"),
    ("For the Beauty of the Earth", "Folliot Pierpoint", "for_the_beauty_of_the_earth_for"),
    ("Just As I Am", "Charlotte Elliott", "just_as_i_am_without_one_plea_but"),
    ("Lead Kindly Light", "John Henry Newman", "lead_kindly_light_amid_the_encircling"),
    ("Battle Hymn of the Republic", "Julia Ward Howe", "mine_eyes_have_seen_the_glory_of"),
    ("Blessed Assurance", "Fanny Crosby", "blessed_assurance_jesus_is_mine_o"),
    ("In the Garden", "C. Austin Miles", "i_come_to_the_garden_alone_while"),
    ("All Hail the Power of Jesus' Name", "Edward Perronet", "all_hail_the_power_of_jesus_name"),
    ("O God Our Help in Ages Past", "Isaac Watts", "o_god_our_help_in_ages_past_our"),
    ("When I Survey the Wondrous Cross", "Isaac Watts", "when_i_survey_the_wondrous_cross_on"),
    ("My Faith Looks Up to Thee", "Ray Palmer", "my_faith_looks_up_to_thee_thou"),
]


def fetch_hymn_text(text_id):
    """Fetch hymn lyrics from hymnary.org."""
    url = f"https://hymnary.org/text/{text_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")

        # Find the hymn text - usually in div.authority_columns or div#TextColumn
        text_div = soup.find("div", class_="authority_columns") or soup.find("div", id="TextColumn")
        if not text_div:
            # Try finding stanzas directly
            stanzas = soup.find_all("p", class_="stanza")
            if stanzas:
                verses = []
                for s in stanzas:
                    text = s.get_text(separator="\n").strip()
                    if text:
                        verses.append(text)
                return verses

        if text_div:
            # Extract stanzas
            stanzas = text_div.find_all("p")
            verses = []
            for p in stanzas:
                text = p.get_text(separator="\n").strip()
                # Skip very short or navigation text
                if len(text) > 10 and "hymnary" not in text.lower():
                    verses.append(text)
            return verses if verses else None

        return None
    except Exception as e:
        print(f"    Error fetching {text_id}: {e}")
        return None


def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")

    existing_hymns = set()
    for row in conn.execute("SELECT title FROM hymns"):
        existing_hymns.add(row[0].lower())

    next_num = conn.execute("SELECT COALESCE(MAX(hymn_number), 150) + 1 FROM hymns").fetchone()[0]
    added = 0

    print(f"Existing hymns: {len(existing_hymns)}")
    print(f"Starting hymn number: {next_num}")
    print()

    for title, author, text_id in HYMNS:
        if title.lower() in existing_hymns:
            print(f"  SKIP {title} (already exists)")
            continue

        print(f"  Fetching: {title}...", end=" ")
        verses = fetch_hymn_text(text_id)

        if not verses:
            print("no text found")
            continue

        # Insert hymn
        cur = conn.execute(
            "INSERT INTO hymns(hymn_number, title, author, first_line, is_public_domain) VALUES(?,?,?,?,1)",
            (next_num, title, author, verses[0].split("\n")[0][:100] if verses else ""),
        )
        hymn_id = cur.lastrowid

        # Insert verses
        for i, verse_text in enumerate(verses, 1):
            conn.execute(
                "INSERT INTO hymn_verses(hymn_id, verse_number, text) VALUES(?,?,?)",
                (hymn_id, i, verse_text),
            )

        conn.commit()
        next_num += 1
        added += 1
        print(f"{len(verses)} verses")

        # Be polite to hymnary.org
        time.sleep(1)

    # Rebuild hymns FTS if it exists
    try:
        conn.execute("DELETE FROM hymns_fts")
        conn.execute("""
            INSERT INTO hymns_fts(rowid, title, author, first_line)
            SELECT id, title, author, first_line FROM hymns
        """)
        conn.commit()
        print(f"\nHymns FTS rebuilt")
    except Exception as e:
        print(f"\nHymns FTS rebuild: {e}")

    total = conn.execute("SELECT COUNT(*) FROM hymns").fetchone()[0]
    total_verses = conn.execute("SELECT COUNT(*) FROM hymn_verses").fetchone()[0]
    print(f"\nTotal hymns: {total}")
    print(f"Total hymn verses: {total_verses}")
    print(f"Added: {added}")

    conn.close()


if __name__ == "__main__":
    main()
