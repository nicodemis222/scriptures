import { QuillPen, XIcon } from './Icons';

interface VerseToolbarProps {
  verseId: number;
  currentHighlightColor: string | null;
  hasNote: boolean;
  onHighlight: (verseId: number, color: string) => void;
  onRemoveHighlight: (verseId: number) => void;
  onToggleNote: (verseId: number) => void;
  onClose: () => void;
}

const HIGHLIGHT_COLORS = [
  { name: 'gold', hex: '#C5A55A' },
  { name: 'rose', hex: '#C4726C' },
  { name: 'sky', hex: '#6BA3BE' },
  { name: 'sage', hex: '#7FA77F' },
  { name: 'lavender', hex: '#9B8EC4' },
] as const;

export function VerseToolbar({
  verseId,
  currentHighlightColor,
  hasNote,
  onHighlight,
  onRemoveHighlight,
  onToggleNote,
  onClose,
}: VerseToolbarProps) {
  const handleColorClick = (color: string) => {
    if (currentHighlightColor === color) {
      onRemoveHighlight(verseId);
    } else {
      onHighlight(verseId, color);
    }
  };

  return (
    <div className="verse-toolbar">
      {HIGHLIGHT_COLORS.map(({ name, hex }) => {
        const isActive = currentHighlightColor === name;
        return (
          <button
            key={name}
            className={`color-btn ${name}`}
            title={`Highlight ${name}`}
            onClick={() => handleColorClick(name)}
            style={isActive ? { border: `2px solid ${hex}`, boxShadow: `0 0 0 1px ${hex}` } : undefined}
          >
            {isActive && (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={hex} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            )}
          </button>
        );
      })}

      <button
        className="action-btn"
        title={hasNote ? 'Edit note' : 'Add note'}
        onClick={() => onToggleNote(verseId)}
      >
        <QuillPen size={18} />
      </button>

      <button
        className="action-btn"
        title="Close"
        onClick={onClose}
      >
        <XIcon size={18} />
      </button>
    </div>
  );
}
