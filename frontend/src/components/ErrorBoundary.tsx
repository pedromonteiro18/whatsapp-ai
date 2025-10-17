import { Component, ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: string | null;
}

/**
 * ErrorBoundary component catches React errors and displays fallback UI
 *
 * Features:
 * - Catches errors in child component tree
 * - Displays user-friendly error message
 * - Provides "Try Again" button to reset error state
 * - Logs errors to console for debugging
 * - Prevents entire app from crashing
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 * ```
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

  /**
   * Update state when an error is caught
   */
  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Log error details for debugging
   */
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error to console
    console.error('ErrorBoundary caught an error:', error);
    console.error('Error component stack:', errorInfo.componentStack);

    // Update state with error info
    this.setState({
      errorInfo: errorInfo.componentStack || null,
    });

    // In production, you might want to send this to an error reporting service
    // Example: Sentry.captureException(error, { contexts: { react: errorInfo } });
  }

  /**
   * Reset error state and try to re-render
   */
  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    // If there's an error, show fallback UI
    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="max-w-md w-full space-y-6 text-center">
            {/* Error Icon */}
            <div className="flex justify-center">
              <div className="rounded-full bg-destructive/10 p-6">
                <AlertCircle className="h-12 w-12 text-destructive" />
              </div>
            </div>

            {/* Error Message */}
            <div className="space-y-2">
              <h1 className="text-2xl font-bold">Something went wrong</h1>
              <p className="text-muted-foreground">
                We encountered an unexpected error. Please try again or contact support if the
                problem persists.
              </p>
            </div>

            {/* Error Details (Development only) */}
            {process.env.NODE_ENV === 'development' && error && (
              <div className="mt-4 p-4 bg-muted rounded-lg text-left">
                <p className="text-sm font-mono text-destructive break-all">
                  {error.toString()}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={this.handleReset} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Try Again
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.href = '/'}
              >
                Go to Homepage
              </Button>
            </div>

            {/* Additional Help */}
            <p className="text-xs text-muted-foreground">
              If this problem continues, please contact our support team.
            </p>
          </div>
        </div>
      );
    }

    // No error, render children normally
    return children;
  }
}
