import { StrictMode, Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/index.css';
import App from './App';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Scriptures app error:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: 40,
          fontFamily: "'Cormorant Garamond', Georgia, serif",
          maxWidth: 600,
          margin: '80px auto',
          textAlign: 'center',
        }}>
          <h2 style={{
            color: '#3A1D6E',
            fontSize: 32,
            fontWeight: 600,
            marginBottom: 16,
          }}>
            Something went wrong
          </h2>
          <p style={{
            color: '#5A5550',
            lineHeight: 1.8,
            fontFamily: "'EB Garamond', Georgia, serif",
            fontSize: 17,
          }}>
            The application encountered an unexpected error. Please restart the app.
          </p>
          <pre style={{
            fontSize: 12,
            color: '#8A8580',
            marginTop: 16,
            whiteSpace: 'pre-wrap',
            fontFamily: "'Inter', system-ui, sans-serif",
          }}>
            {this.state.error?.message}
          </pre>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              marginTop: 24,
              padding: '10px 28px',
              background: '#C5A55A',
              color: 'white',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              fontFamily: "'Inter', system-ui, sans-serif",
              fontSize: 14,
              fontWeight: 600,
              letterSpacing: 0.3,
            }}
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const el = document.getElementById('root');
if (!el) throw new Error('Root element #root not found');

createRoot(el).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
