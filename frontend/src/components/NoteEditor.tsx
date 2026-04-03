import { useState, useRef, useEffect } from 'react';

interface NoteEditorProps {
  verseId: number;
  initialText: string;
  noteId: number | null;
  onSave: (verseId: number, text: string, noteId: number | null) => void;
  onDelete: (noteId: number) => void;
  onCancel: () => void;
}

export function NoteEditor({
  verseId,
  initialText,
  noteId,
  onSave,
  onDelete,
  onCancel,
}: NoteEditorProps) {
  const [text, setText] = useState(initialText);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSave = () => {
    const trimmed = text.trim();
    if (trimmed) {
      onSave(verseId, trimmed, noteId);
    }
  };

  const handleDelete = () => {
    if (noteId !== null) {
      onDelete(noteId);
    }
  };

  return (
    <div
      className="note-editor"
      style={{
        padding: 12,
        borderRadius: 8,
        border: '1px solid var(--border)',
        marginTop: 8,
        background: 'var(--bg)',
      }}
    >
      <textarea
        ref={textareaRef}
        className="note-editor-textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Write a note..."
        style={{
          width: '100%',
          minHeight: 80,
          resize: 'vertical',
          fontFamily: 'var(--font-serif)',
          fontSize: 14,
          background: 'var(--bg)',
          color: 'var(--text)',
          border: '1px solid var(--border)',
          borderRadius: 4,
          padding: 8,
          boxSizing: 'border-box',
        }}
      />

      <div
        className="note-editor-actions"
        style={{ display: 'flex', gap: 8, marginTop: 8 }}
      >
        <button
          onClick={handleSave}
          disabled={!text.trim()}
          style={{
            background: 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            padding: '6px 16px',
            cursor: text.trim() ? 'pointer' : 'default',
            fontFamily: 'var(--font-serif)',
            fontSize: 14,
            opacity: text.trim() ? 1 : 0.5,
          }}
        >
          Save
        </button>

        <button
          onClick={onCancel}
          style={{
            background: 'none',
            color: 'var(--text-muted)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '6px 16px',
            cursor: 'pointer',
            fontFamily: 'var(--font-serif)',
            fontSize: 14,
          }}
        >
          Cancel
        </button>

        {noteId !== null && (
          <button
            onClick={handleDelete}
            style={{
              background: 'none',
              color: 'var(--text-muted)',
              border: 'none',
              borderRadius: 4,
              padding: '6px 16px',
              cursor: 'pointer',
              fontFamily: 'var(--font-serif)',
              fontSize: 14,
              marginLeft: 'auto',
            }}
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
