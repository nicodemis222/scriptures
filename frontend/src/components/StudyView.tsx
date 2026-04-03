import { useState, useEffect } from 'react';
import { getAllHighlights, getAllNotes } from '../hooks/useScriptures';
import type { HighlightWithVerse, NoteWithVerse } from '../types/scriptures';
import { HighlightPen, QuillPen, XIcon } from './Icons';

interface StudyViewProps {
  onClose: () => void;
  onNavigate: (bookTitle: string, chapter: number) => void;
}

const COLOR_MAP: Record<string, string> = {
  gold: '#C5A55A',
  rose: '#C4726C',
  sky: '#6BA3BE',
  sage: '#7FA77F',
  lavender: '#9B8EC4',
};

type Tab = 'highlights' | 'notes';

export function StudyView({ onClose, onNavigate }: StudyViewProps) {
  const [activeTab, setActiveTab] = useState<Tab>('highlights');
  const [highlights, setHighlights] = useState<HighlightWithVerse[]>([]);
  const [notes, setNotes] = useState<NoteWithVerse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [h, n] = await Promise.all([
        getAllHighlights(500, 0),
        getAllNotes(500, 0),
      ]);
      setHighlights(h);
      setNotes(n);
    } catch (err) {
      console.error('Failed to load study data:', err);
    } finally {
      setLoading(false);
    }
  }

  function getColorHex(color: string): string {
    return COLOR_MAP[color] || COLOR_MAP.gold;
  }

  function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trimEnd() + '...';
  }

  return (
    <div className="study-view">
      <div className="study-view-header">
        <h2>My Study</h2>
        <button className="close-btn" onClick={onClose} aria-label="Close">
          <XIcon size={20} />
        </button>
      </div>

      <div className="study-tabs">
        <button
          className={`study-tab ${activeTab === 'highlights' ? 'active' : ''}`}
          onClick={() => setActiveTab('highlights')}
        >
          <HighlightPen size={16} />
          Highlights
        </button>
        <button
          className={`study-tab ${activeTab === 'notes' ? 'active' : ''}`}
          onClick={() => setActiveTab('notes')}
        >
          <QuillPen size={16} />
          Notes
        </button>
      </div>

      <div className="study-content">
        {loading ? (
          <div className="study-empty">
            <p>Loading...</p>
          </div>
        ) : activeTab === 'highlights' ? (
          highlights.length === 0 ? (
            <div className="study-empty">
              <HighlightPen size={32} />
              <p className="study-empty-title">No highlights yet</p>
              <p className="study-empty-desc">
                Long press any verse while reading to add a highlight.
              </p>
            </div>
          ) : (
            <div className="study-list">
              {highlights.map((h) => (
                <div
                  key={h.id}
                  className="study-item ornamental-card"
                  style={{ borderLeft: `4px solid ${getColorHex(h.color)}` }}
                  onClick={() => onNavigate(h.book_title, h.chapter_number)}
                >
                  <span className="study-item-reference">
                    {h.reference || `${h.book_title} ${h.chapter_number}:${h.verse_number}`}
                  </span>
                  <p className="study-item-text">{truncateText(h.text, 150)}</p>
                </div>
              ))}
            </div>
          )
        ) : (
          notes.length === 0 ? (
            <div className="study-empty">
              <QuillPen size={32} />
              <p className="study-empty-title">No notes yet</p>
              <p className="study-empty-desc">
                Tap the note icon on any verse to add a personal note.
              </p>
            </div>
          ) : (
            <div className="study-list">
              {notes.map((n) => (
                <div
                  key={n.id}
                  className="study-item ornamental-card"
                  onClick={() => onNavigate(n.book_title, n.chapter_number)}
                >
                  <span className="study-item-reference">
                    {n.reference || `${n.book_title} ${n.chapter_number}:${n.verse_number}`}
                  </span>
                  <p className="study-item-verse">{truncateText(n.verse_text, 100)}</p>
                  <p className="study-item-note">{truncateText(n.text, 200)}</p>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
