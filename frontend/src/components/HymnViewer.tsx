import type { HymnDetail } from '../types/scriptures';

interface HymnViewerProps {
  hymn: HymnDetail;
  onBack?: () => void;
}

export function HymnViewer({ hymn, onBack }: HymnViewerProps) {
  return (
    <div className="hymn-viewer">
      {/* Breadcrumb */}
      <nav className="verse-breadcrumb">
        <button className="breadcrumb-link" onClick={onBack}>
          Hymns
        </button>
        <span className="breadcrumb-sep">&rsaquo;</span>
        <span className="breadcrumb-current">
          {hymn.hymn_number ? `#${hymn.hymn_number}` : ''} {hymn.title}
        </span>
      </nav>

      {/* Title */}
      <h2 className="hymn-title">
        {hymn.hymn_number ? `${hymn.hymn_number}. ` : ''}
        {hymn.title}
      </h2>

      {/* Credits */}
      {(hymn.author || hymn.composer) && (
        <div className="hymn-credits">
          {hymn.author && <span>Text: {hymn.author}</span>}
          {hymn.author && hymn.composer && <span className="hymn-credits-sep"> | </span>}
          {hymn.composer && <span>Music: {hymn.composer}</span>}
        </div>
      )}

      {/* Verses */}
      <div className="hymn-verses">
        {hymn.verses.map((v, _i) => (
          <div
            key={`${v.verse_type}-${v.verse_number}`}
            className={`hymn-verse${v.verse_type === 'chorus' ? ' hymn-chorus' : ''}`}
          >
            {v.verse_type === 'chorus' ? (
              <p className="hymn-verse-text chorus-text">
                <em>Chorus:</em> {v.text}
              </p>
            ) : (
              <p className="hymn-verse-text">
                <span className="hymn-verse-num">{v.verse_number}.</span>
                {v.text}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
