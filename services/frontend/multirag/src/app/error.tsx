'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md">

        {/* Brand */}
        <div className="flex items-center gap-2.5 mb-8">
          <div className="h-8 w-8 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
            <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813
                   a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813
                   a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
          </div>
          <span className="text-lg font-semibold text-foreground tracking-tight">Lifeforge</span>
        </div>

        {/* Error card */}
        <div className="rounded-xl border border-border bg-surface p-6 space-y-4">

          {/* Icon + heading */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 h-9 w-9 rounded-lg bg-red-50 dark:bg-red-500/10 flex items-center justify-center">
              <svg className="h-5 w-5 text-red-500 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="space-y-0.5 min-w-0">
              <h1 className="text-base font-semibold text-foreground">Something went wrong</h1>
              <p className="text-sm text-foreground-muted">An unexpected error occurred.</p>
            </div>
          </div>

          {/* Error detail */}
          {error.message && (
            <div className="rounded-lg bg-surface-elevated border border-border px-4 py-3">
              <p className="text-sm font-mono text-foreground-muted break-words leading-relaxed">
                {error.message}
              </p>
              {error.digest && (
                <p className="text-xs text-foreground-dim mt-1.5">Digest: {error.digest}</p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-1">
            <button
              onClick={reset}
              className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm bg-accent text-white hover:opacity-90 transition-opacity border border-accent/30"
            >
              Try again
            </button>
            <Link
              href="/test-post"
              className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm text-center bg-surface-elevated text-foreground-muted border border-border hover:border-border-hover hover:text-foreground transition-colors"
            >
              Go home
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
