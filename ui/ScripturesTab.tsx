import { useState, useCallback, useEffect } from 'react';
import { PipBoyList } from '../components/PipBoyList';
import type { PipBoyListItem } from '../components/PipBoyList';

type SubTab = 'BOOK OF MORMON' | 'BIBLE' | 'D&C' | 'COPTIC' | 'DEAD SEA SCROLLS' | 'RUSSIAN ORTHODOX' | 'HYMNS';

interface VerseResult {
  id: number;
  volume_title: string | null;
  book_title: string | null;
  chapter_number: number | null;
  verse_number: number | null;
  reference: string | null;
  text: string;
}

interface BookInfo {
  id: number;
  title: string;
  abbreviation: string | null;
  long_title: string | null;
  num_chapters: number | null;
  book_order: number | null;
  volume_title: string | null;
}

interface HymnSummary {
  id: number;
  hymn_number: number | null;
  title: string;
  author: string | null;
  first_line: string | null;
}

interface HymnVerse {
  verse_number: number;
  verse_type: string;
  text: string;
}

interface HymnDetail {
  id: number;
  hymn_number: number | null;
  title: string;
  author: string | null;
  composer: string | null;
  verses: HymnVerse[];
}

/* ── Volume abbreviation mapping ── */

const SUBTAB_VOLUMES: Record<SubTab, string[]> = {
  'BOOK OF MORMON': ['bom'],
  'BIBLE': ['ot', 'nt'],
  'D&C': ['dc'],
  'COPTIC': ['coptic'],
  'DEAD SEA SCROLLS': ['dss'],
  'RUSSIAN ORTHODOX': ['russian'],
  'HYMNS': [],
};

/* ── Hardcoded fallback book lists (used when API is unavailable) ── */

const BOM_BOOKS = [
  '1 Nephi', '2 Nephi', 'Jacob', 'Enos', 'Jarom', 'Omni',
  'Words of Mormon', 'Mosiah', 'Alma', 'Helaman',
  '3 Nephi', '4 Nephi', 'Mormon', 'Ether', 'Moroni',
];

const BIBLE_BOOKS = [
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

const DC_SECTIONS = [
  ...Array.from({ length: 138 }, (_, i) => `Section ${i + 1}`),
  'Official Declaration 1',
  'Official Declaration 2',
];

const HYMNS_LIST = [
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

const COPTIC_BOOKS = [
  '1 Enoch', 'Jubilees', '1 Meqabyan', '2 Meqabyan', '3 Meqabyan',
  'Sirach', 'Tobit', 'Judith', 'Baruch', 'Wisdom of Solomon',
  '4 Baruch', 'Ascension of Isaiah', 'Joseph ben Gorion',
];

const DSS_BOOKS = [
  'Community Rule', 'War Scroll', 'Thanksgiving Hymns', 'Temple Scroll',
  'Habakkuk Commentary', 'Genesis Apocryphon', 'Damascus Document',
  'Messianic Rule', 'Copper Scroll', 'Isaiah Scroll', 'Psalms Scroll',
  'Book of Giants', 'Songs of Sabbath Sacrifice',
];

const RUSSIAN_BOOKS = [
  '1 Esdras', '2 Esdras', 'Tobit', 'Judith', 'Wisdom of Solomon',
  'Sirach', 'Baruch', 'Letter of Jeremiah', '1 Maccabees', '2 Maccabees',
  '3 Maccabees', '3 Esdras', 'Prayer of Manasseh', 'Psalm 151',
];

const FALLBACK_BOOKS: Record<SubTab, string[]> = {
  'BOOK OF MORMON': BOM_BOOKS,
  'BIBLE': BIBLE_BOOKS,
  'D&C': DC_SECTIONS,
  'COPTIC': COPTIC_BOOKS,
  'DEAD SEA SCROLLS': DSS_BOOKS,
  'RUSSIAN ORTHODOX': RUSSIAN_BOOKS,
  'HYMNS': HYMNS_LIST,
};

/* ── Navigation state ── */

type NavMode = 'books' | 'chapters' | 'search-results';

export function ScripturesTab() {
  const [subTab, setSubTab] = useState<SubTab>('BOOK OF MORMON');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Book list (fetched from API or fallback)
  const [books, setBooks] = useState<BookInfo[]>([]);
  const [booksLoaded, setBooksLoaded] = useState(false);

  // Hymn data
  const [hymnsList, setHymnsList] = useState<HymnSummary[]>([]);
  const [selectedHymn, setSelectedHymn] = useState<HymnDetail | null>(null);

  // Navigation state
  const [navMode, setNavMode] = useState<NavMode>('books');
  const [selectedBook, setSelectedBook] = useState<string | null>(null);
  const [selectedBookChapters, setSelectedBookChapters] = useState<number>(0);
  const [_selectedChapter, setSelectedChapter] = useState<number | null>(null);

  // Content
  const [verses, setVerses] = useState<VerseResult[]>([]);
  const [searchResults, setSearchResults] = useState<VerseResult[]>([]);
  const [contentTitle, setContentTitle] = useState<string>('');

  /* ── Fetch books for current sub-tab ── */

  useEffect(() => {
    let cancelled = false;
    setBooksLoaded(false);
    setBooks([]);

    const volumeAbbrs = SUBTAB_VOLUMES[subTab];
    if (volumeAbbrs.length === 0) {
      // HYMNS — try fetching from hymns API
      (async () => {
        try {
          const resp = await fetch('/api/hymns/list');
          if (resp.ok) {
            const data = await resp.json();
            if (!cancelled) setHymnsList(data.hymns ?? []);
          }
        } catch { /* fallback to hardcoded list */ }
        if (!cancelled) setBooksLoaded(true);
      })();
      return;
    }

    (async () => {
      try {
        const allBooks: BookInfo[] = [];
        for (const vol of volumeAbbrs) {
          const resp = await fetch(`/api/scriptures/books?volume=${vol}`);
          if (resp.ok) {
            const data = await resp.json();
            if (data.books) allBooks.push(...data.books);
          }
        }
        if (!cancelled) {
          setBooks(allBooks);
          setBooksLoaded(true);
        }
      } catch {
        if (!cancelled) {
          setBooks([]);
          setBooksLoaded(true);
        }
      }
    })();

    return () => { cancelled = true; };
  }, [subTab]);

  /* ── Build the left-pane book list items ── */

  const getBookListItems = useCallback((): PipBoyListItem[] => {
    // Hymns: use API list if available, else fallback
    if (subTab === 'HYMNS') {
      if (hymnsList.length > 0) {
        return hymnsList.map((h) => ({
          id: String(h.id),
          label: `${h.hymn_number ?? ''} ${h.title}`.trim(),
          detail: h.author ?? undefined,
        }));
      }
      return FALLBACK_BOOKS[subTab].map((name) => ({
        id: name,
        label: name,
      }));
    }
    // If we got books from API, use them
    if (books.length > 0) {
      return books.map((b) => ({
        id: b.title,
        label: b.title,
        detail: b.num_chapters ? `${b.num_chapters} ch` : undefined,
      }));
    }
    // Fallback to hardcoded
    return FALLBACK_BOOKS[subTab].map((name) => ({
      id: name,
      label: name,
    }));
  }, [books, subTab, hymnsList]);

  /* ── Build chapter list for selected book ── */

  const getChapterListItems = useCallback((): PipBoyListItem[] => {
    if (!selectedBook || selectedBookChapters <= 0) return [];
    return Array.from({ length: selectedBookChapters }, (_, i) => ({
      id: String(i + 1),
      label: `Chapter ${i + 1}`,
    }));
  }, [selectedBook, selectedBookChapters]);

  /* ── Handle book selection ── */

  const handleBookSelect = useCallback(async (item: PipBoyListItem) => {
    const bookTitle = item.id;
    setSelectedBook(bookTitle);
    setSelectedChapter(null);
    setVerses([]);
    setSelectedHymn(null);
    setError(null);

    // HYMNS: fetch from hymns API
    if (subTab === 'HYMNS') {
      setLoading(true);
      const hymnLabel = item.label;
      setContentTitle(hymnLabel);
      try {
        // Try by numeric ID first (from API list), then fallback to search
        const hymnId = parseInt(bookTitle, 10);
        let resp: Response | null = null;
        if (!isNaN(hymnId) && hymnsList.length > 0) {
          resp = await fetch(`/api/hymns/${hymnId}`);
        }
        if (!resp || !resp.ok) {
          // Fallback: search by title
          const searchResp = await fetch(`/api/hymns/search?q=${encodeURIComponent(hymnLabel)}`);
          if (searchResp.ok) {
            const searchData = await searchResp.json();
            if (searchData.results?.length > 0) {
              resp = await fetch(`/api/hymns/${searchData.results[0].id}`);
            }
          }
        }
        if (resp && resp.ok) {
          const hymn: HymnDetail = await resp.json();
          setSelectedHymn(hymn);
          setContentTitle(`${hymn.hymn_number ? `#${hymn.hymn_number} ` : ''}${hymn.title}`);
          // Convert hymn verses to VerseResult format for display
          const hymnVerses: VerseResult[] = hymn.verses.map((v, i) => ({
            id: i,
            volume_title: null,
            book_title: hymn.title,
            chapter_number: null,
            verse_number: v.verse_type === 'chorus' ? null : v.verse_number,
            reference: v.verse_type === 'chorus' ? 'Chorus' : null,
            text: v.text,
          }));
          setVerses(hymnVerses);
        } else {
          setError('Hymn text not available. The hymn database may still be building.');
        }
      } catch {
        setError('Unable to connect to hymn database.');
      } finally {
        setLoading(false);
      }
      return;
    }

    // Determine number of chapters
    const apiBook = books.find((b) => b.title === bookTitle);
    const numChapters = apiBook?.num_chapters ?? 0;

    if (numChapters > 1) {
      // Show chapter list
      setSelectedBookChapters(numChapters);
      setNavMode('chapters');
      setContentTitle(bookTitle);
    } else {
      // Single-chapter book or D&C section — load chapter 1 directly
      setSelectedBookChapters(0);
      setNavMode('books');
      setLoading(true);
      setContentTitle(bookTitle);

      // For D&C sections, extract the number
      let queryBook = bookTitle;
      let queryChapter = 1;
      const sectionMatch = bookTitle.match(/^Section (\d+)$/);
      if (sectionMatch) {
        queryBook = 'Doctrine and Covenants';
        queryChapter = parseInt(sectionMatch[1], 10);
      }
      const odMatch = bookTitle.match(/^Official Declaration (\d+)$/);
      if (odMatch) {
        queryBook = 'Official Declaration';
        queryChapter = parseInt(odMatch[1], 10);
      }

      try {
        const resp = await fetch(
          `/api/scriptures/chapter?book=${encodeURIComponent(queryBook)}&chapter=${queryChapter}`
        );
        if (resp.ok) {
          const data = await resp.json();
          setVerses(data.verses ?? []);
          setContentTitle(data.verses?.[0]?.reference?.split(':')?.[0] ?? bookTitle);
        } else {
          setError('Chapter not found in database. The scripture database may still be building.');
          setVerses([]);
        }
      } catch {
        setError('Unable to connect to scripture database. Please ensure the API is running.');
        setVerses([]);
      } finally {
        setLoading(false);
      }
    }
  }, [books, subTab, hymnsList]);

  /* ── Handle chapter selection ── */

  const handleChapterSelect = useCallback(async (item: PipBoyListItem) => {
    if (!selectedBook) return;
    const chapterNum = parseInt(item.id, 10);
    setSelectedChapter(chapterNum);
    setLoading(true);
    setError(null);
    setVerses([]);

    // For D&C sections, the "book" for API is "Doctrine and Covenants"
    let queryBook = selectedBook;
    const sectionMatch = selectedBook.match(/^Section (\d+)$/);
    if (sectionMatch) {
      queryBook = 'Doctrine and Covenants';
    }

    const displayTitle = `${selectedBook} ${chapterNum}`;
    setContentTitle(displayTitle);

    try {
      const resp = await fetch(
        `/api/scriptures/chapter?book=${encodeURIComponent(queryBook)}&chapter=${chapterNum}`
      );
      if (resp.ok) {
        const data = await resp.json();
        setVerses(data.verses ?? []);
      } else {
        setError('Chapter not found in database. The scripture database may still be building.');
        setVerses([]);
      }
    } catch {
      setError('Unable to connect to scripture database. Please ensure the API is running.');
      setVerses([]);
    } finally {
      setLoading(false);
    }
  }, [selectedBook]);

  /* ── Handle search ── */

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError(null);
    setSearchResults([]);
    setNavMode('search-results');
    setSelectedBook(null);
    setSelectedChapter(null);
    setVerses([]);

    // Apply volume filter based on active sub-tab
    const volumeAbbrs = SUBTAB_VOLUMES[subTab];
    // For multi-volume tabs (like BIBLE = OT+NT), send comma-separated or skip filter
    const volumeParam = volumeAbbrs.length === 1 ? `&volume=${volumeAbbrs[0]}` :
                        volumeAbbrs.length > 1 ? `&volume=${volumeAbbrs.join(',')}` : '';

    try {
      const resp = await fetch(
        `/api/scriptures/search?q=${encodeURIComponent(searchQuery)}${volumeParam}&limit=50`
      );
      if (resp.ok) {
        const data = await resp.json();
        setSearchResults(data.results ?? []);
        if ((data.results ?? []).length === 0) {
          setError(`No results found for "${searchQuery}".`);
        }
      } else {
        setError('Search failed. The scripture database may not be available.');
        setSearchResults([]);
      }
    } catch {
      setError('Unable to connect to scripture database. Please ensure the API is running.');
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, subTab]);

  /* ── Handle search result selection ── */

  const handleSearchResultSelect = useCallback((item: PipBoyListItem) => {
    const verse = searchResults.find((r) => String(r.id) === item.id);
    if (verse) {
      setVerses([verse]);
      setContentTitle(verse.reference ?? 'Verse');
    }
  }, [searchResults]);

  /* ── Handle sub-tab change ── */

  const handleSubTabChange = (st: SubTab) => {
    setSubTab(st);
    setNavMode('books');
    setSelectedBook(null);
    setSelectedChapter(null);
    setSelectedBookChapters(0);
    setSearchResults([]);
    setVerses([]);
    setContentTitle('');
    setError(null);
    setSearchQuery('');
    setSelectedHymn(null);
  };

  /* ── Handle back navigation ── */

  const handleBack = () => {
    if (navMode === 'chapters') {
      setNavMode('books');
      setSelectedBook(null);
      setSelectedBookChapters(0);
      setSelectedChapter(null);
      setVerses([]);
      setContentTitle('');
      setError(null);
    } else if (navMode === 'search-results') {
      setNavMode('books');
      setSearchResults([]);
      setVerses([]);
      setContentTitle('');
      setError(null);
    }
  };

  /* ── Build left-pane list based on nav mode ── */

  const getLeftPaneItems = (): PipBoyListItem[] => {
    if (navMode === 'search-results') {
      return searchResults.map((r) => ({
        id: String(r.id),
        label: r.reference ?? `Verse ${r.id}`,
        detail: r.book_title ?? undefined,
      }));
    }
    if (navMode === 'chapters') {
      return getChapterListItems();
    }
    return getBookListItems();
  };

  const getLeftPaneHandler = () => {
    if (navMode === 'search-results') return handleSearchResultSelect;
    if (navMode === 'chapters') return handleChapterSelect;
    return handleBookSelect;
  };

  const getLeftPaneTitle = (): string => {
    if (navMode === 'search-results') return `RESULTS (${searchResults.length})`;
    if (navMode === 'chapters' && selectedBook) return selectedBook.toUpperCase();
    if (subTab === 'HYMNS') return 'HYMNAL';
    return 'BOOKS';
  };

  const SUB_TABS: SubTab[] = ['BOOK OF MORMON', 'BIBLE', 'D&C', 'COPTIC', 'DEAD SEA SCROLLS', 'RUSSIAN ORTHODOX', 'HYMNS'];

  return (
    <div style={{ fontFamily: 'var(--pip-font)' }}>
      {/* Sub-tabs */}
      <div className="flex gap-2 mb-5">
        {SUB_TABS.map((st) => (
          <button
            key={st}
            onClick={() => handleSubTabChange(st)}
            className="px-4 py-2 tracking-wider"
            style={{
              fontSize: 'var(--pip-text-sm)',
              fontWeight: 600,
              letterSpacing: 'var(--pip-tracking-wide)',
              color: subTab === st ? 'var(--pip-bg)' : 'var(--pip-dim)',
              backgroundColor: subTab === st ? 'var(--pip-primary)' : 'transparent',
              border: `1px solid ${subTab === st ? 'var(--pip-primary)' : 'var(--pip-dark)'}`,
            }}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 mb-5">
        <span style={{ fontSize: 'var(--pip-text-sm)', fontWeight: 600, letterSpacing: 'var(--pip-tracking-wide)', color: 'var(--pip-dim)' }}>SEARCH:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 bg-transparent outline-none px-3 py-2 border"
          style={{
            fontSize: 'var(--pip-text-base)',
            color: 'var(--pip-primary)',
            borderColor: 'var(--pip-dark)',
            fontFamily: 'var(--pip-font)',
          }}
          placeholder={`Search ${subTab.toLowerCase()} verses...`}
        />
        <button
          onClick={handleSearch}
          className="px-4 py-2"
          style={{ fontSize: 'var(--pip-text-sm)', fontWeight: 700, color: 'var(--pip-bg)', backgroundColor: 'var(--pip-primary)' }}
        >
          [SEARCH]
        </button>
      </div>

      {loading && (
        <div className="pip-glow-subtle mb-3" style={{ fontSize: 'var(--pip-text-sm)', color: 'var(--pip-dim)' }}>
          {navMode === 'search-results' ? 'SEARCHING SCRIPTURE DATABASE...' : 'LOADING SCRIPTURE TEXT...'}
        </div>
      )}

      <div className="flex gap-4">
        {/* Navigation / Results pane */}
        <div className="w-72 shrink-0">
          <div className="flex items-center gap-2 mb-2 pb-1 border-b" style={{ borderColor: 'var(--pip-dark)' }}>
            {(navMode === 'chapters' || navMode === 'search-results') && (
              <button
                onClick={handleBack}
                style={{
                  fontSize: 'var(--pip-text-sm)',
                  fontWeight: 700,
                  color: 'var(--pip-primary)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  fontFamily: 'var(--pip-font)',
                }}
              >
                {'<'} BACK
              </button>
            )}
            <span
              style={{
                fontSize: 'var(--pip-text-sm)',
                fontWeight: 700,
                letterSpacing: 'var(--pip-tracking-wider)',
                color: 'var(--pip-dim)',
                marginLeft: navMode !== 'books' ? 'auto' : undefined,
              }}
            >
              {getLeftPaneTitle()}
            </span>
          </div>

          {!booksLoaded && navMode === 'books' ? (
            <div className="py-4" style={{ fontSize: 'var(--pip-text-sm)', color: 'var(--pip-dim)' }}>
              LOADING BOOKS...
            </div>
          ) : (
            <PipBoyList
              items={getLeftPaneItems()}
              onSelect={getLeftPaneHandler()}
              maxHeight="calc(100vh - 320px)"
            />
          )}
        </div>

        {/* Content panel */}
        <div
          className="flex-1 p-4 border overflow-y-auto"
          style={{
            borderColor: 'var(--pip-dark)',
            backgroundColor: 'var(--pip-bg-tint)',
            maxHeight: 'calc(100vh - 260px)',
          }}
        >
          {error && (
            <div
              className="mb-4 p-3 border"
              style={{
                borderColor: 'var(--pip-dark)',
                fontSize: 'var(--pip-text-sm)',
                color: 'var(--pip-dim)',
              }}
            >
              {error}
            </div>
          )}

          {verses.length > 0 ? (
            <>
              <div
                className="pip-glow-text mb-3 pb-2 border-b"
                style={{ fontSize: 'var(--pip-text-lg)', color: 'var(--pip-highlight)', borderColor: 'var(--pip-dark)' }}
              >
                {contentTitle}
              </div>
              {selectedHymn && (selectedHymn.author || selectedHymn.composer) && (
                <div className="mb-3" style={{ fontSize: 'var(--pip-text-sm)', color: 'var(--pip-dim)' }}>
                  {selectedHymn.author && <span>Text: {selectedHymn.author}</span>}
                  {selectedHymn.author && selectedHymn.composer && <span> | </span>}
                  {selectedHymn.composer && <span>Music: {selectedHymn.composer}</span>}
                </div>
              )}
              <div className="space-y-2">
                {verses.map((v) => (
                  <div
                    key={v.id}
                    className="leading-relaxed"
                    style={{
                      fontSize: 'var(--pip-text-base)',
                      lineHeight: 'var(--pip-leading)',
                      color: 'var(--pip-secondary)',
                    }}
                  >
                    {v.reference === 'Chorus' ? (
                      <span
                        style={{
                          fontWeight: 700,
                          fontStyle: 'italic',
                          color: 'var(--pip-dim)',
                          marginRight: '0.5rem',
                          fontSize: 'var(--pip-text-sm)',
                        }}
                      >
                        Chorus:
                      </span>
                    ) : v.verse_number != null ? (
                      <span
                        style={{
                          fontWeight: 700,
                          color: 'var(--pip-primary)',
                          marginRight: '0.5rem',
                          fontSize: 'var(--pip-text-sm)',
                        }}
                      >
                        {v.verse_number}
                      </span>
                    ) : null}
                    {v.text}
                  </div>
                ))}
              </div>
            </>
          ) : !loading && !error ? (
            <div style={{ fontSize: 'var(--pip-text-base)', color: 'var(--pip-dim)' }}>
              <div className="mb-5">Select a book or search for verses to begin reading.</div>
              <div
                className="p-4 border"
                style={{ borderColor: 'var(--pip-dark)' }}
              >
                <div
                  className="mb-2 pb-1 border-b"
                  style={{
                    fontSize: 'var(--pip-text-sm)',
                    fontWeight: 700,
                    letterSpacing: 'var(--pip-tracking-wider)',
                    color: 'var(--pip-highlight)',
                    borderColor: 'var(--pip-dark)',
                  }}
                >
                  SCRIPTURE STUDY
                </div>
                <div style={{ fontSize: 'var(--pip-text-base)', color: 'var(--pip-secondary)' }}>
                  The scripture database provides offline access to the Book of Mormon,
                  Bible (KJV), Doctrine and Covenants, Coptic Bible, Dead Sea Scrolls,
                  Russian Orthodox Bible, and LDS Hymnal. Use the search function to
                  find specific verses or browse by book and chapter.
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
