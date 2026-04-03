export interface Volume {
  id: number;
  title: string;
  abbreviation: string;
  description: string;
}

export interface BookInfo {
  id: number;
  title: string;
  abbreviation: string | null;
  long_title: string | null;
  num_chapters: number | null;
  book_order: number | null;
  volume_title: string | null;
}

export interface VerseResult {
  id: number;
  volume_title: string | null;
  book_title: string | null;
  chapter_number: number | null;
  verse_number: number | null;
  reference: string | null;
  text: string;
}

export interface HymnSummary {
  id: number;
  hymn_number: number | null;
  title: string;
  author: string | null;
  composer: string | null;
  first_line: string | null;
}

export interface HymnVerse {
  verse_number: number;
  verse_type: string;
  text: string;
}

export interface HymnDetail extends HymnSummary {
  verses: HymnVerse[];
}

export interface BundleInfo {
  id: string;
  name: string;
  volume_id: number | null;
  filename: string;
  size_bytes: number;
  verse_count: number;
  installed: boolean;
  installed_verse_count: number;
  version: number;
}

export interface BundleManifest {
  version: number;
  bundles: BundleInfo[];
}

export interface Talk {
  id: number;
  speaker: string;
  title: string;
  date: string | null;
  conference: string | null;
  url: string | null;
  summary: string | null;
}

export interface VolumeStat {
  id: number;
  title: string;
  abbreviation: string;
  description: string | null;
  book_count: number;
  chapter_count: number;
  verse_count: number;
}

export interface Highlight {
  id: number;
  verse_id: number;
  color: string;
  created_at: number;
  start_offset: number | null;
  end_offset: number | null;
  highlighted_text: string | null;
}

export interface HighlightWithVerse extends Highlight {
  text: string;
  reference: string | null;
  book_title: string;
  volume_title: string;
  chapter_number: number;
  verse_number: number;
  // Note: start_offset, end_offset, highlighted_text inherited from Highlight
}

export interface Note {
  id: number;
  verse_id: number;
  text: string;
  created_at: number;
  updated_at: number;
}

export interface NoteWithVerse extends Note {
  verse_text: string;
  reference: string | null;
  book_title: string;
  volume_title: string;
  chapter_number: number;
  verse_number: number;
}

export interface ReadingProgress {
  id: number;
  volume_abbr: string;
  book_title: string;
  chapter: number;
  last_verse: number | null;
  last_read: number;
}

export interface OllamaStatus {
  available: boolean;
  models: { name: string }[];
}

export interface AIResponse {
  response: string;
  model: string;
  context_verses_used: number;
}

export interface AIExplanation {
  verse_reference: string;
  verse_text: string;
  book_title: string;
  explanation: string;
}
