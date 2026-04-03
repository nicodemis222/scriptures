import type { BookInfo } from '../types/scriptures';
import { ChevronLeft } from './Icons';

interface BookListProps {
  books: BookInfo[];
  onSelect: (book: BookInfo) => void;
  selectedBook?: BookInfo | null;
  selectedChapter?: number | null;
  title?: string;
  onBack?: () => void;
}

export function BookList({ books, onSelect, selectedBook, selectedChapter, title, onBack }: BookListProps) {
  return (
    <aside className="book-list">
      <div className="book-list-header">
        {onBack && (
          <button className="book-list-back" onClick={onBack}>
            <ChevronLeft size={14} /> Back
          </button>
        )}
        <span className="book-list-title">{title ?? 'Books'}</span>
      </div>
      <ul className="book-list-items">
        {books.map((book) => {
          const isSelected = selectedBook?.id === book.id;
          return (
            <li key={book.id}>
              <button
                className={`book-list-item${isSelected ? ' active' : ''}`}
                onClick={() => onSelect(book)}
              >
                <span className="book-list-item-name">{book.title}</span>
                {isSelected && selectedChapter && (
                  <span className="book-list-item-chapter">Ch. {selectedChapter}</span>
                )}
                {!isSelected && book.num_chapters != null && book.num_chapters > 0 && (
                  <span className="book-list-item-chapters">
                    {book.num_chapters} ch
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
