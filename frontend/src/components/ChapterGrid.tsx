interface ChapterGridProps {
  bookTitle: string;
  numChapters: number;
  onSelect: (chapter: number) => void;
}

export function ChapterGrid({ bookTitle, numChapters, onSelect }: ChapterGridProps) {
  const chapters = Array.from({ length: numChapters }, (_, i) => i + 1);

  return (
    <div className="chapter-grid-container">
      <h2 className="chapter-grid-title">{bookTitle}</h2>
      <p className="chapter-grid-subtitle">Select a chapter</p>
      <div className="chapter-grid">
        {chapters.map((ch) => (
          <button
            key={ch}
            className="chapter-grid-btn"
            onClick={() => onSelect(ch)}
          >
            {ch}
          </button>
        ))}
      </div>
    </div>
  );
}
