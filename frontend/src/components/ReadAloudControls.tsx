import { useState, useCallback, useRef, useEffect } from 'react';
import {
  readAloudVerses, pauseReading, resumeReading, stopReading, isReading,
  skipVerse, getSetting, setSetting, listVoices, prefetchAudio, isPrefetchReady,
} from '../hooks/useScriptures';
import { listen } from '@tauri-apps/api/event';
import type { VerseResult } from '../types/scriptures';
import type { VoiceInfo } from '../hooks/useScriptures';
import { PlayIcon, PauseIcon, StopIcon, SpeakerIcon, SkipBackIcon, SkipForwardIcon } from './Icons';

interface ReadAloudControlsProps {
  verses: VerseResult[];
  bookTitle: string;
  chapterNumber: number;
}

export function ReadAloudControls({ verses, bookTitle, chapterNumber }: ReadAloudControlsProps) {
  const [playing, setPlaying] = useState(false);
  const [paused, setPaused] = useState(false);
  const [voices, setVoices] = useState<VoiceInfo[]>([]);
  const [selectedVoice, setSelectedVoice] = useState('en_US-lessac-high');
  const [showPlayer, setShowPlayer] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [prefetched, setPrefetched] = useState(false);
  const [verseIndex, setVerseIndex] = useState(0);
  const [totalVerses, setTotalVerses] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Track current verse index from playback events
  useEffect(() => {
    const unlisten = listen<{ verseId: number | null; verseIndex?: number; totalVerses?: number }>('tts-verse-playing', (event) => {
      const { verseIndex: idx, totalVerses: total } = event.payload;
      if (idx != null) setVerseIndex(idx);
      if (total != null) setTotalVerses(total);
    });
    return () => { unlisten.then(fn => fn()); };
  }, []);

  // Load voices on mount, retry if server isn't ready yet
  useEffect(() => {
    let cancelled = false;
    const loadVoices = async () => {
      try {
        const [voiceList, saved] = await Promise.all([
          listVoices(),
          getSetting('ttsVoice'),
        ]);
        if (!cancelled && voiceList.length > 0) {
          setVoices(voiceList);
          if (saved) setSelectedVoice(saved);
          return true;
        }
      } catch { /* unavailable */ }
      return false;
    };
    // Try immediately, then retry every 3s for up to 60s (venv bootstrap may take time)
    void (async () => {
      if (await loadVoices()) return;
      for (let i = 0; i < 20 && !cancelled; i++) {
        await new Promise(r => setTimeout(r, 3000));
        if (cancelled) return;
        if (await loadVoices()) {
          return;
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // Prefetch audio when chapter changes
  useEffect(() => {
    if (verses.length === 0) return;
    setPrefetched(false);

    const fullText = verses.map(v => v.text).join('. ');
    void prefetchAudio(fullText, selectedVoice);

    // Poll for prefetch readiness
    const checkInterval = setInterval(async () => {
      try {
        const ready = await isPrefetchReady();
        if (ready) {
          setPrefetched(true);
          clearInterval(checkInterval);
        }
      } catch { /* ignore */ }
    }, 500);

    return () => clearInterval(checkInterval);
  }, [bookTitle, chapterNumber, verses, selectedVoice]);

  const handleVoiceChange = useCallback((voice: string) => {
    setSelectedVoice(voice);
    void setSetting('ttsVoice', voice);
    // Re-prefetch with new voice
    if (verses.length > 0) {
      setPrefetched(false);
      const fullText = verses.map(v => v.text).join('. ');
      void prefetchAudio(fullText, voice);
    }
  }, [verses]);

  const clearPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPoll = useCallback(() => {
    clearPoll();
    pollRef.current = setInterval(async () => {
      try {
        const status = await isReading();
        if (!status.playing && !status.paused) {
          setPlaying(false);
          setPaused(false);
          setShowPlayer(false);
          clearPoll();
        } else {
          setPlaying(status.playing);
          setPaused(status.paused);
        }
      } catch {
        setPlaying(false);
        setPaused(false);
        clearPoll();
      }
    }, 1000);
  }, [clearPoll]);

  const handlePlay = useCallback(async () => {
    if (verses.length === 0) return;

    setPreparing(true);
    setShowPlayer(true);

    try {
      const rateSetting = await getSetting('ttsRate');
      const rate = rateSetting ? parseInt(rateSetting, 10) : 175;
      const verseInputs = verses.map(v => ({ id: v.id, text: v.text }));

      await readAloudVerses(verseInputs, rate, selectedVoice);
      setPlaying(true);
      setPaused(false);
      setPreparing(false);
      startPoll();
    } catch (err) {
      console.error('ReadAloud failed:', err);
      setPreparing(false);
      setPlaying(false);
      setShowPlayer(false);
    }
  }, [verses, selectedVoice, startPoll]);

  const handleSkipBack = useCallback(async () => {
    const target = Math.max(0, verseIndex - 1);
    try { await skipVerse(target); } catch { /* ignore */ }
    setPlaying(true);
    setPaused(false);
  }, [verseIndex]);

  const handleSkipForward = useCallback(async () => {
    const target = Math.min(totalVerses - 1, verseIndex + 1);
    try { await skipVerse(target); } catch { /* ignore */ }
    setPlaying(true);
    setPaused(false);
  }, [verseIndex, totalVerses]);

  const handlePause = useCallback(async () => {
    try { await pauseReading(); } catch { /* ignore */ }
    setPaused(true);
    setPlaying(false);
  }, []);

  const handleResume = useCallback(async () => {
    try { await resumeReading(); } catch { /* ignore */ }
    setPaused(false);
    setPlaying(true);
  }, []);

  const handleStop = useCallback(async () => {
    clearPoll();
    try { await stopReading(); } catch { /* ignore */ }
    setPlaying(false);
    setPaused(false);
    setShowPlayer(false);
    setPreparing(false);
  }, [clearPoll]);

  useEffect(() => {
    return () => {
      clearPoll();
      stopReading().catch(() => {});
    };
  }, [clearPoll]);

  // Reset on chapter change
  useEffect(() => {
    clearPoll();
    void stopReading().catch(() => {});
    setPlaying(false);
    setPaused(false);
    setShowPlayer(false);
    setPreparing(false);
  }, [bookTitle, chapterNumber, clearPoll]);

  return (
    <>
      {/* Inline controls */}
      {!showPlayer && (
        <div className="read-aloud-controls">
          <SpeakerIcon size={16} />
          {voices.length > 0 && (
            <select
              className="voice-select"
              value={selectedVoice}
              onChange={(e) => handleVoiceChange(e.target.value)}
            >
              {voices.map((v) => (
                <option key={v.voice_id || v.name} value={v.voice_id || v.name}>
                  {v.description || v.name}
                </option>
              ))}
            </select>
          )}
          <button
            className="read-aloud-btn"
            onClick={() => void handlePlay()}
            disabled={verses.length === 0}
            title={prefetched ? 'Play (ready)' : 'Play (will prepare first)'}
          >
            <PlayIcon size={14} />
            {prefetched && <span style={{ fontSize: 8, marginLeft: 2, color: 'var(--accent)' }}>●</span>}
          </button>
        </div>
      )}

      {/* Sticky player bar */}
      {showPlayer && (
        <div className="tts-player">
          <div className="tts-player-inner">
            <div className="tts-player-info">
              <span className="tts-player-title">{bookTitle} {chapterNumber}</span>
              <span className="tts-player-verse">
                {preparing ? 'Preparing audio...' : playing ? 'Playing' : paused ? 'Paused' : 'Ready'}
              </span>
            </div>

            <div className="tts-player-controls">
              <button
                onClick={() => void handleSkipBack()}
                className="tts-player-skip"
                title="Previous verse"
                disabled={preparing || verseIndex <= 0}
              >
                <SkipBackIcon size={16} />
              </button>

              {preparing ? (
                <div className="tts-player-main" style={{ opacity: 0.5 }}>
                  <SpeakerIcon size={18} className="playing" />
                </div>
              ) : playing ? (
                <button onClick={() => void handlePause()} className="tts-player-main" title="Pause">
                  <PauseIcon size={18} />
                </button>
              ) : paused ? (
                <button onClick={() => void handleResume()} className="tts-player-main" title="Resume">
                  <PlayIcon size={18} />
                </button>
              ) : (
                <button onClick={() => void handlePlay()} className="tts-player-main" title="Play">
                  <PlayIcon size={18} />
                </button>
              )}

              <button
                onClick={() => void handleSkipForward()}
                className="tts-player-skip"
                title="Next verse"
                disabled={preparing || verseIndex >= totalVerses - 1}
              >
                <SkipForwardIcon size={16} />
              </button>
            </div>

            <div className="tts-player-right">
              <button onClick={() => void handleStop()} className="tts-player-close" title="Close">
                <StopIcon size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
