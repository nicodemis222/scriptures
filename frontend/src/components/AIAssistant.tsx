import { useState, useEffect, useRef } from 'react';
import {
  checkOllamaStatus, aiQuery, startOllama, checkOllamaInstalled,
  installOllama, pullOllamaModel,
} from '../hooks/useScriptures';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import type { OllamaStatus } from '../types/scriptures';
import { BrainIcon, XIcon } from './Icons';

const MODEL = 'mistral:7b';
const MODEL_LABEL = 'Mistral 7B';
const MODEL_SIZE = '~4.1 GB';

interface AIAssistantProps {
  bookTitle: string | null;
  chapterNumber: number | null;
  onClose: () => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

type SetupState =
  | { kind: 'checking' }
  | { kind: 'not_installed' }
  | { kind: 'installed_not_running' }
  | { kind: 'running_no_model' }
  | { kind: 'ready' };

function hasMistral(status: OllamaStatus): boolean {
  return (status.models || []).some((m: { name: string }) => m.name.startsWith('mistral'));
}

async function detectSetupState(): Promise<SetupState> {
  try {
    const info = await checkOllamaInstalled();
    if (!info.installed) return { kind: 'not_installed' };
    if (!info.running) return { kind: 'installed_not_running' };
    const status = await checkOllamaStatus();
    if (!status.available) return { kind: 'installed_not_running' };
    if (!hasMistral(status)) return { kind: 'running_no_model' };
    return { kind: 'ready' };
  } catch {
    return { kind: 'not_installed' };
  }
}

/**
 * Inline setup panel for when AI engine / model isn't ready. Distinct
 * branches per state, so users always have a workable next step instead of
 * a dead-end "Start AI Engine" button on already-running engines that just
 * lack the model.
 */
function AISetupPanel({ initial, onReady }: { initial: SetupState; onReady: () => void }) {
  const [state, setState] = useState<SetupState>(initial);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [percent, setPercent] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  // Listen for model-pull progress
  useEffect(() => {
    let unlisten: UnlistenFn | undefined;
    let cancelled = false;
    void listen<{ status: string; message: string; percent: number }>(
      'ollama-pull-progress',
      (event) => {
        if (!mountedRef.current) return;
        const { status: evtStatus, message, percent: pct } = event.payload;
        if (pct > 0) setPercent(pct);
        if (message) setStatus(message);
        if (evtStatus === 'success') {
          setPercent(100);
          setStatus('Model ready!');
          // Re-detect, then mark ready
          void detectSetupState().then((s) => {
            if (!mountedRef.current) return;
            setBusy(false);
            if (s.kind === 'ready') onReady();
            else setState(s);
          });
        } else if (evtStatus === 'error') {
          setBusy(false);
          setError(message || 'Model download failed');
        }
      },
    ).then((fn) => {
      if (cancelled) fn();
      else unlisten = fn;
    });
    return () => { cancelled = true; unlisten?.(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runInstall = async () => {
    setError(null);
    setBusy(true);
    setStatus('Installing AI engine…');
    try {
      const r = await installOllama();
      if (!mountedRef.current) return;
      setStatus(`AI engine installed (${r.method || 'ok'}).`);
      await startStep();
    } catch (err) {
      if (!mountedRef.current) return;
      setBusy(false);
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const startStep = async () => {
    setStatus('Starting AI engine…');
    await startOllama();
    // Poll for readiness up to 15s
    for (let i = 0; i < 15; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      if (!mountedRef.current) return;
      const s = await detectSetupState();
      if (s.kind === 'running_no_model' || s.kind === 'ready') {
        if (s.kind === 'ready') {
          setBusy(false);
          onReady();
          return;
        }
        // Engine up, need model — chain into download
        setState({ kind: 'running_no_model' });
        await downloadStep();
        return;
      }
    }
    setBusy(false);
    setError('AI engine did not start. Please try again.');
  };

  const downloadStep = async () => {
    setStatus(`Downloading ${MODEL_LABEL} (${MODEL_SIZE})…`);
    setPercent(0);
    // pull returns immediately; completion fires via event listener
    await pullOllamaModel(MODEL);
  };

  const handleStart = async () => {
    setError(null);
    setBusy(true);
    try {
      await startStep();
    } catch (err) {
      if (!mountedRef.current) return;
      setBusy(false);
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDownload = async () => {
    setError(null);
    setBusy(true);
    try {
      await downloadStep();
    } catch (err) {
      if (!mountedRef.current) return;
      setBusy(false);
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="ai-status" style={{ padding: '20px 16px' }}>
      {state.kind === 'checking' && <p>Checking AI engine status…</p>}

      {state.kind === 'not_installed' && (
        <>
          <p style={{ marginBottom: 16, fontSize: 14 }}>
            AI features require a local AI engine and the Mistral 7B model.
          </p>
          <button
            onClick={() => void runInstall()}
            disabled={busy}
            className="ai-setup-primary-btn"
          >
            {busy ? 'Working…' : `Install AI Engine + ${MODEL_LABEL}`}
          </button>
          <p style={{ fontSize: 11, opacity: 0.6, textAlign: 'center', marginTop: 10 }}>
            Installs the AI engine and downloads {MODEL_LABEL} ({MODEL_SIZE}).
          </p>
        </>
      )}

      {state.kind === 'installed_not_running' && (
        <>
          <p style={{ marginBottom: 16, fontSize: 14 }}>
            The AI engine is installed but not running.
          </p>
          <button
            onClick={() => void handleStart()}
            disabled={busy}
            className="ai-setup-primary-btn"
          >
            {busy ? 'Starting…' : 'Start AI Engine'}
          </button>
        </>
      )}

      {state.kind === 'running_no_model' && (
        <>
          <p style={{ marginBottom: 16, fontSize: 14 }}>
            The AI engine is running but the <strong>{MODEL_LABEL}</strong> model
            isn&rsquo;t downloaded yet.
          </p>
          <button
            onClick={() => void handleDownload()}
            disabled={busy}
            className="ai-setup-primary-btn"
          >
            {busy ? 'Downloading…' : `Download ${MODEL_LABEL} (${MODEL_SIZE})`}
          </button>
          <p style={{ fontSize: 11, opacity: 0.6, textAlign: 'center', marginTop: 10 }}>
            One-time download. Works offline after.
          </p>
        </>
      )}

      {busy && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontSize: 12, color: 'var(--accent)', textAlign: 'center', marginBottom: 8 }}>
            {status}
          </p>
          {percent > 0 && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>
                <span>Downloading</span>
                <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{percent}%</span>
              </div>
              <div style={{ height: 4, background: 'rgba(139, 115, 85, 0.15)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${percent}%`, background: 'var(--accent)', borderRadius: 2, transition: 'width 0.5s ease' }} />
              </div>
            </>
          )}
        </div>
      )}

      {error && (
        <p style={{ marginTop: 12, fontSize: 12, color: '#b85450', background: 'rgba(184, 84, 80, 0.08)', padding: '8px 12px', borderRadius: 6 }}>
          {error}
        </p>
      )}
    </div>
  );
}

export function AIAssistant({ bookTitle, chapterNumber, onClose }: AIAssistantProps) {
  const [setupState, setSetupState] = useState<SetupState>({ kind: 'checking' });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    void (async () => {
      const s = await detectSetupState();
      if (mountedRef.current) setSetupState(s);
    })();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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

      {setupState.kind !== 'ready' ? (
        <AISetupPanel
          initial={setupState}
          onReady={() => setSetupState({ kind: 'ready' })}
        />
      ) : (
        <div className="ai-chat">
          <div className="ai-messages">
            {messages.length === 0 && (
              <div className="ai-welcome">
                <BrainIcon size={32} />
                <p>Ask questions about the scriptures. I can explain passages, find connections, and help with study.</p>
                <p style={{ fontSize: 11, opacity: 0.5, marginTop: 8 }}>Powered by local {MODEL_LABEL}</p>
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
