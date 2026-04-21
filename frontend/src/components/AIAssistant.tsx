import { useState, useEffect, useRef } from 'react';
import { checkOllamaStatus, aiQuery, startOllama, checkOllamaInstalled } from '../hooks/useScriptures';
import type { OllamaStatus } from '../types/scriptures';
import { BrainIcon, XIcon } from './Icons';

const MODEL = 'mistral:7b';

interface AIAssistantProps {
  bookTitle: string | null;
  chapterNumber: number | null;
  onClose: () => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

function hasMistral(status: OllamaStatus): boolean {
  return (status.models || []).some((m: { name: string }) => m.name.startsWith('mistral'));
}

export function AIAssistant({ bookTitle, chapterNumber, onClose }: AIAssistantProps) {
  const [aiStatus, setAiStatus] = useState<OllamaStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const refreshStatus = async () => {
    try {
      const status = await checkOllamaStatus();
      setAiStatus(status);
    } catch {
      setAiStatus({ available: false, models: [] });
    }
  };

  useEffect(() => {
    let cancelled = false;
    setChecking(true);
    (async () => {
      await refreshStatus();
      if (!cancelled) setChecking(false);
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleStart = async () => {
    setStarting(true);
    try {
      const info = await checkOllamaInstalled();
      if (!info.installed) {
        // Fallback: if first-run setup was skipped, direct them back
        alert('AI engine is not installed. Please restart the app to complete setup, or install from the tutorial.');
        return;
      }
      await startOllama();
      await new Promise((r) => setTimeout(r, 1500));
      await refreshStatus();
    } catch (err) {
      alert(`Could not start AI engine: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setStarting(false);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = { role: 'user', content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await aiQuery(
        text.trim(),
        bookTitle ?? undefined,
        chapterNumber ?? undefined,
        MODEL,
      );

      const content = response.response || '(No response from the AI engine. Please try again.)';
      setMessages((prev) => [...prev, { role: 'assistant', content }]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      let userFriendly = errorMsg;
      if (errorMsg.toLowerCase().includes('ollama') || errorMsg.toLowerCase().includes('connect')) {
        userFriendly = 'Could not reach the AI engine. Make sure it is running.';
      }
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${userFriendly}` }]);
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

  const isReady = aiStatus?.available && hasMistral(aiStatus);

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
        <div className="ai-status">Checking AI engine...</div>
      ) : !isReady ? (
        <div className="ai-status" style={{ padding: '20px 16px' }}>
          <p style={{ marginBottom: 16, fontSize: 14 }}>
            The AI engine is not running. Click below to start it.
          </p>
          <button
            onClick={() => void handleStart()}
            disabled={starting}
            style={{
              width: '100%', padding: '12px', background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: '8px', fontFamily: 'var(--font-sans)',
              fontSize: 14, fontWeight: 600, cursor: starting ? 'default' : 'pointer',
              opacity: starting ? 0.6 : 1,
            }}
          >
            {starting ? 'Starting…' : 'Start AI Engine'}
          </button>
          <p style={{ fontSize: 11, opacity: 0.6, textAlign: 'center', marginTop: 12 }}>
            Powered by local Mistral 7B
          </p>
        </div>
      ) : (
        <div className="ai-chat">
          <div className="ai-messages">
            {messages.length === 0 && (
              <div className="ai-welcome">
                <BrainIcon size={32} />
                <p>Ask questions about the scriptures. I can explain passages, find connections, and help with study.</p>
                <p style={{ fontSize: 11, opacity: 0.5, marginTop: 8 }}>Powered by local Mistral 7B</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`ai-message ai-message-${msg.role}`}>
                <div className="ai-message-content">{msg.content}</div>
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
