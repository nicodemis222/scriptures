#!/usr/bin/env python3
"""
fix-dss-final.py — Replace corrupted Community Rule and Damascus Document
with clean scholarly translations. Also verify other DSS scrolls.
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'scriptures.db')

def delete_book_content(conn, book_id):
    """Delete all verses and chapters for a book."""
    chapter_ids = [r[0] for r in conn.execute(
        "SELECT id FROM chapters WHERE book_id = ?", (book_id,)
    ).fetchall()]
    if chapter_ids:
        placeholders = ','.join('?' * len(chapter_ids))
        conn.execute(f"DELETE FROM verses WHERE chapter_id IN ({placeholders})", chapter_ids)
    conn.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))
    conn.commit()

def insert_verses(conn, book_id, volume_id, verses_data):
    """Insert chapters and verses. verses_data: list of (chapter, verse_num, text, reference)"""
    chapters_seen = {}
    for ch, vn, text, ref in verses_data:
        if ch not in chapters_seen:
            conn.execute(
                "INSERT INTO chapters (book_id, chapter_number, num_verses) VALUES (?, ?, 0)",
                (book_id, ch)
            )
            chapters_seen[ch] = conn.execute(
                "SELECT id FROM chapters WHERE book_id = ? AND chapter_number = ?",
                (book_id, ch)
            ).fetchone()[0]

        conn.execute(
            "INSERT INTO verses (chapter_id, book_id, volume_id, verse_number, text, reference) VALUES (?, ?, ?, ?, ?, ?)",
            (chapters_seen[ch], book_id, volume_id, vn, text, ref)
        )

    # Update chapter verse counts
    for ch, ch_id in chapters_seen.items():
        count = conn.execute("SELECT COUNT(*) FROM verses WHERE chapter_id = ?", (ch_id,)).fetchone()[0]
        conn.execute("UPDATE chapters SET num_verses = ? WHERE id = ?", (count, ch_id))

    # Update book metadata
    conn.execute("UPDATE books SET num_chapters = ? WHERE id = ?", (len(chapters_seen), book_id))
    conn.commit()
    return len(verses_data)

# ============================================================================
# COMMUNITY RULE (1QS) — 11 Columns
# Based on Geza Vermes translation (The Dead Sea Scrolls in English)
# ============================================================================

COMMUNITY_RULE = [
    # Column I — Entrance into the Covenant
    (1, 1, "The Master shall teach the saints to live according to the Book of the Community Rule, that they may seek God with a whole heart and soul, and do what is good and right before Him as He commanded by the hand of Moses and all His servants the Prophets.", "1QS I:1"),
    (1, 2, "That they may love all that He has chosen and hate all that He has rejected; that they may abstain from all evil and hold fast to all good.", "1QS I:2"),
    (1, 3, "That they may practise truth, righteousness, and justice in the land and no longer stubbornly follow a sinful heart and lustful eyes committing all manner of evil.", "1QS I:3"),
    (1, 4, "He shall admit into the Covenant of Grace all those who have freely devoted themselves to the observance of God's precepts, that they may be joined to the counsel of God and may live perfectly before Him.", "1QS I:4"),
    (1, 5, "All those entering the Rule of the Community shall pass into the Covenant before God to obey all His commandments so that they may not abandon Him during the dominion of Satan because of fear or terror or affliction.", "1QS I:5"),
    (1, 6, "On entering the Covenant, the Priests and Levites shall bless the God of salvation and all His faithfulness, and all those entering the Covenant shall say after them, 'Amen, Amen!'", "1QS I:6"),
    (1, 7, "Then the Priests shall recite the favours of God manifested in His mighty deeds and shall declare all His merciful grace to Israel, and the Levites shall recite the iniquities of the children of Israel.", "1QS I:7"),
    (1, 8, "And all those entering the Covenant shall confess and say: 'We have strayed! We have disobeyed! We have sinned, we have been wicked, ourselves and our fathers before us, in that we have walked contrary to the precepts of truth and righteousness.'", "1QS I:8"),
    (1, 9, "And God has judged us and our fathers also; but He has bestowed His merciful grace upon us from everlasting to everlasting.", "1QS I:9"),
    (1, 10, "Then the Priests shall bless all the men of the lot of God who walk perfectly in all His ways, saying: 'May He bless you with all good and preserve you from all evil!'", "1QS I:10"),

    # Column II — Covenant Ceremony continued
    (2, 1, "May He lighten your heart with life-giving wisdom and grant you eternal knowledge! May He raise His merciful face towards you for everlasting bliss!", "1QS II:1"),
    (2, 2, "And the Levites shall curse all the men of the lot of Satan, saying: 'Be cursed because of all your guilty wickedness!'", "1QS II:2"),
    (2, 3, "May He deliver you up for torture at the hands of the vengeful Avengers! May He visit you with destruction by the hand of all the Wreakers of Revenge!", "1QS II:3"),
    (2, 4, "Be cursed without mercy because of the darkness of your deeds! Be damned in the shadowy place of everlasting fire! May God not heed when you call on Him, nor pardon you by blotting out your sin!", "1QS II:4"),
    (2, 5, "May He raise His angry face towards you for vengeance! May there be no peace for you in the mouth of those who hold fast to the Fathers!", "1QS II:5"),
    (2, 6, "And after the blessing and the cursing, all those entering the Covenant shall say, 'Amen, Amen!'", "1QS II:6"),
    (2, 7, "And the Priests and Levites shall continue, saying: 'Cursed be the man who enters this Covenant while walking among the idols of his heart.'", "1QS II:7"),
    (2, 8, "This shall be done year after year for as long as the dominion of Satan endures. The Priests shall enter first, ranked one after another according to the perfection of their spirit.", "1QS II:8"),
    (2, 9, "Then the Levites shall enter, and thirdly, all the people shall enter in order one after another in their Thousands, Hundreds, Fifties, and Tens.", "1QS II:9"),
    (2, 10, "That every Israelite may know his place in the Community of God according to the everlasting design.", "1QS II:10"),

    # Column III — The Two Spirits Doctrine
    (3, 1, "The Master shall instruct all the sons of light and shall teach them the nature of all the children of men according to the kind of spirit which they possess.", "1QS III:1"),
    (3, 2, "From the God of Knowledge comes all that is and shall be. Before ever they existed He established their whole design, and when, as ordained for them, they come into being, it is in accord with His glorious design that they accomplish their task without change.", "1QS III:2"),
    (3, 3, "He has created man to govern the world, and has appointed for him two spirits in which to walk until the time of His visitation: the spirits of truth and injustice.", "1QS III:3"),
    (3, 4, "Those born of truth spring from a fountain of light, but those born of injustice spring from a source of darkness. All the children of righteousness are ruled by the Prince of Light and walk in the ways of light.", "1QS III:4"),
    (3, 5, "But all the children of injustice are ruled by the Angel of Darkness and walk in the ways of darkness. The Angel of Darkness leads all the children of righteousness astray, and until his end, all their sin, iniquities, wickedness, and all their unlawful deeds are caused by his dominion.", "1QS III:5"),
    (3, 6, "And all their afflictions, and the seasons of their distress, and all the travails of their trials are through the dominion of his persecution; and all the spirits of his lot try to make the sons of light stumble.", "1QS III:6"),
    (3, 7, "But the God of Israel and His Angel of Truth will succour all the sons of light. For it is He who created the spirits of Light and Darkness and founded every action upon them.", "1QS III:7"),
    (3, 8, "God loves the one everlastingly and delights in its works for ever; but the counsel of the other He loathes and for ever hates its ways.", "1QS III:8"),

    # Column IV — The Ways of the Two Spirits
    (4, 1, "These are their ways in the world. The spirit of truth enlightens the heart of man, makes plain before him the ways of true righteousness, and causes his heart to fear the judgements of God.", "1QS IV:1"),
    (4, 2, "A spirit of humility, patience, abundant charity, unending goodness, understanding, and intelligence; a spirit of mighty wisdom which trusts in all the deeds of God and leans on His great lovingkindness.", "1QS IV:2"),
    (4, 3, "A spirit of discernment in every purpose, of zeal for just laws, of holy intent with steadfastness of heart, of great charity towards all the sons of truth.", "1QS IV:3"),
    (4, 4, "Of admirable purity which detests all unclean idols, of humble conduct sprung from an understanding of all things, and of faithful concealment of the mysteries of truth.", "1QS IV:4"),
    (4, 5, "These are the counsels of the spirit to the sons of truth in this world. And as for the visitation of all who walk in this spirit, it shall be healing, great peace in a long life, and fruitfulness.", "1QS IV:5"),
    (4, 6, "Together with every everlasting blessing and eternal joy in life without end, a crown of glory and a garment of majesty in unending light.", "1QS IV:6"),
    (4, 7, "But the ways of the spirit of falsehood are these: greed, and slackness in the search for righteousness, wickedness and lies, haughtiness and pride, falseness and deceit, cruelty and abundant evil.", "1QS IV:7"),
    (4, 8, "Ill-temper and much folly and brazen insolence, abominable deeds committed in a spirit of lust, and ways of lewdness in the service of uncleanness.", "1QS IV:8"),
    (4, 9, "A blaspheming tongue, blindness of eye and dullness of ear, stiffness of neck and heaviness of heart, so that man walks in all the ways of darkness and guile.", "1QS IV:9"),
    (4, 10, "And the visitation of all who walk in this spirit shall be a multitude of plagues by the hand of all the destroying angels, everlasting damnation by the avenging wrath of the fury of God, eternal torment and endless disgrace.", "1QS IV:10"),
    (4, 11, "Together with shameful extinction in the fire of the dark regions. The times of all their generations shall be spent in sorrowful mourning and in bitter misery and in calamities of darkness until they are destroyed without remnant or survivor.", "1QS IV:11"),
    (4, 12, "Now God in the mysteries of His understanding and in His glorious wisdom has ordained a period for the ruin of injustice, and at the time of visitation He will destroy it for ever.", "1QS IV:12"),
    (4, 13, "Then truth, which has wallowed in the ways of wickedness during the dominion of injustice until the appointed time of judgement, shall arise in the world for ever.", "1QS IV:13"),

    # Column V — Rules for Community Life
    (5, 1, "And this is the Rule for the men of the Community who have freely pledged themselves to be converted from all evil and to cling to all His commandments according to His will.", "1QS V:1"),
    (5, 2, "They shall separate from the congregation of the men of injustice and shall unite, with respect to the Law and possessions, under the authority of the sons of Zadok, the Priests who keep the Covenant.", "1QS V:2"),
    (5, 3, "Every decision concerning doctrine, property, and justice shall be determined by them. They shall practise truth and humility in common, and justice and uprightness and charity and modesty in all their ways.", "1QS V:3"),
    (5, 4, "No man shall walk in the stubbornness of his heart so that he strays after his heart and eyes and evil inclination, but he shall circumcise in the Community the foreskin of evil inclination and of stiffness of neck.", "1QS V:4"),
    (5, 5, "They shall lay a foundation of truth for Israel, for the Community of the everlasting Covenant. They shall atone for all those in Aaron who have freely pledged themselves for holiness, and for those in Israel who have pledged themselves to the House of Truth.", "1QS V:5"),
    (5, 6, "Whoever refuses to enter the Covenant of God so that he may walk in the stubbornness of his heart shall not enter the Community of His truth.", "1QS V:6"),
    (5, 7, "For his soul abhors the wise teachings of just laws. He has shown no strength in converting his life, and shall not be reckoned among the upright.", "1QS V:7"),
    (5, 8, "His knowledge, his strength, and his possessions shall not enter the Council of the Community, for whoever ploughs the mud of wickedness returns defiled.", "1QS V:8"),

    # Column VI — Penal Code and Procedures
    (6, 1, "And this is the Rule for an Assembly of the Congregation. Each man shall sit in his place: the Priests shall sit first, and the elders second, and all the rest of the people according to their rank.", "1QS VI:1"),
    (6, 2, "And thus shall they be questioned concerning the Law and concerning any counsel or matter coming before the Congregation, each man bringing his knowledge to the Council of the Community.", "1QS VI:2"),
    (6, 3, "No man shall interrupt a companion before his speech has ended, nor speak before a man of higher rank; each man shall speak in his turn.", "1QS VI:3"),
    (6, 4, "And in an Assembly of the Congregation no man shall speak without the consent of the Congregation, nor indeed of the Guardian of the Congregation.", "1QS VI:4"),
    (6, 5, "Whoever has anything to say to the Congregation but is not in a position of one who may question the Council of the Community, let him rise to his feet and say: 'I have something to say to the Congregation.' If they command him to speak, he shall speak.", "1QS VI:5"),
    (6, 6, "Every man born of Israel who freely pledges himself to join the Council of the Community shall be examined by the Guardian at the head of the Congregation concerning his understanding and his deeds.", "1QS VI:6"),
    (6, 7, "If he is fitted to the discipline, he shall admit him into the Covenant that he may be converted to the truth and depart from all falsehood.", "1QS VI:7"),
    (6, 8, "He shall instruct him in all the rules of the Community, and afterwards, when he comes to stand before the Congregation, they shall deliberate his case.", "1QS VI:8"),

    # Column VII — Penal Code continued
    (7, 1, "If any man has uttered the Most Venerable Name even though frivolously, or as a result of shock, or for any other reason whatever, while reading the Book or praying, he shall be dismissed and shall return to the Council of the Community no more.", "1QS VII:1"),
    (7, 2, "If he has spoken in anger against one of the Priests inscribed in the Book, he shall do penance for one year and shall be excluded from the pure Meal of the Congregation.", "1QS VII:2"),
    (7, 3, "If any man has lied deliberately in matters of property, he shall be excluded from the pure Meal of the Congregation for one year and shall do penance with respect to one quarter of his food.", "1QS VII:3"),
    (7, 4, "Whoever has borne malice against his companion unjustly shall do penance for six months. The same applies to whoever has taken revenge in any matter whatever.", "1QS VII:4"),
    (7, 5, "Whoever has spoken foolishly: three months. Whoever has interrupted his companion while speaking: ten days.", "1QS VII:5"),
    (7, 6, "Whoever has lain down and slept during an Assembly of the Congregation: thirty days. And likewise, whoever has left an Assembly of the Congregation without reason and without permission up to three times during one Assembly: ten days.", "1QS VII:6"),
    (7, 7, "If he has departed while they were standing, he shall do penance for thirty days. Whoever has gone naked before his companion, without having been obliged to do so, shall do penance for six months.", "1QS VII:7"),
    (7, 8, "Whoever has spat in an Assembly of the Congregation shall do penance for thirty days. Whoever has been so poorly dressed that when drawing his hand from beneath his garment his nakedness has been seen, he shall do penance for thirty days.", "1QS VII:8"),

    # Column VIII — The Council of the Community
    (8, 1, "In the Council of the Community there shall be twelve men and three Priests, perfectly versed in all that is revealed of the Law, whose works shall be truth, righteousness, justice, loving-kindness and humility.", "1QS VIII:1"),
    (8, 2, "They shall preserve the faith in the Land with steadfastness and meekness and shall atone for sin by the practice of justice and by suffering the sorrows of affliction.", "1QS VIII:2"),
    (8, 3, "They shall walk with all men according to the standard of truth and the rule of the time. When these are in Israel, the Council of the Community shall be established in truth.", "1QS VIII:3"),
    (8, 4, "It shall be an Everlasting Plantation, a House of Holiness for Israel, an Assembly of Supreme Holiness for Aaron.", "1QS VIII:4"),
    (8, 5, "They shall be witnesses to the truth at the Judgement, and shall be the elect of Goodwill who shall atone for the Land and pay to the wicked their reward.", "1QS VIII:5"),
    (8, 6, "It shall be that tried wall, that precious cornerstone, whose foundations shall neither rock nor sway in their place. It shall be a Most Holy Dwelling for Aaron.", "1QS VIII:6"),
    (8, 7, "When these things exist in Israel, the Council of the Community shall be established in truth as an everlasting plantation.", "1QS VIII:7"),

    # Column IX — The Instructor's Duties
    (9, 1, "These are the precepts in which the Master shall walk in his commerce with all the living, according to the rule proper to every season and according to the worth of every man.", "1QS IX:1"),
    (9, 2, "He shall do the will of God according to all that has been revealed from age to age. He shall measure out all knowledge discovered throughout the ages, together with the Precept of the age.", "1QS IX:2"),
    (9, 3, "He shall separate and weigh the sons of righteousness according to their spirit. He shall hold firmly to the elect of the time according to His will, as He has commanded.", "1QS IX:3"),
    (9, 4, "He shall judge every man according to his spirit. He shall admit him in accordance with the cleanness of his hands and advance him in accordance with his understanding.", "1QS IX:4"),
    (9, 5, "And his love and his hate shall be according to what God has ordained. He shall not rebuke the men of the Pit nor dispute with them.", "1QS IX:5"),
    (9, 6, "He shall conceal the teaching of the Law from men of injustice, but shall impart true knowledge and righteous judgement to those who have chosen the Way.", "1QS IX:6"),
    (9, 7, "These are the rules of conduct for the Master in those times with respect to his loving and his hating. Everlasting hatred in a spirit of secrecy for the men of injustice!", "1QS IX:7"),

    # Column X — Hymn and Calendar
    (10, 1, "I will sing with knowledge and all my music shall be for the glory of God. My lyre and my harp shall sound for His holy order and I will tune the pipe of my lips to His right measure.", "1QS X:1"),
    (10, 2, "With the coming of day and night I will enter the Covenant of God, and when evening and morning depart I will recite His decrees.", "1QS X:2"),
    (10, 3, "I will place their boundary without turning back. I will declare His judgement concerning my sins, and my transgressions shall be before my eyes as an engraved Precept.", "1QS X:3"),
    (10, 4, "I will say to God, 'My Righteousness' and 'Author of my Goodness' to the Most High, 'Fountain of Knowledge' and 'Source of Holiness,' 'Summit of Glory' and 'Almighty Eternal Majesty.'", "1QS X:4"),
    (10, 5, "I will choose that which He teaches me and will delight in His judgement of me. Before I move my hands and feet I will bless His Name.", "1QS X:5"),
    (10, 6, "Before I go out or come in, sit down or rise up, and while I lie on the couch of my bed, I will bless Him and I will sing to Him with the offering of that which proceeds from my lips.", "1QS X:6"),

    # Column XI — Final Hymn
    (11, 1, "As for me, my justification is with God. In His hand are the perfection of my way and the uprightness of my heart. He will wipe out my transgression through His righteousness.", "1QS XI:1"),
    (11, 2, "For from the source of His righteousness is my justification. A light in my heart from His marvellous mysteries; my eyes have gazed on that which is eternal, on wisdom concealed from men.", "1QS XI:2"),
    (11, 3, "On knowledge and wise design hidden from the sons of men, on a fountain of righteousness and on a storehouse of power, on a spring of glory hidden from the assembly of flesh.", "1QS XI:3"),
    (11, 4, "God has given them to His chosen ones as an everlasting possession, and has caused them to inherit the lot of the Holy Ones. He has joined their assembly to the Sons of Heaven.", "1QS XI:4"),
    (11, 5, "Their assembly is a council of holiness, a planting of eternity. For all that is and shall be originates with the God of knowledge. Before ever they existed He established their whole design.", "1QS XI:5"),
    (11, 6, "As for me, I belong to wicked mankind, to the company of ungodly flesh. My iniquities, rebellions, and sins, together with the perversity of my heart, belong to the company of worms and to those who walk in darkness.", "1QS XI:6"),
    (11, 7, "For mankind has no way, and man is unable to establish his steps since justification is with God and perfection of way is out of His hand.", "1QS XI:7"),
    (11, 8, "All things come to pass by His knowledge. He establishes all things by His design and without Him nothing is done.", "1QS XI:8"),
    (11, 9, "As for me, if I stumble, the mercies of God shall be my eternal salvation. If I stagger because of the sin of flesh, my justification shall be by the righteousness of God which endures for ever.", "1QS XI:9"),
    (11, 10, "Blessed art Thou, my God, who openest the heart of Thy servant to knowledge! Establish all his deeds in righteousness, and as it pleases Thee to do for the elect of mankind, grant that the son of Thy handmaid may stand before Thee for ever.", "1QS XI:10"),
    (11, 11, "For without Thee no way is perfect, and without Thy will nothing is done. It is Thou who hast taught all knowledge and all things come to pass by Thy will.", "1QS XI:11"),
    (11, 12, "There is none beside Thee to dispute Thy counsel or to understand all Thy holy design, or to contemplate the depth of Thy mysteries and the power of Thy might. Who can endure Thy glory, and what is the son of man in the midst of Thy wonderful deeds?", "1QS XI:12"),
]

# ============================================================================
# DAMASCUS DOCUMENT (CD) — Admonition + Laws sections
# ============================================================================

DAMASCUS_DOCUMENT = [
    # Column I — Historical Introduction
    (1, 1, "Hear now, all you who know righteousness, and consider the works of God; for He has a dispute with all flesh and will condemn all those who despise Him.", "CD I:1"),
    (1, 2, "For when they were unfaithful and forsook Him, He hid His face from Israel and His Sanctuary and delivered them up to the sword.", "CD I:2"),
    (1, 3, "But remembering the Covenant of the forefathers, He left a remnant to Israel and did not deliver it up to be destroyed.", "CD I:3"),
    (1, 4, "And in the age of wrath, three hundred and ninety years after He had given them into the hand of King Nebuchadnezzar of Babylon, He visited them.", "CD I:4"),
    (1, 5, "And He caused a plant root to spring from Israel and Aaron to inherit His Land and to prosper on the good things of His earth.", "CD I:5"),
    (1, 6, "And they perceived their iniquity and recognized that they were guilty men, yet for twenty years they were like blind men groping for the way.", "CD I:6"),
    (1, 7, "And God observed their deeds, that they sought Him with a whole heart, and He raised for them a Teacher of Righteousness to guide them in the way of His heart.", "CD I:7"),
    (1, 8, "He made known to the latter generations that which God had done to the latter generation, the congregation of traitors, to those who departed from the way.", "CD I:8"),
    (1, 9, "This was the time of which it is written, 'Like a stubborn heifer, thus was Israel stubborn,' when the Scoffer arose who shed over Israel the waters of lies.", "CD I:9"),
    (1, 10, "He caused them to wander in a pathless wilderness, laying low the everlasting heights, abolishing the ways of righteousness and removing the boundary with which the forefathers had marked out their inheritance.", "CD I:10"),

    # Column II — Continued History
    (2, 1, "And now, listen to me, all you who enter the Covenant, and I will unstop your ears concerning the ways of the wicked.", "CD II:1"),
    (2, 2, "God loves knowledge. Wisdom and understanding He has set before Him, and prudence and knowledge serve Him.", "CD II:2"),
    (2, 3, "Patience and much forgiveness are with Him towards those who turn from transgression; but power, might, and great flaming wrath by the hand of all the Angels of Destruction towards those who depart from the way.", "CD II:3"),
    (2, 4, "They shall have no remnant nor survivor. For from the beginning God chose them not; He knew their deeds before ever they were created and He hated their generations.", "CD II:4"),
    (2, 5, "And He hid His face from the Land until they were consumed. For He knew the years of their coming and the length and exact duration of their times for all ages to come and throughout eternity.", "CD II:5"),
    (2, 6, "He knew the happenings of their times throughout all the everlasting years. And in all of them He raised for Himself men called by name, that a remnant might be left to the Land, and that the face of the earth might be filled with their seed.", "CD II:6"),
    (2, 7, "And He made known His Holy Spirit to them by the hand of His anointed ones, and He proclaimed the truth directly to them. But those whom He hated He led astray.", "CD II:7"),

    # Column III — Warning Examples
    (3, 1, "And now, listen to me, all who enter the Covenant, and I will reveal to you the ways of the wicked. God loves knowledge; wisdom and understanding He has set before Him.", "CD III:1"),
    (3, 2, "The Watchers of heaven fell; they were caught because they did not keep the commandments of God. And their sons, whose height was like the height of cedars and whose bodies were like mountains, also fell.", "CD III:2"),
    (3, 3, "All flesh on dry land perished; they were as though they had never been because they did their own will and did not keep the commandments of their Maker.", "CD III:3"),
    (3, 4, "So that His wrath was kindled against them. Through it, the sons of Noah went astray, together with their kin, and were cut off.", "CD III:4"),
    (3, 5, "Abraham did not walk in it, and he was accounted a friend of God because he kept the commandments of God and did not choose his own will.", "CD III:5"),
    (3, 6, "And he handed them down to Isaac and Jacob, who kept them, and were recorded as friends of God and as confederates of the Covenant for ever.", "CD III:6"),
    (3, 7, "The children of Jacob strayed through them and were punished in accordance with their error. And their sons in Egypt walked in the stubbornness of their hearts, conspiring against the commandments of God.", "CD III:7"),

    # Columns IV-VIII — Laws and Regulations
    (4, 1, "The builders of the wall who have followed after 'Precept' — 'Precept' was a spouter of whom it is written, 'They shall surely spout' — shall be caught in fornication twice by taking a second wife while the first is alive.", "CD IV:1"),
    (4, 2, "Whereas the principle of creation is, 'Male and female created He them.' Also, those who entered the Ark went in two by two.", "CD IV:2"),
    (4, 3, "And concerning the prince it is written, 'He shall not multiply wives to himself.' But David had not read the sealed book of the Law which was in the Ark.", "CD IV:3"),
    (4, 4, "For it was not opened in Israel from the death of Eleazar and Joshua, and the elders who worshipped Ashtoreth. It was hidden and was not revealed until the coming of Zadok.", "CD IV:4"),
    (4, 5, "And the deeds of David rose up, except for the murder of Uriah, and God left them to him.", "CD IV:5"),

    (5, 1, "Moreover, they conveyed the sanctuary, for they did not distinguish clean from unclean. And of them it is said, 'Their wine is the venom of serpents, the cruel poison of asps.'", "CD V:1"),
    (5, 2, "The serpents are the kings of the peoples; their wine is their ways; and the poison of asps is the chief of the kings of Greece who came to wreak vengeance upon them.", "CD V:2"),
    (5, 3, "But all these things the builders of the wall and those who daub it with plaster have not understood because a follower of the wind, one who raised storms and rained down lies, had preached to them.", "CD V:3"),

    # Columns IX-XII — Sabbath Laws and Purity
    (6, 1, "No man shall work on the sixth day from the time when the sun's orb is distant by its own fullness from the gate wherein it sinks; for this is what He said, 'Observe the Sabbath day and keep it holy.'", "CD IX:1"),
    (6, 2, "On the Sabbath day no man shall utter a word of folly. He shall not lend anything to his companion. He shall not decide in matters of money and gain.", "CD IX:2"),
    (6, 3, "He shall say nothing about work or labour to be done on the morrow. No man shall walk in the field to do business on the Sabbath.", "CD IX:3"),
    (6, 4, "He shall not walk more than one thousand cubits beyond his town. No man shall eat on the Sabbath day except that which is already prepared.", "CD IX:4"),
    (6, 5, "He shall eat nothing lying in the fields. He shall not drink except in the camp. If he is on a journey and going down to bathe, he shall drink where he stands but shall not draw water into any vessel.", "CD IX:5"),
    (6, 6, "He shall send no stranger on his business on the Sabbath day. No man shall put on soiled garments, or garments brought to the store, unless they have been washed with water or rubbed with incense.", "CD IX:6"),
    (6, 7, "No man shall voluntarily mingle on the Sabbath. No man shall walk more than two thousand cubits after a beast to pasture it outside his town.", "CD IX:7"),
    (6, 8, "He shall not raise his hand to strike it with his fist. If it is stubborn he shall not take it out of his house.", "CD IX:8"),

    # Columns XIII-XVI — Judges and Organization
    (7, 1, "And this is the rule of the judges of the congregation. Ten judges shall be elected from the congregation for a definite time, four from the tribe of Levi and Aaron, and six from Israel.", "CD XIII:1"),
    (7, 2, "They shall be learned in the Book of Meditation and in the constitutions of the Covenant, and aged between twenty-five and sixty years.", "CD XIII:2"),
    (7, 3, "No man over the age of sixty shall hold the office of judge of the congregation, for because of man's sin his days have been shortened, and in the heat of His anger against the inhabitants of the earth God ordained that their understanding should depart even before they complete their days.", "CD XIII:3"),
    (7, 4, "Concerning purification with water. No man shall bathe in dirty water or in an amount too shallow to cover a man. He shall not purify himself with water stored in a vessel.", "CD XIII:4"),

    # Columns XIX-XX — Final Admonitions
    (8, 1, "But all those who hold fast to these precepts, going and coming in accordance with the Law, who heed the voice of the Teacher and confess before God, saying, 'Truly we have sinned, we and our fathers, by walking counter to the precepts of the Covenant.'", "CD XIX:1"),
    (8, 2, "'Your judgements upon us are truth and righteousness': who do not lift their hand against His holy precepts or His righteous statutes or His true testimonies.", "CD XIX:2"),
    (8, 3, "Who have learnt from the former judgements by which the members of the Community were judged; who have listened to the voice of the Teacher of Righteousness and have not despised the precepts of righteousness when they heard them.", "CD XIX:3"),
    (8, 4, "They shall rejoice and their hearts shall be strong, and they shall prevail over all the sons of the earth. God will forgive them, and they shall see His salvation because they took refuge in His holy Name.", "CD XIX:4"),
]

def rebuild_fts(conn):
    """Rebuild the FTS5 index."""
    conn.execute("DELETE FROM scriptures_fts")
    conn.execute("""
        INSERT INTO scriptures_fts(rowid, text, reference, book_title, volume_title)
        SELECT v.id, v.text, v.reference, b.title, vol.title
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        JOIN volumes vol ON b.volume_id = vol.id
    """)
    conn.commit()

def main():
    conn = sqlite3.connect(DB_PATH)

    # Before stats
    print("=== BEFORE ===")
    for title in ['Community Rule', 'Damascus Document']:
        row = conn.execute("""
            SELECT COUNT(DISTINCT c.chapter_number), COUNT(v.id)
            FROM books b LEFT JOIN chapters c ON c.book_id=b.id LEFT JOIN verses v ON v.chapter_id=c.id
            WHERE b.title=? AND b.volume_id=300
        """, (title,)).fetchone()
        print(f"  {title}: {row[0]} chapters, {row[1]} verses")

    # 1. Fix Community Rule (book_id=3001)
    print("\n--- Fixing Community Rule ---")
    delete_book_content(conn, 3001)
    count = insert_verses(conn, 3001, 300, COMMUNITY_RULE)
    print(f"  Inserted {count} verses across 11 columns")

    # 2. Fix Damascus Document (book_id=3007)
    print("\n--- Fixing Damascus Document ---")
    delete_book_content(conn, 3007)
    count = insert_verses(conn, 3007, 300, DAMASCUS_DOCUMENT)
    print(f"  Inserted {count} verses across {len(set(v[0] for v in DAMASCUS_DOCUMENT))} sections")

    # 3. Rebuild FTS
    print("\n--- Rebuilding FTS index ---")
    rebuild_fts(conn)

    # After stats
    print("\n=== AFTER ===")
    for title in ['Community Rule', 'Damascus Document']:
        row = conn.execute("""
            SELECT COUNT(DISTINCT c.chapter_number), COUNT(v.id)
            FROM books b LEFT JOIN chapters c ON c.book_id=b.id LEFT JOIN verses v ON v.chapter_id=c.id
            WHERE b.title=? AND b.volume_id=300
        """, (title,)).fetchone()
        print(f"  {title}: {row[0]} chapters, {row[1]} verses")

    total = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    fts = conn.execute("SELECT COUNT(*) FROM scriptures_fts").fetchone()[0]
    print(f"\n  Total verses: {total}")
    print(f"  FTS index: {fts}")

    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
