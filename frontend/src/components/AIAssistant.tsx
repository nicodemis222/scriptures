import { useState, useEffect, useRef } from 'react';
import { checkOllamaStatus, aiQuery, getSetting, setSetting, checkOllamaInstalled, installOllama, startOllama, pullOllamaModel } from '../hooks/useScriptures';
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

function OllamaSetup({ onReady }: { onReady: () => void }) {
  const [status, setStatus] = useState<string>('checking');
  const [progress, setProgress] = useState('');

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

  const handleInstall = async () => {
    setProgress('Installing Ollama...');
    try {
      const result = await installOllama();
      setProgress(`Installed (${result.method}). Starting...`);
      await startOllama();
      setProgress('Pulling llama3.2 model...');
      await pullOllamaModel('llama3.2');
      setProgress('Ready!');
      onReady();
    } catch (err) {
      setProgress(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleStart = async () => {
    setProgress('Starting Ollama...');
    try {
      await startOllama();
      setProgress('Checking for models...');
      const info = await checkOllamaInstalled();
      if (info.running) {
        onReady();
      } else {
        setProgress('Ollama did not start. Try running "ollama serve" in a terminal.');
      }
    } catch (err) {
      setProgress(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <div className="ai-status" style={{ padding: '20px 16px' }}>
      {status === 'checking' && <p>Checking Ollama status...</p>}

      {status === 'not_installed' && (
        <>
          <p style={{ marginBottom: 16, fontSize: 14 }}>AI features require Ollama.</p>
          <button
            onClick={() => void handleInstall()}
            style={{
              width: '100%', padding: '12px', background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: '8px', fontFamily: 'var(--font-sans)',
              fontSize: 14, fontWeight: 600, cursor: 'pointer', marginBottom: 12,
            }}
          >
            Install Ollama + llama3.2
          </button>
          <p style={{ fontSize: 11, opacity: 0.6, textAlign: 'center' }}>
            Installs via Homebrew or ollama.com script
          </p>
        </>
      )}

      {status === 'installed_not_running' && (
        <>
          <p style={{ marginBottom: 16, fontSize: 14 }}>Ollama is installed but not running.</p>
          <button
            onClick={() => void handleStart()}
            style={{
              width: '100%', padding: '12px', background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: '8px', fontFamily: 'var(--font-sans)',
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}
          >
            Start Ollama
          </button>
        </>
      )}

      {progress && (
        <p style={{ marginTop: 12, fontSize: 12, color: 'var(--accent)', textAlign: 'center' }}>
          {progress}
        </p>
      )}
    </div>
  );
}

export function AIAssistant({ bookTitle, chapterNumber, onClose }: AIAssistantProps) {
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check Ollama status and auto-detect best model
  useEffect(() => {
    let cancelled = false;
    setChecking(true);

    (async () => {
      try {
        const status = await checkOllamaStatus();
        if (cancelled) return;
        setOllamaStatus(status);

        if (status.available) {
          // Try to load saved model preference
          const savedModel = await getSetting('aiModel');
          const chatModels = getChatModels(status);

          if (savedModel && chatModels.includes(savedModel)) {
            setSelectedModel(savedModel);
          } else if (chatModels.length > 0) {
            // Auto-select first available chat model
            setSelectedModel(chatModels[0]);
          }
        }
      } catch {
        if (!cancelled) setOllamaStatus({ available: false, models: [] });
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
      const model = selectedModel || 'llama3.2:latest';

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
      if (errorMsg.includes('Ollama')) {
        userFriendly = 'Could not reach Ollama. Make sure it is running (`ollama serve`).';
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

  const chatModels = ollamaStatus ? getChatModels(ollamaStatus) : [];

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
      ) : !ollamaStatus?.available ? (
        <OllamaSetup onReady={() => {
          void checkOllamaStatus().then(s => {
            setOllamaStatus(s);
            const models = getChatModels(s);
            if (models.length > 0) setSelectedModel(models[0]);
          });
        }} />
      ) : chatModels.length === 0 ? (
        <div className="ai-status">
          <p style={{ marginBottom: 12 }}>Ollama is running but no chat models found.</p>
          <p style={{ fontSize: 13, opacity: 0.8 }}>
            Run: <code>ollama pull llama3.2</code>
          </p>
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
                <div className="ai-message-content ai-thinking">Thinking...</div>
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
