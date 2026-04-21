import { useEffect, useState } from 'react';
import { listen } from '@tauri-apps/api/event';
import { checkOllamaInstalled, installOllama, startOllama, pullOllamaModel, checkOllamaStatus } from '../hooks/useScriptures';
import { BrainIcon, BookOpen } from './Icons';

const MODEL = 'mistral:7b';
const MODEL_LABEL = 'Mistral 7B';
const MODEL_SIZE = '~4.1 GB';

type Stage = 'checking' | 'ready_to_install' | 'installing' | 'starting' | 'pulling' | 'verifying' | 'done' | 'error';

interface FirstRunSetupProps {
  onComplete: () => void;
}

interface EngineState {
  installed: boolean;
  running: boolean;
  hasModel: boolean;
}

async function getEngineState(): Promise<EngineState> {
  const info = await checkOllamaInstalled();
  let hasModel = false;
  if (info.running) {
    try {
      const status = await checkOllamaStatus();
      hasModel = (status.models || []).some(m => m.name.startsWith('mistral'));
    } catch { /* ignore */ }
  }
  return { installed: info.installed, running: info.running, hasModel };
}

export function FirstRunSetup({ onComplete }: FirstRunSetupProps) {
  const [stage, setStage] = useState<Stage>('checking');
  const [engine, setEngine] = useState<EngineState>({ installed: false, running: false, hasModel: false });
  const [statusMsg, setStatusMsg] = useState('Checking system…');
  const [percent, setPercent] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Listen for model pull progress
  useEffect(() => {
    const unlisten = listen<{ status: string; message: string; percent: number }>('ollama-pull-progress', (event) => {
      const { status: evtStatus, message, percent: pct } = event.payload;
      if (pct > 0) setPercent(pct);
      if (message) setStatusMsg(message);
      if (evtStatus === 'success') {
        setPercent(100);
        setStatusMsg('Model ready!');
        setStage('verifying');
        void verifyAndFinish();
      } else if (evtStatus === 'error') {
        setError(message || 'Model download failed');
        setStage('error');
      }
    });
    return () => { unlisten.then((fn) => fn()); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const state = await getEngineState();
        setEngine(state);
        if (state.installed && state.running && state.hasModel) {
          setStage('done');
          setStatusMsg('Everything is ready!');
        } else {
          setStage('ready_to_install');
          setStatusMsg('Ready to set up');
        }
      } catch {
        setStage('ready_to_install');
        setStatusMsg('Ready to set up');
      }
    })();
  }, []);

  const verifyAndFinish = async () => {
    // Poll a few times to make sure Ollama actually has the model registered
    for (let i = 0; i < 10; i++) {
      await new Promise((r) => setTimeout(r, 1500));
      try {
        const status = await checkOllamaStatus();
        const hasModel = (status.models || []).some(m => m.name.startsWith('mistral'));
        if (hasModel) {
          setEngine(e => ({ ...e, running: true, hasModel: true }));
          setStage('done');
          setStatusMsg('Everything is ready!');
          return;
        }
      } catch { /* retry */ }
    }
    setError('Model finished downloading but could not be verified. Try again or skip for now.');
    setStage('error');
  };

  const runSetup = async () => {
    setError(null);
    setPercent(0);

    try {
      // Step 1: install Ollama if missing
      let state = await getEngineState();
      if (!state.installed) {
        setStage('installing');
        setStatusMsg('Installing AI engine… (one-time, ~150 MB)');
        const result = await installOllama();
        setStatusMsg(`AI engine installed (${result.method || 'ok'}).`);
      }

      // Step 2: start Ollama
      state = await getEngineState();
      if (!state.running) {
        setStage('starting');
        setStatusMsg('Starting AI engine…');
        await startOllama();
        // wait up to 15s for API
        for (let i = 0; i < 15; i++) {
          await new Promise((r) => setTimeout(r, 1000));
          state = await getEngineState();
          if (state.running) break;
        }
        if (!state.running) {
          throw new Error('AI engine did not start. Please try again.');
        }
      }

      // Step 3: pull model
      state = await getEngineState();
      if (!state.hasModel) {
        setStage('pulling');
        setStatusMsg(`Downloading ${MODEL_LABEL} (${MODEL_SIZE})…`);
        setPercent(0);
        // returns immediately; completion fires via event listener above
        await pullOllamaModel(MODEL);
      } else {
        setStage('verifying');
        void verifyAndFinish();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStage('error');
    }
  };

  const showProgressBar = stage === 'pulling' || stage === 'installing' || stage === 'starting';

  return (
    <div className="first-run-overlay">
      <div className="first-run-card ornamental-card">
        <div className="first-run-header">
          <BookOpen size={48} />
          <h1>Welcome to Scriptures</h1>
          <p className="first-run-subtitle">
            A complete offline scripture study companion. Let&rsquo;s get the AI features ready.
          </p>
        </div>

        <div className="first-run-body">
          <div className="first-run-row">
            <span className={`first-run-check ${engine.installed ? 'ok' : ''}`}>
              {engine.installed ? '✓' : '○'}
            </span>
            <div className="first-run-row-text">
              <strong>AI Engine</strong>
              <small>{engine.installed ? 'Installed' : 'Will be installed (~150 MB)'}</small>
            </div>
          </div>

          <div className="first-run-row">
            <span className={`first-run-check ${engine.running ? 'ok' : ''}`}>
              {engine.running ? '✓' : '○'}
            </span>
            <div className="first-run-row-text">
              <strong>Engine Running</strong>
              <small>{engine.running ? 'Running in background' : 'Will be started automatically'}</small>
            </div>
          </div>

          <div className="first-run-row">
            <span className={`first-run-check ${engine.hasModel ? 'ok' : ''}`}>
              {engine.hasModel ? '✓' : '○'}
            </span>
            <div className="first-run-row-text">
              <strong>{MODEL_LABEL} Model</strong>
              <small>{engine.hasModel ? 'Downloaded' : `Will be downloaded (${MODEL_SIZE})`}</small>
            </div>
          </div>
        </div>

        <div className="first-run-status">
          <p className="first-run-status-msg">
            <BrainIcon size={16} /> {statusMsg}
          </p>
          {showProgressBar && (
            <div className="first-run-progress">
              <div className="first-run-progress-bar" style={{ width: `${percent}%` }} />
              <span className="first-run-progress-pct">{percent}%</span>
            </div>
          )}
          {error && (
            <p className="first-run-error">{error}</p>
          )}
        </div>

        <div className="first-run-actions">
          {stage === 'ready_to_install' && (
            <>
              <button className="first-run-btn first-run-btn-primary" onClick={() => void runSetup()}>
                Set Up AI Features
              </button>
              <button className="first-run-btn first-run-btn-ghost" onClick={onComplete}>
                Skip for Now
              </button>
            </>
          )}
          {(stage === 'installing' || stage === 'starting' || stage === 'pulling' || stage === 'verifying' || stage === 'checking') && (
            <>
              <button className="first-run-btn first-run-btn-primary" disabled>
                Working…
              </button>
              <button className="first-run-btn first-run-btn-ghost" onClick={onComplete}>
                Continue in Background
              </button>
            </>
          )}
          {stage === 'done' && (
            <button className="first-run-btn first-run-btn-primary" onClick={onComplete}>
              Begin Scripture Study
            </button>
          )}
          {stage === 'error' && (
            <>
              <button className="first-run-btn first-run-btn-primary" onClick={() => void runSetup()}>
                Try Again
              </button>
              <button className="first-run-btn first-run-btn-ghost" onClick={onComplete}>
                Skip for Now
              </button>
            </>
          )}
        </div>

        <p className="first-run-footnote">
          Scriptures works fully offline. AI features (Scripture Assistant, My Journey,
          Verse Explain, Translation) require the local Mistral 7B engine. You can
          skip now and set it up later from the Scripture Assistant panel.
        </p>
      </div>
    </div>
  );
}
