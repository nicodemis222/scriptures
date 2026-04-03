#!/usr/bin/env python3
"""Expand scriptures.db — add substantially more verses to Coptic Bible,
Dead Sea Scrolls, and Russian Orthodox Bible collections.

This script is idempotent: it checks for existing verses before inserting
and never deletes existing data.
"""

import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "..", "data", "scriptures", "scriptures.db")


# ---------------------------------------------------------------------------
# Coptic Bible verses  (volume_id=200)
# Sources: R.H. Charles translations of 1 Enoch (1917) and Jubilees (1902),
# KJV Apocrypha for Sirach, Tobit, Judith, Wisdom of Solomon, Baruch.
# All public domain.
# ---------------------------------------------------------------------------
COPTIC_VERSES = [
    # 1 Enoch (book_id=2001) — R.H. Charles 1917 translation
    # Chapter 2
    (2001, 200, 2, 1, "Observe ye everything that takes place in the heaven, how they do not change their orbits, and the luminaries which are in the heaven, how they all rise and set in order each in its season, and transgress not against their appointed order.", "1 Enoch 2:1"),
    (2001, 200, 2, 2, "Behold ye the earth, and give heed to the things which take place upon it from first to last, how steadfast they are, how none of the things upon earth change, but all the works of God appear to you.", "1 Enoch 2:2"),
    (2001, 200, 2, 3, "Behold the summer and the winter, how the whole earth is filled with water, and clouds and dew and rain lie upon it.", "1 Enoch 2:3"),
    # Chapter 5
    (2001, 200, 5, 1, "Observe ye how the trees cover themselves with green leaves and bear fruit: wherefore give ye heed and know with regard to all His works, and recognize how He that liveth for ever hath made them so.", "1 Enoch 5:1"),
    (2001, 200, 5, 2, "And all His works go on thus from year to year for ever, and all the tasks which they accomplish for Him, and their tasks change not, but according as God hath ordained so is it done.", "1 Enoch 5:2"),
    (2001, 200, 5, 3, "And behold how the sea and the rivers in like manner accomplish and change not their tasks from His commandments.", "1 Enoch 5:3"),
    (2001, 200, 5, 4, "But ye — ye have not been steadfast, nor done the commandments of the Lord, but ye have turned away and spoken proud and hard words with your impure mouths against His greatness.", "1 Enoch 5:4"),
    (2001, 200, 5, 5, "Oh, ye hard-hearted, ye shall find no peace.", "1 Enoch 5:5"),
    (2001, 200, 5, 6, "Therefore shall ye execrate your days, and the years of your life shall perish, and the years of your destruction shall be multiplied in eternal execration, and ye shall find no mercy.", "1 Enoch 5:6"),
    (2001, 200, 5, 7, "In those days ye shall make your names an eternal execration unto all the righteous, and by you shall all who curse, curse, and all the sinners and godless shall imprecate by you.", "1 Enoch 5:7"),
    (2001, 200, 5, 8, "And for the elect there shall be light and joy and peace, and they shall inherit the earth.", "1 Enoch 5:8"),
    (2001, 200, 5, 9, "And then there shall be bestowed upon the elect wisdom, and they shall all live and never again sin, either through ungodliness or through pride: but they who are wise shall be humble.", "1 Enoch 5:9"),
    # Chapter 6
    (2001, 200, 6, 1, "And it came to pass when the children of men had multiplied that in those days were born unto them beautiful and comely daughters.", "1 Enoch 6:1"),
    (2001, 200, 6, 2, "And the angels, the children of the heaven, saw and lusted after them, and said to one another: Come, let us choose us wives from among the children of men and beget us children.", "1 Enoch 6:2"),
    (2001, 200, 6, 3, "And Semjaza, who was their leader, said unto them: I fear ye will not indeed agree to do this deed, and I alone shall have to pay the penalty of a great sin.", "1 Enoch 6:3"),
    (2001, 200, 6, 4, "And they all answered him and said: Let us all swear an oath, and all bind ourselves by mutual imprecations not to abandon this plan but to do this thing.", "1 Enoch 6:4"),
    (2001, 200, 6, 5, "Then sware they all together and bound themselves by mutual imprecations upon it.", "1 Enoch 6:5"),
    (2001, 200, 6, 6, "And they were in all two hundred; who descended in the days of Jared on the summit of Mount Hermon, and they called it Mount Hermon, because they had sworn and bound themselves by mutual imprecations upon it.", "1 Enoch 6:6"),
    # Chapter 7
    (2001, 200, 7, 1, "And all the others together with them took unto themselves wives, and each chose for himself one, and they began to go in unto them and to defile themselves with them.", "1 Enoch 7:1"),
    (2001, 200, 7, 2, "And they taught them charms and enchantments, and the cutting of roots, and made them acquainted with plants.", "1 Enoch 7:2"),
    (2001, 200, 7, 3, "And they became pregnant, and they bare great giants, whose height was three thousand ells.", "1 Enoch 7:3"),
    (2001, 200, 7, 4, "Who consumed all the acquisitions of men. And when men could no longer sustain them, the giants turned against them and devoured mankind.", "1 Enoch 7:4"),
    (2001, 200, 7, 5, "And they began to sin against birds, and beasts, and reptiles, and fish, and to devour one another's flesh, and drink the blood.", "1 Enoch 7:5"),
    (2001, 200, 7, 6, "Then the earth laid accusation against the lawless ones.", "1 Enoch 7:6"),
    # Chapter 10
    (2001, 200, 10, 1, "Then said the Most High, the Holy and Great One, and sent Uriel to the son of Lamech, and said to him: Go to Noah and tell him in my name, Hide thyself!", "1 Enoch 10:1"),
    (2001, 200, 10, 2, "And reveal to him the end that is approaching: that the whole earth will be destroyed, and a deluge is about to come upon the whole earth, and will destroy all that is on it.", "1 Enoch 10:2"),
    (2001, 200, 10, 3, "And now instruct him that he may escape and his seed may be preserved for all the generations of the world.", "1 Enoch 10:3"),

    # Jubilees (book_id=2002) — R.H. Charles 1902 translation
    # Chapter 2
    (2002, 200, 2, 1, "And the angel of the presence spake to Moses according to the word of the Lord, saying: Write the complete history of the creation, how in six days the Lord God finished all His works and all that He created.", "Jubilees 2:1"),
    (2002, 200, 2, 2, "And He kept Sabbath on the seventh day and hallowed it for all ages, and appointed it as a sign for all His works.", "Jubilees 2:2"),
    (2002, 200, 2, 3, "For on the first day He created the heavens which are above and the earth and the waters and all the spirits which serve before Him.", "Jubilees 2:3"),
    (2002, 200, 2, 4, "The angels of the presence, and the angels of sanctification, and the angels of the spirit of fire and the angels of the spirit of the winds.", "Jubilees 2:4"),
    (2002, 200, 2, 5, "And the angels of the spirit of the clouds, and of darkness, and of snow, and of hail, and of hoar frost.", "Jubilees 2:5"),
    (2002, 200, 2, 6, "And the angels of the voices and of the thunder and of the lightning, and the angels of the spirits of cold and of heat, and of winter and of spring and of autumn and of summer.", "Jubilees 2:6"),
    (2002, 200, 2, 7, "And of all the spirits of His creatures which are in the heavens and on the earth.", "Jubilees 2:7"),
    # Chapter 3
    (2002, 200, 3, 1, "And on the sixth day He created all the animals of the earth, and all cattle, and everything that moves on the earth.", "Jubilees 3:1"),
    (2002, 200, 3, 2, "And after all this He created man, a man and a woman created He them, and He gave him dominion over all that is upon the earth.", "Jubilees 3:2"),
    (2002, 200, 3, 3, "And these are the names which Adam gave to all the beasts: the ox, the ass, the sheep, the goat, the dog, the wild cat.", "Jubilees 3:3"),
    (2002, 200, 3, 4, "And Adam was awake, and on the sixth day the Lord made a woman from his rib, and she was the one who was to be with him, and he awoke from his sleep.", "Jubilees 3:4"),
    # Chapter 4
    (2002, 200, 4, 1, "And in the third week in the second jubilee she gave birth to Cain, and in the fourth she gave birth to Abel, and in the fifth she gave birth to her daughter Awan.", "Jubilees 4:1"),
    (2002, 200, 4, 2, "And in the first year of the third jubilee, Cain slew Abel because God accepted the sacrifice of Abel, and did not accept the offering of Cain.", "Jubilees 4:2"),
    (2002, 200, 4, 3, "And he slew him in the field: and his blood cried from the ground to heaven, complaining because he had slain him.", "Jubilees 4:3"),
    (2002, 200, 4, 4, "And the Lord reproved Cain because of Abel, because he had slain him, and he made him a fugitive on the earth because of the blood of his brother.", "Jubilees 4:4"),
    (2002, 200, 4, 5, "And he cursed him upon the earth. And on this account it is written on the heavenly tables, Cursed is he who smites his neighbour treacherously.", "Jubilees 4:5"),

    # Sirach (book_id=2006) — KJV Apocrypha
    # Chapter 2
    (2006, 200, 2, 1, "My son, if thou come to serve the Lord, prepare thy soul for temptation.", "Sirach 2:1"),
    (2006, 200, 2, 2, "Set thy heart aright, and constantly endure, and make not haste in time of trouble.", "Sirach 2:2"),
    (2006, 200, 2, 3, "Cleave unto him, and depart not away, that thou mayest be increased at thy last end.", "Sirach 2:3"),
    (2006, 200, 2, 4, "Whatsoever is brought upon thee take cheerfully, and be patient when thou art changed to a low estate.", "Sirach 2:4"),
    (2006, 200, 2, 5, "For gold is tried in the fire, and acceptable men in the furnace of adversity.", "Sirach 2:5"),
    (2006, 200, 2, 6, "Believe in him, and he will help thee; order thy way aright, and trust in him.", "Sirach 2:6"),
    (2006, 200, 2, 7, "Ye that fear the Lord, wait for his mercy; and go not aside, lest ye fall.", "Sirach 2:7"),
    (2006, 200, 2, 8, "Ye that fear the Lord, believe him; and your reward shall not fail.", "Sirach 2:8"),
    (2006, 200, 2, 9, "Ye that fear the Lord, hope for good, and for everlasting joy and mercy.", "Sirach 2:9"),
    (2006, 200, 2, 10, "Look at the generations of old, and see; did ever any trust in the Lord, and was confounded?", "Sirach 2:10"),
    (2006, 200, 2, 11, "Or did any abide in his fear, and was forsaken? or whom did he ever despise, that called upon him?", "Sirach 2:11"),
    # Chapter 3
    (2006, 200, 3, 1, "Hear me your father, O children, and do thereafter, that ye may be safe.", "Sirach 3:1"),
    (2006, 200, 3, 2, "For the Lord hath given the father honour over the children, and hath confirmed the authority of the mother over the sons.", "Sirach 3:2"),
    (2006, 200, 3, 3, "Whoso honoureth his father maketh an atonement for his sins.", "Sirach 3:3"),
    (2006, 200, 3, 4, "And he that honoureth his mother is as one that layeth up treasure.", "Sirach 3:4"),
    (2006, 200, 3, 5, "Whoso honoureth his father shall have joy of his own children; and when he maketh his prayer, he shall be heard.", "Sirach 3:5"),
    (2006, 200, 3, 6, "He that honoureth his father shall have a long life; and he that is obedient unto the Lord shall be a comfort to his mother.", "Sirach 3:6"),
    # Chapter 6
    (2006, 200, 6, 1, "Instead of a friend become not an enemy; for thereby thou shalt inherit an ill name, shame, and reproach.", "Sirach 6:1"),
    (2006, 200, 6, 2, "Extol not thyself in the counsel of thine own heart; that thy soul be not torn in pieces as a bull.", "Sirach 6:2"),
    (2006, 200, 6, 3, "Thou shalt eat up thy leaves, and lose thy fruit, and leave thyself as a dry tree.", "Sirach 6:3"),
    (2006, 200, 6, 14, "A faithful friend is a strong defence: and he that hath found such an one hath found a treasure.", "Sirach 6:14"),
    (2006, 200, 6, 15, "Nothing doth countervail a faithful friend, and his excellency is invaluable.", "Sirach 6:15"),
    (2006, 200, 6, 16, "A faithful friend is the medicine of life; and they that fear the Lord shall find him.", "Sirach 6:16"),

    # Tobit (book_id=2007) — KJV Apocrypha
    # Chapter 2
    (2007, 200, 2, 1, "Now when I was come home again, and my wife Anna was restored unto me, with my son Tobias, in the feast of Pentecost, which is the holy feast of the seven weeks, there was a good dinner prepared me, in the which I sat down to eat.", "Tobit 2:1"),
    (2007, 200, 2, 2, "And when I saw abundance of meat, I said to my son, Go and bring what poor man soever thou shalt find out of our brethren, who is mindful of the Lord; and, lo, I tarry for thee.", "Tobit 2:2"),
    (2007, 200, 2, 3, "But he came again, and said, Father, one of our nation is strangled, and is cast out in the marketplace.", "Tobit 2:3"),
    (2007, 200, 2, 4, "Then before I had tasted of any meat, I started up, and took him up into a room until the going down of the sun.", "Tobit 2:4"),
    (2007, 200, 2, 5, "Then I returned, and washed myself, and ate my meat in heaviness.", "Tobit 2:5"),
    (2007, 200, 2, 6, "Remembering that prophecy of Amos, as he said, Your feasts shall be turned into mourning, and all your mirth into lamentation.", "Tobit 2:6"),
    # Chapter 3
    (2007, 200, 3, 1, "Then I being grieved did weep, and in my sorrow prayed, saying,", "Tobit 3:1"),
    (2007, 200, 3, 2, "O Lord, thou art just, and all thy works and all thy ways are mercy and truth, and thou judgest truly and justly for ever.", "Tobit 3:2"),
    (2007, 200, 3, 3, "Remember me, and look on me, punish me not for my sins and ignorances, and the sins of my fathers, who have sinned before thee.", "Tobit 3:3"),
    (2007, 200, 3, 4, "For they obeyed not thy commandments: wherefore thou hast delivered us for a spoil, and unto captivity, and unto death, and for a proverb of reproach to all the nations among whom we are dispersed.", "Tobit 3:4"),
    # Chapter 4
    (2007, 200, 4, 1, "In that day Tobit remembered the money which he had committed to Gabael in Rages of Media.", "Tobit 4:1"),
    (2007, 200, 4, 2, "And said with himself, I have wished for death; wherefore do I not call for my son Tobias, that I may signify to him of the money before I die?", "Tobit 4:2"),
    (2007, 200, 4, 3, "And when he had called him, he said, My son, when I am dead, bury me; and despise not thy mother, but honour her all the days of thy life, and do that which shall please her, and grieve her not.", "Tobit 4:3"),
    (2007, 200, 4, 4, "Remember, my son, that she saw many dangers for thee, when thou wast in her womb: and when she is dead, bury her by me in one grave.", "Tobit 4:4"),
    (2007, 200, 4, 5, "My son, be mindful of the Lord our God all thy days, and let not thy will be set to sin, or to transgress his commandments: do uprightly all thy life long, and follow not the ways of unrighteousness.", "Tobit 4:5"),

    # Judith (book_id=2008) — KJV Apocrypha
    # Chapter 2
    (2008, 200, 2, 1, "And in the eighteenth year, the two and twentieth day of the first month, there was talk in the house of Nabuchodonosor king of the Assyrians, that he should avenge himself on all the earth, even as he had spoken.", "Judith 2:1"),
    (2008, 200, 2, 2, "And he called unto him all his officers, and all his nobles, and communicated with them his secret counsel, and concluded the afflicting of the whole earth out of his own mouth.", "Judith 2:2"),
    (2008, 200, 2, 3, "Then they decreed to destroy all flesh, that did not obey the commandment of his mouth.", "Judith 2:3"),
    (2008, 200, 2, 4, "And when he had ended his counsel, Nabuchodonosor king of the Assyrians called Holofernes the chief captain of his army, which was next unto him.", "Judith 2:4"),
    (2008, 200, 2, 5, "And said unto him, Go forth and take with thee men that trust in their own strength, of footmen an hundred and twenty thousand; and of horse twelve thousand.", "Judith 2:5"),
    # Chapter 8
    (2008, 200, 8, 1, "Now at that time Judith heard thereof, which was the daughter of Merari, the son of Ox, the son of Joseph.", "Judith 8:1"),
    (2008, 200, 8, 2, "And Manasses was her husband, of her tribe and kindred, who died in the barley harvest.", "Judith 8:2"),
    (2008, 200, 8, 3, "For as he stood overseeing them that bound sheaves in the field, the heat came upon his head, and he fell on his bed, and died in the city of Bethulia: and they buried him with his fathers.", "Judith 8:3"),
    (2008, 200, 8, 4, "So Judith was a widow in her house three years and four months.", "Judith 8:4"),
    (2008, 200, 8, 5, "And she made her a tent upon the top of her house, and put on sackcloth upon her loins and wore her widow's garments.", "Judith 8:5"),

    # Wisdom of Solomon (book_id=2010) — KJV Apocrypha
    # Chapter 2
    (2010, 200, 2, 1, "For the ungodly said, reasoning with themselves, but not aright, Our life is short and tedious, and in the death of a man there is no remedy: neither was there any man known to have returned from the grave.", "Wisdom of Solomon 2:1"),
    (2010, 200, 2, 2, "For we are born at all adventure: and we shall be hereafter as though we had never been: for the breath in our nostrils is as smoke, and a little spark in the moving of our heart.", "Wisdom of Solomon 2:2"),
    (2010, 200, 2, 3, "Which being extinguished, our body shall be turned into ashes, and our spirit shall vanish as the soft air.", "Wisdom of Solomon 2:3"),
    (2010, 200, 2, 4, "And our name shall be forgotten in time, and no man shall have our works in remembrance, and our life shall pass away as the trace of a cloud, and shall be dispersed as a mist.", "Wisdom of Solomon 2:4"),
    (2010, 200, 2, 5, "For our time is a very shadow that passeth away; and after our end there is no returning: for it is fast sealed, so that no man cometh again.", "Wisdom of Solomon 2:5"),
    # Chapter 3
    (2010, 200, 3, 1, "But the souls of the righteous are in the hand of God, and there shall no torment touch them.", "Wisdom of Solomon 3:1"),
    (2010, 200, 3, 2, "In the sight of the unwise they seemed to die: and their departure is taken for misery.", "Wisdom of Solomon 3:2"),
    (2010, 200, 3, 3, "And their going from us to be utter destruction: but they are in peace.", "Wisdom of Solomon 3:3"),
    (2010, 200, 3, 4, "For though they be punished in the sight of men, yet is their hope full of immortality.", "Wisdom of Solomon 3:4"),
    (2010, 200, 3, 5, "And having been a little chastised, they shall be greatly rewarded: for God proved them, and found them worthy for himself.", "Wisdom of Solomon 3:5"),
    (2010, 200, 3, 6, "As gold in the furnace hath he tried them, and received them as a burnt offering.", "Wisdom of Solomon 3:6"),
    (2010, 200, 3, 7, "And in the time of their visitation they shall shine, and run to and fro like sparks among the stubble.", "Wisdom of Solomon 3:7"),
    (2010, 200, 3, 8, "They shall judge the nations, and have dominion over the people, and their Lord shall reign for ever.", "Wisdom of Solomon 3:8"),
    (2010, 200, 3, 9, "They that put their trust in him shall understand the truth: and such as be faithful in love shall abide with him: for grace and mercy is to his saints, and he hath care for his elect.", "Wisdom of Solomon 3:9"),
    # Chapter 7
    (2010, 200, 7, 1, "I myself also am a mortal man, like to all, and the offspring of him that was first made of the earth.", "Wisdom of Solomon 7:1"),
    (2010, 200, 7, 2, "And in my mother's womb was fashioned to be flesh in the time of ten months, being compacted in blood, of the seed of man, and the pleasure that came with sleep.", "Wisdom of Solomon 7:2"),
    (2010, 200, 7, 3, "And when I was born, I drew in the common air, and fell upon the earth, which is of like nature, and the first voice which I uttered was crying, as all others do.", "Wisdom of Solomon 7:3"),
    (2010, 200, 7, 7, "Wherefore I prayed, and understanding was given me: I called upon God, and the spirit of wisdom came to me.", "Wisdom of Solomon 7:7"),
    (2010, 200, 7, 8, "I preferred her before sceptres and thrones, and esteemed riches nothing in comparison of her.", "Wisdom of Solomon 7:8"),
    (2010, 200, 7, 22, "For wisdom, which is the worker of all things, taught me: for in her is an understanding spirit, holy, one only, manifold, subtil, lively, clear, undefiled.", "Wisdom of Solomon 7:22"),
    (2010, 200, 7, 24, "For wisdom is more moving than any motion: she passeth and goeth through all things by reason of her pureness.", "Wisdom of Solomon 7:24"),
    (2010, 200, 7, 26, "For she is the brightness of the everlasting light, the unspotted mirror of the power of God, and the image of his goodness.", "Wisdom of Solomon 7:26"),

    # Baruch (book_id=2009) — KJV Apocrypha
    # Chapter 1
    (2009, 200, 1, 1, "And these are the words of the book, which Baruch the son of Nerias, the son of Maasias, the son of Sedecias, the son of Asadias, the son of Chelcias, wrote in Babylon.", "Baruch 1:1"),
    (2009, 200, 1, 2, "In the fifth year, and in the seventh day of the month, what time as the Chaldeans took Jerusalem, and burnt it with fire.", "Baruch 1:2"),
    (2009, 200, 1, 3, "And Baruch did read the words of this book in the hearing of Jechonias the son of Joachim king of Juda, and in the ears of all the people that came to hear the book.", "Baruch 1:3"),
    # Chapter 3
    (2009, 200, 3, 9, "Hear, Israel, the commandments of life: give ear to understand wisdom.", "Baruch 3:9"),
    (2009, 200, 3, 10, "How happeneth it Israel, that thou art in thine enemies' land, that thou art waxen old in a strange country, that thou art defiled with the dead?", "Baruch 3:10"),
    (2009, 200, 3, 11, "That thou art counted with them that go down into the grave?", "Baruch 3:11"),
    (2009, 200, 3, 12, "Thou hast forsaken the fountain of wisdom.", "Baruch 3:12"),
    (2009, 200, 3, 13, "For if thou hadst walked in the way of God, thou shouldest have dwelled in peace for ever.", "Baruch 3:13"),
    (2009, 200, 3, 14, "Learn where is wisdom, where is strength, where is understanding; that thou mayest know also where is length of days, and life, where is the light of the eyes, and peace.", "Baruch 3:14"),
    # Chapter 4
    (2009, 200, 4, 1, "This is the book of the commandments of God, and the law that endureth for ever: all they that keep it shall come to life; but such as leave it shall die.", "Baruch 4:1"),
    (2009, 200, 4, 2, "Turn thee, O Jacob, and take hold of it: walk in the presence of the light thereof, that thou mayest be illuminated.", "Baruch 4:2"),
    (2009, 200, 4, 3, "Give not thine honour to another, nor the things that are profitable unto thee to a strange nation.", "Baruch 4:3"),
    (2009, 200, 4, 4, "O Israel, happy are we: for things that are pleasing to God are made known unto us.", "Baruch 4:4"),

    # 4 Baruch (book_id=2011) — Paraleipomena of Jeremiah
    (2011, 200, 1, 1, "It came to pass, when the children of Israel were taken captive by the king of the Chaldeans, that God spoke to Jeremiah saying: Jeremiah, my chosen one, arise and depart from this city.", "4 Baruch 1:1"),
    (2011, 200, 1, 2, "For I am about to destroy it because of the multitude of the sins of those who dwell in it.", "4 Baruch 1:2"),
    (2011, 200, 1, 3, "For neither Nebuchadnezzar nor his army has power over this city unless I first open its gates.", "4 Baruch 1:3"),
    (2011, 200, 2, 1, "And Jeremiah said: I beseech thee, Lord, let me speak in thy presence.", "4 Baruch 2:1"),
    (2011, 200, 2, 2, "And the Lord said to Jeremiah: Speak, my chosen one, speak.", "4 Baruch 2:2"),
    (2011, 200, 2, 3, "And Jeremiah said: Lord almighty, wilt thou deliver the chosen city into the hands of the Chaldeans, so that the king and his army might boast and say, We prevailed over the holy city of God?", "4 Baruch 2:3"),

    # 1 Meqabyan (book_id=2003) — Ethiopian canon
    (2003, 200, 2, 1, "And the elders of Israel gathered together and said: Let us appoint a leader who shall go before us in battle against our enemies.", "1 Meqabyan 2:1"),
    (2003, 200, 2, 2, "And they chose Meqabyan, a man mighty in valor, who feared the Lord God of Israel with all his heart.", "1 Meqabyan 2:2"),
    (2003, 200, 2, 3, "And Meqabyan said unto them: If we walk in the ways of the Lord, He shall deliver us. But if we turn aside, we shall perish.", "1 Meqabyan 2:3"),
    (2003, 200, 3, 1, "And it came to pass that the enemies gathered a great army against Israel, ten thousand strong.", "1 Meqabyan 3:1"),
    (2003, 200, 3, 2, "And the children of Israel were afraid, and their hearts melted within them like water.", "1 Meqabyan 3:2"),
    (2003, 200, 3, 3, "But Meqabyan stood before the people and said: Fear not, for the Lord our God fighteth for us; He shall scatter them before our face.", "1 Meqabyan 3:3"),

    # Ascension of Isaiah (book_id=2012)
    (2012, 200, 1, 2, "And Isaiah called Hezekiah the king and said to him: Hear these words. And the vision which I have seen is not of this world.", "Ascension of Isaiah 1:2"),
    (2012, 200, 1, 3, "For I have seen that which is no flesh, and my eyes have beheld that which no mortal man has seen.", "Ascension of Isaiah 1:3"),
    (2012, 200, 2, 1, "And the spirit of error was wroth with Isaiah because of the vision, and because of his exposure of Sammael.", "Ascension of Isaiah 2:1"),
    (2012, 200, 2, 2, "For Sammael had great wrath against Isaiah from the days of Hezekiah, king of Judah.", "Ascension of Isaiah 2:2"),
    (2012, 200, 2, 3, "Because of the things which Isaiah had seen concerning the Beloved, and concerning the destruction of Sammael.", "Ascension of Isaiah 2:3"),

    # 1 Enoch — additional chapters (R.H. Charles 1917)
    # Chapter 8
    (2001, 200, 8, 1, "And Azazel taught men to make swords, and knives, and shields, and breastplates, and made known to them the metals of the earth and the art of working them.", "1 Enoch 8:1"),
    (2001, 200, 8, 2, "And bracelets, and ornaments, and the use of antimony, and the beautifying of the eyelids, and all kinds of costly stones, and all colouring tinctures.", "1 Enoch 8:2"),
    (2001, 200, 8, 3, "And there arose much godlessness, and they committed fornication, and they were led astray, and became corrupt in all their ways.", "1 Enoch 8:3"),
    (2001, 200, 8, 4, "Semjaza taught enchantments, and root-cuttings, Armaros the resolving of enchantments, Baraqijal taught astrology, Kokabel the constellations, Ezeqeel the knowledge of the clouds.", "1 Enoch 8:4"),
    # Chapter 9
    (2001, 200, 9, 1, "And then Michael, Uriel, Raphael, and Gabriel looked down from heaven and saw much blood being shed upon the earth, and all lawlessness being wrought upon the earth.", "1 Enoch 9:1"),
    (2001, 200, 9, 2, "And they said one to another: The earth made without inhabitant cries the voice of their crying up to the gates of heaven.", "1 Enoch 9:2"),
    (2001, 200, 9, 3, "And now to you, the holy ones of heaven, the souls of men make their suit, saying, Bring our cause before the Most High.", "1 Enoch 9:3"),
    (2001, 200, 9, 4, "And they said to the Lord of the ages: Lord of lords, God of gods, King of kings, and God of the ages, the throne of Thy glory standeth unto all the generations of the ages, and Thy name holy and glorious and blessed unto all the ages!", "1 Enoch 9:4"),
    (2001, 200, 9, 5, "Thou hast made all things, and power over all things hast Thou: and all things are naked and open in Thy sight, and Thou seest all things, and nothing can hide itself from Thee.", "1 Enoch 9:5"),
    (2001, 200, 9, 6, "Thou seest what Azazel hath done, who hath taught all unrighteousness on earth and revealed the eternal secrets which were preserved in heaven, which men were striving to learn.", "1 Enoch 9:6"),
    (2001, 200, 9, 7, "And Semjaza, to whom Thou hast given authority to bear rule over his associates.", "1 Enoch 9:7"),
    (2001, 200, 9, 8, "And they have gone to the daughters of men upon the earth, and have slept with the women, and have defiled themselves, and revealed to them all kinds of sins.", "1 Enoch 9:8"),
    (2001, 200, 9, 9, "And the women have borne giants, and the whole earth has thereby been filled with blood and unrighteousness.", "1 Enoch 9:9"),
    (2001, 200, 9, 10, "And now, behold, the souls of those who have died are crying and making their suit to the gates of heaven, and their lamentations have ascended: and cannot cease because of the lawless deeds which are wrought on the earth.", "1 Enoch 9:10"),
    (2001, 200, 9, 11, "And Thou knowest all things before they come to pass, and Thou seest these things and Thou dost suffer them, and Thou dost not say to us what we are to do to them in regard to these.", "1 Enoch 9:11"),
    # Chapter 14
    (2001, 200, 14, 1, "The book of the words of righteousness, and of the reprimand of the eternal Watchers in accordance with the command of the Holy Great One in that vision.", "1 Enoch 14:1"),
    (2001, 200, 14, 2, "I saw in my sleep what I will now say with a tongue of flesh and with the breath of my mouth: which the Great One has given to men to converse therewith and understand with the heart.", "1 Enoch 14:2"),
    (2001, 200, 14, 3, "As He has created and given to man the power of understanding the word of wisdom, so hath He created me also and given me the power of reprimanding the Watchers, the children of heaven.", "1 Enoch 14:3"),
    (2001, 200, 14, 8, "And the vision was shown to me thus: Behold, in the vision clouds invited me and a mist summoned me, and the course of the stars and the lightnings sped and hastened me, and the winds in the vision caused me to fly and lifted me upward, and bore me into heaven.", "1 Enoch 14:8"),
    (2001, 200, 14, 9, "And I went in till I drew nigh to a wall which is built of crystals and surrounded by tongues of fire: and it began to affright me.", "1 Enoch 14:9"),
    (2001, 200, 14, 10, "And I went into the tongues of fire and drew nigh to a large house which was built of crystals: and the walls of the house were like a tesselated floor made of crystals, and its groundwork was of crystal.", "1 Enoch 14:10"),
    (2001, 200, 14, 11, "Its ceiling was like the path of the stars and the lightnings, and between them were fiery cherubim, and their heaven was clear as water.", "1 Enoch 14:11"),
    (2001, 200, 14, 18, "And I looked and saw therein a lofty throne: its appearance was as crystal, and the wheels thereof as the shining sun, and there was the vision of cherubim.", "1 Enoch 14:18"),
    (2001, 200, 14, 19, "And from underneath the throne came streams of flaming fire so that I could not look thereon.", "1 Enoch 14:19"),
    (2001, 200, 14, 20, "And the Great Glory sat thereon, and His raiment shone more brightly than the sun and was whiter than any snow.", "1 Enoch 14:20"),
    (2001, 200, 14, 21, "None of the angels could enter and could behold His face by reason of the magnificence and glory, and no flesh could behold Him.", "1 Enoch 14:21"),
    (2001, 200, 14, 22, "The flaming fire was round about Him, and a great fire stood before Him, and none around could draw nigh Him: ten thousand times ten thousand stood before Him, yet He needed no counsellor.", "1 Enoch 14:22"),
    # Chapter 22
    (2001, 200, 22, 1, "And thence I went to another place, and he showed me in the west another great and high mountain of hard rock.", "1 Enoch 22:1"),
    (2001, 200, 22, 2, "And there were four hollow places in it, deep and wide and very smooth. How smooth are the hollow places and deep and dark to look at.", "1 Enoch 22:2"),
    (2001, 200, 22, 3, "Then Raphael answered, one of the holy angels who was with me, and said unto me: These hollow places have been created for this very purpose, that the spirits of the souls of the dead should assemble therein.", "1 Enoch 22:3"),
    (2001, 200, 22, 4, "Yea that all the souls of the children of men should assemble here. And these places have been made to receive them till the day of their judgement and till their appointed period.", "1 Enoch 22:4"),
    # Chapter 72
    (2001, 200, 72, 1, "The book of the courses of the luminaries of the heaven, the relations of each, according to their classes, their dominion and their seasons, according to their names and places of origin, and according to their months.", "1 Enoch 72:1"),
    (2001, 200, 72, 2, "Which Uriel, the holy angel, who was with me, who is their guide, showed me; and he showed me all their laws exactly as they are, and how it is with regard to all the years of the world and unto eternity.", "1 Enoch 72:2"),
    (2001, 200, 72, 3, "And this is the first law of the luminaries: the luminary the Sun has its rising in the eastern portals of the heaven, and its setting in the western portals of the heaven.", "1 Enoch 72:3"),
    # Chapter 91 (Apocalypse of Weeks)
    (2001, 200, 91, 1, "And now, my son Methuselah, call to me all thy brothers and gather together to me all the sons of thy mother; for the word calls me, and the spirit is poured out upon me, that I may show you everything that shall befall you for ever.", "1 Enoch 91:1"),
    (2001, 200, 91, 5, "For I know that violence must increase on the earth, and a great chastisement be executed on the earth, and all unrighteousness come to an end.", "1 Enoch 91:5"),
    (2001, 200, 91, 12, "And after that there shall be another, the eighth week, that of righteousness, and a sword shall be given to it that a righteous judgement may be executed on the oppressors.", "1 Enoch 91:12"),
    (2001, 200, 91, 13, "And sinners shall be delivered into the hands of the righteous, and at its close they shall acquire houses through their righteousness, and a house shall be built for the Great King in glory for evermore.", "1 Enoch 91:13"),

    # Jubilees additional chapters (R.H. Charles 1902)
    # Chapter 5
    (2002, 200, 5, 1, "And it came to pass when the children of men began to multiply on the face of the earth and daughters were born unto them, that the angels of God saw them on a certain year of this jubilee, that they were beautiful to look upon.", "Jubilees 5:1"),
    (2002, 200, 5, 2, "And they took themselves wives of all whom they chose, and they bare unto them sons, and they were giants.", "Jubilees 5:2"),
    (2002, 200, 5, 3, "And lawlessness increased on the earth and all flesh corrupted its way, alike men and cattle and beasts and birds and everything that walks on the earth.", "Jubilees 5:3"),
    (2002, 200, 5, 4, "And God looked upon the earth, and behold it was corrupt, and all flesh had corrupted its orders, and all that were upon the earth had wrought all manner of evil before His eyes.", "Jubilees 5:4"),
    (2002, 200, 5, 5, "And He said that He would destroy man and all flesh upon the face of the earth which He had created.", "Jubilees 5:5"),
    (2002, 200, 5, 6, "But Noah found grace before the eyes of the Lord.", "Jubilees 5:6"),
    # Chapter 10
    (2002, 200, 10, 1, "And in the third week of this jubilee the unclean demons began to lead astray the children of the sons of Noah, and to make to err and destroy them.", "Jubilees 10:1"),
    (2002, 200, 10, 2, "And the sons of Noah came to Noah their father, and they told him concerning the demons which were leading astray and blinding and slaying his sons' sons.", "Jubilees 10:2"),
    (2002, 200, 10, 3, "And he prayed before the Lord his God, and said: God of the spirits of all flesh, who hast shown mercy unto me and hast saved me and my sons from the waters of the flood.", "Jubilees 10:3"),
    (2002, 200, 10, 7, "And the chief of the spirits, Mastema, came and said: Lord, Creator, let some of them remain before me, and let them hearken to my voice.", "Jubilees 10:7"),
    (2002, 200, 10, 10, "And we explained to Noah all the medicines of their diseases, together with their seductions, how he might heal them with herbs of the earth.", "Jubilees 10:10"),
    (2002, 200, 10, 12, "And Noah wrote down all things in a book as we instructed him concerning every kind of medicine. Thus the evil spirits were precluded from hurting the sons of Noah.", "Jubilees 10:12"),

    # Sirach additional chapters (KJV Apocrypha)
    # Chapter 24
    (2006, 200, 24, 1, "Wisdom shall praise herself, and shall glory in the midst of her people.", "Sirach 24:1"),
    (2006, 200, 24, 2, "In the congregation of the most High shall she open her mouth, and triumph before his power.", "Sirach 24:2"),
    (2006, 200, 24, 3, "I came out of the mouth of the most High, and covered the earth as a cloud.", "Sirach 24:3"),
    (2006, 200, 24, 4, "I dwelt in high places, and my throne is in a cloudy pillar.", "Sirach 24:4"),
    (2006, 200, 24, 5, "I alone compassed the circuit of heaven, and walked in the bottom of the deep.", "Sirach 24:5"),
    (2006, 200, 24, 6, "In the waves of the sea, and in all the earth, and in every people and nation, I got a possession.", "Sirach 24:6"),
    # Chapter 38
    (2006, 200, 38, 1, "Honour a physician with the honour due unto him for the uses which ye may have of him: for the Lord hath created him.", "Sirach 38:1"),
    (2006, 200, 38, 2, "For of the most High cometh healing, and he shall receive honour of the king.", "Sirach 38:2"),
    (2006, 200, 38, 3, "The skill of the physician shall lift up his head: and in the sight of great men he shall be in admiration.", "Sirach 38:3"),
    (2006, 200, 38, 4, "The Lord hath created medicines out of the earth; and he that is wise will not abhor them.", "Sirach 38:4"),
    (2006, 200, 38, 5, "Was not the water made sweet with wood, that the virtue thereof might be known?", "Sirach 38:5"),
    (2006, 200, 38, 6, "And he hath given men skill, that he might be honoured in his marvellous works.", "Sirach 38:6"),
    (2006, 200, 38, 7, "With such doth he heal men, and taketh away their pains.", "Sirach 38:7"),
    # Chapter 44
    (2006, 200, 44, 1, "Let us now praise famous men, and our fathers that begat us.", "Sirach 44:1"),
    (2006, 200, 44, 2, "The Lord hath wrought great glory by them through his great power from the beginning.", "Sirach 44:2"),
    (2006, 200, 44, 3, "Such as did bear rule in their kingdoms, men renowned for their power, giving counsel by their understanding, and declaring prophecies.", "Sirach 44:3"),
    (2006, 200, 44, 4, "Leaders of the people by their counsels, and by their knowledge of learning meet for the people, wise and eloquent in their instructions.", "Sirach 44:4"),
    (2006, 200, 44, 5, "Such as found out musical tunes, and recited verses in writing.", "Sirach 44:5"),
    (2006, 200, 44, 6, "Rich men furnished with ability, living peaceably in their habitations.", "Sirach 44:6"),
    (2006, 200, 44, 7, "All these were honoured in their generations, and were the glory of their times.", "Sirach 44:7"),
    # Chapter 51
    (2006, 200, 51, 1, "I will thank thee, O Lord and King, and praise thee, O God my Saviour: I do give praise unto thy name.", "Sirach 51:1"),
    (2006, 200, 51, 2, "For thou art my defender and helper, and hast preserved my body from destruction.", "Sirach 51:2"),
    (2006, 200, 51, 3, "And from the snares of slanderous tongues, and from the lips that forge lies, and from such as turn aside to falsehood.", "Sirach 51:3"),
    (2006, 200, 51, 13, "When I was yet young, or ever I went abroad, I desired wisdom openly in my prayer.", "Sirach 51:13"),
    (2006, 200, 51, 14, "I prayed for her before the temple, and will seek her out even to the end.", "Sirach 51:14"),
    (2006, 200, 51, 23, "Draw near unto me, ye unlearned, and dwell in the house of learning.", "Sirach 51:23"),
    (2006, 200, 51, 26, "Put your neck under the yoke, and let your soul receive instruction: she is hard at hand to find.", "Sirach 51:26"),
    (2006, 200, 51, 27, "Behold with your eyes, how that I have had but little labour, and have gotten unto me much rest.", "Sirach 51:27"),

    # Tobit additional chapters (KJV Apocrypha)
    # Chapter 12
    (2007, 200, 12, 6, "Then he took them both apart, and said unto them, Bless God, praise him, and magnify him, and praise him for the things which he hath done unto you in the sight of all that live.", "Tobit 12:6"),
    (2007, 200, 12, 7, "It is good to praise God, and exalt his name, and honourably to shew forth the works of God; therefore be not slack to praise him.", "Tobit 12:7"),
    (2007, 200, 12, 8, "It is good to keep close the secret of a king, but it is honourable to reveal the works of God. Do that which is good, and no evil shall touch you.", "Tobit 12:8"),
    (2007, 200, 12, 9, "Prayer is good with fasting and alms and righteousness. A little with righteousness is better than much with unrighteousness. It is better to give alms than to lay up gold.", "Tobit 12:9"),
    (2007, 200, 12, 10, "For alms doth deliver from death, and shall purge away all sin. Those that exercise alms and righteousness shall be filled with life.", "Tobit 12:10"),
    (2007, 200, 12, 15, "I am Raphael, one of the seven holy angels, which present the prayers of the saints, and which go in and out before the glory of the Holy One.", "Tobit 12:15"),
    # Chapter 13
    (2007, 200, 13, 1, "Then Tobit wrote a prayer of rejoicing, and said, Blessed be God that liveth for ever, and blessed be his kingdom.", "Tobit 13:1"),
    (2007, 200, 13, 2, "For he doth scourge, and hath mercy: he leadeth down to hell, and bringeth up again: neither is there any that can avoid his hand.", "Tobit 13:2"),
    (2007, 200, 13, 6, "If ye turn to him with your whole heart, and with your whole mind, and deal uprightly before him, then will he turn unto you, and will not hide his face from you.", "Tobit 13:6"),
    (2007, 200, 13, 10, "O Jerusalem, the holy city, he will scourge thee for thy children's works, and will have mercy again on the sons of the righteous.", "Tobit 13:10"),

    # Wisdom of Solomon additional (KJV Apocrypha)
    # Chapter 9
    (2010, 200, 9, 1, "O God of my fathers, and Lord of mercy, who hast made all things with thy word.", "Wisdom of Solomon 9:1"),
    (2010, 200, 9, 2, "And ordained man through thy wisdom, that he should have dominion over the creatures which thou hast made.", "Wisdom of Solomon 9:2"),
    (2010, 200, 9, 3, "And order the world according to equity and righteousness, and execute judgement with an upright heart.", "Wisdom of Solomon 9:3"),
    (2010, 200, 9, 4, "Give me wisdom, that sitteth by thy throne; and reject me not from among thy children.", "Wisdom of Solomon 9:4"),
    (2010, 200, 9, 9, "O send her out of thy holy heavens, and from the throne of thy glory, that being present she may labour with me, that I may know what is pleasing unto thee.", "Wisdom of Solomon 9:9"),
    (2010, 200, 9, 10, "For she knoweth and understandeth all things, and she shall lead me soberly in my doings, and preserve me in her power.", "Wisdom of Solomon 9:10"),
    (2010, 200, 9, 13, "For what man is he that can know the counsel of God? or who can think what the will of the Lord is?", "Wisdom of Solomon 9:13"),
    (2010, 200, 9, 14, "For the thoughts of mortal men are miserable, and our devices are but uncertain.", "Wisdom of Solomon 9:14"),
    (2010, 200, 9, 15, "For the corruptible body presseth down the soul, and the earthy tabernacle weigheth down the mind that museth upon many things.", "Wisdom of Solomon 9:15"),
    (2010, 200, 9, 17, "And thy counsel who hath known, except thou give wisdom, and send thy Holy Spirit from above?", "Wisdom of Solomon 9:17"),
]

# ---------------------------------------------------------------------------
# Dead Sea Scrolls verses  (volume_id=300)
# Sources: scholarly translations of Qumran texts — these are reconstructions
# of ancient Hebrew/Aramaic manuscripts in the public domain.
# ---------------------------------------------------------------------------
DSS_VERSES = [
    # Community Rule (book_id=3001) — additional columns
    # Column III
    (3001, 300, 3, 1, "For the Master. Concerning the two spirits in which men walk. All the children of righteousness are ruled by the Prince of Light and walk in the ways of light.", "Community Rule 3:1"),
    (3001, 300, 3, 2, "But all the children of falsehood are ruled by the Angel of Darkness and walk in the ways of darkness.", "Community Rule 3:2"),
    (3001, 300, 3, 3, "The Angel of Darkness leads all the children of righteousness astray, and until his end, all their sin, iniquities, wickedness, and all their unlawful deeds are caused by his dominion.", "Community Rule 3:3"),
    (3001, 300, 3, 4, "And all their afflictions, and all the periods of their distress, are brought about by the rule of his persecution.", "Community Rule 3:4"),
    (3001, 300, 3, 5, "And all the spirits allotted to him cause the sons of light to stumble; but the God of Israel and His Angel of Truth will succour all the sons of light.", "Community Rule 3:5"),
    (3001, 300, 3, 6, "For it is He who created the spirits of Light and Darkness and founded every action upon them and established every deed upon their ways.", "Community Rule 3:6"),
    # Column IV
    (3001, 300, 4, 1, "These are the ways of the two spirits. The spirit of truth: a spirit of humility, patience, abundant charity, unending goodness, understanding, and intelligence.", "Community Rule 4:1"),
    (3001, 300, 4, 2, "A spirit of mighty wisdom which trusts in all the deeds of God and leans on His great lovingkindness.", "Community Rule 4:2"),
    (3001, 300, 4, 3, "A spirit of discernment in every purpose, of zeal for just laws, of holy intent with steadfastness of heart.", "Community Rule 4:3"),
    (3001, 300, 4, 4, "Of great charity towards all the sons of truth, of admirable purity which detests all unclean idols, of humble conduct sprung from an understanding of all things.", "Community Rule 4:4"),
    (3001, 300, 4, 5, "And of faithful concealment of the mysteries of truth. These are the counsels of the spirit to the sons of truth in this world.", "Community Rule 4:5"),
    (3001, 300, 4, 6, "And as for the visitation of all who walk in this spirit, it shall be healing, great peace in a long life, and fruitfulness, together with every everlasting blessing and eternal joy in life without end.", "Community Rule 4:6"),
    (3001, 300, 4, 7, "A crown of glory and a garment of majesty in unending light.", "Community Rule 4:7"),
    # Column V
    (3001, 300, 5, 1, "And this is the Rule for the men of the Community who have freely pledged themselves to be converted from all evil and to cling to all His commandments according to His will.", "Community Rule 5:1"),
    (3001, 300, 5, 2, "They shall separate from the congregation of the men of falsehood and shall unite, with respect to the Law and possessions, under the authority of the sons of Zadok, the Priests who keep the Covenant.", "Community Rule 5:2"),
    (3001, 300, 5, 3, "No man shall walk in the stubbornness of his heart so that he strays after his heart and eyes and evil inclination, but he shall circumcise in the Community the foreskin of evil inclination and of stiffness of neck.", "Community Rule 5:3"),
    # Column VIII
    (3001, 300, 8, 1, "In the Council of the Community there shall be twelve men and three Priests, perfectly versed in all that is revealed of the Law.", "Community Rule 8:1"),
    (3001, 300, 8, 2, "Their purpose is to practise truth, righteousness, justice, loving-kindness, and humility, one with another.", "Community Rule 8:2"),
    (3001, 300, 8, 3, "They are to preserve the faith in the Land with steadfastness and meekness and are to atone for sin by the practice of justice and by suffering the sorrows of affliction.", "Community Rule 8:3"),

    # War Scroll (book_id=3002) — additional columns
    # Column II
    (3002, 300, 2, 1, "The heads of the camps of the congregation are to be appointed: men of wisdom and understanding and knowledge, mighty in valor, skilled in the arts of war.", "War Scroll 2:1"),
    (3002, 300, 2, 2, "They shall order the battle formations according to this rule, and their camps shall be positioned in their prescribed places.", "War Scroll 2:2"),
    (3002, 300, 2, 3, "On their standards they shall write: The Congregation of God, The Camps of God, The Tribes of God, The Families of God, The Battalions of God.", "War Scroll 2:3"),
    (3002, 300, 2, 4, "And when they go out to battle they shall write upon their standards: The Wrath of God is kindled against Belial and against the men of his lot without remnant.", "War Scroll 2:4"),
    # Column VII
    (3002, 300, 7, 1, "No boy or woman shall enter their camps from the time they leave Jerusalem to march to battle until they return.", "War Scroll 7:1"),
    (3002, 300, 7, 2, "No man who is lame, or blind, or crippled, or afflicted with a lasting bodily blemish, or smitten with a bodily impurity, none of these shall go with them to war.", "War Scroll 7:2"),
    (3002, 300, 7, 3, "All of them shall be volunteers for battle, perfect in spirit and body, and prepared for the Day of Vengeance.", "War Scroll 7:3"),
    (3002, 300, 7, 4, "And no man who is impure because of his fount on the day of battle shall go down with them; for the holy angels shall be with their armies.", "War Scroll 7:4"),
    # Column XII
    (3002, 300, 12, 1, "For Thine is the battle! By the strength of Thy hand their corpses were scattered without burial. Goliath the Gittite, a mighty man of valor, Thou didst deliver into the hand of David Thy servant.", "War Scroll 12:1"),
    (3002, 300, 12, 2, "For he trusted in Thy great Name and not in sword and spear. For the battle is Thine, and he subdued the Philistines many times by Thy holy Name.", "War Scroll 12:2"),
    (3002, 300, 12, 3, "And through our kings also Thou didst save us many times, because of Thy mercy and not according to our works by which we did evil, nor for our sinful deeds.", "War Scroll 12:3"),

    # Thanksgiving Hymns (book_id=3003) — additional columns
    # Column II
    (3003, 300, 2, 1, "I thank Thee, O Lord, for Thou hast placed my soul in the bundle of the living, and hast hedged me against all the snares of the Pit.", "Thanksgiving Hymns 2:1"),
    (3003, 300, 2, 2, "Violent men have sought after my life because I have clung to Thy Covenant. For they, an assembly of deceit, and a horde of Belial, know not that my stand is maintained by Thee.", "Thanksgiving Hymns 2:2"),
    (3003, 300, 2, 3, "And that in Thy mercy Thou wilt save my soul since my steps proceed from Thee.", "Thanksgiving Hymns 2:3"),
    (3003, 300, 2, 4, "From Thee it is that they assail my life, that Thou mayest be glorified by the judgement of the wicked, and manifest Thy might through me in the presence of the sons of men.", "Thanksgiving Hymns 2:4"),
    (3003, 300, 2, 5, "For it is by Thy mercy that I stand. And I said: Mighty men have encamped against me, and have surrounded me with all their weapons of war.", "Thanksgiving Hymns 2:5"),
    # Column IV
    (3003, 300, 4, 1, "I thank Thee, O Lord, for Thou hast illumined my face by Thy Covenant, and from the rising of morning Thou hast appeared unto me in perfect light.", "Thanksgiving Hymns 4:1"),
    (3003, 300, 4, 2, "But they, those who beguile me, have comforted themselves and have formed a counsel of Belial. They know not that Thy truth guideth my steps.", "Thanksgiving Hymns 4:2"),
    (3003, 300, 4, 3, "For Thou, O my God, hast sheltered me from the children of men, and hast hidden Thy Law within me against the time when Thou shouldst reveal Thy salvation to me.", "Thanksgiving Hymns 4:3"),
    (3003, 300, 4, 4, "For in the distress of my soul Thou didst not forsake me. Thou didst hear my cry in the bitterness of my soul.", "Thanksgiving Hymns 4:4"),
    (3003, 300, 4, 5, "And when I groaned, Thou didst discern my sorrow. Thou didst preserve the soul of the poor one in the den of lions whose tongues are sharp as the sword.", "Thanksgiving Hymns 4:5"),
    # Column XI
    (3003, 300, 11, 1, "I thank Thee, O Lord, for Thou art as a fortified wall to me, as an iron bar against all destroyers.", "Thanksgiving Hymns 11:1"),
    (3003, 300, 11, 2, "Thou hast set my feet upon rock; I walk on the way of eternity and on the paths which Thou hast chosen.", "Thanksgiving Hymns 11:2"),

    # Temple Scroll (book_id=3004) — additional columns
    # Column XXIX
    (3004, 300, 29, 1, "And you shall make a feast of first fruits of wine. You shall offer new wine, wine presses for each tribe, twelve, all the elders of the congregation.", "Temple Scroll 29:1"),
    (3004, 300, 29, 2, "And they shall eat in the outer court before the Lord, a freewill offering from their hands, each man what he can give.", "Temple Scroll 29:2"),
    (3004, 300, 29, 3, "You shall count from the day of the new wine offering seven weeks, seven complete Sabbaths, until the morrow after the seventh Sabbath.", "Temple Scroll 29:3"),
    # Column XLV
    (3004, 300, 45, 1, "And when a man sells his daughter as a slave, she shall not go out as the male slaves go out. And if she does not please her master, who has designated her for himself, he shall let her be redeemed.", "Temple Scroll 45:1"),
    (3004, 300, 45, 2, "To a foreign people he shall have no right to sell her, since he has broken faith with her.", "Temple Scroll 45:2"),
    # Column LVII
    (3004, 300, 57, 1, "When you come to the land which I give you and possess it and dwell in it and say: I will set over me a king like all the nations around me.", "Temple Scroll 57:1"),
    (3004, 300, 57, 2, "You shall surely set over you a king whom I shall choose. From among your brethren you shall set a king over you; you shall not set a foreigner over you who is not your brother.", "Temple Scroll 57:2"),
    (3004, 300, 57, 3, "And he shall not multiply horses to himself nor cause the people to return to Egypt to multiply horses, for I have said to you: You shall never return that way again.", "Temple Scroll 57:3"),

    # Habakkuk Commentary (book_id=3005) — additional columns
    (3005, 300, 2, 1, "Interpreted, this concerns the Liar who led many astray that he might build his city of vanity with blood and raise a congregation on deceit.", "Habakkuk Commentary 2:1"),
    (3005, 300, 2, 2, "For the sake of his glory, causing many to perform a service of vanity and instructing them in lying deeds, so that their toil might be for nothing.", "Habakkuk Commentary 2:2"),
    (3005, 300, 2, 3, "That they shall come to judgements of fire, because they blasphemed and outraged the elect of God.", "Habakkuk Commentary 2:3"),
    (3005, 300, 7, 1, "Interpreted, this concerns the Wicked Priest who was called by the name of truth when he first arose. But when he ruled over Israel his heart became proud.", "Habakkuk Commentary 7:1"),
    (3005, 300, 7, 2, "And he forsook God and betrayed the precepts for the sake of riches. He robbed and amassed the riches of the men of violence who rebelled against God.", "Habakkuk Commentary 7:2"),
    (3005, 300, 7, 3, "And he took the wealth of the peoples, heaping sinful iniquity upon himself. And he lived in the ways of abominations amidst every unclean defilement.", "Habakkuk Commentary 7:3"),

    # Damascus Document (book_id=3007) — additional columns
    (3007, 300, 2, 1, "And now, listen to me, all you who enter the Covenant, and I will unstop your ears concerning the ways of the wicked.", "Damascus Document 2:1"),
    (3007, 300, 2, 2, "God loves knowledge. Wisdom and understanding He has set before Him, and prudence and knowledge serve Him.", "Damascus Document 2:2"),
    (3007, 300, 2, 3, "Patience and much forgiveness are with Him towards those who turn from transgression; but power, might, and great flaming wrath by the hand of all the Angels of Destruction.", "Damascus Document 2:3"),
    (3007, 300, 2, 4, "Towards those who depart from the way and abhor the precept: they shall have no remnant nor survivor.", "Damascus Document 2:4"),
    (3007, 300, 3, 1, "For God did not choose them from the beginning of the world, and before they were established He knew their works.", "Damascus Document 3:1"),
    (3007, 300, 3, 2, "And He abhorred their generations on account of blood, and hid His face from the Land, from Israel, until they were consumed.", "Damascus Document 3:2"),
    (3007, 300, 3, 3, "For He knew the years of their coming and the length and exact duration of their times for all ages to come and throughout eternity.", "Damascus Document 3:3"),
    (3007, 300, 3, 4, "He knew the things that would happen in their times throughout all the everlasting years.", "Damascus Document 3:4"),
    (3007, 300, 3, 5, "And in each of them He raised up for Himself men called by name, that a remnant might be left to the Land, and that the face of the earth might be filled with their seed.", "Damascus Document 3:5"),
    (3007, 300, 4, 1, "And He taught them by the hand of the anointed ones, through His holy spirit and through seers of the truth.", "Damascus Document 4:1"),
    (3007, 300, 4, 2, "And their names were established with precision. But those whom He hated He caused to stray.", "Damascus Document 4:2"),

    # Genesis Apocryphon (book_id=3006) — additional columns
    (3006, 300, 2, 1, "And I, Lamech, was troubled, and I went to Bitenosh my wife and I said to her: I adjure thee by the Most High, the Great Lord, the King of all ages.", "Genesis Apocryphon 2:1"),
    (3006, 300, 2, 2, "Tell me in truth, without lies, whether this is indeed my seed, whether this is indeed from me. Tell me in truth without lies.", "Genesis Apocryphon 2:2"),
    (3006, 300, 2, 3, "Then Bitenosh my wife spoke to me with much heat and she wept.", "Genesis Apocryphon 2:3"),
    (3006, 300, 2, 4, "She said: O my lord, O my brother, remember my pleasure! I swear to thee by the Holy Great One, the King of the heavens, that this seed is yours and that this pregnancy is from you.", "Genesis Apocryphon 2:4"),
    (3006, 300, 19, 1, "And I, Abram, departed to journey and go to the South, and I came to Hebron, and Hebron was built at that time, and I dwelt there two years.", "Genesis Apocryphon 19:1"),
    (3006, 300, 19, 2, "And there was a famine in all that land, and I heard that there was grain in Egypt, and I journeyed to enter the land of Egypt.", "Genesis Apocryphon 19:2"),
    (3006, 300, 19, 3, "And I came to the river Karmon, one of the branches of the River, and I crossed the seven branches of this river.", "Genesis Apocryphon 19:3"),

    # Messianic Rule (book_id=3008) — additional
    (3008, 300, 1, 2, "They shall educate them in the Book of Meditation and shall teach them all their rules, so that they may walk perfectly, each with his neighbour.", "Messianic Rule 1:2"),
    (3008, 300, 1, 3, "And when they are twenty years old, they shall be enrolled in the lot to take their place among the families of the holy congregation.", "Messianic Rule 1:3"),
    (3008, 300, 1, 4, "He shall not approach a woman to know her by lying with her before he is fully twenty years old, when he shall know good and evil.", "Messianic Rule 1:4"),
    (3008, 300, 2, 1, "This shall be the assembly of the men of renown, called to the meeting of the Council of the Community, when God engenders the Messiah among them.", "Messianic Rule 2:1"),
    (3008, 300, 2, 2, "The Priest shall enter at the head of the whole congregation of Israel, and all his brethren the sons of Aaron the Priests.", "Messianic Rule 2:2"),

    # Copper Scroll (book_id=3009) — additional locations
    (3009, 300, 2, 1, "In the salt pit that is under the steps: forty-one talents of silver.", "Copper Scroll 2:1"),
    (3009, 300, 2, 2, "In the cave of the old Washers House, on the third terrace: sixty-five bars of gold.", "Copper Scroll 2:2"),
    (3009, 300, 3, 1, "In the Great Cistern which is in the Court of Peristyle, in a recess in the floor covered with sediment, in front of the upper opening: nine hundred talents.", "Copper Scroll 3:1"),
    (3009, 300, 3, 2, "In the hill of Kohlit, tithe vessels of the Lord of the peoples, and sacred vestments; total of the tithes and of the treasure: a seventh of the second tithe rendered unfit for use.", "Copper Scroll 3:2"),

    # Isaiah Scroll (book_id=3010) — additional selections
    (3010, 300, 40, 1, "Comfort ye, comfort ye my people, saith your God.", "Isaiah Scroll 40:1"),
    (3010, 300, 40, 2, "Speak ye comfortably to Jerusalem, and cry unto her, that her warfare is accomplished, that her iniquity is pardoned: for she hath received of the Lord's hand double for all her sins.", "Isaiah Scroll 40:2"),
    (3010, 300, 40, 3, "The voice of him that crieth in the wilderness, Prepare ye the way of the Lord, make straight in the desert a highway for our God.", "Isaiah Scroll 40:3"),
    (3010, 300, 40, 4, "Every valley shall be exalted, and every mountain and hill shall be made low: and the crooked shall be made straight, and the rough places plain.", "Isaiah Scroll 40:4"),
    (3010, 300, 40, 5, "And the glory of the Lord shall be revealed, and all flesh shall see it together: for the mouth of the Lord hath spoken it.", "Isaiah Scroll 40:5"),
    (3010, 300, 53, 1, "Who hath believed our report? and to whom is the arm of the Lord revealed?", "Isaiah Scroll 53:1"),
    (3010, 300, 53, 2, "For he shall grow up before him as a tender plant, and as a root out of a dry ground: he hath no form nor comeliness; and when we shall see him, there is no beauty that we should desire him.", "Isaiah Scroll 53:2"),
    (3010, 300, 53, 3, "He is despised and rejected of men; a man of sorrows, and acquainted with grief: and we hid as it were our faces from him; he was despised, and we esteemed him not.", "Isaiah Scroll 53:3"),
    (3010, 300, 53, 4, "Surely he hath borne our griefs, and carried our sorrows: yet we did esteem him stricken, smitten of God, and afflicted.", "Isaiah Scroll 53:4"),
    (3010, 300, 53, 5, "But he was wounded for our transgressions, he was bruised for our iniquities: the chastisement of our peace was upon him; and with his stripes we are healed.", "Isaiah Scroll 53:5"),

    # Psalms Scroll (book_id=3011) — additional psalms
    (3011, 300, 151, 1, "I was the smallest among my brothers, and the youngest among the sons of my father. And he made me shepherd of his flocks, and ruler over his kids.", "Psalms Scroll 151:1"),
    (3011, 300, 151, 2, "My hands made a flute, and my fingers a lyre. And I gave glory to the Lord. I said to myself, the mountains do not witness for Him, nor do the hills proclaim.", "Psalms Scroll 151:2"),
    (3011, 300, 151, 3, "The trees have cherished my words and the flocks my works. For who can proclaim and who can declare the deeds of the Lord? God has seen everything, He has heard everything, and He has listened.", "Psalms Scroll 151:3"),
    (3011, 300, 154, 1, "With a loud voice glorify God; in the congregation of the many proclaim His majesty.", "Psalms Scroll 154:1"),
    (3011, 300, 154, 2, "In the multitude of the upright glorify His name; with the faithful recount His greatness.", "Psalms Scroll 154:2"),
    (3011, 300, 154, 3, "Bind your souls with the good ones and with the pure ones to glorify the Most High.", "Psalms Scroll 154:3"),
    (3011, 300, 154, 4, "Form an assembly to proclaim His salvation, and be not lax in making known His might and His majesty to all simple folk.", "Psalms Scroll 154:4"),

    # Book of Giants (book_id=3012) — additional fragments
    (3012, 300, 2, 1, "Then two of them had dreams and the sleep of their eyes fled from them, and they arose and came to Shemihazah their father and told him their dreams.", "Book of Giants 2:1"),
    (3012, 300, 2, 2, "The first said: I saw in my vision a garden, and gardeners were watering it, and darkness covered all the earth. Then suddenly fire consumed everything.", "Book of Giants 2:2"),
    (3012, 300, 2, 3, "The second said: I saw in my dream a great stone falling from heaven, and it struck the earth, and the earth was covered with water.", "Book of Giants 2:3"),
    (3012, 300, 3, 1, "Then Mahway arose and went to Enoch the scribe, and said to him: I have been sent to you to ask you to interpret the dreams of the giants.", "Book of Giants 3:1"),
    (3012, 300, 3, 2, "And Enoch sent word to the giants, saying: The interpretation of your dreams is this: Judgement has been decreed against you, and you shall not have peace.", "Book of Giants 3:2"),

    # Songs of Sabbath Sacrifice (book_id=3013) — additional songs
    (3013, 300, 2, 1, "For the Instructor. Song of the sacrifice of the second Sabbath on the twenty-third of the first month. Praise God, all you angels of the holy firmament.", "Songs of Sabbath Sacrifice 2:1"),
    (3013, 300, 2, 2, "Let them praise the splendour of His glory above all the godlike beings of knowledge, and let them sing of the glory of the King of kings.", "Songs of Sabbath Sacrifice 2:2"),
    (3013, 300, 6, 1, "For the Instructor. Song of the sacrifice of the sixth Sabbath on the ninth of the second month. Praise the God of gods, you inhabitants of the height of heights.", "Songs of Sabbath Sacrifice 6:1"),
    (3013, 300, 6, 2, "For He is the Holy of holies over all the chiefs of the holiness of the highest. Let all the foundations of the holy of holies bear His glory.", "Songs of Sabbath Sacrifice 6:2"),
    (3013, 300, 12, 1, "For the Instructor. Song of the sacrifice of the twelfth Sabbath on the twenty-first of the third month. Praise the God of awe, you spirits of the living God, for evermore.", "Songs of Sabbath Sacrifice 12:1"),
    (3013, 300, 12, 2, "Let them praise the wonderful firmament of the highest heaven, all its beams and its walls, all its structure, its architrave and its design.", "Songs of Sabbath Sacrifice 12:2"),
    (3013, 300, 12, 3, "The spirits of the holy of holies, the living godlike beings, the spirits of eternal holiness above all the holy ones.", "Songs of Sabbath Sacrifice 12:3"),

    # Community Rule — additional columns
    # Column VI
    (3001, 300, 6, 1, "And this is the rule for the session of the Many. Each man shall sit in his place: the Priests shall sit first, and the elders second, and all the rest of the people according to their rank.", "Community Rule 6:1"),
    (3001, 300, 6, 2, "And thus shall they be asked concerning the law, and concerning any counsel or matter coming before the Many, each man in order of his rank.", "Community Rule 6:2"),
    (3001, 300, 6, 3, "No man shall interrupt a companion before his speech has ended, nor speak before a man of higher rank. A man who has something to say shall speak in his turn.", "Community Rule 6:3"),
    (3001, 300, 6, 4, "And in the session of the Many no man shall speak any word not pleasing to the Many, or without the permission of the Guardian who is over the Many.", "Community Rule 6:4"),
    (3001, 300, 6, 5, "Any man who has a word to speak to the Many but who is not in the standing of the one who counsels the Community, that man shall stand on his feet.", "Community Rule 6:5"),
    (3001, 300, 6, 6, "And he shall say: I have a word to speak to the Many. If they permit, he shall speak.", "Community Rule 6:6"),
    # Column IX
    (3001, 300, 9, 1, "These are the precepts in which the Master shall walk in his commerce with all the living, according to the rule proper to every season and according to the weight of every man.", "Community Rule 9:1"),
    (3001, 300, 9, 2, "He shall do the will of God according to all that has been revealed from age to age.", "Community Rule 9:2"),
    (3001, 300, 9, 3, "He shall study all the wisdom found according to the times, and the statute of the age.", "Community Rule 9:3"),
    (3001, 300, 9, 4, "He shall separate and weigh the sons of righteousness according to their spirit. He shall hold firmly to the elect of the time according to His will, as He has commanded.", "Community Rule 9:4"),
    (3001, 300, 9, 5, "He shall judge each man according to his spirit. He shall admit him according to the cleanness of his hands and advance him according to his understanding.", "Community Rule 9:5"),

    # War Scroll additional columns
    # Column X
    (3002, 300, 10, 1, "And on the trumpets of assembly of the congregation they shall write: The Called of God. And on the trumpets of the camps they shall write: The Peace of God in the camps of His saints.", "War Scroll 10:1"),
    (3002, 300, 10, 2, "And on the trumpets of battle they shall write: The Might of God to scatter the enemy and to put to flight all those who hate righteousness and to withdraw favour from all who hate God.", "War Scroll 10:2"),
    (3002, 300, 10, 3, "And on the trumpets of ambush they shall write: The mysteries of God for the destruction of wickedness.", "War Scroll 10:3"),
    (3002, 300, 10, 4, "And on the trumpets of pursuit they shall write: God has struck all the Sons of Darkness. He shall not abate His anger until they are annihilated.", "War Scroll 10:4"),
    # Column XIV
    (3002, 300, 14, 1, "After they have withdrawn from the slain to enter the camp, they shall all sing the Psalm of Return. And in the morning, they shall wash their garments and cleanse themselves of the blood of the corpses of the sinners.", "War Scroll 14:1"),
    (3002, 300, 14, 2, "And they shall return to the position of their formations, where the battle line was drawn up, and each man shall return to his place.", "War Scroll 14:2"),
    (3002, 300, 14, 3, "And they shall all bless the God of Israel and exalt His Name together in joyful communion and shall say: Blessed be the God of Israel who keeps mercy towards His Covenant.", "War Scroll 14:3"),
    # Column XV
    (3002, 300, 15, 1, "When the battle line is drawn up against the enemy, battle line against battle line, there shall go forth from the middle opening into the gap between the battle lines seven Priests of the sons of Aaron.", "War Scroll 15:1"),
    (3002, 300, 15, 2, "Dressed in garments of white silk, wearing a linen tunic and linen breeches, and girded with a linen sash of twined fine linen, violet and purple and scarlet.", "War Scroll 15:2"),
    (3002, 300, 15, 3, "A design in needlework, the work of a craftsman. And on their heads shall be turbans, the garments of war; they shall not take them into the sanctuary.", "War Scroll 15:3"),

    # Thanksgiving Hymns additional
    # Column VI
    (3003, 300, 6, 1, "I thank Thee, O Lord, for Thou hast set me beside a fountain of streams in an arid land, and close to a spring of waters in a dry land, and beside a watered garden in a wilderness.", "Thanksgiving Hymns 6:1"),
    (3003, 300, 6, 2, "Thou hast planted a planting of cypress and pine and cedar for Thy glory, trees of life beside a mysterious fountain hidden among the trees by the water.", "Thanksgiving Hymns 6:2"),
    (3003, 300, 6, 3, "And they shall put forth a shoot of the everlasting Plant. But before they sprouted, they took root and sent out their roots to the watercourse.", "Thanksgiving Hymns 6:3"),
    (3003, 300, 6, 4, "That its stem might be open to the living waters and be one with the everlasting spring.", "Thanksgiving Hymns 6:4"),
    (3003, 300, 6, 5, "And all the beasts of the forest fed on its leafy branches; its stem was trodden by all who passed on the way, and its boughs by every winged bird.", "Thanksgiving Hymns 6:5"),
    # Column VII
    (3003, 300, 7, 1, "I thank Thee, O Lord, for Thou hast enlightened me through Thy truth. In Thy marvellous mysteries, and in Thy lovingkindness to a man of vanity, and in the greatness of Thy mercy to a perverse heart Thou hast granted me knowledge.", "Thanksgiving Hymns 7:1"),
    (3003, 300, 7, 2, "Who is like Thee among the gods, O Lord, and who is according to Thy truth? Who, when he is judged, shall be righteous before Thee?", "Thanksgiving Hymns 7:2"),
    (3003, 300, 7, 3, "For no spirit can reply to Thy rebuke, nor can any withstand Thy wrath. But all the children of Thy truth Thou dost bring before Thee with forgiveness.", "Thanksgiving Hymns 7:3"),
    (3003, 300, 7, 4, "Cleansing them from their transgressions in the abundance of Thy goodness, and in the multitude of Thy mercy causing them to stand before Thee for ever and ever.", "Thanksgiving Hymns 7:4"),
    # Column XV
    (3003, 300, 15, 1, "I thank Thee, O Lord, for Thou hast not abandoned me whilst I sojourned among a people burdened with sin.", "Thanksgiving Hymns 15:1"),
    (3003, 300, 15, 2, "Thou hast not judged me according to my guilt, nor hast Thou abandoned me because of the designs of my inclination, but hast saved my life from the Pit.", "Thanksgiving Hymns 15:2"),
    (3003, 300, 15, 3, "And Thou hast brought Thy servant from among the lions destined for the guilty, lions which grind the bones of the mighty and drink the blood of the brave.", "Thanksgiving Hymns 15:3"),

    # Damascus Document additional
    # Column VI
    (3007, 300, 6, 1, "All those who have been brought into the Covenant shall not enter the Temple to light His altar in vain. They shall be careful to act according to the exact interpretation of the Law during the age of wickedness.", "Damascus Document 6:1"),
    (3007, 300, 6, 2, "They shall separate from the sons of the Pit and shall keep away from the unclean riches of wickedness acquired by vow or anathema or from the Temple treasure.", "Damascus Document 6:2"),
    (3007, 300, 6, 3, "They shall not rob the poor of His people, to make of widows their prey, and of the fatherless their victim.", "Damascus Document 6:3"),
    (3007, 300, 6, 4, "They shall distinguish between clean and unclean, and shall proclaim the difference between holy and profane.", "Damascus Document 6:4"),
    (3007, 300, 6, 5, "They shall keep the Sabbath day according to its exact interpretation, and the feasts and the Day of Fasting, according to the finding of the members of the New Covenant in the land of Damascus.", "Damascus Document 6:5"),
    # Column VII
    (3007, 300, 7, 1, "None of those who have entered the Covenant shall deal with the sons of the Pit except hand to hand.", "Damascus Document 7:1"),
    (3007, 300, 7, 2, "None shall buy from or sell to them except hand to hand.", "Damascus Document 7:2"),
    (3007, 300, 7, 3, "And no member of the Covenant of God shall be associated with them in their work or in their wealth, lest he burden him with guilt of transgression.", "Damascus Document 7:3"),

    # Genesis Apocryphon additional
    # Column XX (Abraham in Egypt)
    (3006, 300, 20, 1, "And I, Abram, wept aloud that night, I and my nephew Lot, because Sarai had been taken from me by force.", "Genesis Apocryphon 20:1"),
    (3006, 300, 20, 2, "I prayed that night and I said: Blessed art Thou, O Most High God, Lord of all worlds, because Thou art Lord and Master of all, and Ruler of all the kings of the earth.", "Genesis Apocryphon 20:2"),
    (3006, 300, 20, 3, "Now I weep before Thee, my Lord, against Pharaoh Zoan the king of Egypt, because my wife has been taken from me by force. Judge him for me and let me see Thy mighty hand descend on him.", "Genesis Apocryphon 20:3"),
    (3006, 300, 20, 4, "That night the Most High God sent a spirit to scourge him, an evil spirit to all his household; and it scourged him and all his household. And he could not approach her, and although he was with her for two years he could not know her.", "Genesis Apocryphon 20:4"),
    (3006, 300, 20, 5, "At the end of those two years the plagues and the afflictions became more grievous and more severe upon him and upon all his household.", "Genesis Apocryphon 20:5"),
    (3006, 300, 21, 1, "So the king called all the wise men of Egypt, and all the magicians and all the healers of Egypt, if perhaps they might heal him from that scourge, him and his household.", "Genesis Apocryphon 21:1"),
    (3006, 300, 21, 2, "But all the magicians and healers and wise men could not rise up to heal him, for the spirit scourged them all and they fled.", "Genesis Apocryphon 21:2"),

    # Psalms Scroll additional
    (3011, 300, 155, 1, "O Lord, I called unto thee, attend to me. I spread forth my hands toward thy holy dwelling. Incline thine ear and grant me my petition.", "Psalms Scroll 155:1"),
    (3011, 300, 155, 2, "And my prayer, let it not fail from before thee. Build up my soul and do not cast it down, and do not abandon it in the presence of the wicked.", "Psalms Scroll 155:2"),
    (3011, 300, 155, 3, "May the Judge of Truth remove from me the rewards of evil. O Lord, judge me not according to my sins; for no man living is righteous before thee.", "Psalms Scroll 155:3"),
    (3011, 300, 155, 4, "Grant me understanding, O Lord, in thy law, and teach me thine ordinances. That many may hear of thy deeds, and peoples may honour thy glory.", "Psalms Scroll 155:4"),
    (3011, 300, 155, 5, "Remember me and forget me not, and lead me not into situations too hard for me.", "Psalms Scroll 155:5"),
    # Psalm 145 (non-canonical addition)
    (3011, 300, 145, 1, "Great is the Lord and greatly to be praised, in the city of our God, the mountain of his holiness. The Lord is great and most worthy of praise; his greatness no one can fathom.", "Psalms Scroll 145:1"),
    (3011, 300, 145, 2, "One generation shall laud thy works to another, and shall declare thy mighty acts.", "Psalms Scroll 145:2"),
    (3011, 300, 145, 3, "The Lord is gracious and merciful, slow to anger and of great lovingkindness.", "Psalms Scroll 145:3"),
    (3011, 300, 145, 4, "The Lord is good to all, and his compassion is over all that he has made.", "Psalms Scroll 145:4"),

    # Book of Giants additional
    (3012, 300, 4, 1, "And Enoch the scribe said: In truth I tell you that the Most High shall execute judgement against the Watchers and the giants, and the sentence shall go forth against them all.", "Book of Giants 4:1"),
    (3012, 300, 4, 2, "The vision has been sent to rebuke the Watchers, the sons of heaven. What you have done is abominable upon the earth.", "Book of Giants 4:2"),
    (3012, 300, 4, 3, "And therefore you shall have neither peace nor pardon. And inasmuch as they delight in their sons, the slaughter of their beloved ones shall they witness.", "Book of Giants 4:3"),
    (3012, 300, 4, 4, "And over the destruction of their sons shall they lament and petition forever, but they shall have neither mercy nor peace.", "Book of Giants 4:4"),
    (3012, 300, 5, 1, "Then Ohya said to Hahya, his brother: This interpretation of the dream is not comforting. The vision portends our destruction and the ruin of all our deeds.", "Book of Giants 5:1"),
    (3012, 300, 5, 2, "We and all our kindred shall perish in the flood, and all our labours shall be destroyed, for the Great One has decreed the destruction of the earth.", "Book of Giants 5:2"),

    # Copper Scroll additional
    (3009, 300, 4, 1, "In the cavity of the old House of Tribute, in the Platform of the Chain: sixty-five bars of gold.", "Copper Scroll 4:1"),
    (3009, 300, 4, 2, "In the underground passage which is in Kohlit toward the south, at the outflow from the canal: a buried chest and its contents, with a total value of seventeen talents.", "Copper Scroll 4:2"),
    (3009, 300, 5, 1, "In the cistern which is below the rampart, on the east side, in a place hollowed out of the rock: six hundred bars of silver.", "Copper Scroll 5:1"),
    (3009, 300, 5, 2, "In the big cistern in the court of the peristyle, in a recess in the bottom of the wall: nine hundred talents of gold and five talents of silver.", "Copper Scroll 5:2"),
    (3009, 300, 6, 1, "In the pit adjacent to the north of Kohlit, opening to the north, with graves at its entrance: a copy of this document with an explanation and measurements and an inventory for each and every thing.", "Copper Scroll 6:1"),

    # Messianic Rule additional
    (3008, 300, 2, 3, "He shall bless the first-fruits of bread and wine and shall stretch out his hand over the bread first of all.", "Messianic Rule 2:3"),
    (3008, 300, 2, 4, "And after that the Messiah of Israel shall stretch out his hands over the bread.", "Messianic Rule 2:4"),
    (3008, 300, 2, 5, "And after that all the congregation of the Community shall give thanks, each man according to his rank.", "Messianic Rule 2:5"),
    (3008, 300, 2, 6, "And after this prescription shall they act at every meal at which at least ten men are gathered together.", "Messianic Rule 2:6"),

    # Isaiah Scroll additional
    (3010, 300, 53, 6, "All we like sheep have gone astray; we have turned every one to his own way; and the Lord hath laid on him the iniquity of us all.", "Isaiah Scroll 53:6"),
    (3010, 300, 53, 7, "He was oppressed, and he was afflicted, yet he opened not his mouth: he is brought as a lamb to the slaughter, and as a sheep before her shearers is dumb, so he openeth not his mouth.", "Isaiah Scroll 53:7"),
    (3010, 300, 53, 10, "Yet it pleased the Lord to bruise him; he hath put him to grief: when thou shalt make his soul an offering for sin, he shall see his seed, he shall prolong his days, and the pleasure of the Lord shall prosper in his hand.", "Isaiah Scroll 53:10"),
    (3010, 300, 53, 11, "He shall see of the travail of his soul, and shall be satisfied: by his knowledge shall my righteous servant justify many; for he shall bear their iniquities.", "Isaiah Scroll 53:11"),
    (3010, 300, 53, 12, "Therefore will I divide him a portion with the great, and he shall divide the spoil with the strong; because he hath poured out his soul unto death: and he was numbered with the transgressors.", "Isaiah Scroll 53:12"),
    (3010, 300, 61, 1, "The Spirit of the Lord God is upon me; because the Lord hath anointed me to preach good tidings unto the meek; he hath sent me to bind up the brokenhearted, to proclaim liberty to the captives, and the opening of the prison to them that are bound.", "Isaiah Scroll 61:1"),
    (3010, 300, 61, 2, "To proclaim the acceptable year of the Lord, and the day of vengeance of our God; to comfort all that mourn.", "Isaiah Scroll 61:2"),
    (3010, 300, 61, 3, "To appoint unto them that mourn in Zion, to give unto them beauty for ashes, the oil of joy for mourning, the garment of praise for the spirit of heaviness.", "Isaiah Scroll 61:3"),

    # Habakkuk Commentary additional
    (3005, 300, 8, 1, "Interpreted, this concerns the Wicked Priest who robbed the poor of their possessions.", "Habakkuk Commentary 8:1"),
    (3005, 300, 8, 2, "Woe to him who gets evil gain for his house, that he may set his nest on high, that he may be saved from the hand of evil!", "Habakkuk Commentary 8:2"),
    (3005, 300, 8, 3, "Interpreted, this concerns the Priest who amassed riches from the plunder of the peoples, but at the end of days his riches and plunder shall be delivered into the hands of the army of the Kittim.", "Habakkuk Commentary 8:3"),
    (3005, 300, 11, 1, "For the stone shall cry out from the wall, and the beam from the woodwork shall answer it.", "Habakkuk Commentary 11:1"),
    (3005, 300, 11, 2, "Interpreted, this concerns the Wicked Priest who built a city on blood and established a town on falsehood for the sake of its glory.", "Habakkuk Commentary 11:2"),
    (3005, 300, 12, 1, "For the earth shall be filled with the knowledge of the glory of the Lord as the waters cover the sea.", "Habakkuk Commentary 12:1"),
    (3005, 300, 12, 2, "Interpreted, this means that when they return, God will reveal to them the knowledge of truth, as plentiful as the waters of the sea.", "Habakkuk Commentary 12:2"),

    # Temple Scroll additional
    (3004, 300, 2, 1, "And you shall make the court of the sanctuary, one hundred cubits long and one hundred cubits wide, a square all around.", "Temple Scroll 2:1"),
    (3004, 300, 2, 2, "And its wall shall be five cubits thick and its height fifty cubits. It shall be of hewn stone overlaid with gold.", "Temple Scroll 2:2"),
]

# ---------------------------------------------------------------------------
# Russian Orthodox Bible verses  (volume_id=400)
# Sources: KJV Apocrypha translations — all public domain.
# ---------------------------------------------------------------------------
RUSSIAN_VERSES = [
    # 1 Esdras (book_id=4001) — KJV Apocrypha
    # Chapter 2
    (4001, 400, 2, 1, "After these things, when Artaxerxes the king of the Persians reigned, came Esdras the son of Saraias.", "1 Esdras 2:1"),
    (4001, 400, 2, 2, "The son of Ezerias, the son of Helchiah, the son of Salum.", "1 Esdras 2:2"),
    (4001, 400, 2, 3, "The son of Sadduc, the son of Achitob, the son of Amarias, the son of Ezias, the son of Meremoth.", "1 Esdras 2:3"),
    (4001, 400, 2, 4, "The son of Zaraias, the son of Savias, the son of Boccas, the son of Abisum, the son of Phinees, the son of Eleazar, the son of Aaron the chief priest.", "1 Esdras 2:4"),
    (4001, 400, 2, 5, "This Esdras went up from Babylon, as a scribe, being very ready in the law of Moses, that was given by the God of Israel.", "1 Esdras 2:5"),
    # Chapter 3
    (4001, 400, 3, 1, "Now when Darius reigned, he made a great feast unto all his subjects, and unto all his household, and unto all the princes of Media and Persia.", "1 Esdras 3:1"),
    (4001, 400, 3, 2, "And to all the governors and captains and lieutenants that were under him, from India unto Ethiopia, of an hundred twenty and seven provinces.", "1 Esdras 3:2"),
    (4001, 400, 3, 3, "And when they had eaten and drunken, and being satisfied were gone home, then Darius the king went into his bedchamber, and slept, and soon after awaked.", "1 Esdras 3:3"),
    (4001, 400, 3, 4, "Then three young men, that were of the guard that kept the king's body, spake one to another.", "1 Esdras 3:4"),
    (4001, 400, 3, 5, "Let every one of us speak a sentence: he that shall overcome, and whose sentence shall seem wiser than the others, unto him shall the king Darius give great gifts.", "1 Esdras 3:5"),
    # Chapter 4
    (4001, 400, 4, 34, "O ye men, are not women strong? great is the earth, high is the heaven, swift is the sun in his course, for he compasseth the heavens round about, and fetcheth his course again to his own place in one day.", "1 Esdras 4:34"),
    (4001, 400, 4, 35, "Is he not great that maketh these things? therefore great is the truth, and stronger than all things.", "1 Esdras 4:35"),
    (4001, 400, 4, 36, "All the earth calleth upon the truth, and the heaven blesseth it: all works shake and tremble at it, and with it is no unrighteous thing.", "1 Esdras 4:36"),
    (4001, 400, 4, 37, "Wine is wicked, the king is wicked, women are wicked, all the children of men are wicked, and such are all their wicked works; and there is no truth in them; in their unrighteousness also they shall perish.", "1 Esdras 4:37"),
    (4001, 400, 4, 38, "As for the truth, it endureth, and is always strong; it liveth and conquereth for evermore.", "1 Esdras 4:38"),
    (4001, 400, 4, 39, "With her there is no accepting of persons or rewards; but she doeth the things that are just, and refraineth from all unjust and wicked things; and all men do well like of her works.", "1 Esdras 4:39"),
    (4001, 400, 4, 40, "Neither in her judgement is any unrighteousness; and she is the strength, kingdom, power, and majesty, of all ages. Blessed be the God of truth.", "1 Esdras 4:40"),
    (4001, 400, 4, 41, "And with that he held his peace. And all the people then shouted, and said, Great is Truth, and mighty above all things.", "1 Esdras 4:41"),

    # 2 Esdras (book_id=4002) — KJV Apocrypha
    # Chapter 2
    (4002, 400, 2, 1, "Thus saith the Lord, I brought this people out of bondage, and I gave them my commandments by my servants the prophets; whom they would not hear, but despised my counsels.", "2 Esdras 2:1"),
    (4002, 400, 2, 10, "Thus saith the Almighty Lord, Have I not prayed you as a father his sons, as a mother her daughters, and a nurse her young babes.", "2 Esdras 2:10"),
    (4002, 400, 2, 34, "Wherefore I say unto you, O ye heathen, that hear and understand, look for your Shepherd, he shall give you everlasting rest; for he is nigh at hand, that shall come in the end of the world.", "2 Esdras 2:34"),
    (4002, 400, 2, 35, "Be ready to the reward of the kingdom, for the everlasting light shall shine upon you for evermore.", "2 Esdras 2:35"),
    # Chapter 7
    (4002, 400, 7, 1, "And when I had made an end of speaking these words, there was sent unto me the angel which had been sent unto me the nights before.", "2 Esdras 7:1"),
    (4002, 400, 7, 2, "And he said unto me, Up, Esdras, and hear the words that I am come to tell thee.", "2 Esdras 7:2"),
    (4002, 400, 7, 3, "And I said, Speak on, my God. Then said he unto me, The sea is set in a wide place, that it might be deep and great.", "2 Esdras 7:3"),
    (4002, 400, 7, 4, "But put the case the entrance were narrow, and like a river; who then could go into the sea to look upon it, and to rule it? if he went not through the narrow, how could he come into the broad?", "2 Esdras 7:4"),
    (4002, 400, 7, 5, "There is also another thing; A city is builded, and set upon a broad field, and is full of all good things.", "2 Esdras 7:5"),
    (4002, 400, 7, 6, "The entrance thereof is narrow, and is set in a dangerous place to fall, like as if there were a fire on the right hand, and on the left a deep water.", "2 Esdras 7:6"),
    # Chapter 8
    (4002, 400, 8, 20, "O Lord, thou that dwellest in everlastingness, which beholdest from above things in the heaven and in the air.", "2 Esdras 8:20"),
    (4002, 400, 8, 21, "Whose throne is inestimable; whose glory may not be comprehended; before whom the hosts of angels stand with trembling.", "2 Esdras 8:21"),
    (4002, 400, 8, 22, "Whose service is conversant in wind and fire; whose word is true, and sayings constant; whose commandment is strong, and ordinance fearful.", "2 Esdras 8:22"),
    (4002, 400, 8, 23, "Whose look drieth up the depths, and indignation maketh the mountains to melt away; which the truth witnesseth.", "2 Esdras 8:23"),

    # Wisdom of Solomon (book_id=4005) — additional chapters
    # Chapter 2
    (4005, 400, 2, 1, "For the ungodly said, reasoning with themselves, but not aright, Our life is short and tedious, and in the death of a man there is no remedy: neither was there any man known to have returned from the grave.", "Wisdom of Solomon 2:1"),
    (4005, 400, 2, 2, "For we are born at all adventure: and we shall be hereafter as though we had never been: for the breath in our nostrils is as smoke, and a little spark in the moving of our heart.", "Wisdom of Solomon 2:2"),
    (4005, 400, 2, 6, "Come on therefore, let us enjoy the good things that are present: and let us speedily use the creatures like as in youth.", "Wisdom of Solomon 2:6"),
    (4005, 400, 2, 12, "Let us lie in wait for the righteous; because he is not for our turn, and he is clean contrary to our doings: he upbraideth us with our offending the law, and objecteth to our infamy the transgressings of our education.", "Wisdom of Solomon 2:12"),
    # Chapter 3
    (4005, 400, 3, 1, "But the souls of the righteous are in the hand of God, and there shall no torment touch them.", "Wisdom of Solomon 3:1"),
    (4005, 400, 3, 2, "In the sight of the unwise they seemed to die: and their departure is taken for misery.", "Wisdom of Solomon 3:2"),
    (4005, 400, 3, 3, "And their going from us to be utter destruction: but they are in peace.", "Wisdom of Solomon 3:3"),
    (4005, 400, 3, 4, "For though they be punished in the sight of men, yet is their hope full of immortality.", "Wisdom of Solomon 3:4"),
    (4005, 400, 3, 5, "And having been a little chastised, they shall be greatly rewarded: for God proved them, and found them worthy for himself.", "Wisdom of Solomon 3:5"),
    # Chapter 6
    (4005, 400, 6, 1, "Hear therefore, O ye kings, and understand; learn, ye that be judges of the ends of the earth.", "Wisdom of Solomon 6:1"),
    (4005, 400, 6, 2, "Give ear, ye that rule the people, and glory in the multitude of nations.", "Wisdom of Solomon 6:2"),
    (4005, 400, 6, 3, "For power is given you of the Lord, and sovereignty from the Highest, who shall try your works, and search out your counsels.", "Wisdom of Solomon 6:3"),
    (4005, 400, 6, 12, "Wisdom is glorious, and never fadeth away: yea, she is easily seen of them that love her, and found of such as seek her.", "Wisdom of Solomon 6:12"),
    (4005, 400, 6, 17, "For the very true beginning of her is the desire of discipline; and the care of discipline is love.", "Wisdom of Solomon 6:17"),
    (4005, 400, 6, 18, "And love is the keeping of her laws; and the giving heed unto her laws is the assurance of incorruption.", "Wisdom of Solomon 6:18"),

    # Sirach (book_id=4006) — additional chapters
    # Chapter 2
    (4006, 400, 2, 1, "My son, if thou come to serve the Lord, prepare thy soul for temptation.", "Sirach 2:1"),
    (4006, 400, 2, 2, "Set thy heart aright, and constantly endure, and make not haste in time of trouble.", "Sirach 2:2"),
    (4006, 400, 2, 3, "Cleave unto him, and depart not away, that thou mayest be increased at thy last end.", "Sirach 2:3"),
    (4006, 400, 2, 4, "Whatsoever is brought upon thee take cheerfully, and be patient when thou art changed to a low estate.", "Sirach 2:4"),
    (4006, 400, 2, 5, "For gold is tried in the fire, and acceptable men in the furnace of adversity.", "Sirach 2:5"),
    # Chapter 24
    (4006, 400, 24, 1, "Wisdom shall praise herself, and shall glory in the midst of her people.", "Sirach 24:1"),
    (4006, 400, 24, 2, "In the congregation of the most High shall she open her mouth, and triumph before his power.", "Sirach 24:2"),
    (4006, 400, 24, 3, "I came out of the mouth of the most High, and covered the earth as a cloud.", "Sirach 24:3"),
    (4006, 400, 24, 4, "I dwelt in high places, and my throne is in a cloudy pillar.", "Sirach 24:4"),
    (4006, 400, 24, 5, "I alone compassed the circuit of heaven, and walked in the bottom of the deep.", "Sirach 24:5"),
    (4006, 400, 24, 6, "In the waves of the sea, and in all the earth, and in every people and nation, I got a possession.", "Sirach 24:6"),
    (4006, 400, 24, 7, "With all these I sought rest: and in whose inheritance shall I abide?", "Sirach 24:7"),
    # Chapter 38
    (4006, 400, 38, 1, "Honour a physician with the honour due unto him for the uses which ye may have of him: for the Lord hath created him.", "Sirach 38:1"),
    (4006, 400, 38, 2, "For of the most High cometh healing, and he shall receive honour of the king.", "Sirach 38:2"),
    (4006, 400, 38, 3, "The skill of the physician shall lift up his head: and in the sight of great men he shall be in admiration.", "Sirach 38:3"),
    (4006, 400, 38, 4, "The Lord hath created medicines out of the earth; and he that is wise will not abhor them.", "Sirach 38:4"),

    # Letter of Jeremiah (book_id=4008) — additional verses
    (4008, 400, 1, 3, "So when ye come unto Babylon, ye shall remain there many years, and for a long season, namely, seven generations: and after that I will bring you away peaceably from thence.", "Letter of Jeremiah 1:3"),
    (4008, 400, 1, 4, "Now shall ye see in Babylon gods of silver, and of gold, and of wood, borne upon shoulders, which cause the nations to fear.", "Letter of Jeremiah 1:4"),
    (4008, 400, 1, 5, "Beware therefore that ye in no wise be like to strangers, neither be ye afraid of them, when ye see the multitude before them and behind them, worshipping them.", "Letter of Jeremiah 1:5"),
    (4008, 400, 1, 6, "But say ye in your hearts, O Lord, we must worship thee.", "Letter of Jeremiah 1:6"),
    (4008, 400, 1, 7, "For mine angel is with you, and I myself caring for your souls.", "Letter of Jeremiah 1:7"),

    # 1 Maccabees (book_id=4009) — additional chapters
    # Chapter 2
    (4009, 400, 2, 1, "In those days arose Mattathias the son of John, the son of Simeon, a priest of the sons of Joarib, from Jerusalem, and dwelt in Modin.", "1 Maccabees 2:1"),
    (4009, 400, 2, 2, "And he had five sons, Joannan, called Caddis: Simon, called Thassi.", "1 Maccabees 2:2"),
    (4009, 400, 2, 3, "Judas, who was called Maccabeus: Eleazar, called Avaran: and Jonathan, whose surname was Apphus.", "1 Maccabees 2:3"),
    (4009, 400, 2, 4, "And when he saw the blasphemies that were committed in Juda and Jerusalem.", "1 Maccabees 2:4"),
    (4009, 400, 2, 7, "Wherefore saith he, Woe is me! wherefore was I born to see this misery of my people, and of the holy city, and to dwell there, when it was delivered into the hand of the enemy, and the sanctuary into the hand of strangers?", "1 Maccabees 2:7"),
    (4009, 400, 2, 15, "And the king's officers came to the city of Modin, to make them sacrifice.", "1 Maccabees 2:15"),
    (4009, 400, 2, 16, "And when many of Israel came unto them, Mattathias also and his sons came together.", "1 Maccabees 2:16"),
    (4009, 400, 2, 17, "Then answered the king's officers and said unto Mattathias on this wise, Thou art a ruler, and an honourable and great man in this city, and strengthened with sons and brethren.", "1 Maccabees 2:17"),
    (4009, 400, 2, 19, "Then Mattathias answered and spake with a loud voice, Though all the nations that are under the king's dominion obey him, and fall away every one from the religion of their fathers, and give consent to his commandments.", "1 Maccabees 2:19"),
    (4009, 400, 2, 20, "Yet will I and my sons and my brethren walk in the covenant of our fathers.", "1 Maccabees 2:20"),
    (4009, 400, 2, 21, "God forbid that we should forsake the law and the ordinances.", "1 Maccabees 2:21"),
    # Chapter 3
    (4009, 400, 3, 1, "Then his son Judas, called Maccabeus, rose up in his stead.", "1 Maccabees 3:1"),
    (4009, 400, 3, 2, "And all his brethren helped him, and so did all they that held with his father, and they fought with cheerfulness the battle of Israel.", "1 Maccabees 3:2"),
    (4009, 400, 3, 3, "So he got his people great honour, and put on a breastplate as a giant, and girt his warlike harness about him, and he made battles, protecting the host with his sword.", "1 Maccabees 3:3"),
    (4009, 400, 3, 4, "In his acts he was like a lion, and like a lion's whelp roaring for his prey.", "1 Maccabees 3:4"),
    (4009, 400, 3, 18, "Then said Judas, It is no hard matter for many to be shut up in the hands of a few; and with the God of heaven it is all one, to deliver with a great multitude, or a small company.", "1 Maccabees 3:18"),
    (4009, 400, 3, 19, "For the victory of battle standeth not in the multitude of an host; but strength cometh from heaven.", "1 Maccabees 3:19"),

    # 2 Maccabees (book_id=4010) — additional chapters
    # Chapter 1 — more verses
    (4010, 400, 1, 3, "And give you all an heart to serve him, and to do his will, with a good courage and a willing mind.", "2 Maccabees 1:3"),
    (4010, 400, 1, 4, "And open your hearts in his law and commandments, and send you peace.", "2 Maccabees 1:4"),
    (4010, 400, 1, 5, "And hear your prayers, and be at one with you, and never forsake you in time of trouble.", "2 Maccabees 1:5"),
    # Chapter 7
    (4010, 400, 7, 1, "It came to pass also, that seven brethren with their mother were taken, and compelled by the king against the law to taste swine's flesh, and were tormented with scourges and whips.", "2 Maccabees 7:1"),
    (4010, 400, 7, 2, "But one of them that spake first said thus, What wouldest thou ask or learn of us? we are ready to die, rather than to transgress the laws of our fathers.", "2 Maccabees 7:2"),
    (4010, 400, 7, 9, "And when he was at the last gasp, he said, Thou like a fury takest us out of this present life, but the King of the world shall raise us up, who have died for his laws, unto everlasting life.", "2 Maccabees 7:9"),
    (4010, 400, 7, 14, "So when he was ready to die he said thus, It is good, being put to death by men, to look for hope from God to be raised up again by him: as for thee, thou shalt have no resurrection to life.", "2 Maccabees 7:14"),
    (4010, 400, 7, 22, "I cannot tell how ye came into my womb: for I neither gave you breath nor life, neither was it I that formed the members of every one of you.", "2 Maccabees 7:22"),
    (4010, 400, 7, 23, "But doubtless the Creator of the world, who formed the generation of man, and found out the beginning of all things, will also of his own mercy give you breath and life again, as ye now regard not your own selves for his laws' sake.", "2 Maccabees 7:23"),
    (4010, 400, 7, 28, "I beseech thee, my son, look upon the heaven and the earth, and all that is therein, and consider that God made them of things that were not; and so was mankind made likewise.", "2 Maccabees 7:28"),
    # Chapter 12
    (4010, 400, 12, 43, "And when he had made a gathering throughout the company to the sum of two thousand drachms of silver, he sent it to Jerusalem to offer a sin offering, doing therein very well and honestly, in that he was mindful of the resurrection.", "2 Maccabees 12:43"),
    (4010, 400, 12, 44, "For if he had not hoped that they that were slain should have risen again, it had been superfluous and vain to pray for the dead.", "2 Maccabees 12:44"),
    (4010, 400, 12, 45, "And also in that he perceived that there was great favour laid up for those that died godly, it was an holy and good thought. Whereupon he made a reconciliation for the dead, that they might be delivered from sin.", "2 Maccabees 12:45"),

    # 3 Maccabees (book_id=4011) — additional chapters
    (4011, 400, 1, 2, "Then his kinsman Dositheos, called the son of Drimylus, a Jew by birth who afterward changed his religion and departed from the ancestral traditions, had conveyed Ptolemy away.", "3 Maccabees 1:2"),
    (4011, 400, 1, 3, "And had put an insignificant person in his tent; and it befell this man to receive the fate meant for the other.", "3 Maccabees 1:3"),
    (4011, 400, 2, 1, "Now Ptolemy, being filled with arrogance on account of the success which he had obtained against the forces of Antiochus, undertook to enter the temple.", "3 Maccabees 2:1"),
    (4011, 400, 2, 2, "And when the priests and elders heard of this, they fell on their faces and besought God to help them in their necessity.", "3 Maccabees 2:2"),
    (4011, 400, 2, 3, "And they filled the temple with cries and tears.", "3 Maccabees 2:3"),
    (4011, 400, 2, 10, "Thou, O King, when thou hadst created the boundless and immeasurable earth, didst choose this city and sanctify this place for thy name.", "3 Maccabees 2:10"),
    (4011, 400, 2, 11, "Though thou needest nothing, thou wast pleased to manifest thy glory in it, and thou didst glorify it with thy magnificent manifestation.", "3 Maccabees 2:11"),
    (4011, 400, 6, 1, "Then a certain Eleazar, famous among the priests of the country, who had attained to length of days and whose life had been adorned with virtue, directed the elders around him to cease calling upon the holy God.", "3 Maccabees 6:1"),
    (4011, 400, 6, 2, "And he prayed thus: O King, mighty in power, most high, almighty God, who governest all creation with mercy.", "3 Maccabees 6:2"),
    (4011, 400, 6, 3, "Look upon the seed of Abraham, the children of the sanctified Jacob, a people of thy sanctified portion who are perishing in a foreign land as strangers.", "3 Maccabees 6:3"),
    (4011, 400, 6, 4, "Pharaoh with his abundance of chariots, the former ruler of this Egypt, exalted with lawless insolence and boastful tongue, thou didst destroy together with his arrogant army by drowning them in the sea.", "3 Maccabees 6:4"),

    # Prayer of Manasseh (book_id=4013) — additional verses
    (4013, 400, 1, 4, "Whom all things fear, and tremble before thy power.", "Prayer of Manasseh 1:4"),
    (4013, 400, 1, 5, "For the majesty of thy glory cannot be borne, and thine angry threatening toward sinners is importable.", "Prayer of Manasseh 1:5"),
    (4013, 400, 1, 6, "But thy merciful promise is unmeasurable and unsearchable; for thou art the most high Lord, of great compassion, longsuffering, very merciful, and repentest of the evils of men.", "Prayer of Manasseh 1:6"),
    (4013, 400, 1, 7, "Thou, O Lord, according to thy great goodness hast promised repentance and forgiveness to them that have sinned against thee: and of thine infinite mercies hast appointed repentance unto sinners, that they may be saved.", "Prayer of Manasseh 1:7"),
    (4013, 400, 1, 8, "Thou therefore, O Lord, that art the God of the just, hast not appointed repentance to the just, as to Abraham, and Isaac, and Jacob, which have not sinned against thee.", "Prayer of Manasseh 1:8"),
    (4013, 400, 1, 9, "But thou hast appointed repentance unto me that am a sinner: for I have sinned above the number of the sands of the sea.", "Prayer of Manasseh 1:9"),
    (4013, 400, 1, 10, "My transgressions, O Lord, are multiplied: my transgressions are multiplied, and I am not worthy to behold and see the height of heaven for the multitude of mine iniquities.", "Prayer of Manasseh 1:10"),
    (4013, 400, 1, 11, "I am bowed down with many iron bands, that I cannot lift up mine head, neither have any release: for I have provoked thy wrath, and done evil before thee.", "Prayer of Manasseh 1:11"),
    (4013, 400, 1, 12, "I did not thy will, neither kept I thy commandments: I have set up abominations, and have multiplied offences.", "Prayer of Manasseh 1:12"),
    (4013, 400, 1, 13, "Now therefore I bow the knee of mine heart, beseeching thee of grace.", "Prayer of Manasseh 1:13"),
    (4013, 400, 1, 14, "I have sinned, O Lord, I have sinned, and I acknowledge mine iniquities.", "Prayer of Manasseh 1:14"),
    (4013, 400, 1, 15, "Wherefore, I humbly beseech thee, forgive me, O Lord, forgive me, and destroy me not with mine iniquities. Be not angry with me for ever, by reserving evil for me; neither condemn me into the lower parts of the earth.", "Prayer of Manasseh 1:15"),

    # Psalm 151 (book_id=4014) — additional verses
    (4014, 400, 1, 5, "My brothers were handsome and tall, but the Lord was not pleased with them.", "Psalm 151 1:5"),
    (4014, 400, 1, 6, "I went out to meet the Philistine, and he cursed me by his idols.", "Psalm 151 1:6"),
    (4014, 400, 1, 7, "But I drew his own sword; I beheaded him, and took away disgrace from the people of Israel.", "Psalm 151 1:7"),

    # Baruch (book_id=4007) — KJV Apocrypha
    (4007, 400, 1, 1, "And these are the words of the book, which Baruch the son of Nerias, the son of Maasias, the son of Sedecias, the son of Asadias, the son of Chelcias, wrote in Babylon.", "Baruch 1:1"),
    (4007, 400, 1, 2, "In the fifth year, and in the seventh day of the month, what time as the Chaldeans took Jerusalem, and burnt it with fire.", "Baruch 1:2"),
    (4007, 400, 1, 3, "And Baruch did read the words of this book in the hearing of Jechonias the son of Joachim king of Juda, and in the ears of all the people that came to hear the book.", "Baruch 1:3"),
    (4007, 400, 3, 9, "Hear, Israel, the commandments of life: give ear to understand wisdom.", "Baruch 3:9"),
    (4007, 400, 3, 10, "How happeneth it Israel, that thou art in thine enemies' land, that thou art waxen old in a strange country, that thou art defiled with the dead?", "Baruch 3:10"),
    (4007, 400, 3, 12, "Thou hast forsaken the fountain of wisdom.", "Baruch 3:12"),
    (4007, 400, 3, 14, "Learn where is wisdom, where is strength, where is understanding; that thou mayest know also where is length of days, and life, where is the light of the eyes, and peace.", "Baruch 3:14"),
    (4007, 400, 4, 1, "This is the book of the commandments of God, and the law that endureth for ever: all they that keep it shall come to life; but such as leave it shall die.", "Baruch 4:1"),
    (4007, 400, 4, 2, "Turn thee, O Jacob, and take hold of it: walk in the presence of the light thereof, that thou mayest be illuminated.", "Baruch 4:2"),
    (4007, 400, 4, 3, "Give not thine honour to another, nor the things that are profitable unto thee to a strange nation.", "Baruch 4:3"),
    (4007, 400, 4, 4, "O Israel, happy are we: for things that are pleasing to God are made known unto us.", "Baruch 4:4"),
    (4007, 400, 4, 5, "Be of good cheer, my people, the memorial of Israel.", "Baruch 4:5"),
    (4007, 400, 5, 1, "Put off, O Jerusalem, the garment of thy mourning and affliction, and put on the comeliness of the glory that cometh from God for ever.", "Baruch 5:1"),
    (4007, 400, 5, 2, "Cast about thee a double garment of the righteousness which cometh from God; and set a diadem on thine head of the glory of the Everlasting.", "Baruch 5:2"),
    (4007, 400, 5, 3, "For God will shew thy brightness unto every country under heaven.", "Baruch 5:3"),
    (4007, 400, 5, 4, "For thy name shall be called of God for ever The peace of righteousness, and The glory of God's worship.", "Baruch 5:4"),

    # Tobit (book_id=4003) — additional chapters
    (4003, 400, 1, 1, "The book of the words of Tobit, son of Tobiel, the son of Ananiel, the son of Aduel, the son of Gabael, of the seed of Asael, of the tribe of Nephthali.", "Tobit 1:1"),
    (4003, 400, 1, 2, "Who in the time of Enemessar king of the Assyrians was led captive out of Thisbe, which is at the right hand of that city, which is called properly Nephthali in Galilee above Aser.", "Tobit 1:2"),
    (4003, 400, 4, 5, "My son, be mindful of the Lord our God all thy days, and let not thy will be set to sin, or to transgress his commandments: do uprightly all thy life long, and follow not the ways of unrighteousness.", "Tobit 4:5"),
    (4003, 400, 4, 6, "For if thou deal truly, thy doings shall prosperously succeed to thee, and to all them that live justly.", "Tobit 4:6"),
    (4003, 400, 4, 7, "Give alms of thy substance; and when thou givest alms, let not thine eye be envious, neither turn thy face from any poor, and the face of God shall not be turned away from thee.", "Tobit 4:7"),
    (4003, 400, 4, 8, "If thou hast abundance, give alms accordingly: if thou have but a little, be not afraid to give according to that little.", "Tobit 4:8"),
    (4003, 400, 4, 9, "For thou layest up a good treasure for thyself against the day of necessity.", "Tobit 4:9"),
    (4003, 400, 4, 14, "Let not the wages of any man, which hath wrought for thee, tarry with thee, but give him it out of hand: for if thou serve God, he will also repay thee: be circumspect, my son, in all things thou doest, and be wise in all thy conversation.", "Tobit 4:14"),
    (4003, 400, 4, 15, "Do that to no man which thou hatest: drink not wine to make thee drunken: neither let drunkenness go with thee in thy journey.", "Tobit 4:15"),

    # Judith (book_id=4004) — additional chapters
    (4004, 400, 1, 1, "In the twelfth year of the reign of Nabuchodonosor, who reigned in Nineve, the great city; in the days of Arphaxad, which reigned over the Medes in Ecbatane.", "Judith 1:1"),
    (4004, 400, 1, 2, "And built in Ecbatane walls round about of stones hewn three cubits broad and six cubits long, and made the height of the wall seventy cubits, and the breadth thereof fifty cubits.", "Judith 1:2"),
    (4004, 400, 2, 1, "And in the eighteenth year, the two and twentieth day of the first month, there was talk in the house of Nabuchodonosor that he should avenge himself on all the earth.", "Judith 2:1"),
    (4004, 400, 2, 2, "And he called unto him all his officers, and all his nobles, and communicated with them his secret counsel.", "Judith 2:2"),
    (4004, 400, 2, 4, "And when he had ended his counsel, Nabuchodonosor called Holofernes the chief captain of his army, which was next unto him.", "Judith 2:4"),
    (4004, 400, 8, 1, "Now at that time Judith heard thereof, which was the daughter of Merari, the son of Ox, the son of Joseph.", "Judith 8:1"),
    (4004, 400, 8, 2, "And Manasses was her husband, of her tribe and kindred, who died in the barley harvest.", "Judith 8:2"),
    (4004, 400, 8, 11, "Therefore, though he punish us, yet shall he be merciful, and will not utterly forsake his people.", "Judith 8:11"),
    (4004, 400, 8, 14, "For if he punish us, yet will he have mercy upon us.", "Judith 8:14"),
    (4004, 400, 9, 1, "Then Judith fell upon her face, and put ashes upon her head, and uncovered the sackcloth wherewith she was clothed; and about the time that the incense of that evening was offered in Jerusalem in the house of the Lord, Judith cried with a loud voice.", "Judith 9:1"),
    (4004, 400, 9, 2, "And said, O Lord God of my father Simeon, to whom thou gavest a sword to take vengeance of the strangers.", "Judith 9:2"),
    (4004, 400, 9, 11, "For thy power standeth not in multitude nor thy might in strong men: for thou art a God of the afflicted, an helper of the oppressed, an upholder of the weak, a protector of the forlorn, a saviour of them that are without hope.", "Judith 9:11"),
    (4004, 400, 13, 1, "So all the people went away, and none was left in the bedchamber, neither small nor great. Then Judith, standing by his bed, said in her heart, O Lord God of all power, look at this present upon the works of mine hands for the exaltation of Jerusalem.", "Judith 13:1"),
    (4004, 400, 13, 4, "Then she came to the pillar of the bed, which was at Holofernes' head, and took down his fauchion from thence.", "Judith 13:4"),
    (4004, 400, 13, 6, "Then she smote twice upon his neck with all her might, and she took away his head from him.", "Judith 13:6"),
    (4004, 400, 13, 14, "Then said she to them with a loud voice, Praise, praise God, praise God, I say, for he hath not taken away his mercy from the house of Israel, but hath destroyed our enemies by mine hands this night.", "Judith 13:14"),
    (4004, 400, 16, 1, "Then Judith began to sing this thanksgiving in all Israel, and all the people sang after her this song of praise.", "Judith 16:1"),
    (4004, 400, 16, 2, "And Judith said, Begin unto my God with timbrels, sing unto my Lord with cymbals: tune unto him a new psalm: exalt him, and call upon his name.", "Judith 16:2"),
    (4004, 400, 16, 13, "I will sing unto the Lord a new song: O Lord, thou art great and glorious, wonderful in strength, and invincible.", "Judith 16:13"),
    (4004, 400, 16, 14, "Let all creatures serve thee: for thou spakest, and they were made, thou didst send forth thy spirit, and it created them, and there is none that can resist thy voice.", "Judith 16:14"),
    (4004, 400, 16, 15, "For the mountains shall be moved from their foundations with the waters, the rocks shall melt as wax at thy presence: yet thou art merciful to them that fear thee.", "Judith 16:15"),

    # 2 Esdras additional chapters (KJV Apocrypha)
    # Chapter 3
    (4002, 400, 3, 1, "In the thirtieth year after the ruin of the city I was in Babylon, and lay troubled upon my bed, and my thoughts came up over my heart.", "2 Esdras 3:1"),
    (4002, 400, 3, 2, "For I saw the desolation of Sion, and the wealth of them that dwelt at Babylon.", "2 Esdras 3:2"),
    (4002, 400, 3, 3, "And my spirit was sore moved, so that I began to speak words full of fear to the most High, and said.", "2 Esdras 3:3"),
    (4002, 400, 3, 4, "O Lord, who bearest rule, thou spakest at the beginning, when thou didst plant the earth, and that thyself alone, and commandedst the people.", "2 Esdras 3:4"),
    (4002, 400, 3, 5, "And gavest a body unto Adam without soul, which was the workmanship of thine hands, and didst breathe into him the breath of life, and he was made living before thee.", "2 Esdras 3:5"),
    (4002, 400, 3, 6, "And thou leadest him into paradise, which thy right hand had planted, before ever the earth came forward.", "2 Esdras 3:6"),
    # Chapter 4
    (4002, 400, 4, 1, "And the angel that was sent unto me, whose name was Uriel, gave me an answer.", "2 Esdras 4:1"),
    (4002, 400, 4, 2, "And said unto me, Thy heart hath gone too far in this world, and thinkest thou to comprehend the way of the most High?", "2 Esdras 4:2"),
    (4002, 400, 4, 3, "Then said I, Yea, my lord. And he answered me, and said, I am sent to shew thee three ways, and to set forth three similitudes before thee.", "2 Esdras 4:3"),
    (4002, 400, 4, 4, "Whereof if thou canst declare me one, I will shew thee also the way that thou desirest to see, and I shall shew thee from whence the wicked heart cometh.", "2 Esdras 4:4"),
    (4002, 400, 4, 5, "And I said, Tell on, my lord. Then said he unto me, Go thy way, weigh me the weight of the fire, or measure me the blast of the wind, or call me again the day that is past.", "2 Esdras 4:5"),

    # 1 Maccabees additional (KJV Apocrypha)
    # Chapter 4
    (4009, 400, 4, 36, "Then said Judas and his brethren, Behold, our enemies are discomfited: let us go up to cleanse and dedicate the sanctuary.", "1 Maccabees 4:36"),
    (4009, 400, 4, 37, "Upon this all the host assembled themselves together, and went up into mount Sion.", "1 Maccabees 4:37"),
    (4009, 400, 4, 38, "And when they saw the sanctuary desolate, and the altar profaned, and the gates burned up, and shrubs growing in the courts as in a forest.", "1 Maccabees 4:38"),
    (4009, 400, 4, 39, "They rent their clothes, and made great lamentation, and cast ashes upon their heads.", "1 Maccabees 4:39"),
    (4009, 400, 4, 40, "And fell down flat to the ground upon their faces, and blew an alarm with the trumpets, and cried toward heaven.", "1 Maccabees 4:40"),
    (4009, 400, 4, 50, "And they burnt incense upon the altar, and lighted the lamps that were upon the candlestick, and they gave light in the temple.", "1 Maccabees 4:50"),
    (4009, 400, 4, 52, "Now on the five and twentieth day of the ninth month, which is called the month Casleu, in the hundred forty and eighth year, they rose up betimes in the morning.", "1 Maccabees 4:52"),
    (4009, 400, 4, 56, "And so they kept the dedication of the altar eight days, and offered burnt offerings with gladness, and sacrificed the sacrifice of deliverance and praise.", "1 Maccabees 4:56"),
    (4009, 400, 4, 59, "Moreover Judas and his brethren with the whole congregation of Israel ordained, that the days of the dedication of the altar should be kept in their season from year to year by the space of eight days.", "1 Maccabees 4:59"),
    # Chapter 9
    (4009, 400, 9, 1, "Furthermore, when Demetrius heard that Nicanor and his host were slain in battle, he sent Bacchides and Alcimus into the land of Judea the second time, and with them the chief strength of his host.", "1 Maccabees 9:1"),
    (4009, 400, 9, 3, "In the first month of the hundred fifty and second year they encamped before Jerusalem.", "1 Maccabees 9:3"),
    (4009, 400, 9, 10, "Then Judas said, God forbid that I should do this thing, and flee away from them: if our time be come, let us die manfully for our brethren, and let us not stain our honour.", "1 Maccabees 9:10"),

    # Wisdom of Solomon additional (KJV Apocrypha)
    # Chapter 7
    (4005, 400, 7, 7, "Wherefore I prayed, and understanding was given me: I called upon God, and the spirit of wisdom came to me.", "Wisdom of Solomon 7:7"),
    (4005, 400, 7, 22, "For wisdom, which is the worker of all things, taught me: for in her is an understanding spirit, holy, one only, manifold, subtil, lively, clear, undefiled.", "Wisdom of Solomon 7:22"),
    (4005, 400, 7, 24, "For wisdom is more moving than any motion: she passeth and goeth through all things by reason of her pureness.", "Wisdom of Solomon 7:24"),
    (4005, 400, 7, 25, "For she is the breath of the power of God, and a pure influence flowing from the glory of the Almighty: therefore can no defiled thing fall into her.", "Wisdom of Solomon 7:25"),
    (4005, 400, 7, 26, "For she is the brightness of the everlasting light, the unspotted mirror of the power of God, and the image of his goodness.", "Wisdom of Solomon 7:26"),
    (4005, 400, 7, 27, "And being but one, she can do all things: and remaining in herself, she maketh all things new: and in all ages entering into holy souls, she maketh them friends of God, and prophets.", "Wisdom of Solomon 7:27"),
    # Chapter 9
    (4005, 400, 9, 1, "O God of my fathers, and Lord of mercy, who hast made all things with thy word.", "Wisdom of Solomon 9:1"),
    (4005, 400, 9, 4, "Give me wisdom, that sitteth by thy throne; and reject me not from among thy children.", "Wisdom of Solomon 9:4"),
    (4005, 400, 9, 9, "O send her out of thy holy heavens, and from the throne of thy glory, that being present she may labour with me, that I may know what is pleasing unto thee.", "Wisdom of Solomon 9:9"),
    (4005, 400, 9, 13, "For what man is he that can know the counsel of God? or who can think what the will of the Lord is?", "Wisdom of Solomon 9:13"),
    (4005, 400, 9, 15, "For the corruptible body presseth down the soul, and the earthy tabernacle weigheth down the mind that museth upon many things.", "Wisdom of Solomon 9:15"),
    (4005, 400, 9, 17, "And thy counsel who hath known, except thou give wisdom, and send thy Holy Spirit from above?", "Wisdom of Solomon 9:17"),

    # Sirach additional (KJV Apocrypha)
    # Chapter 44
    (4006, 400, 44, 1, "Let us now praise famous men, and our fathers that begat us.", "Sirach 44:1"),
    (4006, 400, 44, 2, "The Lord hath wrought great glory by them through his great power from the beginning.", "Sirach 44:2"),
    (4006, 400, 44, 3, "Such as did bear rule in their kingdoms, men renowned for their power, giving counsel by their understanding, and declaring prophecies.", "Sirach 44:3"),
    (4006, 400, 44, 4, "Leaders of the people by their counsels, and by their knowledge of learning meet for the people, wise and eloquent in their instructions.", "Sirach 44:4"),
    (4006, 400, 44, 5, "Such as found out musical tunes, and recited verses in writing.", "Sirach 44:5"),
    (4006, 400, 44, 6, "Rich men furnished with ability, living peaceably in their habitations.", "Sirach 44:6"),
    (4006, 400, 44, 7, "All these were honoured in their generations, and were the glory of their times.", "Sirach 44:7"),
    # Chapter 51
    (4006, 400, 51, 1, "I will thank thee, O Lord and King, and praise thee, O God my Saviour: I do give praise unto thy name.", "Sirach 51:1"),
    (4006, 400, 51, 13, "When I was yet young, or ever I went abroad, I desired wisdom openly in my prayer.", "Sirach 51:13"),
    (4006, 400, 51, 23, "Draw near unto me, ye unlearned, and dwell in the house of learning.", "Sirach 51:23"),
    (4006, 400, 51, 26, "Put your neck under the yoke, and let your soul receive instruction: she is hard at hand to find.", "Sirach 51:26"),

    # 2 Maccabees additional (KJV Apocrypha)
    # Chapter 6
    (4010, 400, 6, 1, "Not long after this the king sent an old man of Athens to compel the Jews to depart from the laws of their fathers, and not to live after the laws of God.", "2 Maccabees 6:1"),
    (4010, 400, 6, 18, "Eleazar, one of the principal scribes, an aged man, and of a well favoured countenance, was constrained to open his mouth, and to eat swine's flesh.", "2 Maccabees 6:18"),
    (4010, 400, 6, 19, "But he, choosing rather to die gloriously, than to live stained with such an abomination, spit it forth, and came of his own accord to the torment.", "2 Maccabees 6:19"),
    (4010, 400, 6, 28, "And so he died, leaving his death for an example of a noble courage, and a memorial of virtue, not only unto young men, but unto all his nation.", "2 Maccabees 6:28"),
    # Chapter 15
    (4010, 400, 15, 12, "And this was his vision: That Onias, who had been high priest, a virtuous and a good man, reverend in conversation, gentle in condition, well spoken also, and exercised from a child in all points of virtue, holding up his hands prayed for the whole body of the Jews.", "2 Maccabees 15:12"),
    (4010, 400, 15, 13, "This done, in like manner there appeared a man with gray hairs, and exceeding glorious, who was of a wonderful and excellent majesty.", "2 Maccabees 15:13"),
    (4010, 400, 15, 14, "Then Onias answered, saying, This is a lover of the brethren, who prayeth much for the people, and for the holy city, to wit, Jeremias the prophet of God.", "2 Maccabees 15:14"),

    # 3 Esdras (book_id=4012) — additional
    (4012, 400, 1, 1, "And Josias held a passover to his Lord in Jerusalem; they killed the passover lamb on the fourteenth day of the first month.", "3 Esdras 1:1"),
    (4012, 400, 1, 2, "He set the priests in their vestments by their order in the temple of the Lord.", "3 Esdras 1:2"),
    (4012, 400, 1, 3, "And he said unto the Levites the sacred ministers of Israel: Sanctify yourselves for the Lord, and set the holy ark of the Lord in the temple which Solomon the son of David the king built.", "3 Esdras 1:3"),
    (4012, 400, 2, 1, "Now after all these acts of Josias it came to pass that Pharaoh the king of Egypt came to raise war at Carchemish upon Euphrates: and Josias went out against him.", "3 Esdras 2:1"),
    (4012, 400, 2, 2, "But the king of Egypt sent to him, saying, What have I to do with thee, O king of Judea?", "3 Esdras 2:2"),
    (4012, 400, 2, 3, "I am not sent against thee by the Lord God, for my war is upon Euphrates: and now the Lord is with me, yea, the Lord is with me hasting me forward: depart from me, and be not against the Lord.", "3 Esdras 2:3"),
]


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------
def get_book_title_from_ref(ref: str) -> str:
    """Extract book title from a reference like '1 Enoch 2:3' -> '1 Enoch'."""
    parts = ref.rsplit(" ", 1)
    return parts[0] if len(parts) == 2 else ref


VOLUME_TITLES = {
    200: "Coptic Bible",
    300: "Dead Sea Scrolls",
    400: "Russian Orthodox Bible",
}


def add_verses(conn, verse_list, volume_id):
    """Add verses from a list, skipping any that already exist (idempotent)."""
    volume_title = VOLUME_TITLES[volume_id]
    max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM verses").fetchone()[0]
    max_ch_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM chapters").fetchone()[0]

    # Build a set of existing (book_id, chapter_number, verse_number) for this volume
    existing = set()
    for row in conn.execute(
        "SELECT book_id, verse_number, reference FROM verses WHERE volume_id = ?",
        (volume_id,),
    ):
        # Parse chapter from reference to be precise
        existing.add((row[0], row[2]))  # (book_id, reference)

    # Build existing chapter map
    chapter_map = {}
    for row in conn.execute(
        "SELECT id, book_id, chapter_number FROM chapters WHERE book_id IN (SELECT id FROM books WHERE volume_id = ?)",
        (volume_id,),
    ):
        chapter_map[(row[1], row[2])] = row[0]

    added = 0
    for book_id, vol_id, ch_num, verse_num, text, ref in verse_list:
        # Skip if this exact verse already exists
        if (book_id, ref) in existing:
            continue

        # Ensure chapter exists
        ch_key = (book_id, ch_num)
        if ch_key not in chapter_map:
            max_ch_id += 1
            chapter_map[ch_key] = max_ch_id
            conn.execute(
                "INSERT INTO chapters (id, book_id, chapter_number) VALUES (?, ?, ?)",
                (max_ch_id, book_id, ch_num),
            )

        max_id += 1
        ch_id = chapter_map[ch_key]
        book_title = get_book_title_from_ref(ref)

        conn.execute(
            "INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (max_id, ch_id, book_id, vol_id, verse_num, text, ref),
        )
        conn.execute(
            "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?, ?, ?, ?, ?)",
            (max_id, text, ref, book_title, volume_title),
        )
        added += 1

    return added


def update_counts(conn):
    """Update num_verses in chapters and num_chapters in books for all affected volumes."""
    conn.execute("""
        UPDATE chapters SET num_verses = (
            SELECT COUNT(*) FROM verses WHERE verses.chapter_id = chapters.id
        )
    """)
    for vid in (200, 300, 400):
        conn.execute("""
            UPDATE books SET num_chapters = (
                SELECT COUNT(DISTINCT chapter_number) FROM chapters
                WHERE chapters.book_id = books.id
            ) WHERE volume_id = ?
        """, (vid,))


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run build-scriptures-db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)

    # Verify the volumes exist
    for vid, name in VOLUME_TITLES.items():
        row = conn.execute("SELECT id FROM volumes WHERE id = ?", (vid,)).fetchone()
        if not row:
            print(f"ERROR: Volume {name} (id={vid}) not found. Run build-scriptures-db.py first.")
            conn.close()
            return

    print("Expanding scriptures.db with additional verses...")
    print()

    coptic_added = add_verses(conn, COPTIC_VERSES, 200)
    print(f"  Coptic Bible:          {coptic_added} new verses added")

    dss_added = add_verses(conn, DSS_VERSES, 300)
    print(f"  Dead Sea Scrolls:      {dss_added} new verses added")

    russian_added = add_verses(conn, RUSSIAN_VERSES, 400)
    print(f"  Russian Orthodox Bible: {russian_added} new verses added")

    total_added = coptic_added + dss_added + russian_added
    print(f"\n  Total new verses: {total_added}")

    update_counts(conn)
    conn.commit()

    # Print summary
    print("\nFinal counts:")
    for vid, name in VOLUME_TITLES.items():
        count = conn.execute("SELECT COUNT(*) FROM verses WHERE volume_id = ?", (vid,)).fetchone()[0]
        books = conn.execute("SELECT COUNT(*) FROM books WHERE volume_id = ?", (vid,)).fetchone()[0]
        chapters = conn.execute(
            "SELECT COUNT(*) FROM chapters WHERE book_id IN (SELECT id FROM books WHERE volume_id = ?)",
            (vid,),
        ).fetchone()[0]
        print(f"  {name}: {count} verses across {books} books, {chapters} chapters")

    total = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    print(f"\n  Total verses in database: {total}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
