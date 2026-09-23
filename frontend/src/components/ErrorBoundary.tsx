import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorId: string | null;
}

class ErrorBoundary extends Component<Props, State> {
  public override state: State = {
    hasError: false,
    error: null,
    errorId: null,
  };

  public override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to monitoring service
    const errorId = this.logError(error, errorInfo);
    
    this.setState({
      hasError: true,
      error,
      errorId,
    });
  }

  private logError(error: Error, errorInfo: ErrorInfo): string {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    
    // Log to console in development
    console.error(`[ErrorBoundary] ${errorId}:`, error, errorInfo);
    
    // Send to monitoring service in production
    if (import.meta.env.PROD) {
      this.sendToMonitoring(errorId, error, errorInfo);
    }
    
    return errorId;
  }

  private sendToMonitoring(errorId: string, error: Error, errorInfo: ErrorInfo) {
    // Sentry integration
    const sentry = (window as any).Sentry;
    if (sentry) {
      sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack,
          },
        },
        extra: {
          errorId,
        },
      });
      return;
    }

    // Fallback: send to backend
    fetch('/api/v1/errors', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        error_id: errorId,
        message: error.message,
        stack: error.stack,
        component_stack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        url: window.location.href,
      }),
    }).catch(() => {
      // Ignore monitoring failures
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorId: null,
    });
  };

  public override render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <div className="error-content">
            <h1>Oops! Something went wrong</h1>
            <p>We're sorry, but something unexpected happened.</p>
            {this.state.errorId && (
              <p className="error-id">
                Error ID: {this.state.errorId}
              </p>
            )}
            {import.meta.env.DEV && this.state.error && (
              <details className="error-details">
                <summary>Error details</summary>
                <pre>{this.state.error.message}</pre>
                <pre>{this.state.error.stack}</pre>
              </details>
            )}
            <button onClick={this.handleReset} className="error-button">
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;