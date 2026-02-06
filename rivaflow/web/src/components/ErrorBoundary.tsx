import { Component, ErrorInfo, ReactNode } from 'react';
import * as Sentry from '@sentry/react';
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

    // Send to Sentry error tracking
    Sentry.captureException(error, { extra: { componentStack: errorInfo?.componentStack } });
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
        <div className="min-h-screen bg-surface flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-card rounded-lg shadow-lg border border-border p-6">
            <div className="flex items-center mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500 mr-3" />
              <h1 className="text-2xl font-bold text-text">Oops! Something went wrong</h1>
            </div>

            <p className="text-muted mb-4">
              We're sorry, but something unexpected happened. The error has been logged
              and we'll look into it.
            </p>

            {/* Show error details in development */}
            {import.meta.env.DEV && this.state.error && (
              <details className="mb-4 p-3 bg-surface rounded border border-border">
                <summary className="cursor-pointer text-sm font-medium text-accent mb-2">
                  Error Details (Development Only)
                </summary>
                <div className="mt-2">
                  <p className="text-xs font-mono text-red-400 mb-2">
                    {this.state.error.toString()}
                  </p>
                  {this.state.errorInfo && (
                    <pre className="text-xs overflow-auto max-h-48 text-muted">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </details>
            )}

            <div className="flex space-x-3">
              <button
                onClick={this.handleReset}
                className="flex-1 btn btn-primary"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 btn btn-secondary"
              >
                Go to Dashboard
              </button>
            </div>

            <p className="text-xs text-muted mt-4 text-center">
              If the problem persists, please{' '}
              <a href="/feedback" className="text-accent hover:underline">
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
