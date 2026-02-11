import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component to catch JavaScript errors in child components
 * and display a fallback UI instead of crashing the entire app.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <YourComponent />
 *   </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error to error reporting service
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Store error info in state for display in development
    this.setState({
      error,
      errorInfo,
    });

  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Render custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--bg)' }}>
          <div className="max-w-md w-full rounded-[14px] shadow-lg p-6" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="flex items-center mb-4">
              <AlertTriangle className="w-8 h-8 mr-3" style={{ color: 'var(--error)' }} />
              <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Oops! Something went wrong</h1>
            </div>

            <p className="mb-4" style={{ color: 'var(--muted)' }}>
              We're sorry, but something unexpected happened. The error has been logged
              and we'll look into it.
            </p>

            {/* Show error details in development */}
            {import.meta.env.DEV && this.state.error && (
              <details className="mb-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                <summary className="cursor-pointer text-sm font-medium mb-2" style={{ color: 'var(--accent)' }}>
                  Error Details (Development Only)
                </summary>
                <div className="mt-2">
                  <p className="text-xs font-mono mb-2" style={{ color: 'var(--error)' }}>
                    {this.state.error.toString()}
                  </p>
                  {this.state.errorInfo && (
                    <pre className="text-xs overflow-auto max-h-48" style={{ color: 'var(--muted)' }}>
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </details>
            )}

            <div className="flex space-x-3">
              <button
                onClick={this.handleReset}
                className="flex-1 py-3 px-4 rounded-[14px] font-semibold text-sm"
                style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 py-3 px-4 rounded-[14px] font-semibold text-sm"
                style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
              >
                Go to Dashboard
              </button>
            </div>

            <p className="text-xs mt-4 text-center" style={{ color: 'var(--muted)' }}>
              If the problem persists, please{' '}
              <a href="/contact" style={{ color: 'var(--accent)' }} className="hover:underline">
                report the issue
              </a>
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
