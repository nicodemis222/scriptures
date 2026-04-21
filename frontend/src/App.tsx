import { useState, useEffect, useCallback, useRef } from 'react';
import { listen } from '@tauri-apps/api/event';
import { VolumeNav } from './components/VolumeNav';
import { BookList } from './components/BookList';
import { ChapterGrid } from './components/ChapterGrid';
import { VerseDisplay } from './components/VerseDisplay';
import { SearchBar } from './components/SearchBar';
import { HymnViewer } from './components/HymnViewer';
import { AssetManager } from './components/AssetManager';
import { Tutorial } from './components/Tutorial';
import { StudyView } from './components/StudyView';
import { SettingsPanel } from './components/SettingsPanel';
import { MyJourney } from './components/MyJourney';
import { AIAssistant } from './components/AIAssistant';
import { FirstRunSetup } from './components/FirstRunSetup';
import { ToastContainer } from './components/Toast';
import {
  SunIcon,
  MoonIcon,
  BookmarkRibbon,
  GlobeIcon,
  SpeakerIcon,
  BrainIcon,
  GearIcon,
  BookOpen,
} from './components/Icons';
import { getBooks, getChapter, getHymns, getHymn, getSetting } from './hooks/useScriptures';
import { SUBTAB_VOLUMES, FALLBACK_BOOKS, HYMNS_LIST, DEFAULT_TAB_ORDER } from './data/constants';
import type { SubTab } from './data/constants';
import type { BookInfo, VerseResult, HymnSummary, HymnDetail } from './types/scriptures';

type ViewMode = 'books' | 'chapters' | 'verses' | 'search' | 'assets' | 'hymns' | 'study' | 'settings' | 'journey';

function App() {
  const [activeTab, setActiveTab] = useState<SubTab>('BOOK OF MORMON');
  const [tabOrder, setTabOrder] = useState<SubTab[]>(() => {
    const saved = localStorage.getItem('tabOrder');
    if (saved) {
      try { return JSON.parse(saved); } catch { /* fall through */ }
    }
    return DEFAULT_TAB_ORDER;
  });
  const [books, setBooks] = useState<BookInfo[]>([]);
  const [selectedBook, setSelectedBook] = useState<BookInfo | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null);
  const [verses, setVerses] = useState<VerseResult[]>([]);
  const [searchResults, setSearchResults] = useState<VerseResult[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('books');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Hymns state
  const [hymnsList, setHymnsList] = useState<HymnSummary[]>([]);
  const [selectedHymn, setSelectedHymn] = useState<HymnDetail | null>(null);

  // AI panel
  const [showAI, setShowAI] = useState(false);

  // Tutorial
  const [showTutorial, setShowTutorial] = useState(
    () => localStorage.getItem('tutorial_completed') !== 'true'
  );

  // First-run AI setup (shown after tutorial on fresh install)
  const [showFirstRunSetup, setShowFirstRunSetup] = useState(
    () => localStorage.getItem('setup_completed') !== 'true'
  );

  // TTS setup progress (global banner)
  const [ttsSetup, setTtsSetup] = useState<{ message: string; percent: number } | null>(null);
  const ttsTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const unlisten = listen<{ stage: string; message: string; percent?: number }>('tts-setup-progress', (event) => {
      const { stage, message, percent } = event.payload;
      if (ttsTimerRef.current) clearTimeout(ttsTimerRef.current);
      if (stage === 'complete') {
        setTtsSetup({ message, percent: 100 });
        ttsTimerRef.current = setTimeout(() => setTtsSetup(null), 3000);
      } else if (stage === 'error') {
        setTtsSetup({ message, percent: 0 });
        ttsTimerRef.current = setTimeout(() => setTtsSetup(null), 10000);
      } else {
        setTtsSetup({ message, percent: percent ?? 0 });
      }
    });
    return () => {
      if (ttsTimerRef.current) clearTimeout(ttsTimerRef.current);
      unlisten.then(fn => fn());
    };
  }, []);

  const handleTutorialComplete = () => {
    setShowTutorial(false);
    localStorage.setItem('tutorial_completed', 'true');
  };

  const handleShowTutorial = () => {
    setShowTutorial(true);
  };

  const handleFirstRunSetupComplete = () => {
    setShowFirstRunSetup(false);
    localStorage.setItem('setup_completed', 'true');
  };

  // Dark mode
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    getSetting('fontSize').then(size => {
      if (size) document.documentElement.style.setProperty('--verse-size', `${size}px`);
    }).catch(() => {});
  }, []);

  /* -- Fetch books when tab changes -- */
  useEffect(() => {
    let cancelled = false;

    setBooks([]);
    setSelectedBook(null);
    setSelectedChapter(null);
    setVerses([]);
    setSearchResults([]);
    setSelectedHymn(null);
    setError(null);

    const volumeAbbrs = SUBTAB_VOLUMES[activeTab];

    if (activeTab === 'HYMNS') {
      setViewMode('hymns');
      (async () => {
        try {
          const hymns = await getHymns();
          if (!cancelled) setHymnsList(hymns);
        } catch {
          if (!cancelled) setHymnsList([]);
        }
      })();
      return () => { cancelled = true; };
    }

    setViewMode('books');

    if (volumeAbbrs.length === 0) return;

    setLoading(true);
    (async () => {
      try {
        const results = await Promise.all(volumeAbbrs.map(vol => getBooks(vol)));
        const allBooks: BookInfo[] = results.flat();
        if (!cancelled) {
          setBooks(allBooks);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          const fallback = FALLBACK_BOOKS[activeTab];
          setBooks(
            fallback.map((title, i) => ({
              id: i,
              title,
              abbreviation: null,
              long_title: null,
              num_chapters: null,
              book_order: i,
              volume_title: activeTab,
            }))
          );
          setLoading(false);
        }
      }
    })();

    return () => { cancelled = true; };
  }, [activeTab]);

  /* -- Handlers -- */

  const handleTabChange = (tab: SubTab) => {
    setActiveTab(tab);
  };

  const handleReorder = useCallback((newOrder: SubTab[]) => {
    setTabOrder(newOrder);
    localStorage.setItem('tabOrder', JSON.stringify(newOrder));
  }, []);

  const handleBookSelect = useCallback(async (book: BookInfo) => {
    setSelectedBook(book);
    setSelectedChapter(null);
    setVerses([]);
    setError(null);
    setSelectedHymn(null);

    const sectionMatch = book.title.match(/^Section (\d+)$/);
    const odMatch = book.title.match(/^Official Declaration (\d+)$/);

    if (sectionMatch || odMatch) {
      const queryBook = sectionMatch ? 'Doctrine and Covenants' : 'Official Declaration';
      const queryChapter = parseInt((sectionMatch ?? odMatch)![1], 10);

      setLoading(true);
      try {
        const chapterVerses = await getChapter(queryBook, queryChapter);
        setVerses(chapterVerses);
        setSelectedChapter(queryChapter);
        setViewMode('verses');
        document.querySelector('.app-content')?.scrollTo(0, 0);
      } catch {
        setError('Unable to load chapter. The backend may not be running.');
      } finally {
        setLoading(false);
      }
      return;
    }

    if (book.num_chapters != null && book.num_chapters > 1) {
      setViewMode('chapters');
    } else {
      setLoading(true);
      try {
        const chapterVerses = await getChapter(book.title, 1);
        setVerses(chapterVerses);
        setSelectedChapter(1);
        setViewMode('verses');
        document.querySelector('.app-content')?.scrollTo(0, 0);
      } catch {
        setError('Unable to load chapter. The backend may not be running.');
      } finally {
        setLoading(false);
      }
    }
  }, []);

  const handleChapterSelect = useCallback(async (chapter: number) => {
    if (!selectedBook) return;

    setSelectedChapter(chapter);
    setLoading(true);
    setError(null);

    try {
      const chapterVerses = await getChapter(selectedBook.title, chapter);
      setVerses(chapterVerses);
      setViewMode('verses');
      document.querySelector('.app-content')?.scrollTo(0, 0);
    } catch {
      setError('Unable to load chapter. The backend may not be running.');
    } finally {
      setLoading(false);
    }
  }, [selectedBook]);

  const handleVerseSelect = useCallback((verse: VerseResult) => {
    setVerses([verse]);
    setViewMode('search');
  }, []);

  const handleSearchResults = useCallback((results: VerseResult[]) => {
    setSearchResults(results);
    if (results.length > 0) {
      setVerses(results);
      setViewMode('search');
    }
  }, []);

  const handleHymnSelect = useCallback(async (hymn: HymnSummary) => {
    setLoading(true);
    setError(null);
    try {
      const detail = await getHymn(hymn.id);
      setSelectedHymn(detail);
      setViewMode('hymns');
    } catch {
      setError('Unable to load hymn. The backend may not be running.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleHymnBack = () => {
    setSelectedHymn(null);
    setViewMode('hymns');
  };

  const handleNextBook = useCallback(async () => {
    if (!selectedBook) return;
    const idx = books.findIndex((b) => b.id === selectedBook.id);
    if (idx < 0 || idx >= books.length - 1) return;
    const nextBook = books[idx + 1];
    setSelectedBook(nextBook);
    setLoading(true);
    setError(null);
    try {
      const chapterVerses = await getChapter(nextBook.title, 1);
      setVerses(chapterVerses);
      setSelectedChapter(1);
      setViewMode('verses');
      document.querySelector('.app-content')?.scrollTo(0, 0);
    } catch {
      setError('Unable to load chapter. The backend may not be running.');
    } finally {
      setLoading(false);
    }
  }, [selectedBook, books]);

  const handlePrevBook = useCallback(async () => {
    if (!selectedBook) return;
    const idx = books.findIndex((b) => b.id === selectedBook.id);
    if (idx <= 0) return;
    const prevBook = books[idx - 1];
    setSelectedBook(prevBook);
    const lastChapter = prevBook.num_chapters ?? 1;
    setLoading(true);
    setError(null);
    try {
      const chapterVerses = await getChapter(prevBook.title, lastChapter);
      setVerses(chapterVerses);
      setSelectedChapter(lastChapter);
      setViewMode('verses');
      document.querySelector('.app-content')?.scrollTo(0, 0);
    } catch {
      setError('Unable to load chapter. The backend may not be running.');
    } finally {
      setLoading(false);
    }
  }, [selectedBook, books]);

  const handleBackToBooks = () => {
    setSelectedBook(null);
    setSelectedChapter(null);
    setVerses([]);
    setViewMode('books');
    setError(null);
  };

  const handleBackToChapters = () => {
    setSelectedChapter(null);
    setVerses([]);
    setViewMode('chapters');
    setError(null);
  };

  // Navigate from study view to a specific chapter
  const handleStudyNavigate = useCallback(async (bookTitle: string, chapter: number) => {
    setViewMode('books'); // reset first
    setLoading(true);
    setError(null);
    try {
      const chapterVerses = await getChapter(bookTitle, chapter);
      setVerses(chapterVerses);
      setSelectedChapter(chapter);
      setSelectedBook({ id: 0, title: bookTitle, abbreviation: null, long_title: null, num_chapters: null, book_order: null, volume_title: null });
      setViewMode('verses');
    } catch {
      setError('Unable to load chapter.');
    } finally {
      setLoading(false);
    }
  }, []);

  /* -- Hymn list as BookInfo for sidebar -- */

  const hymnBooks: BookInfo[] =
    hymnsList.length > 0
      ? hymnsList.map((h) => ({
          id: h.id,
          title: `${h.hymn_number ?? ''} ${h.title}`.trim(),
          abbreviation: null,
          long_title: h.author,
          num_chapters: null,
          book_order: h.hymn_number,
          volume_title: 'Hymns',
        }))
      : HYMNS_LIST.map((title, i) => ({
          id: i,
          title,
          abbreviation: null,
          long_title: null,
          num_chapters: null,
          book_order: i + 1,
          volume_title: 'Hymns',
        }));

  const handleHymnBookSelect = useCallback(async (book: BookInfo) => {
    const match = hymnsList.find((h) => h.id === book.id);
    if (match) {
      await handleHymnSelect(match);
    } else {
      setError('Hymn data not available from backend.');
    }
  }, [hymnsList, handleHymnSelect]);

  /* -- Volume title for breadcrumb -- */
  const volumeTitle = activeTab !== 'HYMNS' ? activeTab : undefined;

  /* -- Render content area -- */

  const renderContent = () => {
    if (viewMode === 'assets') {
      return <AssetManager onClose={() => setViewMode('books')} />;
    }

    if (viewMode === 'study') {
      return <StudyView onClose={() => setViewMode('books')} onNavigate={handleStudyNavigate} />;
    }

    if (viewMode === 'settings') {
      return (
        <SettingsPanel
          onClose={() => setViewMode('books')}
          theme={theme}
          onThemeChange={setTheme}
          onShowTutorial={handleShowTutorial}
        />
      );
    }

    if (viewMode === 'journey') {
      return (
        <MyJourney
          onClose={() => setViewMode('books')}
          onNavigate={handleStudyNavigate}
        />
      );
    }

    if (error) {
      return (
        <div className="content-area">
          <div className="error-banner">{error}</div>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="content-area">
          <div className="loading-indicator">Loading...</div>
        </div>
      );
    }

    // Hymns tab with selected hymn
    if (activeTab === 'HYMNS' && selectedHymn) {
      return <HymnViewer hymn={selectedHymn} onBack={handleHymnBack} />;
    }

    // Verses view
    if (viewMode === 'verses' && verses.length > 0 && selectedBook) {
      return (
        <VerseDisplay
          verses={verses}
          bookTitle={selectedBook.title}
          chapterNumber={selectedChapter}
          volumeTitle={volumeTitle}
          numChapters={selectedBook.num_chapters ?? undefined}
          onChapterChange={handleChapterSelect}
          onBookClick={handleBackToChapters}
          onVolumeClick={handleBackToBooks}
          onNextBook={handleNextBook}
          onPrevBook={handlePrevBook}
        />
      );
    }

    // Search results — empty state
    if (viewMode === 'search' && verses.length === 0) {
      return (
        <div className="content-area">
          <h2 className="verse-header">Search Results</h2>
          <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-serif)', fontSize: 16, marginTop: 16 }}>
            No verses found. Try different keywords or search in another volume.
          </p>
        </div>
      );
    }

    // Search results
    if (viewMode === 'search' && verses.length > 0) {
      return (
        <div className="content-area">
          <h2 className="verse-header">Search Results</h2>
          <p className="search-result-count">{verses.length} verse{verses.length !== 1 ? 's' : ''} found</p>
          <div className="search-results-list">
            {verses.map((v) => {
              const ref = (v.reference && v.reference.trim())
                ? v.reference
                : `${v.book_title || 'Unknown'} ${v.chapter_number ?? ''}:${v.verse_number ?? ''}`;
              return (
                <button
                  key={v.id}
                  className="search-result-card ornamental-card"
                  onClick={() => {
                    if (v.book_title && v.chapter_number) {
                      void handleStudyNavigate(v.book_title, v.chapter_number);
                    }
                  }}
                >
                  <div className="search-result-header">
                    <span className="search-result-ref">{ref}</span>
                    {v.volume_title && (
                      <span className="search-result-volume">{v.volume_title}</span>
                    )}
                  </div>
                  <p className="search-result-text">
                    <sup className="verse-number">{v.verse_number}</sup>
                    {v.text}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      );
    }

    // Chapter grid
    if (viewMode === 'chapters' && selectedBook && selectedBook.num_chapters) {
      return (
        <ChapterGrid
          bookTitle={selectedBook.title}
          numChapters={selectedBook.num_chapters}
          onSelect={handleChapterSelect}
        />
      );
    }

    // Default: welcome
    return (
      <div className="content-area">
        <div className="welcome">
          <h2 className="welcome-title">Scripture Study</h2>
          <p className="welcome-text">
            "For the word of God is quick, and powerful, and sharper than any two-edged sword."
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      {/* Top navigation */}
      <header className="app-header">
        <span className="app-title">Scriptures</span>
        <VolumeNav activeTab={activeTab} onTabChange={handleTabChange} tabOrder={tabOrder} onReorder={handleReorder} />
        <div className="header-actions">
          <button
            className="header-btn"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <SunIcon size={18} /> : <MoonIcon size={18} />}
          </button>
          <button
            className="header-btn"
            onClick={() => setViewMode(viewMode === 'study' ? 'books' : 'study')}
            title="My Study"
          >
            <BookmarkRibbon size={18} />
          </button>
          <button className="header-btn" disabled title="Read Aloud (use controls in verse view)">
            <SpeakerIcon size={18} />
          </button>
          <button className="header-btn" disabled title="Language (coming soon)">
            <GlobeIcon size={18} />
          </button>
          <button
            className="header-btn"
            onClick={() => setShowAI(!showAI)}
            title="AI Assistant"
          >
            <BrainIcon size={18} />
          </button>
          <button
            className="header-btn"
            onClick={handleShowTutorial}
            title="Tutorial"
          >
            <BookOpen size={18} />
          </button>
          <button
            className="header-btn"
            onClick={() => setViewMode(viewMode === 'settings' ? 'books' : 'settings')}
            title="Settings"
          >
            <GearIcon size={18} />
          </button>
        </div>
      </header>

      {/* Search */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'var(--bg)', flexShrink: 0, borderBottom: '1px solid var(--border-light)', paddingRight: 20 }}>
        <div style={{ flex: 1 }}>
          <SearchBar
            activeTab={activeTab}
            onVerseSelect={handleVerseSelect}
            onHymnSelect={handleHymnSelect}
            onSearchResults={handleSearchResults}
          />
        </div>
        <button className="journey-btn" onClick={() => setViewMode('journey')} title="My Journey">
          <BookOpen size={16} /> My Journey
        </button>
      </div>

      {/* TTS setup progress banner */}
      {ttsSetup && (
        <div className="tts-global-banner">
          <div className="tts-global-banner-text">
            <span className="tts-global-banner-icon">&#9835;</span>
            {ttsSetup.message}
            {ttsSetup.percent > 0 && ttsSetup.percent < 100 && (
              <span className="tts-global-banner-pct">{ttsSetup.percent}%</span>
            )}
          </div>
          <div className="tts-global-banner-bar">
            <div
              className="tts-global-banner-fill"
              style={{ width: `${ttsSetup.percent}%` }}
            />
          </div>
        </div>
      )}

      {/* Main layout */}
      <div className="app-body">
        {/* Sidebar */}
        {viewMode !== 'assets' && viewMode !== 'study' && viewMode !== 'settings' && viewMode !== 'journey' && (
          <BookList
            books={activeTab === 'HYMNS' ? hymnBooks : books}
            onSelect={activeTab === 'HYMNS' ? handleHymnBookSelect : handleBookSelect}
            selectedBook={selectedBook}
            selectedChapter={selectedChapter}
            title={
              activeTab === 'HYMNS'
                ? 'Hymnal'
                : viewMode === 'search'
                  ? `Results (${searchResults.length})`
                  : 'Books'
            }
            onBack={
              viewMode === 'chapters' || viewMode === 'verses'
                ? handleBackToBooks
                : undefined
            }
          />
        )}

        {/* Content */}
        <main className="app-content">
          {renderContent()}
        </main>

        {/* AI Assistant Panel */}
        {showAI && (
          <AIAssistant
            bookTitle={selectedBook?.title ?? null}
            chapterNumber={selectedChapter}
            onClose={() => setShowAI(false)}
          />
        )}
      </div>

      {/* Tutorial overlay */}
      {showTutorial && <Tutorial onComplete={handleTutorialComplete} />}

      {/* First-run AI setup — shown after tutorial is dismissed */}
      {!showTutorial && showFirstRunSetup && (
        <FirstRunSetup onComplete={handleFirstRunSetupComplete} />
      )}

      <ToastContainer />
    </div>
  );
}

export default App;
