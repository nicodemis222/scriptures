import { useState, useEffect, useCallback } from 'react';
import { open } from '@tauri-apps/plugin-shell';
import type { Talk } from '../types/scriptures';
import { getRelatedTalks } from '../hooks/useScriptures';

interface RelatedContentProps {
  bookTitle: string;
  chapterNumber: number;
}

export function RelatedContent({ bookTitle, chapterNumber }: RelatedContentProps) {
  const [talks, setTalks] = useState<Talk[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getRelatedTalks(bookTitle, chapterNumber)
      .then((result) => {
        if (!cancelled) setTalks(result);
      })
      .catch(() => {
        if (!cancelled) setTalks([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [bookTitle, chapterNumber]);

  const handleOpenUrl = useCallback((url: string) => {
    if (/^https?:\/\//i.test(url)) {
      void open(url);
    }
  }, []);

  if (loading) {
    return (
      <div className="related-content">
        <div className="related-header" onClick={() => setExpanded(!expanded)}>
          <span className="related-icon">&#128214;</span>
          <span>Related Talks</span>
          <span className="related-toggle">{expanded ? '\u25BC' : '\u25B6'}</span>
        </div>
        {expanded && <div className="related-loading">Loading...</div>}
      </div>
    );
  }

  if (talks.length === 0) return null;

  return (
    <div className="related-content">
      <div className="related-header" onClick={() => setExpanded(!expanded)}>
        <span className="related-icon">&#128214;</span>
        <span>Related Talks ({talks.length})</span>
        <span className="related-toggle">{expanded ? '\u25BC' : '\u25B6'}</span>
      </div>
      {expanded && (
        <div className="related-list">
          {talks.map((talk) => (
            <div key={talk.id} className="related-talk ornamental-card">
              <div className="talk-title">
                {talk.url && /^https?:\/\//i.test(talk.url) ? (
                  <button
                    className="talk-link"
                    onClick={() => handleOpenUrl(talk.url!)}
                  >
                    {talk.title}
                  </button>
                ) : (
                  talk.title
                )}
              </div>
              <div className="talk-meta">
                <span className="talk-speaker">{talk.speaker}</span>
                {talk.conference && (
                  <span className="talk-conference"> &mdash; {talk.conference}</span>
                )}
              </div>
              {talk.summary && (
                <div className="talk-summary">{talk.summary}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
