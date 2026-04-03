import { useState, useEffect } from 'react';
import { getSetting, setSetting } from '../hooks/useScriptures';
import { XIcon } from './Icons';

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
  const [aiModel, setAiModel] = useState('phi3:mini');

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const [fs, lang, rate, model] = await Promise.all([
        getSetting('fontSize'),
        getSetting('language'),
        getSetting('ttsRate'),
        getSetting('aiModel'),
      ]);
      if (fs) setFontSize(parseInt(fs, 10));
      if (lang) setLanguage(lang);
      if (rate) setTtsRate(parseInt(rate, 10));
      if (model) setAiModel(model);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  }

  function handleFontSizeChange(size: number) {
    setFontSize(size);
    document.documentElement.style.setProperty('--verse-size', `${size}px`);
    setSetting('fontSize', String(size));
  }

  function handleLanguageChange(lang: string) {
    setLanguage(lang);
    setSetting('language', lang);
  }

  function handleTtsRateChange(rate: number) {
    setTtsRate(rate);
    setSetting('ttsRate', String(rate));
  }

  function handleAiModelChange(model: string) {
    setAiModel(model);
    setSetting('aiModel', model);
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
            Translation uses Ollama AI. Select a language here as default, or use the language dropdown in the verse reader to translate on the fly. Requires Ollama running locally.
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
        </section>

        {/* AI Assistant */}
        <section className="settings-section ornamental-card">
          <h3>AI Assistant</h3>

          <p className="settings-note">
            Requires Ollama running locally. Install from ollama.ai
          </p>

          <div className="settings-row">
            <label>Model</label>
            <input
              type="text"
              value={aiModel}
              onChange={(e) => handleAiModelChange(e.target.value)}
              placeholder="phi3:mini"
            />
          </div>
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
            <p><strong>Scriptures</strong> v0.1.0</p>
            <p>A complete offline scripture study companion with highlights, notes, and AI-powered insights.</p>
          </div>
        </section>
      </div>
    </div>
  );
}
