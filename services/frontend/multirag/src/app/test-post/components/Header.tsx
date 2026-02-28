import { SparkleIcon, SunIcon, MoonIcon } from './Icons';

interface HeaderProps {
  backendStatus: 'connecting' | 'online' | 'offline';
  isDark: boolean;
  onToggleTheme: () => void;
}

export const Header = ({ backendStatus, isDark, onToggleTheme }: HeaderProps) => {
  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 h-8 w-8 rounded-lg bg-accent flex items-center justify-center">
        <SparkleIcon className="h-4 w-4 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Lifeforge
          </h1>
          {backendStatus === 'online' && (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border dark:border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400" />
              Live
            </span>
          )}
          {backendStatus === 'offline' && (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-500 dark:bg-red-500/10 dark:text-red-400 dark:border dark:border-red-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-red-500 dark:bg-red-400" />
              Offline
            </span>
          )}
        </div>
        <p className="text-sm text-foreground-dim mt-0.5">AI-powered document intelligence</p>
      </div>
      <a
        href="/analytics"
        className="flex-shrink-0 text-xs text-foreground-dim hover:text-foreground transition-colors"
      >
        Analytics ↗
      </a>
      <button
        onClick={onToggleTheme}
        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        className="flex-shrink-0 p-1.5 rounded-lg text-foreground-dim hover:text-foreground hover:bg-surface-elevated transition-colors"
      >
        {isDark ? (
          <SunIcon className="h-4 w-4" />
        ) : (
          <MoonIcon className="h-4 w-4" />
        )}
      </button>
    </div>
  );
};
