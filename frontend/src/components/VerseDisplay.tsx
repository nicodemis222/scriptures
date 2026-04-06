import { useState, useEffect, useCallback, useRef } from 'react';
import type { VerseResult, Highlight, Note } from '../types/scriptures';
import {
  getHighlightsForChapter,
  getNotesForChapter,
  addHighlight,
  removeHighlight,
  addNote,
  updateNote,
  deleteNote,
  translateChapter,
} from '../hooks/useScriptures';
import { listen } from '@tauri-apps/api/event';
import { RelatedContent } from './RelatedContent';
import { ReadAloudControls } from './ReadAloudControls';
import { VerseToolbar } from './VerseToolbar';
import { NoteEditor } from './NoteEditor';
import { GoldDivider } from './Icons';
import { showToast } from './Toast';

interface SelectionRange {
  start: number;
  end: number;
  text: string;
}

interface ToolbarPosition {
  top: number;
  left: number;
}

interface VerseDisplayProps {
  verses: VerseResult[];
  bookTitle: string;
  chapterNumber: number | null;
  volumeTitle?: string;
  numChapters?: number;
  onChapterChange?: (chapter: number) => void;
  onBookClick?: () => void;
  onVolumeClick?: () => void;
  onNextBook?: () => void;
  onPrevBook?: () => void;
}

function renderHighlightedText(text: string, verseHighlights: Highlight[]): React.ReactNode {
  // Filter to sub-verse highlights (have offsets)
  const rangeHighlights = verseHighlights
    .filter((h) => h.start_offset != null && h.end_offset != null)
    .sort((a, b) => (a.start_offset ?? 0) - (b.start_offset ?? 0));

  // Check for whole-verse highlight
  const wholeVerse = verseHighlights.find((h) => h.start_offset == null);

  if (rangeHighlights.length === 0 && wholeVerse) {
    // Whole verse highlight (existing behavior)
    return <span className={`verse-highlighted-${wholeVerse.color}`}>{text}</span>;
  }

  if (rangeHighlights.length === 0) return text;

  // Build segments from range highlights
  const segments: React.ReactNode[] = [];
  let lastEnd = 0;

  for (const h of rangeHighlights) {
    const start = h.start_offset!;
    const end = h.end_offset!;

    // Add unhighlighted text before this range
    if (start > lastEnd) {
      segments.push(<span key={`gap-${lastEnd}`}>{text.slice(lastEnd, start)}</span>);
    }
    // Add highlighted range
    segments.push(
      <span key={h.id} className={`verse-highlight-inline verse-highlighted-${h.color}`}>
        {text.slice(start, end)}
      </span>
    );
    lastEnd = Math.max(lastEnd, end);
  }
  // Add remaining unhighlighted text
  if (lastEnd < text.length) {
    segments.push(<span key={`tail-${lastEnd}`}>{text.slice(lastEnd)}</span>);
  }

  // If there's also a whole-verse highlight, wrap everything in it
  if (wholeVerse) {
    return <span className={`verse-highlighted-${wholeVerse.color}`}>{segments}</span>;
  }

  return <>{segments}</>;
}

export function VerseDisplay({
  verses,
  bookTitle,
  chapterNumber,
  volumeTitle,
  numChapters,
  onChapterChange,
  onBookClick,
  onVolumeClick,
  onNextBook,
  onPrevBook,
}: VerseDisplayProps) {
  const [highlights, setHighlights] = useState<Map<number, Highlight[]>>(new Map());
  const [notes, setNotes] = useState<Map<number, Note>>(new Map());
  const [selectedVerseId, setSelectedVerseId] = useState<number | null>(null);
  const [selectionRange, setSelectionRange] = useState<SelectionRange | null>(null);
  const [toolbarPosition, setToolbarPosition] = useState<ToolbarPosition | null>(null);
  const [editingNoteVerseId, setEditingNoteVerseId] = useState<number | null>(null);
  const [readingVerseId, setReadingVerseId] = useState<number | null>(null);
  const readingVerseRef = useRef<number | null>(null);

  // Listen for tts-verse-playing events to highlight + scroll to the current verse
  useEffect(() => {
    const unlisten = listen<{ verseId: number | null }>('tts-verse-playing', (event) => {
      const { verseId } = event.payload;
      setReadingVerseId(verseId);
      readingVerseRef.current = verseId;
      if (verseId != null) {
        const el = document.querySelector(`[data-verse-id="${verseId}"]`);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
    return () => { unlisten.then(fn => fn()); };
  }, []);

  // Clear highlight on chapter change
  useEffect(() => {
    setReadingVerseId(null);
    readingVerseRef.current = null;
  }, [bookTitle, chapterNumber]);

  // Translation state
  const [translations, setTranslations] = useState<Map<number, string>>(new Map());
  const [translating, setTranslating] = useState(false);
  const [activeLanguage, setActiveLanguage] = useState<string | null>(null);

  const LANGUAGES = ['Spanish', 'French', 'Portuguese', 'German', 'Italian', 'Chinese', 'Korean', 'Japanese', 'Russian', 'Arabic'];

  const handleTranslate = useCallback(async (language: string) => {
    if (!bookTitle || chapterNumber == null) return;
    if (language === activeLanguage) {
      // Toggle off
      setTranslations(new Map());
      setActiveLanguage(null);
      return;
    }
    setTranslating(true);
    setActiveLanguage(language);
    try {
      const result = await translateChapter(bookTitle, chapterNumber, language);
      const map = new Map<number, string>();
      for (const t of result.translations) {
        if (t.translated_text) map.set(t.verse_id, t.translated_text);
      }
      setTranslations(map);
    } catch {
      setTranslations(new Map());
      setActiveLanguage(null);
    } finally {
      setTranslating(false);
    }
  }, [bookTitle, chapterNumber, activeLanguage]);

  // Clear translations when chapter changes
  useEffect(() => {
    setTranslations(new Map());
    setActiveLanguage(null);
  }, [bookTitle, chapterNumber]);

  // Load highlights and notes when chapter changes
  useEffect(() => {
    if (!bookTitle || chapterNumber == null) return;
    let cancelled = false;

    (async () => {
      try {
        const [hl, nt] = await Promise.all([
          getHighlightsForChapter(bookTitle, chapterNumber),
          getNotesForChapter(bookTitle, chapterNumber),
        ]);
        if (cancelled) return;
        // Group highlights by verse_id (multiple per verse now)
        const hlMap = new Map<number, Highlight[]>();
        for (const h of hl) {
          const existing = hlMap.get(h.verse_id) || [];
          existing.push(h);
          hlMap.set(h.verse_id, existing);
        }
        setHighlights(hlMap);
        setNotes(new Map(nt.map((n) => [n.verse_id, n])));
      } catch {
        // Silently fail -- highlights/notes are optional
      }
    })();

    return () => { cancelled = true; };
  }, [bookTitle, chapterNumber]);

  // Text selection handler for sub-verse highlighting
  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const range = selection.getRangeAt(0);
    // Find the verse element containing the selection
    const verseEl = (range.startContainer.parentElement)?.closest('[data-verse-id]') as HTMLElement | null;
    if (!verseEl) return;

    const verseId = Number(verseEl.getAttribute('data-verse-id'));
    const verseText = verseEl.getAttribute('data-verse-text') || '';
    const selectedText = selection.toString().trim();
    if (!selectedText) return;

    // Calculate offsets within the verse text
    const start = verseText.indexOf(selectedText);
    const end = start + selectedText.length;

    if (start >= 0) {
      setSelectedVerseId(verseId);
      setSelectionRange({ start, end, text: selectedText });
      // Position toolbar near selection
      const rect = range.getBoundingClientRect();
      setToolbarPosition({ top: rect.top - 50, left: rect.left });
    }
  }, []);

  // Close toolbar when clicking outside (only if no text selection)
  const handleVerseClick = useCallback((verseId: number) => {
    const selection = window.getSelection();
    // Don't toggle toolbar if user just selected text (handleMouseUp will handle it)
    if (selection && !selection.isCollapsed) return;

    setSelectionRange(null);
    setToolbarPosition(null);
    setSelectedVerseId((prev) => (prev === verseId ? null : verseId));
  }, []);

  const handleHighlight = useCallback(async (verseId: number, color: string) => {
    try {
      // Remove existing highlight at the same range before adding new color
      const existing = highlights.get(verseId) || [];
      const isWholeVerse = !selectionRange;
      const overlapping = existing.find((h) =>
        isWholeVerse
          ? h.start_offset == null // existing whole-verse highlight
          : h.start_offset === selectionRange?.start && h.end_offset === selectionRange?.end
      );
      if (overlapping) {
        await removeHighlight(overlapping.id);
      }

      const result = await addHighlight(
        verseId,
        color,
        selectionRange?.start,
        selectionRange?.end,
        selectionRange?.text,
      );
      setHighlights((prev) => {
        const next = new Map(prev);
        let list = next.get(verseId) || [];
        // Remove the old one if it was replaced
        if (overlapping) {
          list = list.filter((h) => h.id !== overlapping.id);
        }
        next.set(verseId, [...list, result]);
        return next;
      });
      showToast('Highlight saved', 'success');
    } catch {
      showToast('Failed to save. Please try again.', 'error');
    }
    setSelectedVerseId(null);
    setSelectionRange(null);
    setToolbarPosition(null);
    window.getSelection()?.removeAllRanges();
  }, [selectionRange, highlights]);

  const handleRemoveHighlight = useCallback(async (verseId: number) => {
    const verseHls = highlights.get(verseId);
    if (!verseHls || verseHls.length === 0) return;

    // If there's a selection range active, try to find a matching sub-verse highlight to remove
    // Otherwise remove the most recent highlight (last in array)
    let hlToRemove: Highlight | undefined;
    if (selectionRange) {
      hlToRemove = verseHls.find(
        (h) => h.start_offset === selectionRange.start && h.end_offset === selectionRange.end
      );
    }
    if (!hlToRemove) {
      // Remove the last-added highlight for this verse
      hlToRemove = verseHls[verseHls.length - 1];
    }
    if (!hlToRemove) return;

    try {
      await removeHighlight(hlToRemove.id);
      setHighlights((prev) => {
        const next = new Map(prev);
        const existing = next.get(verseId) || [];
        const filtered = existing.filter((h) => h.id !== hlToRemove!.id);
        if (filtered.length === 0) {
          next.delete(verseId);
        } else {
          next.set(verseId, filtered);
        }
        return next;
      });
      showToast('Highlight removed', 'info');
    } catch {
      showToast('Failed to save. Please try again.', 'error');
    }
    setSelectedVerseId(null);
    setSelectionRange(null);
    setToolbarPosition(null);
    window.getSelection()?.removeAllRanges();
  }, [highlights, selectionRange]);

  const handleToggleNote = useCallback((verseId: number) => {
    setEditingNoteVerseId((prev) => (prev === verseId ? null : verseId));
    setSelectedVerseId(null);
    setSelectionRange(null);
    setToolbarPosition(null);
  }, []);

  const handleSaveNote = useCallback(async (verseId: number, text: string, noteId: number | null) => {
    try {
      if (noteId) {
        await updateNote(noteId, text);
        setNotes((prev) => {
          const next = new Map(prev);
          const existing = prev.get(verseId);
          if (existing) next.set(verseId, { ...existing, text, updated_at: Date.now() / 1000 });
          return next;
        });
      } else {
        const result = await addNote(verseId, text);
        setNotes((prev) => {
          const next = new Map(prev);
          next.set(verseId, result);
          return next;
        });
      }
      showToast(noteId ? 'Note updated' : 'Note saved', 'success');
    } catch {
      showToast('Failed to save. Please try again.', 'error');
    }
    setEditingNoteVerseId(null);
  }, []);

  const handleDeleteNote = useCallback(async (noteId: number) => {
    try {
      await deleteNote(noteId);
      setNotes((prev) => {
        const next = new Map(prev);
        for (const [vid, n] of next) {
          if (n.id === noteId) { next.delete(vid); break; }
        }
        return next;
      });
      showToast('Note deleted', 'info');
    } catch {
      showToast('Failed to save. Please try again.', 'error');
    }
    setEditingNoteVerseId(null);
  }, []);

  const headerText = chapterNumber ? `${bookTitle} ${chapterNumber}` : bookTitle;

  return (
    <div className="verse-display">
      {/* Breadcrumb + Read Aloud */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <nav className="verse-breadcrumb">
          {volumeTitle && (
            <>
              <button className="breadcrumb-link" onClick={onVolumeClick}>
                {volumeTitle}
              </button>
              <span className="breadcrumb-sep">&rsaquo;</span>
            </>
          )}
          {bookTitle && (
            <>
              <button className="breadcrumb-link" onClick={onBookClick}>
                {bookTitle}
              </button>
              {chapterNumber && (
                <>
                  <span className="breadcrumb-sep">&rsaquo;</span>
                  <span className="breadcrumb-current">Chapter {chapterNumber}</span>
                </>
              )}
            </>
          )}
        </nav>
        {verses.length > 0 && chapterNumber && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ReadAloudControls verses={verses} bookTitle={bookTitle} chapterNumber={chapterNumber} />
            <div style={{ position: 'relative' }}>
              <select
                className="translate-select"
                value={activeLanguage || ''}
                onChange={(e) => void handleTranslate(e.target.value || 'English')}
                disabled={translating}
              >
                <option value="">English</option>
                {LANGUAGES.map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
              {translating && <span className="translate-loading">Translating...</span>}
            </div>
          </div>
        )}
      </div>

      {/* Header */}
      <h2 className="verse-header">{headerText}</h2>

      {/* Ornamental Divider */}
      <div className="ornamental-divider">
        <GoldDivider size={200} />
      </div>

      {/* Verses */}
      <div className="verse-body">
        {verses.map((v) => {
          const verseHighlights = highlights.get(v.id) || [];
          const note = notes.get(v.id);
          const isSelected = selectedVerseId === v.id;
          const isEditingNote = editingNoteVerseId === v.id;
          // For toolbar: show the most recent highlight color
          const latestHl = verseHighlights.length > 0 ? verseHighlights[verseHighlights.length - 1] : null;

          return (
            <div key={v.id} style={{ position: 'relative' }}>
              <p
                data-verse-id={v.id}
                data-verse-text={v.text}
                className={`verse-line${readingVerseId === v.id ? ' verse-reading-current' : ''}`}
                onClick={() => handleVerseClick(v.id)}
                onMouseUp={handleMouseUp}
                style={{ cursor: 'text', borderRadius: 4, padding: '2px 4px', margin: '0 -4px 10px' }}
              >
                {v.verse_number != null && (
                  <sup className="verse-number">{v.verse_number}</sup>
                )}
                {verseHighlights.length > 0
                  ? renderHighlightedText(v.text, verseHighlights)
                  : v.text
                }
                {note && !isEditingNote && (
                  <span
                    style={{ marginLeft: 6, color: 'var(--accent)', fontSize: 14, cursor: 'pointer' }}
                    onClick={(e) => { e.stopPropagation(); handleToggleNote(v.id); }}
                    title="View note"
                  >
                    &#9998;
                  </span>
                )}
              </p>

              {/* Translated text */}
              {activeLanguage && translations.get(v.id) && (
                <p className="verse-translation">
                  <span className="verse-translation-lang">{activeLanguage}:</span>{' '}
                  {translations.get(v.id)}
                </p>
              )}

              {/* Floating toolbar */}
              {isSelected && (
                <div
                  style={
                    toolbarPosition
                      ? { position: 'fixed', top: toolbarPosition.top, left: toolbarPosition.left, zIndex: 50 }
                      : { position: 'absolute', top: -44, left: 0, zIndex: 50 }
                  }
                >
                  <VerseToolbar
                    verseId={v.id}
                    currentHighlightColor={latestHl?.color ?? null}
                    hasNote={!!note}
                    onHighlight={handleHighlight}
                    onRemoveHighlight={handleRemoveHighlight}
                    onToggleNote={handleToggleNote}
                    onClose={() => {
                      setSelectedVerseId(null);
                      setSelectionRange(null);
                      setToolbarPosition(null);
                      window.getSelection()?.removeAllRanges();
                    }}
                  />
                </div>
              )}

              {/* Note editor */}
              {isEditingNote && (
                <NoteEditor
                  verseId={v.id}
                  initialText={note?.text ?? ''}
                  noteId={note?.id ?? null}
                  onSave={handleSaveNote}
                  onDelete={handleDeleteNote}
                  onCancel={() => setEditingNoteVerseId(null)}
                />
              )}
            </div>
          );
        })}
        {/* Chapter Navigation */}
        {chapterNumber && numChapters && onChapterChange && (
          <div className="chapter-nav">
            {chapterNumber <= 1 && onPrevBook ? (
              <button
                className="chapter-nav-btn"
                onClick={onPrevBook}
              >
                &larr; Prev Book
              </button>
            ) : (
              <button
                className="chapter-nav-btn"
                disabled={chapterNumber <= 1}
                onClick={() => onChapterChange(chapterNumber - 1)}
              >
                &larr; Previous Chapter
              </button>
            )}
            <span className="chapter-nav-info">
              Chapter {chapterNumber} of {numChapters}
            </span>
            {chapterNumber >= numChapters && onNextBook ? (
              <button
                className="chapter-nav-btn"
                onClick={onNextBook}
              >
                Next Book &rarr;
              </button>
            ) : (
              <button
                className="chapter-nav-btn"
                disabled={chapterNumber >= numChapters}
                onClick={() => onChapterChange(chapterNumber + 1)}
              >
                Next Chapter &rarr;
              </button>
            )}
          </div>
        )}
      </div>

      {/* Related Talks */}
      {bookTitle && chapterNumber && (
        <RelatedContent bookTitle={bookTitle} chapterNumber={chapterNumber} />
      )}
    </div>
  );
}
