import { useState, useEffect, useRef } from 'react';
import { checkOllamaStatus, aiQuery, getSetting, setSetting, checkOllamaInstalled, installOllama, startOllama, pullOllamaModel } from '../hooks/useScriptures';
import { listen } from '@tauri-apps/api/event';
import type { OllamaStatus } from '../types/scriptures';
import { BrainIcon, XIcon } from './Icons';

interface AIAssistantProps {
  bookTitle: string | null;
  chapterNumber: number | null;
  onClose: () => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
}

// Filter out embedding-only models
function getChatModels(status: OllamaStatus): string[] {
  return (status.models || [])
    .map((m: { name: string }) => m.name)
    .filter((name: string) => !name.includes('embed') && !name.includes('nomic'));
}

function AIEngineSetup({ onReady }: { onReady: () => void }) {
  const [status, setStatus] = useState<string>('checking');
  const [progress, setProgress] = useState('');
  const [pullPercent, setPullPercent] = useState(0);
  const [pulling, setPulling] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const info = await checkOllamaInstalled();
        if (info.running) {
          setStatus('running');
          onReady();
        } else if (info.installed) {
          setStatus('installed_not_running');
        } else {
          setStatus('not_installed');
        }
      } catch {
        setStatus('not_installed');
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Listen for model pull progress events
  useEffect(() => {
    const unlisten = listen<{ status: string; message: string; percent: number; completed: number; total: number }>('ollama-pull-progress', (event) => {
      const { message, percent } = event.payload;
      setProgress(message);
      if (percent > 0) setPullPercent(percent);
    });
    return () => { unlisten.then(fn => fn()); };
  }, []);

  const handleInstall = async () => {
    setProgress('Installing AI engine...');
    setPulling(false);
    try {
      const result = await installOllama();
      setProgress(`Installed (${result.method}). Starting...`);
      await startOllama();
      setProgress('Downloading Qwen 2.5...');
      setPulling(true);
      setPullPercent(0);
      await pullOllamaModel('qwen2.5');
      setProgress('Ready!');
      setPulling(false);
      setPullPercent(100);
      onReady();
    } catch (err) {
      setPulling(false);
      setProgress(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleStart = async () => {
    setProgress('Starting AI engine...');
    try {
      await startOllama();
      setProgress('Checking for models...');
      const info = await checkOllamaInstalled();
      if (info.running) {
        onReady();
      } else {
        setProgress('AI engine did not start. Try running "ollama serve" in a terminal.');
      }
    } catch (err) {
      setProgress(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <div className="ai-status" style={{ padding: '20px 16px' }}>
      {status === 'checking' && <p>Checking AI engine status...</p>}

      {status === 'not_installed' && !pulling && (
        <>
          <p style={{ marginBottom: 16, fontSize: 14 }}>AI features require a local AI engine to be installed.</p>
          <button
            onClick={() => void handleInstall()}
            disabled={!!progress && !progress.startsWith('Error')}
            style={{
              width: '100%', padding: '12px', background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: '8px', fontFamily: 'var(--font-sans)',
              fontSize: 14, fontWeight: 600, cursor: 'pointer', marginBottom: 12,
              opacity: progress && !progress.startsWith('Error') ? 0.6 : 1,
            }}
          >
            Install AI Engine + Qwen 2.5
          </button>
          <p style={{ fontSize: 11, opacity: 0.6, textAlign: 'center' }}>
            Installs the local AI runtime and Qwen 2.5 model
          </p>
        </>
      )}

      {status === 'installed_not_running' && (
        <>
          <p style={{ marginBottom: 16, fontSize: 14 }}>AI engine is installed but not running.</p>
          <button
            onClick={() => void handleStart()}
            style={{
              width: '100%', padding: '12px', background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: '8px', fontFamily: 'var(--font-sans)',
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}
          >
            Start AI Engine
          </button>
        </>
      )}

      {progress && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontSize: 12, color: 'var(--accent)', textAlign: 'center', marginBottom: 8 }}>
            {progress}
          </p>
          {pulling && (
            <div style={{ marginTop: 4 }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between', fontSize: 11,
                color: 'var(--text-secondary)', marginBottom: 4,
              }}>
                <span>Downloading model</span>
                <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{pullPercent}%</span>
              </div>
              <div style={{
                height: 4, background: 'rgba(139, 115, 85, 0.15)',
                borderRadius: 2, overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%', width: `${pullPercent}%`,
                  background: 'var(--accent)', borderRadius: 2,
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AIAssistant({ bookTitle, chapterNumber, onClose }: AIAssistantProps) {
  const [aiStatus, setAiStatus] = useState<OllamaStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check AI engine status and auto-detect best model
  useEffect(() => {
    let cancelled = false;
    setChecking(true);

    (async () => {
      try {
        const status = await checkOllamaStatus();
        if (cancelled) return;
        setAiStatus(status);

        if (status.available) {
          const savedModel = await getSetting('aiModel');
          const chatModels = getChatModels(status);

          if (savedModel && chatModels.includes(savedModel)) {
            setSelectedModel(savedModel);
          } else if (chatModels.length > 0) {
            setSelectedModel(chatModels[0]);
          }
        }
      } catch {
        if (!cancelled) setAiStatus({ available: false, models: [] });
      } finally {
        if (!cancelled) setChecking(false);
      }
    })();

    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    void setSetting('aiModel', model);
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = { role: 'user', content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const model = selectedModel || 'qwen2.5:latest';

      const response = await aiQuery(
        text.trim(),
        bookTitle ?? undefined,
        chapterNumber ?? undefined,
        model,
      );

      const content = response.response || '(No response from model. Try a different model or rephrase your question.)';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content, model },
      ]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      let userFriendly = errorMsg;
      if (errorMsg.includes('Ollama') || errorMsg.includes('ollama')) {
        userFriendly = 'Could not reach the AI engine. Make sure it is running.';
      } else if (errorMsg.includes('parse')) {
        userFriendly = 'Received an unexpected response from the model. Try a different model.';
      }
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${userFriendly}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void sendMessage(input);
  };

  const handleExplainChapter = () => {
    if (!bookTitle || chapterNumber == null) return;
    void sendMessage(`Explain the key themes and teachings in ${bookTitle} chapter ${chapterNumber}`);
  };

  const handleRelatedPassages = () => {
    if (!bookTitle || chapterNumber == null) return;
    void sendMessage(`What other scriptures relate to the themes in ${bookTitle} ${chapterNumber}?`);
  };

  const chatModels = aiStatus ? getChatModels(aiStatus) : [];

  return (
    <div className="ai-panel">
      <div className="ai-panel-header ornamental-card">
        <div className="ai-panel-title">
          <BrainIcon size={20} />
          <span>Scripture Assistant</span>
        </div>
        <button className="ai-close-btn" onClick={onClose} title="Close AI Assistant">
          <XIcon size={18} />
        </button>
      </div>

      {checking ? (
        <div className="ai-status">Checking AI availability...</div>
      ) : !aiStatus?.available ? (
        <AIEngineSetup onReady={() => {
          void checkOllamaStatus().then(s => {
            setAiStatus(s);
            const models = getChatModels(s);
            if (models.length > 0) setSelectedModel(models[0]);
          });
        }} />
      ) : chatModels.length === 0 ? (
        <div className="ai-status">
          <p style={{ marginBottom: 12 }}>AI engine is running but no chat models found.</p>
          <button
            className="ai-action-btn"
            onClick={async () => {
              try {
                const btn = document.querySelector('.ai-action-btn') as HTMLButtonElement;
                if (btn) { btn.disabled = true; btn.textContent = 'Downloading Qwen 2.5... (this may take a minute)'; }
                await pullOllamaModel('qwen2.5');
                const s = await checkOllamaStatus();
                setAiStatus(s);
                const models = getChatModels(s);
                if (models.length > 0) setSelectedModel(models[0]);
              } catch (err) {
                alert(`Failed to download model: ${err instanceof Error ? err.message : String(err)}`);
              }
            }}
          >
            Download Qwen 2.5 Model
          </button>
        </div>
      ) : (
        <div className="ai-chat">
          {/* Model selector */}
          <div className="ai-model-selector">
            <label>Model:</label>
            <select
              value={selectedModel}
              onChange={(e) => handleModelChange(e.target.value)}
              disabled={loading}
            >
              {chatModels.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div className="ai-messages">
            {messages.length === 0 && (
              <div className="ai-welcome">
                <BrainIcon size={32} />
                <p>Ask questions about the scriptures. I can explain passages, find connections, and help with study.</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`ai-message ai-message-${msg.role}`}>
                <div className="ai-message-content">
                  {msg.content}
                  {msg.model && msg.role === 'assistant' && !msg.content.startsWith('Error') && (
                    <div className="ai-message-model">{msg.model}</div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="ai-message ai-message-assistant">
                <div className="ai-message-content ai-thinking">
                  Thinking<span className="ai-thinking-dots"><span>.</span><span>.</span><span>.</span><span>.</span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {bookTitle && chapterNumber != null && (
            <div className="ai-quick-actions">
              <button onClick={handleExplainChapter} disabled={loading}>
                Explain this chapter
              </button>
              <button onClick={handleRelatedPassages} disabled={loading}>
                Find related passages
              </button>
            </div>
          )}

          <form className="ai-input" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about the scriptures..."
              disabled={loading}
            />
            <button type="submit" disabled={!input.trim() || loading}>
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
