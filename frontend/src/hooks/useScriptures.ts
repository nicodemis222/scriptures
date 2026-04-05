import { invoke } from '@tauri-apps/api/core';
import type {
  Volume, BookInfo, VerseResult, HymnSummary, HymnDetail, Talk,
  BundleManifest, VolumeStat, Highlight, HighlightWithVerse, Note,
  NoteWithVerse, ReadingProgress, OllamaStatus, AIResponse, AIExplanation,
} from '../types/scriptures';

export async function getVolumes(): Promise<Volume[]> {
  return invoke('get_volumes');
}

export async function getBooks(volume: string): Promise<BookInfo[]> {
  return invoke('get_books', { volume });
}

export async function getChapter(book: string, chapter: number): Promise<VerseResult[]> {
  return invoke('get_chapter', { book, chapter });
}

export async function getVerse(book: string, chapter: number, verse: number): Promise<VerseResult> {
  return invoke('get_verse', { book, chapter, verse });
}

export async function searchScriptures(
  q: string,
  volume?: string,
  limit?: number,
  offset?: number
): Promise<VerseResult[]> {
  // Build params object, omitting undefined values so Tauri sees them as missing (None in Rust)
  const params: Record<string, unknown> = { q };
  if (volume !== undefined && volume !== null) params.volume = volume;
  if (limit !== undefined) params.limit = limit;
  if (offset !== undefined) params.offset = offset;
  return invoke('search_scriptures', params);
}

export async function getHymns(): Promise<HymnSummary[]> {
  return invoke('get_hymns');
}

export async function searchHymns(q: string): Promise<HymnSummary[]> {
  return invoke('search_hymns', { q });
}

export async function getHymn(id: number): Promise<HymnDetail> {
  return invoke('get_hymn', { id });
}

export async function getRelatedTalks(book: string, chapter: number): Promise<Talk[]> {
  return invoke('get_related_talks', { book, chapter });
}

export async function searchTalks(q: string): Promise<Talk[]> {
  return invoke('search_talks', { q });
}

export async function getVolumeStats(): Promise<VolumeStat[]> {
  return invoke('get_volume_stats');
}

export async function listBundles(): Promise<BundleManifest> {
  return invoke('list_bundles');
}

// Highlights
export async function addHighlight(
  verse_id: number,
  color: string,
  start_offset?: number,
  end_offset?: number,
  highlighted_text?: string,
): Promise<Highlight> {
  return invoke('add_highlight', {
    verseId: verse_id,
    color,
    startOffset: start_offset,
    endOffset: end_offset,
    highlightedText: highlighted_text,
  });
}
export async function removeHighlight(id: number): Promise<void> {
  return invoke('remove_highlight', { id });
}
export async function getHighlightsForChapter(book: string, chapter: number): Promise<Highlight[]> {
  return invoke('get_highlights_for_chapter', { book, chapter });
}

// Notes
export async function addNote(verse_id: number, text: string): Promise<Note> {
  return invoke('add_note', { verseId: verse_id, text });
}
export async function updateNote(id: number, text: string): Promise<void> {
  return invoke('update_note', { id, text });
}
export async function deleteNote(id: number): Promise<void> {
  return invoke('delete_note', { id });
}
export async function getNotesForChapter(book: string, chapter: number): Promise<Note[]> {
  return invoke('get_notes_for_chapter', { book, chapter });
}

// Reading Progress
export async function saveReadingProgress(volume_abbr: string, book_title: string, chapter: number, last_verse: number | null): Promise<void> {
  return invoke('save_reading_progress', { volumeAbbr: volume_abbr, bookTitle: book_title, chapter, lastVerse: last_verse });
}
export async function getReadingProgress(): Promise<ReadingProgress[]> {
  return invoke('get_reading_progress');
}

// Settings
export async function getSetting(key: string): Promise<string | null> {
  return invoke('get_setting', { key });
}
export async function setSetting(key: string, value: string): Promise<void> {
  return invoke('set_setting', { key, value });
}

// Study View
export async function getAllHighlights(limit?: number, offset?: number): Promise<HighlightWithVerse[]> {
  return invoke('get_all_highlights', { limit, offset });
}
export async function getAllNotes(limit?: number, offset?: number): Promise<NoteWithVerse[]> {
  return invoke('get_all_notes', { limit, offset });
}

// TTS
export interface VoiceInfo {
  name: string;
  locale: string;
  engine?: string;
  description?: string;
  voice_id?: string;
  language?: string;
}

export interface TtsStatus {
  playing: boolean;
  paused: boolean;
}

export async function listVoices(): Promise<VoiceInfo[]> {
  return invoke('list_voices');
}


export async function prefetchAudio(text: string, voice?: string): Promise<void> {
  const params: Record<string, unknown> = { text };
  if (voice) params.voice = voice;
  return invoke('prefetch_audio', params);
}

export async function isPrefetchReady(): Promise<boolean> {
  return invoke('is_prefetch_ready');
}

export async function readAloud(text: string, rate?: number, voice?: string): Promise<void> {
  const params: Record<string, unknown> = { text };
  if (rate !== undefined) params.rate = rate;
  if (voice !== undefined && voice !== 'default') params.voice = voice;
  return invoke('read_aloud', params);
}

export async function pauseReading(): Promise<void> {
  return invoke('pause_reading');
}

export async function resumeReading(): Promise<void> {
  return invoke('resume_reading');
}

export async function stopReading(): Promise<void> {
  return invoke('stop_reading');
}

export async function isReading(): Promise<TtsStatus> {
  return invoke('is_reading');
}

// AI
export async function checkOllamaStatus(): Promise<OllamaStatus> {
  return invoke('check_ollama_status');
}
export async function aiQuery(prompt: string, contextBook?: string, contextChapter?: number, model?: string): Promise<AIResponse> {
  return invoke('ai_query', { prompt, contextBook, contextChapter, model });
}
export async function aiExplain(verseId: number): Promise<AIExplanation> {
  return invoke('ai_explain', { verseId });
}

// Ollama Management
export async function checkOllamaInstalled(): Promise<{ installed: boolean; running: boolean }> {
  return invoke('check_ollama_installed');
}

export async function installOllama(): Promise<{ status: string; method?: string }> {
  return invoke('install_ollama');
}

export async function startOllama(): Promise<{ status: string; pid?: number }> {
  return invoke('start_ollama');
}

export async function pullOllamaModel(model: string): Promise<{ status: string; model: string }> {
  return invoke('pull_ollama_model', { model });
}

// Translation
export interface TranslatedVerse {
  verse_id: number;
  verse_number: number;
  translated_text: string;
}

export interface TranslationResult {
  translations: TranslatedVerse[];
  from_cache: boolean;
}

export async function translateChapter(book: string, chapter: number, targetLanguage: string): Promise<TranslationResult> {
  return invoke('translate_chapter', { book, chapter, targetLanguage });
}
