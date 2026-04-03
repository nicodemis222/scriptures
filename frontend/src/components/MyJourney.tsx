import { useState, useCallback, useEffect } from 'react';
import { getAllHighlights, getAllNotes, aiQuery, getSetting, setSetting } from '../hooks/useScriptures';
import { BookOpen, BrainIcon, XIcon } from './Icons';
import type { HighlightWithVerse, NoteWithVerse } from '../types/scriptures';

interface MyJourneyProps {
  onClose: () => void;
  onNavigate: (bookTitle: string, chapter: number) => void;
}

interface JourneyData {
  response: string;
  highlightCount: number;
  noteCount: number;
  bookCount: number;
  topBooks: string;
  colorInsights: string;
  generatedAt: string;
}

const COLOR_MEANING: Record<string, string> = {
  gold: 'Key Doctrine',
  rose: 'Covenants & Promises',
  sky: 'Prophecy',
  sage: 'Commandments',
  lavender: 'Personal Inspiration',
};

export function MyJourney({ onClose, onNavigate }: MyJourneyProps) {
  const [loading, setLoading] = useState(false);
  const [journey, setJourney] = useState<JourneyData | null>(null);
  const [empty, setEmpty] = useState(false);

  // Load saved journey on mount
  useEffect(() => {
    void (async () => {
      try {
        const saved = await getSetting('journeyData');
        if (saved) {
          const data: JourneyData = JSON.parse(saved);
          setJourney(data);
        }
      } catch { /* no saved journey */ }
    })();
  }, []);

  const saveJourney = useCallback(async (data: JourneyData) => {
    try {
      await setSetting('journeyData', JSON.stringify(data));
    } catch { /* save failed silently */ }
  }, []);

  const generate = useCallback(async () => {
    setLoading(true);
    try {
      const [highlights, notes] = await Promise.all([
        getAllHighlights(500),
        getAllNotes(500),
      ]);

      if (highlights.length === 0 && notes.length === 0) {
        setEmpty(true);
        setLoading(false);
        return;
      }

      const bookMap = new Map<string, number>();
      const colorMap = new Map<string, number>();

      highlights.forEach((h: HighlightWithVerse) => {
        bookMap.set(h.book_title, (bookMap.get(h.book_title) || 0) + 1);
        colorMap.set(h.color, (colorMap.get(h.color) || 0) + 1);
      });

      notes.forEach((n: NoteWithVerse) => {
        bookMap.set(n.book_title, (bookMap.get(n.book_title) || 0) + 1);
      });

      const topBooks = [...bookMap.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([book, count]) => `${book} (${count})`)
        .join(', ');

      const colorInsights = [...colorMap.entries()]
        .sort((a, b) => b[1] - a[1])
        .map(([color, count]) => `${COLOR_MEANING[color] || color}: ${count}`)
        .join(', ');

      const sampleNotes = notes
        .slice(0, 10)
        .map((n: NoteWithVerse) => `[${n.reference || n.book_title}]: ${n.text}`)
        .join('\n');

      const sampleHighlights = highlights
        .filter((h: HighlightWithVerse) => h.highlighted_text)
        .slice(0, 10)
        .map((h: HighlightWithVerse) => `[${h.reference || h.book_title}]: ${h.highlighted_text}`)
        .join('\n');

      const prompt = `You are a personal scripture study guide. Based on this person's study patterns, provide a warm, insightful assessment in these sections:

## Your Study Summary
A brief, encouraging summary of their study journey. Mention specific books and themes.

## Themes You're Exploring
3-5 themes they seem drawn to based on their highlights and notes.

## Spiritual Growth Assessment
Where they are in their study journey — what areas they're strong in, what they might explore next.

## Recommended Reading Path
5 specific scripture references to read next with brief explanations. Format as "Book Chapter:Verse".

## Weekly Study Goal
A gentle, achievable suggestion for the coming week.

Study Data:
- Highlights: ${highlights.length}, Notes: ${notes.length}
- Most studied: ${topBooks}
- Focus areas: ${colorInsights}
${sampleNotes ? `\nSample notes:\n${sampleNotes}` : ''}
${sampleHighlights ? `\nSample highlights:\n${sampleHighlights}` : ''}

Be encouraging, specific, and reverent.`;

      const result = await aiQuery(prompt);

      const data: JourneyData = {
        response: result.response,
        highlightCount: highlights.length,
        noteCount: notes.length,
        bookCount: bookMap.size,
        topBooks,
        colorInsights,
        generatedAt: new Date().toLocaleDateString(),
      };

      setJourney(data);
      await saveJourney(data);
    } catch (err) {
      console.error('Journey generation failed:', err);
      setJourney({
        response: 'Unable to generate your study journey. Please make sure Ollama is running and try again.',
        highlightCount: 0,
        noteCount: 0,
        bookCount: 0,
        topBooks: '',
        colorInsights: '',
        generatedAt: new Date().toLocaleDateString(),
      });
    } finally {
      setLoading(false);
    }
  }, [saveJourney]);

  const handleScriptureClick = useCallback((text: string) => {
    const match = text.match(/([\w\s]+?)\s+(\d+)/);
    if (match) {
      onNavigate(match[1].trim(), parseInt(match[2], 10));
    }
  }, [onNavigate]);

  return (
    <div className="my-journey-layout">
      {/* Main content */}
      <div className="my-journey">
        <div className="settings-header">
          <h2>My Journey</h2>
          <button className="close-btn" onClick={onClose} aria-label="Close">
            <XIcon size={20} />
          </button>
        </div>

        {!journey && !loading && !empty && (
          <>
            <p style={{ fontFamily: 'var(--font-serif)', fontSize: 16, color: 'var(--text-light)', marginBottom: 24, lineHeight: 1.8 }}>
              Your personal scripture study companion. Generate an AI-powered analysis of your highlights,
              notes, and reading patterns to receive personalized guidance for your study journey.
            </p>
            <button className="journey-generate-btn" onClick={() => void generate()}>
              <BrainIcon size={24} />
              Generate My Journey
            </button>
          </>
        )}

        {loading && (
          <div className="journey-empty">
            <BrainIcon size={36} />
            <p style={{ marginTop: 16 }}>Analyzing your study patterns...</p>
            <p style={{ marginTop: 8, fontSize: 14, opacity: 0.7 }}>This may take a moment while the AI reviews your highlights and notes.</p>
          </div>
        )}

        {empty && (
          <div className="journey-empty">
            <BookOpen size={48} />
            <p style={{ marginTop: 16 }}>Start highlighting and taking notes to build your personal study journey.</p>
            <p style={{ marginTop: 8, fontSize: 14, opacity: 0.7 }}>
              As you study, your highlights and notes will reveal patterns and themes
              that guide your scripture exploration.
            </p>
          </div>
        )}

        {journey && (
          <>
            {/* Stats bar */}
            <div className="journey-stats">
              <div className="journey-stat ornamental-card">
                <div className="journey-stat-number">{journey.highlightCount}</div>
                <div className="journey-stat-label">Highlights</div>
              </div>
              <div className="journey-stat ornamental-card">
                <div className="journey-stat-number">{journey.noteCount}</div>
                <div className="journey-stat-label">Notes</div>
              </div>
              <div className="journey-stat ornamental-card">
                <div className="journey-stat-number">{journey.bookCount}</div>
                <div className="journey-stat-label">Books</div>
              </div>
            </div>

            {/* AI Response */}
            <div className="journey-content">{journey.response}</div>

            {/* Regenerate */}
            <div style={{ marginTop: 32, textAlign: 'center' }}>
              <button
                className="journey-generate-btn"
                onClick={() => void generate()}
                style={{ width: 'auto', padding: '12px 32px', fontSize: 14, borderWidth: 1 }}
                disabled={loading}
              >
                <BrainIcon size={16} />
                {loading ? 'Regenerating...' : 'Refresh Journey'}
              </button>
              {journey.generatedAt && (
                <p style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                  Last generated: {journey.generatedAt}
                </p>
              )}
            </div>
          </>
        )}
      </div>

      {/* Right sidebar — Study Lifecycle Summary */}
      {journey && journey.highlightCount > 0 && (
        <div className="journey-sidebar">
          <h3>Study Overview</h3>

          {/* Top books */}
          {journey.topBooks && (
            <div className="journey-sidebar-section">
              <h4>Most Studied</h4>
              <div className="journey-sidebar-list">
                {journey.topBooks.split(', ').map((book, i) => {
                  const match = book.match(/^(.+?)\s*\((\d+)\)$/);
                  return (
                    <button
                      key={i}
                      className="journey-sidebar-item"
                      onClick={() => match && handleScriptureClick(match[1])}
                    >
                      <span className="journey-sidebar-item-name">{match ? match[1] : book}</span>
                      {match && <span className="journey-sidebar-item-count">{match[2]}</span>}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Color focus */}
          {journey.colorInsights && (
            <div className="journey-sidebar-section">
              <h4>Study Focus</h4>
              <div className="journey-sidebar-colors">
                {journey.colorInsights.split(', ').map((item, i) => {
                  const parts = item.split(': ');
                  const label = parts[0];
                  const count = parts[1];
                  const colorName = Object.entries(COLOR_MEANING).find(([, v]) => v === label)?.[0] || 'gold';
                  return (
                    <div key={i} className="journey-color-item">
                      <span className={`journey-color-dot color-${colorName}`} />
                      <span className="journey-color-label">{label}</span>
                      <span className="journey-color-count">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quick tip */}
          <div className="journey-sidebar-section">
            <h4>Quick Tip</h4>
            <p style={{ fontSize: 12, color: 'var(--text-light)', lineHeight: 1.6, fontFamily: 'var(--font-serif)' }}>
              Try highlighting with different colors to track themes across books.
              Gold for doctrine, Rose for covenants, Sky for prophecy.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
