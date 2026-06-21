import { useState, useEffect } from 'react';
import {
  getSetting, setSetting,
  enhancedVoicesStatus, installCommandLineTools, setupEnhancedVoices,
  type EnhancedVoicesStatus,
} from '../hooks/useScriptures';
import { XIcon } from './Icons';

/**
 * Opt-in setup for Piper "enhanced" neural voices. Read Aloud already works via
 * macOS `say` with zero setup; this lets the user upgrade to higher-quality
 * voices. We NEVER auto-trigger this and never invoke the python3 shim — the
 * status check and CLT install are explicit and consent-gated.
 */
function EnhancedVoices() {
  const [status, setStatus] = useState<EnhancedVoicesStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const refresh = async () => {
    try { setStatus(await enhancedVoicesStatus()); } catch { /* ignore */ }
  };
  useEffect(() => { void refresh(); }, []);

  if (!status) return null;

  if (status.server_running || status.venv_ready) {
    return (
      <p className="settings-note">
        ✓ <strong>Enhanced neural voices</strong> are active. Read Aloud is using
        the high-quality Piper voices.
      </p>
    );
  }

  const handleSetup = async () => {
    setBusy(true); setMsg(null);
    try {
      if (!status.clt_installed) {
        await installCommandLineTools();
        setMsg('Apple’s installer was opened. Finish the install, then click “Set Up” again.');
        setBusy(false);
        void refresh();
        return;
      }
      const r = await setupEnhancedVoices();
      if (r.status === 'already_ready') {
        setMsg('Enhanced voices are ready.');
      } else {
        setMsg('Setting up enhanced voices… progress shows in the banner above. This downloads ~220 MB and needs internet.');
      }
    } catch (err) {
      setMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
      void refresh();
    }
  };

  return (
    <div style={{ marginTop: 12 }}>
      <p className="settings-note" style={{ marginBottom: 10 }}>
        Read Aloud works now using your Mac&rsquo;s built-in voice. For higher-quality
        <strong> neural voices</strong>, set up the optional enhanced engine
        {status.clt_installed
          ? ' (one-time ~220 MB download, needs internet).'
          : '. This first needs Apple’s Command Line Tools.'}
      </p>
      <button className="settings-btn" onClick={() => void handleSetup()} disabled={busy}>
        {busy ? 'Working…' : status.clt_installed ? 'Set Up Enhanced Voices' : 'Install Command Line Tools'}
      </button>
      {msg && <p className="settings-note" style={{ marginTop: 8 }}>{msg}</p>}
    </div>
  );
}

interface SettingsPanelProps {
  onClose: () => void;
  theme: string;
  onThemeChange: (theme: string) => void;
  onShowTutorial: () => void;
}

const LANGUAGES = [
  'English',
  'Spanish',
  'French',
  'Portuguese',
  'German',
  'Italian',
  'Chinese',
  'Korean',
  'Japanese',
  'Russian',
];

export function SettingsPanel({ onClose, theme, onThemeChange, onShowTutorial }: SettingsPanelProps) {
  const [fontSize, setFontSize] = useState(18);
  const [language, setLanguage] = useState('English');
  const [ttsRate, setTtsRate] = useState(175);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const [fs, lang, rate] = await Promise.all([
          getSetting('fontSize'),
          getSetting('language'),
          getSetting('ttsRate'),
        ]);
        if (cancelled) return;
        if (fs) setFontSize(parseInt(fs, 10));
        if (lang) setLanguage(lang);
        if (rate) setTtsRate(parseInt(rate, 10));
      } catch (err) {
        console.error('Failed to load settings:', err);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // Persist a setting without leaving a floating promise (which can surface as
  // an unhandled rejection). Failures are non-fatal — log and move on.
  function persist(key: string, value: string) {
    void setSetting(key, value).catch((err) => {
      console.error(`Failed to save setting ${key}:`, err);
    });
  }

  function handleFontSizeChange(size: number) {
    setFontSize(size);
    document.documentElement.style.setProperty('--verse-size', `${size}px`);
    persist('fontSize', String(size));
  }

  function handleLanguageChange(lang: string) {
    setLanguage(lang);
    persist('language', lang);
  }

  function handleTtsRateChange(rate: number) {
    setTtsRate(rate);
    persist('ttsRate', String(rate));
  }

  return (
    <div className="settings-panel">
      <div className="settings-header">
        <h2>Settings</h2>
        <button className="close-btn" onClick={onClose} aria-label="Close">
          <XIcon size={20} />
        </button>
      </div>

      <div className="settings-content">
        {/* Appearance */}
        <section className="settings-section ornamental-card">
          <h3>Appearance</h3>

          <div className="settings-row">
            <label>Theme</label>
            <div className="theme-buttons">
              {(['light', 'dark', 'system'] as const).map((t) => (
                <button
                  key={t}
                  className={`theme-btn ${theme === t ? 'active' : ''}`}
                  onClick={() => onThemeChange(t)}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="settings-row">
            <label>Font Size: {fontSize}px</label>
            <input
              type="range"
              min={14}
              max={24}
              value={fontSize}
              onChange={(e) => handleFontSizeChange(parseInt(e.target.value, 10))}
            />
          </div>
        </section>

        {/* Language */}
        <section className="settings-section ornamental-card">
          <h3>Language</h3>

          <div className="settings-row">
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <p className="settings-note">
            Translation uses the local Mistral AI engine. Select a language here as default, or use the language dropdown in the verse reader to translate on the fly. Requires the AI engine to be running.
          </p>
        </section>

        {/* Read Aloud */}
        <section className="settings-section ornamental-card">
          <h3>Read Aloud</h3>

          <div className="settings-row">
            <label>Speed: {ttsRate} words per minute</label>
            <input
              type="range"
              min={100}
              max={300}
              value={ttsRate}
              onChange={(e) => handleTtsRateChange(parseInt(e.target.value, 10))}
            />
          </div>

          <EnhancedVoices />
        </section>

        {/* AI Assistant */}
        <section className="settings-section ornamental-card">
          <h3>AI Assistant</h3>

          <p className="settings-note">
            Powered by the local <strong>Mistral 7B</strong> model. AI features (Scripture Assistant,
            My Journey, Verse Explain, Translation) all use this single engine —
            no model selection needed. Set up at first launch.
          </p>
        </section>

        {/* Help */}
        <section className="settings-section ornamental-card">
          <h3>Help</h3>

          <div className="settings-row">
            <button className="settings-btn" onClick={onShowTutorial}>
              View Tutorial
            </button>
          </div>

          <div className="settings-about">
            <p><strong>Scriptures</strong> v0.4.0</p>
            <p>A complete offline scripture study companion with highlights, notes, and AI-powered insights.</p>
          </div>
        </section>
      </div>
    </div>
  );
}
