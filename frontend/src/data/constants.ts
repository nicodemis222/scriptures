export type SubTab =
  | 'BOOK OF MORMON'
  | 'BIBLE'
  | 'D&C'
  | 'PEARL OF GREAT PRICE'
  | 'COPTIC'
  | 'DEAD SEA SCROLLS'
  | 'RUSSIAN ORTHODOX'
  | 'ANCIENT WITNESSES'
  | 'HYMNS';

export const SUB_TABS: SubTab[] = [
  'BOOK OF MORMON',
  'BIBLE',
  'D&C',
  'PEARL OF GREAT PRICE',
  'COPTIC',
  'DEAD SEA SCROLLS',
  'RUSSIAN ORTHODOX',
  'ANCIENT WITNESSES',
  'HYMNS',
];

export const SUBTAB_VOLUMES: Record<SubTab, string[]> = {
  'BOOK OF MORMON': ['bom'],
  'BIBLE': ['ot', 'nt'],
  'D&C': ['dc'],
  'PEARL OF GREAT PRICE': ['pgp'],
  'COPTIC': ['coptic'],
  'DEAD SEA SCROLLS': ['dss'],
  'RUSSIAN ORTHODOX': ['russian'],
  'ANCIENT WITNESSES': ['aw'],
  'HYMNS': [],
};

/* ── Hardcoded fallback book lists (used when backend is unavailable) ── */

export const BOM_BOOKS = [
  '1 Nephi', '2 Nephi', 'Jacob', 'Enos', 'Jarom', 'Omni',
  'Words of Mormon', 'Mosiah', 'Alma', 'Helaman',
  '3 Nephi', '4 Nephi', 'Mormon', 'Ether', 'Moroni',
];

export const BIBLE_BOOKS = [
  // Old Testament
  'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
  'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
  '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
  'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
  'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah',
  'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
  'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah',
  'Haggai', 'Zechariah', 'Malachi',
  // New Testament
  'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
  '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
  'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
  '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
  'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
  'Jude', 'Revelation',
];

export const DC_SECTIONS = [
  ...Array.from({ length: 138 }, (_, i) => `Section ${i + 1}`),
  'Official Declaration 1',
  'Official Declaration 2',
];

export const PGP_BOOKS = [
  'Moses', 'Abraham', 'Joseph Smith--Matthew', 'Joseph Smith--History',
  'Articles of Faith',
];

export const COPTIC_BOOKS = [
  '1 Enoch', 'Jubilees', '1 Meqabyan', '2 Meqabyan', '3 Meqabyan',
  'Sirach', 'Tobit', 'Judith', 'Baruch', 'Wisdom of Solomon',
  '4 Baruch', 'Ascension of Isaiah', 'Joseph ben Gorion',
];

export const DSS_BOOKS = [
  'Community Rule', 'War Scroll', 'Thanksgiving Hymns', 'Temple Scroll',
  'Habakkuk Commentary', 'Genesis Apocryphon', 'Damascus Document',
  'Messianic Rule', 'Copper Scroll', 'Isaiah Scroll', 'Psalms Scroll',
  'Book of Giants', 'Songs of Sabbath Sacrifice',
];

export const RUSSIAN_BOOKS = [
  '1 Esdras', '2 Esdras', 'Tobit', 'Judith', 'Wisdom of Solomon',
  'Sirach', 'Baruch', 'Letter of Jeremiah', '1 Maccabees', '2 Maccabees',
  '3 Maccabees', '3 Esdras', 'Prayer of Manasseh', 'Psalm 151',
];

export const HYMNS_LIST = [
  'The Morning Breaks', 'The Spirit of God', 'Now Let Us Rejoice',
  'Truth Eternal', 'High on the Mountain Top', 'Redeemer of Israel',
  'Israel, Israel, God Is Calling', 'Awake and Arise',
  'Come, Rejoice', 'Come, Sing to the Lord',
  'What Was Witnessed in the Heavens?', 'Twas Witnessed in the Morning Sky',
  'An Angel from on High', 'Sweet Is the Peace the Gospel Brings',
  'I Saw a Mighty Angel Fly', 'What Glorious Scenes Mine Eyes Behold',
  'Awake, Ye Saints of God, Awake!', 'The Voice of God Again Is Heard',
  'We Thank Thee, O God, for a Prophet', 'God of Power, God of Right',
  'Come, Listen to a Prophet\'s Voice', 'The Happy Day at Last Has Come',
  'God Be with You Till We Meet Again', 'Truth Reflects upon Our Senses',
  'Now We\'ll Sing with One Accord', 'Joseph Smith\'s First Prayer',
  'Praise to the Man', 'Saints, Behold How Great Jehovah',
  'A Poor Wayfaring Man of Grief', 'Come, Come, Ye Saints',
  'O God, the Eternal Father', 'The Great King of Kings',
  'Our Mountain Home So Dear', 'O Ye Mountains High',
  'For the Strength of the Hills', 'They, the Builders of the Nation',
  'The Wintry Day, Descending to Its Close', 'Come, All Ye Saints of Zion',
  'O Saints of Zion', 'Arise, O Glorious Zion',
  'Let Zion in Her Beauty Rise', 'Hark! The Song of Jubilee',
  'Zion Stands with Hills Surrounded', 'On the Mountain\'s Top Appearing',
  'Lead Me into Life Eternal', 'Glorious Things of Thee Are Spoken',
  'We Will Sing of Zion', 'Glorious Things Are Sung of Zion',
  'Adam-ondi-Ahman', 'Come, Thou Glorious Day of Promise',
  'Sons of Michael, He Approaches', 'The Day Dawn Is Breaking',
  'Let Earth\'s Inhabitants Rejoice', 'Behold, the Mountain of the Lord',
  'Lo, the Mighty God Appearing!', 'Ere You Left Your Room This Morning',
  'Come, Ye Children of the Lord', 'We Ever Pray for Thee',
  'Come, O Thou King of Kings', 'As the Dew from Heaven Distilling',
  'On This Day of Joy and Gladness', 'Great King of Heaven',
  'Hosanna to the Living God!', 'Come, All Ye Saints Who Dwell on Earth',
  'Rejoice, the Lord Is King!', 'Glory to God on High',
  'How Wondrous and Great', 'Praise to the Lord, the Almighty',
  'Every Star Is Lost in Light', 'Sing Praise to Him',
  'Praise the Lord with Heart and Voice', 'Praise God, from Whom All Blessings Flow',
  'In Hymns of Praise', 'God of Our Fathers, Whose Almighty Hand',
  'With All the Power of Heart and Tongue', 'God of Our Fathers, Known of Old',
  'Press Forward, Saints', 'God Speed the Right',
  'My Redeemer Lives', 'How Firm a Foundation',
  'Count Your Blessings', 'Be Still, My Soul',
  'I Know That My Redeemer Lives', 'Abide with Me!',
  'Sweet Hour of Prayer', 'I Need Thee Every Hour',
  'Come unto Jesus', 'Nearer, My God, to Thee',
  'How Great Thou Art', 'Lord, I Would Follow Thee',
  'More Holiness Give Me', 'Where Can I Turn for Peace?',
  'Be Thou Humble', 'Master, the Tempest Is Raging',
  'Rock of Ages', 'O My Father',
  'We Are All Enlisted', 'Onward, Christian Soldiers',
  'Put Your Shoulder to the Wheel', 'True to the Faith',
  'Do What Is Right', 'Choose the Right',
  'Know This, That Every Soul Is Free', 'Let Us All Press On',
  'Hope of Israel', 'Carry On',
  'Called to Serve', 'I\'ll Go Where You Want Me to Go',
  'I Am a Child of God', 'Teach Me to Walk in the Light',
  'Love One Another', 'Because I Have Been Given Much',
  'Lord, Dismiss Us with Thy Blessing', 'The Lord Be with Us',
  'Each Life That Touches Ours for Good',
];

export const DEFAULT_TAB_ORDER: SubTab[] = [
  'BOOK OF MORMON', 'BIBLE', 'D&C', 'PEARL OF GREAT PRICE',
  'COPTIC', 'DEAD SEA SCROLLS', 'RUSSIAN ORTHODOX', 'ANCIENT WITNESSES', 'HYMNS',
];

export const FALLBACK_BOOKS: Record<SubTab, string[]> = {
  'BOOK OF MORMON': BOM_BOOKS,
  'BIBLE': BIBLE_BOOKS,
  'D&C': DC_SECTIONS,
  'PEARL OF GREAT PRICE': PGP_BOOKS,
  'COPTIC': COPTIC_BOOKS,
  'DEAD SEA SCROLLS': DSS_BOOKS,
  'RUSSIAN ORTHODOX': RUSSIAN_BOOKS,
  'ANCIENT WITNESSES': [
    'Josephus - Antiquities', 'Tacitus - Annals', 'Pliny the Younger - Letters',
    'Suetonius - Lives of Caesars', 'Mara bar Serapion', 'Lucian of Samosata',
    'Didache', '1 Clement', 'Epistle of Barnabas', 'Shepherd of Hermas',
    'Letters of Ignatius', 'Epistle to Diognetus', 'Gospel of Thomas',
  ],
  'HYMNS': HYMNS_LIST,
};
