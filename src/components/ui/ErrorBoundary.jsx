import React from 'react';

/**
 * Standard React Error Boundary component
 * Catches rendering exceptions and provides graceful fallback UI with recovery.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('InsightFlow ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[300px] flex items-center justify-center p-6">
          <div className="glass-card max-w-md w-full p-6 rounded-2xl border border-rose-500/30 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center mx-auto">
              <span className="material-symbols-outlined text-2xl">error_outline</span>
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Something went wrong</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {this.state.error?.message || 'An unexpected rendering error occurred.'}
              </p>
            </div>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              Reload View
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
