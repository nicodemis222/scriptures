import { useState, useRef, useEffect } from 'react';
import { searchScriptures, searchHymns } from '../hooks/useScriptures';
import type { SubTab } from '../data/constants';
import type { VerseResult, HymnSummary } from '../types/scriptures';
import { SearchIcon } from './Icons';
import { showToast } from './Toast';

interface SearchBarProps {
  activeTab: SubTab;
  onVerseSelect: (verse: VerseResult) => void;
  onHymnSelect: (hymn: HymnSummary) => void;
  onSearchResults: (results: VerseResult[]) => void;
}

export function SearchBar({ activeTab, onVerseSelect, onHymnSelect, onSearchResults }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<VerseResult[]>([]);
  const [hymnResults, setHymnResults] = useState<HymnSummary[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async () => {
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    setResults([]);
    setHymnResults([]);

    try {
      if (activeTab === 'HYMNS') {
        const hymns = await searchHymns(q);
        setHymnResults(hymns);
        setShowDropdown(hymns.length > 0);
      } else {
        // Always search ALL scriptures globally — no volume filter
        const allVerses = await searchScriptures(q, undefined, 100);
        setResults(allVerses);
        setShowDropdown(allVerses.length > 0);
        onSearchResults(allVerses);
      }
    } catch (err) {
      console.error('Search failed:', err);
      showToast('Search failed', 'error');
      setResults([]);
      setHymnResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') void handleSearch();
    if (e.key === 'Escape') setShowDropdown(false);
  };

  const formatRef = (v: VerseResult): string => {
    if (v.reference && v.reference.trim()) return v.reference;
    const book = v.book_title || 'Unknown';
    const ch = v.chapter_number ?? '';
    const vs = v.verse_number ?? '';
    return `${book} ${ch}:${vs}`;
  };

  return (
    <div className="search-bar-container">
      <div className="search-bar">
        <SearchIcon size={18} className="search-bar-icon" />
        <input
          ref={inputRef}
          type="text"
          className="search-input"
          placeholder="Search all scriptures..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0 || hymnResults.length > 0) setShowDropdown(true);
          }}
        />
        <button className="search-btn" onClick={handleSearch} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {showDropdown && (
        <div className="search-dropdown" ref={dropdownRef}>
          {activeTab === 'HYMNS'
            ? hymnResults.map((h) => (
                <button
                  key={h.id}
                  className="search-result-item"
                  onClick={() => {
                    onHymnSelect(h);
                    setShowDropdown(false);
                  }}
                >
                  <span className="search-result-ref">
                    {h.hymn_number ? `#${h.hymn_number}` : ''} {h.title}
                  </span>
                  {h.author && (
                    <span className="search-result-snippet">{h.author}</span>
                  )}
                </button>
              ))
            : results.slice(0, 8).map((v) => (
                <button
                  key={v.id}
                  className="search-result-item"
                  onClick={() => {
                    onVerseSelect(v);
                    setShowDropdown(false);
                  }}
                >
                  <span className="search-result-ref">{formatRef(v)}</span>
                  {v.volume_title && (
                    <span className="search-result-snippet" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {v.volume_title}
                    </span>
                  )}
                  <span className="search-result-snippet">
                    {v.text.length > 100 ? v.text.slice(0, 100) + '...' : v.text}
                  </span>
                </button>
              ))}
          {results.length > 8 && (
            <div style={{ padding: '8px 16px', fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
              Showing 8 of {results.length} results — see full list below
            </div>
          )}
        </div>
      )}
    </div>
  );
}
