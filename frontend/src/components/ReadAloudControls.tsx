import { useState, useCallback, useRef, useEffect } from 'react';
import { readAloud, pauseReading, resumeReading, stopReading, isReading, getSetting, setSetting, listVoices } from '../hooks/useScriptures';
import type { VerseResult } from '../types/scriptures';
import type { VoiceInfo } from '../hooks/useScriptures';
import { PlayIcon, PauseIcon, StopIcon, SpeakerIcon } from './Icons';

interface ReadAloudControlsProps {
  verses: VerseResult[];
  bookTitle: string;
  chapterNumber: number;
}

export function ReadAloudControls({ verses, bookTitle, chapterNumber }: ReadAloudControlsProps) {
  const [playing, setPlaying] = useState(false);
  const [paused, setPaused] = useState(false);
  const [voices, setVoices] = useState<VoiceInfo[]>([]);
  const [selectedVoice, setSelectedVoice] = useState('default');
  const [showPlayer, setShowPlayer] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [voiceList, saved] = await Promise.all([
          listVoices(),
          getSetting('ttsVoice'),
        ]);
        setVoices(voiceList);
        if (saved) setSelectedVoice(saved);
      } catch { /* voices unavailable */ }
    })();
  }, []);

  const handleVoiceChange = useCallback((voice: string) => {
    setSelectedVoice(voice);
    void setSetting('ttsVoice', voice);
  }, []);

  const clearPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // Start polling for playback status
  const startPoll = useCallback(() => {
    clearPoll();
    pollRef.current = setInterval(async () => {
      try {
        const status = await isReading();
        if (!status.playing && !status.paused) {
          // Playback finished naturally
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

    try {
      const rateSetting = await getSetting('ttsRate');
      const rate = rateSetting ? parseInt(rateSetting, 10) : 175;
      const voice = selectedVoice !== 'default' ? selectedVoice : undefined;

      // Send entire chapter as one block — natural flow, no gaps
      const fullText = verses
        .map(v => v.text)
        .join('. ');  // Period+space gives natural pause between verses

      await readAloud(fullText, rate, voice);
      setPlaying(true);
      setPaused(false);
      setShowPlayer(true);
      startPoll();
    } catch (err) {
      console.error('ReadAloud failed:', err);
      setPlaying(false);
    }
  }, [verses, selectedVoice, startPoll]);

  const handlePause = useCallback(async () => {
    try {
      await pauseReading();
      setPaused(true);
      setPlaying(false);
    } catch { /* ignore */ }
  }, []);

  const handleResume = useCallback(async () => {
    try {
      await resumeReading();
      setPaused(false);
      setPlaying(true);
    } catch { /* ignore */ }
  }, []);

  const handleStop = useCallback(async () => {
    clearPoll();
    try { await stopReading(); } catch { /* ignore */ }
    setPlaying(false);
    setPaused(false);
    setShowPlayer(false);
  }, [clearPoll]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearPoll();
      stopReading().catch(() => {});
    };
  }, [clearPoll]);

  // Reset when chapter changes
  useEffect(() => {
    clearPoll();
    void stopReading().catch(() => {});
    setPlaying(false);
    setPaused(false);
    setShowPlayer(false);
  }, [bookTitle, chapterNumber, clearPoll]);

  return (
    <>
      {/* Inline play button (in header area) */}
      {!showPlayer && (
        <div className="read-aloud-controls">
          <SpeakerIcon size={16} />
          {voices.length > 1 && (
            <select
              className="voice-select"
              value={selectedVoice}
              onChange={(e) => handleVoiceChange(e.target.value)}
              title="Select voice"
            >
              <option value="default">Default Voice</option>
              {voices.map((v) => (
                <option key={v.name} value={v.name}>
                  {v.name} {v.engine === 'vibevoice' ? '(Neural)' : ''}
                </option>
              ))}
            </select>
          )}
          <button className="read-aloud-btn" onClick={() => void handlePlay()} disabled={verses.length === 0}
            title={`Read ${bookTitle} ${chapterNumber} aloud`}>
            <PlayIcon size={14} />
          </button>
        </div>
      )}

      {/* Sticky floating player bar */}
      {showPlayer && (
        <div className="tts-player">
          <div className="tts-player-inner">
            <div className="tts-player-info">
              <span className="tts-player-title">{bookTitle} {chapterNumber}</span>
              <span className="tts-player-verse">
                {playing ? 'Playing...' : paused ? 'Paused' : 'Ready'}
              </span>
            </div>

            <div className="tts-player-controls">
              {playing ? (
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
            </div>

            <div className="tts-player-right">
              {voices.length > 1 && (
                <select
                  className="voice-select"
                  value={selectedVoice}
                  onChange={(e) => handleVoiceChange(e.target.value)}
                  disabled={playing}
                >
                  <option value="default">Default</option>
                  {voices.map((v) => (
                    <option key={v.name} value={v.name}>
                      {v.name} {v.engine === 'vibevoice' ? '(Neural)' : ''}
                    </option>
                  ))}
                </select>
              )}
              <button onClick={() => void handleStop()} className="tts-player-close" title="Close player">
                <StopIcon size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
