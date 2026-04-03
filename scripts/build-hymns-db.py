#!/usr/bin/env python3
"""Build hymn tables into existing scriptures.db for ARK.

Adds hymns, hymn_verses, and hymns_fts tables to the existing scriptures database.
Does NOT delete or rebuild the existing database — only adds hymn data.
"""

import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "scriptures", "scriptures.db")

HYMN_SCHEMA = """
CREATE TABLE IF NOT EXISTS hymns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hymn_number INTEGER,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    composer TEXT DEFAULT '',
    first_line TEXT DEFAULT '',
    is_public_domain BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS hymn_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hymn_id INTEGER REFERENCES hymns(id),
    verse_number INTEGER NOT NULL,
    verse_type TEXT DEFAULT 'verse',
    text TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS hymns_fts USING fts5(
    title, author, first_line, lyrics,
    content='',
    tokenize='porter'
);
"""

# --------------------------------------------------------------------------
# Full hymn data: (hymn_number, title, author, verses)
# verses is a list of (verse_number, verse_type, text)
# --------------------------------------------------------------------------

HYMNS_DATA = [
    (1, "The Morning Breaks", "Parley P. Pratt", [
        (1, "verse", "The morning breaks, the shadows flee; Lo, Zion's standard is unfurled! The dawning of a brighter day Majestic rises on the world."),
        (2, "verse", "The clouds of error disappear Before the rays of truth divine; The glory bursting from afar Wide o'er the nations soon will shine."),
        (3, "verse", "The Gentile fulness now comes in, And Israel's blessings are at hand. Lo, Judah's remnant, cleansed from sin, Shall in their promised Canaan stand."),
        (4, "verse", "Jehovah speaks! Let earth give ear, And Gentile nations turn and live. His mighty arm is making bare, His cov'nant people to receive."),
        (5, "verse", "Angels from heav'n and truth from earth Have met, and both have record borne; Thus Zion's light is bursting forth To bring her ransomed children home."),
    ]),
    (2, "The Spirit of God", "William W. Phelps", [
        (1, "verse", "The Spirit of God like a fire is burning! The latter-day glory begins to come forth; The visions and blessings of old are returning, And angels are coming to visit the earth."),
        (2, "chorus", "We'll sing and we'll shout with the armies of heaven, Hosanna, hosanna to God and the Lamb! Let glory to them in the highest be given, Henceforth and forever, Amen and amen!"),
        (3, "verse", "The Lord is extending the Saints' understanding, Restoring their judges and all as at first. The knowledge and power of God are expanding; The veil o'er the earth is beginning to burst."),
        (4, "verse", "We'll call in our solemn assemblies in spirit, To spread forth the kingdom of heaven abroad, That we through our faith may begin to inherit The visions and blessings and glories of God."),
        (5, "verse", "How blessed the day when the lamb and the lion Shall lie down together without any ire, And Ephraim be crowned with his blessing in Zion, As Jesus descends with his chariot of fire!"),
    ]),
    (3, "Now Let Us Rejoice", "William W. Phelps", [
        (1, "verse", "Now let us rejoice in the day of salvation. No longer as strangers on earth need we roam. Good tidings are sounding to us and each nation, And shortly the hour of redemption will come."),
        (2, "verse", "We'll love one another and never dissemble But cease to do evil and ever be one. And when the ungodly are fearing and tremble, We'll watch for the day when the Savior will come."),
        (3, "verse", "In faith we'll rely on the arm of Jehovah To guide thru these last days of trouble and gloom, And after the scourges and harvest are over, We'll rise with the just when the Savior doth come."),
    ]),
    (4, "Truth Eternal", "Parley P. Pratt", [
        (1, "verse", "Truth eternal, truth divine, In thine ancient fulness shine! Burst the fetters of the mind From the millions of mankind!"),
        (2, "verse", "Truth again restored to earth, Opened with a prophet's birth, Priest and king and judge of worth— Bring the knowledge of our God!"),
    ]),
    (5, "High on the Mountain Top", "Joel H. Johnson", [
        (1, "verse", "High on the mountain top A banner is unfurled. Ye nations, now look up; It waves to all the world."),
        (2, "verse", "For God remembers still His promise made of old That he on Zion's hill Truth's standard would unfold!"),
        (3, "verse", "His house shall there be reared, His glory to display, And people shall be heard In distant lands to say:"),
    ]),
    (6, "Redeemer of Israel", "William W. Phelps", [
        (1, "verse", "Redeemer of Israel, Our only delight, On whom for a blessing we call, Our shadow by day and our pillar by night, Our King, our Deliverer, our all!"),
        (2, "verse", "We know he is coming To gather his sheep And lead them to Zion in love, For he has commanded and certainly keep A place in his kingdom above."),
    ]),
    (7, "Israel, Israel, God Is Calling", "Richard Smyth", [
        (1, "verse", "Israel, Israel, God is calling, Calling thee from lands of woe. Babylon the great is falling; God shall all her tow'rs o'erthrow."),
        (2, "verse", "Come to Zion, come to Zion Ere his floods of anger flow. Come to Zion, come to Zion Ere his floods of anger flow."),
    ]),
    (8, "Awake and Arise", "Theodore E. Curtis", [
        (1, "verse", "Awake and arise, O ye slumbering nations! The heavens have opened their portals again. The last and the greatest of all dispensations Has burst like a dawn o'er the children of men!"),
    ]),
    (9, "Come, Rejoice", "Tracy Y. Cannon", [
        (1, "verse", "Come, rejoice, the King of glory Speaks to men his truths again, Sending forth his proclamation To the nations once again."),
    ]),
    (10, "Come, Sing to the Lord", "Gerrit de Jong Jr.", [
        (1, "verse", "Come, sing to the Lord, his name to praise, Who formed the earth in latter days; His hand has led his people on And placed them where his light has shone."),
    ]),
    (11, "What Was Witnessed in the Heavens?", "John S. Davis", [
        (1, "verse", "What was witnessed in the heavens? Why, an angel, earthward bound. Had he something with him bringing? Yes, the gospel, joyful sound!"),
    ]),
    (12, "'Twas Witnessed in the Morning Sky", "Anonymous", [
        (1, "verse", "'Twas witnessed in the morning sky, A token from above, That God in mercy had drawn nigh To prove his tender love."),
    ]),
    (13, "An Angel from on High", "Parley P. Pratt", [
        (1, "verse", "An angel from on high The long, long silence broke; Descending from the sky, These gracious words he spoke:"),
        (2, "verse", "Lo! in Cumorah's lonely hill A sacred record lies concealed. Lo! in Cumorah's lonely hill A sacred record lies concealed."),
    ]),
    (14, "Sweet Is the Peace the Gospel Brings", "Mary Ann Morton", [
        (1, "verse", "Sweet is the peace the gospel brings To those who truly seek the truth. And in the word of God we find The joy that satisfies our youth."),
    ]),
    (15, "I Saw a Mighty Angel Fly", "George Manwaring", [
        (1, "verse", "I saw a mighty angel fly, To earth he seemed to come, Restoring truth and liberty And everlasting gospel home."),
    ]),
    (16, "What Glorious Scenes Mine Eyes Behold", "Anonymous", [
        (1, "verse", "What glorious scenes mine eyes behold! What wonders burst upon my sight! These things prophetic bards foretold Are now revealed in heav'nly light."),
    ]),
    (17, "Awake, Ye Saints of God, Awake!", "Eliza R. Snow", [
        (1, "verse", "Awake, ye Saints of God, awake! Call on the Lord in mighty prayer That he will Zion's bondage break And bring to naught the fowler's snare."),
    ]),
    (18, "The Voice of God Again Is Heard", "Evan Stephens", [
        (1, "verse", "The voice of God again is heard; The silence has been broken. The curse of darkness is dispersed, The Lord from heav'n has spoken."),
    ]),
    (19, "We Thank Thee, O God, for a Prophet", "William Fowler", [
        (1, "verse", "We thank thee, O God, for a prophet To guide us in these latter days. We thank thee for sending the gospel To lighten our minds with its rays. We thank thee for every blessing Bestowed by thy bounteous hand. We feel it a pleasure to serve thee And love to obey thy command."),
        (2, "verse", "When dark clouds of trouble hang o'er us And threaten our peace to destroy, There is hope smiling brightly before us, And we know that deliv'rance is nigh. We doubt not the Lord nor his goodness We've proved him in days that are past. The wicked who fight against Zion Will surely be smitten at last."),
        (3, "verse", "We'll sing of his goodness and mercy. We'll praise him by day and by night, Rejoice in his glorious gospel, And bask in its life-giving light. Thus on to eternal perfection The honest and faithful will go, While they who reject this glad message Shall never such happiness know."),
    ]),
    (20, "God of Power, God of Right", "Wallace F. Bennett", [
        (1, "verse", "God of power, God of right, Guide us with thy priesthood's might. In this land which thou hast blest May thy kingdom stand confessed."),
    ]),
    (21, "Come, Listen to a Prophet's Voice", "Joseph S. Murdock", [
        (1, "verse", "Come, listen to a prophet's voice, And hear the word of God, And in the way of truth rejoice, And sing for joy aloud."),
    ]),
    (22, "The Happy Day at Last Has Come", "Philo Dibble", [
        (1, "verse", "The happy day at last has come When truth so long expected Bursts forth in glory like the sun, No more by men rejected."),
    ]),
    (23, "God Be with You Till We Meet Again", "Jeremiah E. Rankin", [
        (1, "verse", "God be with you till we meet again; By his counsels guide, uphold you; With his sheep securely fold you. God be with you till we meet again."),
        (2, "chorus", "Till we meet, till we meet, Till we meet at Jesus' feet; Till we meet, till we meet, God be with you till we meet again."),
        (3, "verse", "God be with you till we meet again; When life's perils thick confound you, Put his arms unfailing round you. God be with you till we meet again."),
    ]),
    (24, "Truth Reflects upon Our Senses", "Eliza R. Snow", [
        (1, "verse", "Truth reflects upon our senses; Gospel light reveals to some. If there still be offenses, Woe to them by whom they come!"),
    ]),
    (25, "Now We'll Sing with One Accord", "William W. Phelps", [
        (1, "verse", "Now we'll sing with one accord To our Prophet and our Lord, Him to whom we now look forth For the truth and living word."),
    ]),
    (26, "Joseph Smith's First Prayer", "George Manwaring", [
        (1, "verse", "Oh, how lovely was the morning! Radiant beamed the sun above. Bees were humming, sweet birds singing, Music ringing thro' the grove."),
        (2, "verse", "Humbly kneeling, sweet appealing\u2014'Twas the boy's first uttered prayer\u2014When the pow'rs of sin assailing Filled his soul with deep despair."),
        (3, "verse", "But undaunted, still he trusted In his Heav'nly Father's care. And with faith and virtue scouted Ev'ry whisper of despair."),
        (4, "verse", "Suddenly a light descended, Brighter far than noonday sun, And a shining, glorious pillar O'er him fell, around him shone."),
    ]),
    (27, "Praise to the Man", "William W. Phelps", [
        (1, "verse", "Praise to the man who communed with Jehovah! Jesus anointed that Prophet and Seer. Blessed to open the last dispensation, Kings shall extol him, and nations revere."),
        (2, "chorus", "Hail to the Prophet, ascended to heaven! Traitors and tyrants now fight him in vain. Mingling with Gods, he can plan for his brethren; Death cannot conquer the hero again."),
        (3, "verse", "Praise to his mem'ry, he died as a martyr; Honored and blest be his ever great name! Long shall his blood, which was shed by assassins, Plead unto heav'n while the earth lauds his fame."),
        (4, "verse", "Great is his glory and endless his priesthood. Ever and ever the keys he will hold. Faithful and true, he will enter his kingdom, Crowned in the midst of the prophets of old."),
        (5, "verse", "Sacrifice brings forth the blessings of heaven; Earth must atone for the blood of that man. Wake up the world for the conflict of justice. Millions shall know \"Brother Joseph\" again."),
    ]),
    (28, "Saints, Behold How Great Jehovah", "Anonymous", [
        (1, "verse", "Saints, behold how great Jehovah Comforts those who mourn his name; Let the knowledge of the Savior Fill your souls with living flame."),
    ]),
    (29, "A Poor Wayfaring Man of Grief", "James Montgomery", [
        (1, "verse", "A poor wayfaring Man of grief Hath often crossed me on my way, Who sued so humbly for relief That I could never answer nay. I had not pow'r to ask his name, Whereto he went, or whence he came; Yet there was something in his eye That won my love; I knew not why."),
        (2, "verse", "Once, when my scanty meal was spread, He entered; not a word he spake, Just perishing for want of bread. I gave him all; he blessed it, brake. And ate, but gave me part again. Mine was an angel's portion then, For while I fed with eager haste, The crust was manna to my taste."),
        (3, "verse", "I spied him where a fountain burst Clear from the rock; his strength was gone. The heedless water mocked his thirst; He heard it, saw it hurrying on. I ran and raised the suff'rer up; Thrice from the stream he drained my cup, Dipt, and returned it running o'er; I drank and never thirsted more."),
        (4, "verse", "Strippt, wounded, beaten nigh to death, I found him by the highway side. I roused his pulse, brought back his breath, Revived his spirit, and supplied Wine, oil, refreshment—he was healed. I had myself a wound concealed, But from that hour forgot the smart, And peace bound up my broken heart."),
        (5, "verse", "In pris'n I saw him next, condemned To meet a traitor's doom at morn. The tide of lying tongues I stemmed, And honored him 'mid shame and scorn. My friendship's utmost zeal to try, He asked if I for him would die. The flesh was weak; my blood ran chill, But the free spirit cried, \"I will!\""),
        (6, "verse", "Then in a moment to my view The stranger started from disguise. The tokens in his hands I knew; The Savior stood before mine eyes. He spake, and my poor name he named, \"Of me thou hast not been ashamed. These deeds shall thy memorial be; Fear not, thou didst them unto me.\""),
    ]),
    (30, "Come, Come, Ye Saints", "William Clayton", [
        (1, "verse", "Come, come, ye Saints, no toil nor labor fear; But with joy wend your way. Though hard to you this journey may appear, Grace shall be as your day. 'Tis better far for us to strive Our useless cares from us to drive; Do this, and joy your hearts will swell— All is well! All is well!"),
        (2, "verse", "Why should we mourn or think our lot is hard? 'Tis not so; all is right. Why should we think to earn a great reward If we now shun the fight? Gird up your loins; fresh courage take. Our God will never us forsake; And soon we'll have this tale to tell— All is well! All is well!"),
        (3, "verse", "We'll find the place which God for us prepared, Far away in the West, Where none shall come to hurt or make afraid; There the Saints will be blessed. We'll make the air with music ring, Shout praises to our God and King; Above the rest these words we'll tell— All is well! All is well!"),
        (4, "verse", "And should we die before our journey's through, Happy day! All is well! We then are free from toil and sorrow, too; With the just we shall dwell! But if our lives are spared again To see the Saints their rest obtain, Oh, how we'll make this chorus swell— All is well! All is well!"),
    ]),
    (31, "O God, the Eternal Father", "William W. Phelps", [
        (1, "verse", "O God, the Eternal Father, Who dwells amid the sky, In Jesus' name we ask thee To bless and sanctify."),
        (2, "verse", "If we are pure before thee As emblems of thy Son, We ask thee for thy Spirit That of the two we'll be one."),
    ]),
    (32, "The Great King of Kings", "Anonymous", [
        (1, "verse", "The great King of Kings and the Lord of the earth Has sent forth his gospel to all. His messengers go to the nations afar To gather the last ones and call."),
    ]),
    (33, "Our Mountain Home So Dear", "Emmeline B. Wells", [
        (1, "verse", "Our mountain home so dear, Where crystal waters clear Flow ever free, flow ever free. Where fragrant breezes blow, Where perfect wildflowers grow, Our mountain home so dear."),
    ]),
    (34, "O Ye Mountains High", "Charles W. Penrose", [
        (1, "verse", "O ye mountains high, where the clear blue sky Arches over the vales of the free, Where the pure breezes blow and the clear streamlets flow, How I've longed to your bosom to flee!"),
    ]),
    (35, "For the Strength of the Hills", "Felicia D. Hemans", [
        (1, "verse", "For the strength of the hills we bless thee, Our God, our fathers' God. Thou hast made thy children mighty By the touch of the mountain sod."),
    ]),
    (36, "They, the Builders of the Nation", "Ida R. Alldredge", [
        (1, "verse", "They, the builders of the nation, Blazing trails along the way; Stepping-stones for gen'rations Were their deeds of ev'ry day."),
    ]),
    (37, "The Wintry Day, Descending to Its Close", "Orson F. Whitney", [
        (1, "verse", "The wintry day, descending to its close, Invites all wearied nature to repose, And shades of night are falling dense and fast, Like sable curtains closing o'er the past."),
    ]),
    (38, "Come, All Ye Saints of Zion", "William W. Phelps", [
        (1, "verse", "Come, all ye Saints of Zion, And let us praise the Lord; His ransomed are returning According to his word."),
    ]),
    (39, "O Saints of Zion", "Anonymous", [
        (1, "verse", "O Saints of Zion, hear the voice From heav'n's eternal King; Whose promise sure to those who serve Glad tidings e'er shall bring."),
    ]),
    (40, "Arise, O Glorious Zion", "William G. Mills", [
        (1, "verse", "Arise, O glorious Zion, Thou joy of latter days, Whom countless hearts are seeking With songs of grateful praise."),
    ]),
    (41, "Let Zion in Her Beauty Rise", "Edward Partridge", [
        (1, "verse", "Let Zion in her beauty rise; Her light begins to shine. Ere long her King will rend the skies, Majestic and divine."),
    ]),
    (42, "Hark! The Song of Jubilee", "Anonymous", [
        (1, "verse", "Hark! the song of jubilee, Loud as mighty thunders roar, Or the fullness of the sea When it breaks upon the shore."),
    ]),
    (43, "Zion Stands with Hills Surrounded", "Thomas Kelly", [
        (1, "verse", "Zion stands with hills surrounded, Zion, kept by pow'r divine. All her foes shall be confounded, Though the world in arms combine."),
    ]),
    (44, "On the Mountain's Top Appearing", "Thomas Kelly", [
        (1, "verse", "On the mountain's top appearing, Lo, the sacred herald stands, Welcome news to Zion bearing, Zion long in hostile lands."),
    ]),
    (45, "Lead Me into Life Eternal", "John A. Widtsoe", [
        (1, "verse", "Lead me into life eternal By the gospel's joyful sound, Let my heart find peace supernal Ere life's evening sun goes down."),
    ]),
    (46, "Glorious Things of Thee Are Spoken", "John Newton", [
        (1, "verse", "Glorious things of thee are spoken, Zion, city of our God. He whose word cannot be broken Formed thee for his own abode."),
    ]),
    (47, "We Will Sing of Zion", "Anonymous", [
        (1, "verse", "We will sing of Zion, City of our King, Temple, hill, and valley, Gladly praise we sing."),
    ]),
    (48, "Glorious Things Are Sung of Zion", "William W. Phelps", [
        (1, "verse", "Glorious things are sung of Zion, Enoch's city seen of old, Where the righteous, being perfect, Walked with God in streets of gold."),
    ]),
    (49, "Adam-ondi-Ahman", "William W. Phelps", [
        (1, "verse", "This earth was once a garden place, With all her glories common, And men did live a holy race, And worship Jesus face to face, In Adam-ondi-Ahman."),
    ]),
    (50, "Come, Thou Glorious Day of Promise", "Anonymous", [
        (1, "verse", "Come, thou glorious day of promise; Come and spread thy cheerful ray, When the scattered sheep of Israel Shall no longer go astray."),
    ]),
    (51, "Sons of Michael, He Approaches", "Eliza R. Snow", [
        (1, "verse", "Sons of Michael, he approaches! Rise, the ancient father greet. Bow, ye thousands, low before him; Minister before his feet."),
    ]),
    (52, "The Day Dawn Is Breaking", "Joseph L. Townsend", [
        (1, "verse", "The day dawn is breaking, the world is awaking, The clouds of night's darkness are fleeing away. The worldwide commotion, from ocean to ocean, Now heralds the time of the beautiful day."),
    ]),
    (53, "Let Earth's Inhabitants Rejoice", "William W. Phelps", [
        (1, "verse", "Let earth's inhabitants rejoice, And gladly make a joyful noise, The Lord has set his hand again The fallen state of man to mend."),
    ]),
    (54, "Behold, the Mountain of the Lord", "Anonymous", [
        (1, "verse", "Behold, the mountain of the Lord In latter days shall rise On mountain tops above the hills And draw the wond'ring eyes."),
    ]),
    (55, "Lo, the Mighty God Appearing!", "Anonymous", [
        (1, "verse", "Lo, the mighty God appearing! From on high Jehovah speaks! Eastern lands the summons hearing, O'er the west his mandate breaks."),
    ]),
    (56, "Ere You Left Your Room This Morning", "Mary A. Kidder", [
        (1, "verse", "Ere you left your room this morning, Did you think to pray? In the name of Christ, our Savior, Did you sue for loving favor As a shield today?"),
    ]),
    (57, "Come, Ye Children of the Lord", "James H. Wallis", [
        (1, "verse", "Come, ye children of the Lord, Let us sing with one accord. Let us raise a joyful strain To our Lord who soon will reign."),
    ]),
    (58, "We Ever Pray for Thee", "Evan Stephens", [
        (1, "verse", "We ever pray for thee, our Prophet dear, That God will give to thee comfort and cheer; As the advancing years furrow thy brow, Still may the light within shine bright as now."),
    ]),
    (59, "Come, O Thou King of Kings", "Parley P. Pratt", [
        (1, "verse", "Come, O thou King of Kings! We've waited long for thee, With healing in thy wings, To set thy people free."),
    ]),
    (60, "As the Dew from Heaven Distilling", "Parley P. Pratt", [
        (1, "verse", "As the dew from heav'n distilling Gently on the grass descends And revives it, thus fulfilling What thy providence intends."),
    ]),
    (61, "On This Day of Joy and Gladness", "Anonymous", [
        (1, "verse", "On this day of joy and gladness, Lord, we praise thy holy name; God of Israel, banish sadness, Light within our hearts a flame."),
    ]),
    (62, "Great King of Heaven", "Anonymous", [
        (1, "verse", "Great King of heaven, our hearts we raise To thee in grateful hymns of praise. The light of truth shines forth to see, The dawn of sacred liberty."),
    ]),
    (63, "Hosanna to the Living God!", "Anonymous", [
        (1, "verse", "Hosanna to the living God! His name we praise forevermore; The Lamb once slain, through his atoning blood, We enter in the open door."),
    ]),
    (64, "Come, All Ye Saints Who Dwell on Earth", "William W. Phelps", [
        (1, "verse", "Come, all ye Saints who dwell on earth, Your cheerful voices raise. Our God and King let us extol And sing our hymns of praise."),
    ]),
    (65, "Rejoice, the Lord Is King!", "Charles Wesley", [
        (1, "verse", "Rejoice, the Lord is King! Your Lord and King adore! Mortals, give thanks and sing And triumph evermore."),
    ]),
    (66, "Glory to God on High", "James Allen", [
        (1, "verse", "Glory to God on high! Let heav'n and earth reply. Praise ye his name. His love and grace adore, Who all our sorrows bore. Sing aloud evermore: Worthy the Lamb!"),
    ]),
    (67, "How Wondrous and Great", "Henry U. Onderdonk", [
        (1, "verse", "How wondrous and great Thy works, God of praise! How just, King of Saints, And true are thy ways!"),
    ]),
    (68, "Praise to the Lord, the Almighty", "Joachim Neander", [
        (1, "verse", "Praise to the Lord, the Almighty, the King of creation! O my soul, praise him, for he is thy health and salvation! All ye who hear, Now to his temple draw near; Join me in glad adoration!"),
    ]),
    (69, "Every Star Is Lost in Light", "Anonymous", [
        (1, "verse", "Ev'ry star is lost in light As the sun streams o'er the sky; So all earthly splendors bright Fade before God's glory nigh."),
    ]),
    (70, "Sing Praise to Him", "Anonymous", [
        (1, "verse", "Sing praise to him who reigns above, The God of all creation, The God of pow'r, the God of love, The God of our salvation."),
    ]),
    (71, "Praise the Lord with Heart and Voice", "Tracy Y. Cannon", [
        (1, "verse", "Praise the Lord with heart and voice, In his holy name rejoice, For the blessings that abound, For the truths that we have found."),
    ]),
    (72, "Praise God, from Whom All Blessings Flow", "Thomas Ken", [
        (1, "verse", "Praise God, from whom all blessings flow; Praise him, all creatures here below; Praise him above, ye heav'nly host; Praise Father, Son, and Holy Ghost."),
    ]),
    (73, "In Hymns of Praise", "Anonymous", [
        (1, "verse", "In hymns of praise your voices raise, To him who rules on high; Whose counsels form the raging storm And spread the joys of morning nigh."),
    ]),
    (74, "God of Our Fathers, Whose Almighty Hand", "Daniel C. Roberts", [
        (1, "verse", "God of our fathers, whose almighty hand Leads forth in beauty all the starry band Of shining worlds in splendor through the skies, Our grateful songs before thy throne arise."),
    ]),
    (75, "With All the Power of Heart and Tongue", "Isaac Watts", [
        (1, "verse", "With all the pow'r of heart and tongue, I'll praise my Maker in my song. Angels shall hear the notes I raise, Approve the song, and join the praise."),
    ]),
    (76, "God of Our Fathers, Known of Old", "Rudyard Kipling", [
        (1, "verse", "God of our fathers, known of old, Lord of our far-flung battle line, Beneath whose awful hand we hold Dominion over palm and pine."),
    ]),
    (77, "Press Forward, Saints", "Marvin K. Gardner", [
        (1, "verse", "Press forward, Saints, with steadfast faith in Christ, With hope's bright flame alight in heart and mind, With love of God and love of all mankind."),
    ]),
    (78, "God Speed the Right", "Anonymous", [
        (1, "verse", "Now to heav'n our prayer ascending, God speed the right! In a noble cause contending, God speed the right!"),
    ]),
    (79, "My Redeemer Lives", "Gordon B. Hinckley", [
        (1, "verse", "I know that my Redeemer lives, Triumphant Savior, Son of God, Victorious over pain and death, My King, my Leader, and my Lord."),
    ]),
    (85, "How Firm a Foundation", "Robert Keen", [
        (1, "verse", "How firm a foundation, ye Saints of the Lord, Is laid for your faith in his excellent word! What more can he say than to you he hath said, Who unto the Savior for refuge have fled?"),
        (2, "verse", "In ev'ry condition\u2014in sickness, in health, In poverty's vale or abounding in wealth, At home or abroad, on the land or the sea\u2014 As thy days may demand, so thy succor shall be."),
        (3, "verse", "Fear not, I am with thee; oh, be not dismayed, For I am thy God and will still give thee aid. I'll strengthen thee, help thee, and cause thee to stand, Upheld by my righteous, omnipotent hand."),
        (4, "verse", "When through the deep waters I call thee to go, The rivers of sorrow shall not thee o'erflow, For I will be with thee, thy troubles to bless, And sanctify to thee thy deepest distress."),
        (5, "verse", "When through fiery trials thy pathway shall lie, My grace, all sufficient, shall be thy supply. The flame shall not hurt thee; I only design Thy dross to consume and thy gold to refine."),
        (6, "verse", "The soul that on Jesus hath leaned for repose I will not, I cannot, desert to his foes; That soul, though all hell should endeavor to shake, I'll never, no never, no never forsake!"),
    ]),
    (86, "How Great Thou Art", "Stuart K. Hine", [
        (1, "verse", "O Lord my God, when I in awesome wonder Consider all the worlds thy hands have made, I see the stars, I hear the rolling thunder, Thy pow'r throughout the universe displayed."),
        (2, "chorus", "Then sings my soul, my Savior God, to thee, How great thou art! How great thou art! Then sings my soul, my Savior God, to thee, How great thou art! How great thou art!"),
        (3, "verse", "When through the woods and forest glades I wander And hear the birds sing sweetly in the trees, When I look down from lofty mountain grandeur And hear the brook and feel the gentle breeze."),
        (4, "verse", "And when I think that God, his Son not sparing, Sent him to die, I scarce can take it in, That on the cross my burden gladly bearing He bled and died to take away my sin."),
        (5, "verse", "When Christ shall come, with shout of acclamation, And take me home, what joy shall fill my heart! Then I shall bow in humble adoration And there proclaim, \"My God, how great thou art!\""),
    ]),
    (87, "Count Your Blessings", "Johnson Oatman Jr.", [
        (1, "verse", "When upon life's billows you are tempest-tossed, When you are discouraged, thinking all is lost, Count your many blessings; name them one by one, And it will surprise you what the Lord has done."),
        (2, "chorus", "Count your blessings; Name them one by one. Count your blessings; See what God hath done. Count your blessings; Name them one by one. Count your many blessings; See what God hath done."),
        (3, "verse", "Are you ever burdened with a load of care? Does the cross seem heavy you are called to bear? Count your many blessings; ev'ry doubt will fly, And you will be singing as the days go by."),
        (4, "verse", "When you look at others with their lands and gold, Think that Christ has promised you his wealth untold. Count your many blessings; money cannot buy Your reward in heaven nor your home on high."),
        (5, "verse", "So amid the conflict, whether great or small, Do not be discouraged; God is over all. Count your many blessings; angels will attend, Help and comfort give you to your journey's end."),
    ]),
    (88, "Be Still, My Soul", "Katharina von Schlegel", [
        (1, "verse", "Be still, my soul: The Lord is on thy side; With patience bear thy cross of grief or pain. Leave to thy God to order and provide; In ev'ry change he faithful will remain."),
        (2, "verse", "Be still, my soul: Thy God doth undertake To guide the future as he has the past. Thy hope, thy confidence let nothing shake; All now mysterious shall be bright at last."),
        (3, "verse", "Be still, my soul: The hour is hast'ning on When we shall be forever with the Lord, When disappointment, grief, and fear are gone, Sorrow forgot, love's purest joys restored."),
    ]),
    (89, "The Lord Is My Light", "James Nicholson", [
        (1, "verse", "The Lord is my light; then why should I fear? By day and by night his presence is near. He is my salvation from sorrow and sin; This blessed assurance the Spirit doth bring."),
        (2, "chorus", "The Lord is my light, my joy, and my song; By day and by night he leads me along."),
        (3, "verse", "The Lord is my light; though clouds may arise, Faith, stronger than sight, looks up through the skies Where Jesus forever in glory doth reign; Then how can I ever in darkness remain?"),
        (4, "verse", "The Lord is my light; the Lord is my strength; I know in his might I'll conquer at length. My weakness in mercy he covers with pow'r, And, walking by faith, I sing ev'ry hour."),
        (5, "verse", "The Lord is my light, my all and in all; There is in his sight no darkness at all. He is my Redeemer, my Savior, and King; With Saints and with angels his praises I'll sing."),
    ]),
    (90, "I Know That My Redeemer Lives", "Samuel Medley", [
        (1, "verse", "I know that my Redeemer lives. What comfort this sweet sentence gives! He lives, he lives, who once was dead. He lives, my ever-living Head."),
        (2, "verse", "He lives to bless me with his love. He lives to plead for me above. He lives my hungry soul to feed. He lives to bless in time of need."),
        (3, "verse", "He lives to grant me rich supply. He lives to guide me with his eye. He lives to comfort me when faint. He lives to hear my soul's complaint."),
        (4, "verse", "He lives to silence all my fears. He lives to wipe away my tears. He lives to calm my troubled heart. He lives all blessings to impart."),
        (5, "verse", "He lives, my kind, wise heav'nly Friend. He lives and loves me to the end. He lives, and while he lives, I'll sing. He lives, my Prophet, Priest, and King."),
        (6, "verse", "He lives and grants me daily breath. He lives, and I shall conquer death. He lives my mansion to prepare. He lives to bring me safely there."),
        (7, "verse", "He lives! All glory to his name! He lives, my Savior, still the same. Oh, sweet the joy this sentence gives: \"I know that my Redeemer lives!\""),
        (8, "verse", "He lives! All glory to his name! He lives, my Savior, still the same. Oh, sweet the joy this sentence gives: \"I know that my Redeemer lives!\""),
    ]),
    (91, "Abide with Me!", "Henry F. Lyte", [
        (1, "verse", "Abide with me! Fast falls the eventide; The darkness deepens. Lord, with me abide! When other helpers fail and comforts flee, Help of the helpless, oh, abide with me!"),
        (2, "verse", "Swift to its close ebbs out life's little day; Earth's joys grow dim; its glories pass away. Change and decay in all around I see; O thou who changest not, abide with me!"),
    ]),
    (92, "Sweet Hour of Prayer", "William W. Walford", [
        (1, "verse", "Sweet hour of prayer! Sweet hour of prayer! That calls me from a world of care And bids me at my Father's throne Make all my wants and wishes known. In seasons of distress and grief, My soul has often found relief, And oft escaped the tempter's snare By thy return, sweet hour of prayer!"),
        (2, "verse", "Sweet hour of prayer! Sweet hour of prayer! The joys I feel, the bliss I share Of those whose anxious spirits burn With strong desires for thy return! With such I hasten to the place Where God my Savior shows his face, And gladly take my station there, And wait for thee, sweet hour of prayer!"),
        (3, "verse", "Sweet hour of prayer! Sweet hour of prayer! Thy wings shall my petition bear To him whose truth and faithfulness Engage the waiting soul to bless. And since he bids me seek his face, Believe his word, and trust his grace, I'll cast on him my ev'ry care, And wait for thee, sweet hour of prayer!"),
    ]),
    (93, "I Need Thee Every Hour", "Annie S. Hawks", [
        (1, "verse", "I need thee ev'ry hour, Most gracious Lord. No tender voice like thine Can peace afford."),
        (2, "chorus", "I need thee, oh, I need thee; Ev'ry hour I need thee! Oh, bless me now, my Savior; I come to thee!"),
        (3, "verse", "I need thee ev'ry hour; Stay thou nearby. Temptations lose their pow'r When thou art nigh."),
        (4, "verse", "I need thee ev'ry hour, In joy or pain. Come quickly and abide, Or life is vain."),
        (5, "verse", "I need thee ev'ry hour, Most holy One. Oh, make me thine indeed, Thou blessed Son!"),
    ]),
    (94, "Come unto Jesus", "Orson Pratt Huish", [
        (1, "verse", "Come unto Jesus, ye heavy laden, Careworn and fainting, by sin oppressed. He'll safely guide you unto that haven Where all who trust him may rest."),
    ]),
    (95, "Nearer, My God, to Thee", "Sarah F. Adams", [
        (1, "verse", "Nearer, my God, to thee, Nearer to thee! E'en though it be a cross That raiseth me, Still all my song shall be, Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (2, "verse", "Though like the wanderer, The sun gone down, Darkness be over me, My rest a stone, Yet in my dreams I'd be Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (3, "verse", "There let the way appear, Steps unto heav'n; All that thou sendest me, In mercy giv'n; Angels to beckon me Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (4, "verse", "Then, with my waking thoughts Bright with thy praise, Out of my stony griefs Bethel I'll raise; So by my woes to be Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (5, "verse", "Or if, on joyful wing, Cleaving the sky, Sun, moon, and stars forgot, Upward I fly, Still all my song shall be, Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
    ]),
    (96, "Lord, I Would Follow Thee", "Susan Evans McCloud", [
        (1, "verse", "Savior, may I learn to love thee, Walk the path that thou hast shown, Pause to help and lift another, Finding strength beyond my own."),
    ]),
    (97, "More Holiness Give Me", "Philip Paul Bliss", [
        (1, "verse", "More holiness give me, More strivings within, More patience in suff'ring, More sorrow for sin."),
        (2, "verse", "More gratitude give me, More trust in the Lord, More pride in his glory, More hope in his word."),
        (3, "verse", "More purity give me, More strength to o'ercome, More freedom from earth-stains, More longings for home."),
    ]),
    (98, "Where Can I Turn for Peace?", "Emma Lou Thayne", [
        (1, "verse", "Where can I turn for peace? Where is my solace When other sources cease to make me whole? When with a wounded heart, anger, or malice, I draw myself apart, Searching my soul?"),
    ]),
    (99, "Be Thou Humble", "Grietje Terburg Rowley", [
        (1, "verse", "Be thou humble in thy weakness, and the Lord thy God shall lead thee, Shall lead thee by the hand and give thee answer to thy prayers."),
    ]),
    (100, "Master, the Tempest Is Raging", "Mary Ann Baker", [
        (1, "verse", "Master, the tempest is raging! The billows are tossing high! The sky is o'ershadowed with blackness. No shelter or help is nigh. Carest thou not that we perish? How canst thou lie asleep When each moment so madly is threat'ning A grave in the angry deep?"),
        (2, "chorus", "The winds and the waves shall obey thy will: Peace, be still. Whether the wrath of the storm-tossed sea Or demons or men or whatever it be, No waters can swallow the ship where lies The Master of ocean and earth and skies. They all shall sweetly obey thy will: Peace, be still; peace, be still. They all shall sweetly obey thy will: Peace, peace, be still."),
        (3, "verse", "Master, with anguish of spirit I bow in my grief today. The depths of my sad heart are troubled. Oh, waken and save, I pray! Torrents of sin and of anguish Sweep o'er my sinking soul, And I perish! I perish! dear Master. Oh, hasten and take control!"),
        (4, "verse", "Master, the terror is over, The elements sweetly rest. Earth's sun in the calm lake is mirrored, And heaven's within my breast. Linger, O blessed Redeemer! Leave me alone no more, And with joy I shall make the blest harbor And rest on the blissful shore."),
    ]),
    (101, "Rock of Ages", "Augustus M. Toplady", [
        (1, "verse", "Rock of Ages, cleft for me, Let me hide myself in thee; Let the water and the blood, From thy wounded side which flowed, Be of sin the double cure: Save from wrath and make me pure."),
        (2, "verse", "Not the labors of my hands Can fulfil thy law's demands; Could my zeal no respite know, Could my tears forever flow, All for sin could not atone; Thou must save, and thou alone."),
        (3, "verse", "Nothing in my hand I bring, Simply to the cross I cling; Naked, come to thee for dress; Helpless, look to thee for grace; Foul, I to the fountain fly; Wash me, Savior, or I die!"),
        (4, "verse", "While I draw this fleeting breath, When mine eyes shall close in death, When I rise to worlds unknown, And behold thee on thy throne, Rock of Ages, cleft for me, Let me hide myself in thee."),
    ]),
    (102, "O My Father", "Eliza R. Snow", [
        (1, "verse", "O my Father, thou that dwellest In the high and glorious place, When shall I regain thy presence And again behold thy face? In thy holy habitation, Did my spirit once reside? In my first primeval childhood Was I nurtured near thy side?"),
        (2, "verse", "For a wise and glorious purpose Thou hast placed me here on earth And withheld the recollection Of my former friends and birth. Yet ofttimes a secret something Whispered, \"You're a stranger here,\" And I felt that I had wandered From a more exalted sphere."),
        (3, "verse", "I had learned to call thee Father, Thru thy Spirit from on high, But, until the key of knowledge Was restored, I knew not why. In the heav'ns are parents single? No, the thought makes reason stare! Truth is reason; truth eternal Tells me I've a mother there."),
        (4, "verse", "When I leave this frail existence, When I lay this mortal by, Father, Mother, may I meet you In your royal courts on high? Then, at length, when I've completed All you sent me forth to do, With your mutual approbation Let me come and dwell with you."),
    ]),
    (103, "We Are All Enlisted", "Anonymous", [
        (1, "verse", "We are all enlisted till the conflict is o'er; Happy are we! Happy are we! Soldiers in the army, there's a bright crown in store; We shall win and wear it by and by."),
        (2, "chorus", "Haste to the battle, quick to the field; Truth is our helmet, buckler, and shield. Stand by our colors; proudly they wave! We're joyfully, joyfully marching to our home."),
        (3, "verse", "Hark! the sound of battle sounding loudly and clear; Come join the ranks! Come join the ranks! We are waiting now for soldiers; who'll volunteer? Rally round the standard of the cross."),
        (4, "verse", "Fighting for a kingdom, and the world is our foe; Happy are we! Happy are we! Ev'ry day its strength diminish'th as we go; Righteousness our armor and our stay."),
    ]),
    (104, "Onward, Christian Soldiers", "Sabine Baring-Gould", [
        (1, "verse", "Onward, Christian soldiers, Marching as to war, With the cross of Jesus Going on before. Christ, the royal Master, Leads against the foe; Forward into battle See his banners go!"),
        (2, "chorus", "Onward, Christian soldiers, Marching as to war, With the cross of Jesus Going on before."),
        (3, "verse", "At the sign of triumph Satan's host doth flee; On then, Christian soldiers, On to victory! Hell's foundations quiver At the shout of praise; Brothers, lift your voices, Loud your anthems raise."),
        (4, "verse", "Like a mighty army Moves the Church of God; Brothers, we are treading Where the Saints have trod. We are not divided, All one body we, One in hope and doctrine, One in charity."),
        (5, "verse", "Onward, then, ye faithful, Join our happy throng, Blend with ours your voices In the triumph song; Glory, laud, and honor Unto Christ the King; This thro' countless ages Men and angels sing."),
    ]),
    (105, "Put Your Shoulder to the Wheel", "Will L. Thompson", [
        (1, "verse", "The world has need of willing men Who wear the worker's seal. Come, help the good work move along; Put your shoulder to the wheel."),
        (2, "chorus", "Put your shoulder to the wheel; push along, Do your duty with a heart full of song, We all have work; let no one shirk. Put your shoulder to the wheel."),
    ]),
    (106, "True to the Faith", "Evan Stephens", [
        (1, "verse", "Shall the youth of Zion falter In defending truth and right? While the enemy assaileth, Shall we shrink or shun the fight? No!"),
        (2, "chorus", "True to the faith that our parents have cherished, True to the truth for which martyrs have perished, To God's command, Soul, heart, and hand, Faithful and true we will ever stand."),
    ]),
    (107, "Do What Is Right", "Anonymous", [
        (1, "verse", "Do what is right; the day-dawn is breaking, Hailing a future of freedom and light. Angels above us are silent notes taking Of ev'ry action; then do what is right!"),
        (2, "chorus", "Do what is right; let the consequence follow. Battle for freedom in spirit and might; And with stout hearts look ye forth till tomorrow. God will protect you; then do what is right!"),
    ]),
    (108, "Choose the Right", "Joseph L. Townsend", [
        (1, "verse", "Choose the right when a choice is placed before you. In the right the Holy Spirit guides; And its light is forever shining o'er you, When in the right your heart confides."),
        (2, "chorus", "Choose the right! Choose the right! Let wisdom mark the way before. In its light, choose the right! And God will bless you evermore."),
        (3, "verse", "Choose the right! Let no spirit of digression Tempt the pure in heart astray. Choose the right! There is peace in righteous doing. Choose the right day by day."),
        (4, "verse", "Choose the right! There is safety in its counsel. Choose the right! There is wisdom in its way. Choose the right! And its beauty will enfold you. Choose the right day by day."),
    ]),
    (109, "Know This, That Every Soul Is Free", "Anonymous", [
        (1, "verse", "Know this, that ev'ry soul is free To choose his life and what he'll be; For this eternal truth is giv'n: That God will force no man to heav'n."),
    ]),
    (110, "Let Us All Press On", "Evan Stephens", [
        (1, "verse", "Let us all press on in the work of the Lord, That when life is o'er we may gain a reward; In the fight for right let us wield a sword, The mighty sword of truth."),
        (2, "chorus", "Fear not, though the enemy deride; Courage, for the Lord is on our side. We will heed not what the wicked may say, But the Lord alone we will obey."),
        (3, "verse", "We will not retreat, though our numbers may be few When compared with the opposite host in view; But an unseen pow'r will aid me and you In the glorious cause of truth."),
        (4, "verse", "If we do what's right we have no need to fear, For the Lord, our helper, will ever be near; In the days of trial his Saints he will cheer, And prosper the cause of truth."),
    ]),
    (111, "Hope of Israel", "Joseph L. Townsend", [
        (1, "verse", "Hope of Israel, Zion's army, Children of the promised day, See, the Chieftain signals onward, And the battle's in array!"),
        (2, "chorus", "Hope of Israel, rise in might With the sword of truth and right; Sound the war-cry, \"Watch and pray!\" Vanquish ev'ry foe today."),
    ]),
    (112, "Carry On", "Ruth May Fox", [
        (1, "verse", "Firm as the mountains around us, Stalwart and brave we stand On the rock our fathers planted For us in this goodly land."),
        (2, "chorus", "Carry on, carry on, carry on! Ev'ry youth in his place with courage and faith, Let us carry on, and on, and on!"),
    ]),
    (113, "Called to Serve", "Grace Gordon", [
        (1, "verse", "Called to serve him, heav'nly King of glory, Chosen e'er to witness for his name, Far and wide we tell the Father's story, Far and wide his love proclaim."),
        (2, "chorus", "Onward, ever onward, as we glory in his name; Onward, ever onward, as we glory in his name; Forward, pressing forward, as a triumph song we sing. God our strength will be; press forward ever, Called to serve our King."),
    ]),
    (114, "I'll Go Where You Want Me to Go", "Mary Brown", [
        (1, "verse", "It may not be on the mountain height Or over the stormy sea, It may not be at the battle's front My Lord will have need of me."),
        (2, "chorus", "I'll go where you want me to go, dear Lord, Over mountain or plain or sea; I'll say what you want me to say, dear Lord; I'll be what you want me to be."),
    ]),
    (115, "I Am a Child of God", "Naomi W. Randall", [
        (1, "verse", "I am a child of God, And he has sent me here, Has given me an earthly home With parents kind and dear."),
        (2, "chorus", "Lead me, guide me, walk beside me, Help me find the way. Teach me all that I must do To live with him someday."),
        (3, "verse", "I am a child of God, And so my needs are great; Help me to understand his words Before it grows too late."),
        (4, "verse", "I am a child of God. Rich blessings are in store; If I but learn to do his right, I'll live with him once more."),
        (5, "verse", "I am a child of God. His promises are sure; Celestial glory shall be mine If I can but endure."),
    ]),
    (116, "I Know My Father Lives", "Reid N. Nibley", [
        (1, "verse", "I know my Father lives and loves me too. The Spirit whispers this to me and tells me it is true."),
    ]),
    (117, "Teach Me to Walk in the Light", "Clara W. McMaster", [
        (1, "verse", "Teach me to walk in the light of his love; Teach me to pray to my Father above; Teach me to know of the things that are right; Teach me, teach me to walk in the light."),
        (2, "verse", "Come, little child, and together we'll learn Of his commandments, that we may return Home to his presence, to live in his sight\u2014 Always, always to walk in the light."),
        (3, "verse", "Father in Heaven, we thank thee this day For loving guidance to show us the way. Grateful, we praise thee with songs of delight! Gladly, gladly we'll walk in the light."),
    ]),
    (118, "Love One Another", "Luacine Clark Fox", [
        (1, "verse", "As I have loved you, Love one another. This new commandment: Love one another. By this shall men know Ye are my disciples, If ye have love One to another."),
    ]),
    (119, "Because I Have Been Given Much", "Grace Noll Crowell", [
        (1, "verse", "Because I have been given much, I too must give; Because of thy great bounty, Lord, each day I live."),
        (2, "verse", "Because I have been sheltered, fed, by thy good care, I cannot see another's lack and I not share."),
        (3, "verse", "Because I have been blessed by thy great love, dear Lord, I'll share thy love again, according to thy word."),
    ]),
    (120, "Lord, Dismiss Us with Thy Blessing", "John Fawcett", [
        (1, "verse", "Lord, dismiss us with thy blessing; Fill our hearts with joy and peace. Let us each, thy love possessing, Triumph in redeeming grace."),
    ]),
    (121, "The Lord Be with Us", "John Ellerton", [
        (1, "verse", "The Lord be with us as each day His blessings we receive, His gifts of love to us displayed, Who in his name believe."),
    ]),
    (122, "Each Life That Touches Ours for Good", "Karen Lynn Davidson", [
        (1, "verse", "Each life that touches ours for good Reflects thine own great mercy, Lord; Thou sendest blessings from above Thru words and deeds of those who love."),
    ]),
    (123, "God Be with You Till We Meet Again", "Jeremiah E. Rankin", [
        (1, "verse", "God be with you till we meet again; By his counsels guide, uphold you; With his sheep securely fold you. God be with you till we meet again."),
        (2, "chorus", "Till we meet, till we meet, Till we meet at Jesus' feet; Till we meet, till we meet, God be with you till we meet again."),
        (3, "verse", "God be with you till we meet again; When life's perils thick confound you, Put his arms unfailing round you. God be with you till we meet again."),
    ]),
    # Additional hymns referenced in ScripturesTab with LDS hymnal numbers
    (92, "For the Beauty of the Earth", "Folliott S. Pierpoint", [
        (1, "verse", "For the beauty of the earth, For the beauty of the skies, For the love which from our birth Over and around us lies. Lord of all, to thee we raise This our hymn of grateful praise."),
        (2, "verse", "For the beauty of each hour Of the day and of the night, Hill and vale and tree and flow'r, Sun and moon and stars of light. Lord of all, to thee we raise This our hymn of grateful praise."),
        (3, "verse", "For the joy of ear and eye, For the heart and mind's delight, For the mystic harmony Linking sense to sound and sight. Lord of all, to thee we raise This our hymn of grateful praise."),
        (4, "verse", "For the joy of human love, Brother, sister, parent, child, Friends on earth, and friends above, For all gentle thoughts and mild. Lord of all, to thee we raise This our hymn of grateful praise."),
        (5, "verse", "For thy church that evermore Lifteth holy hands above, Off'ring up on ev'ry shore Her pure sacrifice of love. Lord of all, to thee we raise This our hymn of grateful praise."),
    ]),
    (95, "Now Thank We All Our God", "Martin Rinkart", [
        (1, "verse", "Now thank we all our God With heart and hands and voices, Who wondrous things hath done, In whom his world rejoices. Who from our mothers' arms Hath blessed us on our way With countless gifts of love And still is ours today."),
        (2, "verse", "Oh, may this bounteous God Through all our life be near us, With ever joyful hearts And blessed peace to cheer us. And keep us in his grace And guide us when perplexed, And free us from all ills In this world and the next."),
        (3, "verse", "All praise and thanks to God The Father now be given, The Son, and him who reigns With them in highest heaven— The one eternal God, Whom earth and heav'n adore; For thus it was, is now, And shall be evermore."),
    ]),
    (97, "Lead, Kindly Light", "John Henry Newman", [
        (1, "verse", "Lead, kindly Light, amid th'encircling gloom; Lead thou me on! The night is dark, and I am far from home; Lead thou me on! Keep thou my feet; I do not ask to see The distant scene—one step enough for me."),
        (2, "verse", "I was not ever thus, nor prayed that thou Shouldst lead me on; I loved to choose and see my path; but now Lead thou me on! I loved the garish day, and, spite of fears, Pride ruled my will; remember not past years."),
        (3, "verse", "So long thy pow'r hath blessed me, sure it still Will lead me on O'er moor and fen, o'er crag and torrent, till The night is gone; And with the morn those angel faces smile, Which I have loved long since, and lost awhile!"),
    ]),
    (98, "I Need Thee Every Hour", "Annie S. Hawks", [
        (1, "verse", "I need thee ev'ry hour, Most gracious Lord. No tender voice like thine Can peace afford."),
        (2, "chorus", "I need thee, oh, I need thee; Ev'ry hour I need thee! Oh, bless me now, my Savior; I come to thee!"),
        (3, "verse", "I need thee ev'ry hour; Stay thou nearby. Temptations lose their pow'r When thou art nigh."),
        (4, "verse", "I need thee ev'ry hour, In joy or pain. Come quickly and abide, Or life is vain."),
        (5, "verse", "I need thee ev'ry hour, Most holy One. Oh, make me thine indeed, Thou blessed Son!"),
    ]),
    (100, "Nearer, My God, to Thee", "Sarah F. Adams", [
        (1, "verse", "Nearer, my God, to thee, Nearer to thee! E'en though it be a cross That raiseth me, Still all my song shall be, Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (2, "verse", "Though like the wanderer, The sun gone down, Darkness be over me, My rest a stone, Yet in my dreams I'd be Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (3, "verse", "There let the way appear, Steps unto heav'n; All that thou sendest me, In mercy giv'n; Angels to beckon me Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (4, "verse", "Then, with my waking thoughts Bright with thy praise, Out of my stony griefs Bethel I'll raise; So by my woes to be Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
        (5, "verse", "Or if, on joyful wing, Cleaving the sky, Sun, moon, and stars forgot, Upward I fly, Still all my song shall be, Nearer, my God, to thee! Nearer, my God, to thee, Nearer to thee!"),
    ]),
    (116, "Come, Follow Me", "John Nicholson", [
        (1, "verse", "\"Come, follow me,\" the Savior said. Then let us in his footsteps tread, For thus alone can we be one With God's own loved, begotten Son."),
        (2, "verse", "\"Come, follow me,\" a simple phrase, Yet truth's sublime, effulgent rays Are in these simple words combined To form a guide for all mankind."),
        (3, "verse", "Is there a place too dark or drear? Or is there one we need not fear? Can we not find some safe retreat From him who deigns our steps to meet?"),
        (4, "verse", "Then let us in his footsteps tread, And walk the path which Jesus led. Then let us all his words obey And be prepared to meet the day."),
    ]),
    (118, "Ye Simple Souls Who Stray", "Charles Wesley", [
        (1, "verse", "Ye simple souls who stray Far from the path of peace, That lonely, unfrequented way To life and happiness."),
    ]),
    (124, "Be Still, My Soul", "Katharina von Schlegel", [
        (1, "verse", "Be still, my soul: The Lord is on thy side; With patience bear thy cross of grief or pain. Leave to thy God to order and provide; In ev'ry change he faithful will remain."),
        (2, "verse", "Be still, my soul: Thy God doth undertake To guide the future as he has the past. Thy hope, thy confidence let nothing shake; All now mysterious shall be bright at last."),
        (3, "verse", "Be still, my soul: The hour is hast'ning on When we shall be forever with the Lord, When disappointment, grief, and fear are gone, Sorrow forgot, love's purest joys restored."),
    ]),
    (134, "I Believe in Christ", "Bruce R. McConkie", [
        (1, "verse", "I believe in Christ; he is my King! With all my heart to him I'll sing; I'll raise my voice in praise and joy, In grand amens my tongue employ."),
        (2, "verse", "I believe in Christ; he is God's Son. On earth to dwell his soul did come. He healed the sick; the dead he raised. Good works were his; his name be praised."),
        (3, "verse", "I believe in Christ; oh blessed name! As Mary's Son he came to reign 'Mid mortal men, his earthly kin, To save them from the woes of sin."),
        (4, "verse", "I believe in Christ\u2014so come what may. With him I'll stand in that great day When on this earth he comes again To rule among the sons of men."),
    ]),
    (136, "I Know That My Redeemer Lives", "Samuel Medley", [
        (1, "verse", "I know that my Redeemer lives. What comfort this sweet sentence gives! He lives, he lives, who once was dead. He lives, my ever-living Head."),
        (2, "verse", "He lives to bless me with his love. He lives to plead for me above. He lives my hungry soul to feed. He lives to bless in time of need."),
        (3, "verse", "He lives to grant me rich supply. He lives to guide me with his eye. He lives to comfort me when faint. He lives to hear my soul's complaint."),
        (4, "verse", "He lives to silence all my fears. He lives to wipe away my tears. He lives to calm my troubled heart. He lives all blessings to impart."),
        (5, "verse", "He lives, my kind, wise heav'nly Friend. He lives and loves me to the end. He lives, and while he lives, I'll sing. He lives, my Prophet, Priest, and King."),
        (6, "verse", "He lives and grants me daily breath. He lives, and I shall conquer death. He lives my mansion to prepare. He lives to bring me safely there."),
        (7, "verse", "He lives! All glory to his name! He lives, my Savior, still the same. Oh, sweet the joy this sentence gives: \"I know that my Redeemer lives!\""),
        (8, "verse", "He lives! All glory to his name! He lives, my Savior, still the same. Oh, sweet the joy this sentence gives: \"I know that my Redeemer lives!\""),
    ]),
    (152, "God Be with You Till We Meet Again", "Jeremiah E. Rankin", [
        (1, "verse", "God be with you till we meet again; By his counsels guide, uphold you; With his sheep securely fold you. God be with you till we meet again."),
        (2, "chorus", "Till we meet, till we meet, Till we meet at Jesus' feet; Till we meet, till we meet, God be with you till we meet again."),
        (3, "verse", "God be with you till we meet again; When life's perils thick confound you, Put his arms unfailing round you. God be with you till we meet again."),
    ]),
    (219, "Because I Have Been Given Much", "Grace Noll Crowell", [
        (1, "verse", "Because I have been given much, I too must give; Because of thy great bounty, Lord, each day I live."),
        (2, "verse", "Because I have been sheltered, fed, by thy good care, I cannot see another's lack and I not share."),
        (3, "verse", "Because I have been blessed by thy great love, dear Lord, I'll share thy love again, according to thy word."),
    ]),
    (239, "Choose the Right", "Joseph L. Townsend", [
        (1, "verse", "Choose the right when a choice is placed before you. In the right the Holy Spirit guides; And its light is forever shining o'er you, When in the right your heart confides."),
        (2, "chorus", "Choose the right! Choose the right! Let wisdom mark the way before. In its light, choose the right! And God will bless you evermore."),
        (3, "verse", "Choose the right! Let no spirit of digression Tempt the pure in heart astray. Choose the right! There is peace in righteous doing. Choose the right day by day."),
        (4, "verse", "Choose the right! There is safety in its counsel. Choose the right! There is wisdom in its way. Choose the right! And its beauty will enfold you. Choose the right day by day."),
    ]),
    (241, "Count Your Blessings", "Johnson Oatman Jr.", [
        (1, "verse", "When upon life's billows you are tempest-tossed, When you are discouraged, thinking all is lost, Count your many blessings; name them one by one, And it will surprise you what the Lord has done."),
        (2, "chorus", "Count your blessings; Name them one by one. Count your blessings; See what God hath done. Count your blessings; Name them one by one. Count your many blessings; See what God hath done."),
        (3, "verse", "Are you ever burdened with a load of care? Does the cross seem heavy you are called to bear? Count your many blessings; ev'ry doubt will fly, And you will be singing as the days go by."),
        (4, "verse", "When you look at others with their lands and gold, Think that Christ has promised you his wealth untold. Count your many blessings; money cannot buy Your reward in heaven nor your home on high."),
        (5, "verse", "So amid the conflict, whether great or small, Do not be discouraged; God is over all. Count your many blessings; angels will attend, Help and comfort give you to your journey's end."),
    ]),
    (246, "Onward, Christian Soldiers", "Sabine Baring-Gould", [
        (1, "verse", "Onward, Christian soldiers, Marching as to war, With the cross of Jesus Going on before. Christ, the royal Master, Leads against the foe; Forward into battle See his banners go!"),
        (2, "chorus", "Onward, Christian soldiers, Marching as to war, With the cross of Jesus Going on before."),
        (3, "verse", "At the sign of triumph Satan's host doth flee; On then, Christian soldiers, On to victory! Hell's foundations quiver At the shout of praise; Brothers, lift your voices, Loud your anthems raise."),
        (4, "verse", "Like a mighty army Moves the Church of God; Brothers, we are treading Where the Saints have trod. We are not divided, All one body we, One in hope and doctrine, One in charity."),
        (5, "verse", "Onward, then, ye faithful, Join our happy throng, Blend with ours your voices In the triumph song; Glory, laud, and honor Unto Christ the King; This thro' countless ages Men and angels sing."),
    ]),
    (248, "Put Your Shoulder to the Wheel", "Will L. Thompson", [
        (1, "verse", "The world has need of willing men Who wear the worker's seal. Come, help the good work move along; Put your shoulder to the wheel."),
        (2, "chorus", "Put your shoulder to the wheel; push along, Do your duty with a heart full of song, We all have work; let no one shirk. Put your shoulder to the wheel."),
    ]),
    (249, "Called to Serve", "Grace Gordon", [
        (1, "verse", "Called to serve him, heav'nly King of glory, Chosen e'er to witness for his name, Far and wide we tell the Father's story, Far and wide his love proclaim."),
        (2, "chorus", "Onward, ever onward, as we glory in his name; Onward, ever onward, as we glory in his name; Forward, pressing forward, as a triumph song we sing. God our strength will be; press forward ever, Called to serve our King."),
    ]),
    (250, "We Are All Enlisted", "Anonymous", [
        (1, "verse", "We are all enlisted till the conflict is o'er; Happy are we! Happy are we! Soldiers in the army, there's a bright crown in store; We shall win and wear it by and by."),
        (2, "chorus", "Haste to the battle, quick to the field; Truth is our helmet, buckler, and shield. Stand by our colors; proudly they wave! We're joyfully, joyfully marching to our home."),
        (3, "verse", "Hark! the sound of battle sounding loudly and clear; Come join the ranks! Come join the ranks! We are waiting now for soldiers; who'll volunteer? Rally round the standard of the cross."),
        (4, "verse", "Fighting for a kingdom, and the world is our foe; Happy are we! Happy are we! Ev'ry day its strength diminish'th as we go; Righteousness our armor and our stay."),
    ]),
    (255, "Carry On", "Ruth May Fox", [
        (1, "verse", "Firm as the mountains around us, Stalwart and brave we stand On the rock our fathers planted For us in this goodly land."),
        (2, "chorus", "Carry on, carry on, carry on! Ev'ry youth in his place with courage and faith, Let us carry on, and on, and on!"),
    ]),
    (256, "As Zion's Youth in Latter Days", "Anonymous", [
        (1, "verse", "As Zion's youth in latter days, We stand with valiant heart, With willing hands and open minds, Prepared to do our part."),
    ]),
    (270, "I'll Go Where You Want Me to Go", "Mary Brown", [
        (1, "verse", "It may not be on the mountain height Or over the stormy sea, It may not be at the battle's front My Lord will have need of me."),
        (2, "chorus", "I'll go where you want me to go, dear Lord, Over mountain or plain or sea; I'll say what you want me to say, dear Lord; I'll be what you want me to be."),
    ]),
    (301, "I Am a Child of God", "Naomi W. Randall", [
        (1, "verse", "I am a child of God, And he has sent me here, Has given me an earthly home With parents kind and dear."),
        (2, "chorus", "Lead me, guide me, walk beside me, Help me find the way. Teach me all that I must do To live with him someday."),
        (3, "verse", "I am a child of God, And so my needs are great; Help me to understand his words Before it grows too late."),
        (4, "verse", "I am a child of God. Rich blessings are in store; If I but learn to do his right, I'll live with him once more."),
        (5, "verse", "I am a child of God. His promises are sure; Celestial glory shall be mine If I can but endure."),
    ]),
    (302, "I Know My Father Lives", "Reid N. Nibley", [
        (1, "verse", "I know my Father lives and loves me too. The Spirit whispers this to me and tells me it is true."),
    ]),
    (303, "Teach Me to Walk in the Light", "Clara W. McMaster", [
        (1, "verse", "Teach me to walk in the light of his love; Teach me to pray to my Father above; Teach me to know of the things that are right; Teach me, teach me to walk in the light."),
        (2, "verse", "Come, little child, and together we'll learn Of his commandments, that we may return Home to his presence, to live in his sight\u2014 Always, always to walk in the light."),
        (3, "verse", "Father in Heaven, we thank thee this day For loving guidance to show us the way. Grateful, we praise thee with songs of delight! Gladly, gladly we'll walk in the light."),
    ]),
    (308, "Love One Another", "Luacine Clark Fox", [
        (1, "verse", "As I have loved you, Love one another. This new commandment: Love one another. By this shall men know Ye are my disciples, If ye have love One to another."),
    ]),
]


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run build-scriptures-db.py first to create the base database.")
        return

    print(f"Opening existing database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    # Drop existing hymn tables if re-running (to allow idempotent runs)
    conn.execute("DROP TABLE IF EXISTS hymn_verses")
    conn.execute("DROP TABLE IF EXISTS hymns")
    # FTS virtual tables need special handling
    try:
        conn.execute("DROP TABLE IF EXISTS hymns_fts")
    except Exception:
        pass

    # Create hymn tables
    conn.executescript(HYMN_SCHEMA)
    print("Created hymn tables (hymns, hymn_verses, hymns_fts)")

    # Track unique hymns by (hymn_number, title) to handle duplicates
    # Some hymns appear with both their sequential number and LDS hymnal number
    seen = {}  # (hymn_number, title) -> hymn_id
    hymn_count = 0
    verse_count = 0
    fts_count = 0

    for hymn_number, title, author, verses in HYMNS_DATA:
        key = (hymn_number, title)
        if key in seen:
            # Skip duplicate entries
            continue

        # Get first line from first verse
        first_line = verses[0][2] if verses else ""
        # Truncate first_line to the first sentence
        dot_idx = first_line.find(".")
        if dot_idx > 0 and dot_idx < 80:
            first_line_short = first_line[: dot_idx + 1]
        else:
            first_line_short = first_line[:80]

        cursor = conn.execute(
            "INSERT INTO hymns (hymn_number, title, author, composer, first_line, is_public_domain) VALUES (?, ?, ?, '', ?, 1)",
            (hymn_number, title, author, first_line_short),
        )
        hymn_id = cursor.lastrowid
        seen[key] = hymn_id
        hymn_count += 1

        # Insert verses
        all_lyrics = []
        for verse_num, verse_type, text in verses:
            conn.execute(
                "INSERT INTO hymn_verses (hymn_id, verse_number, verse_type, text) VALUES (?, ?, ?, ?)",
                (hymn_id, verse_num, verse_type, text),
            )
            verse_count += 1
            all_lyrics.append(text)

        # Populate FTS index
        lyrics_combined = " ".join(all_lyrics)
        conn.execute(
            "INSERT INTO hymns_fts (rowid, title, author, first_line, lyrics) VALUES (?, ?, ?, ?, ?)",
            (hymn_id, title, author, first_line_short, lyrics_combined),
        )
        fts_count += 1

    conn.commit()

    # Print summary
    final_hymn_count = conn.execute("SELECT COUNT(*) FROM hymns").fetchone()[0]
    final_verse_count = conn.execute("SELECT COUNT(*) FROM hymn_verses").fetchone()[0]
    conn.close()

    print(f"\nDone! Added hymn data to {DB_PATH}")
    print(f"  {final_hymn_count} hymns")
    print(f"  {final_verse_count} hymn verses")
    print(f"  {fts_count} FTS entries")


if __name__ == "__main__":
    main()
