import Link from 'next/link';

export default function NotFound() {
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

        {/* 404 card */}
        <div className="rounded-xl border border-border bg-surface p-6 space-y-4">
          <div className="space-y-1">
            <p className="text-7xl font-bold text-accent/20 leading-none select-none tabular-nums">404</p>
            <h1 className="text-base font-semibold text-foreground mt-3">Page not found</h1>
            <p className="text-sm text-foreground-muted">
              The page you&apos;re looking for doesn&apos;t exist or has been moved.
            </p>
          </div>

          <Link
            href="/test-post"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm bg-accent text-white hover:opacity-90 transition-opacity border border-accent/30"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
            Back to app
          </Link>
        </div>

      </div>
    </div>
  );
}
