import { useEffect, useState } from 'react';
import { dailyVerse, getReadingProgress } from '../hooks/useScriptures';
import type { VerseResult, ReadingProgress } from '../types/scriptures';
import { BookOpen } from './Icons';

interface WelcomeHomeProps {
  onNavigate: (book: string, chapter: number, verse?: number | null) => void;
}

/**
 * The reader's home screen: a verse of the day and a "continue reading" jump —
 * the daily-engagement + resume hooks every Bible app opens with. Replaces the
 * old static welcome card.
 */
export function WelcomeHome({ onNavigate }: WelcomeHomeProps) {
  const [verse, setVerse] = useState<VerseResult | null>(null);
  const [resume, setResume] = useState<ReadingProgress | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const v = await dailyVerse();
        if (!cancelled) setVerse(v);
      } catch { /* no AI/DB — show nothing */ }
      try {
        const prog = await getReadingProgress();
        if (!cancelled && prog.length > 0) setResume(prog[0]);
      } catch { /* none yet */ }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="content-area">
      <div className="welcome-home">
        <h2 className="welcome-title">Scripture Study</h2>

        {resume && (
          <button
            className="home-card home-resume"
            onClick={() => onNavigate(resume.book_title, resume.chapter, resume.last_verse)}
          >
            <span className="home-card-label">Continue reading</span>
            <span className="home-card-ref">
              <BookOpen size={15} /> {resume.book_title} {resume.chapter}
            </span>
          </button>
        )}

        {verse && (
          <button
            className="home-card home-votd"
            onClick={() => verse.book_title && verse.chapter_number
              && onNavigate(verse.book_title, verse.chapter_number, verse.verse_number)}
          >
            <span className="home-card-label">Verse of the day</span>
            <p className="home-votd-text">{verse.text}</p>
            <span className="home-card-ref">{verse.reference}</span>
          </button>
        )}

        <p className="welcome-text">
          &ldquo;For the word of God is quick, and powerful, and sharper than any two-edged sword.&rdquo;
        </p>
      </div>
    </div>
  );
}
