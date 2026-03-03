import { SparkleIcon, SunIcon, MoonIcon, PanelLeftIcon } from './Icons';

interface HeaderProps {
  backendStatus: 'connecting' | 'online' | 'offline';
  isDark: boolean;
  onToggleTheme: () => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export const Header = ({ backendStatus, isDark, onToggleTheme, sidebarOpen, onToggleSidebar }: HeaderProps) => (
  <header className="h-12 flex items-center px-5 border-b border-border bg-surface/80 backdrop-blur-sm shrink-0 z-10">
    <button
      onClick={onToggleSidebar}
      aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
      className={`h-7 w-7 flex items-center justify-center rounded transition-colors mr-1
        ${sidebarOpen ? 'text-accent hover:bg-accent-muted' : 'text-foreground-dim hover:text-foreground hover:bg-surface-elevated'}`}
    >
      <PanelLeftIcon className="h-3.5 w-3.5" />
    </button>

    <div className="flex items-center gap-2.5">
      <div className="h-5 w-5 rounded flex items-center justify-center bg-accent">
        <SparkleIcon className="h-3 w-3 text-white" />
      </div>
      <span className="text-sm font-semibold tracking-tight text-foreground">Lifeforge</span>
    </div>

    <div className="ml-3">
      {backendStatus === 'online' && (
        <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest text-emerald-500 dark:text-emerald-400">
          <span className="h-1 w-1 rounded-full bg-emerald-500 dark:bg-emerald-400" />
          live
        </span>
      )}
      {backendStatus === 'offline' && (
        <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest text-red-500 dark:text-red-400">
          <span className="h-1 w-1 rounded-full bg-red-500" />
          offline
        </span>
      )}
    </div>

    <button
      onClick={onToggleTheme}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="ml-auto h-7 w-7 flex items-center justify-center rounded text-foreground-dim hover:text-foreground hover:bg-surface-elevated transition-colors"
    >
      {isDark ? <SunIcon className="h-3.5 w-3.5" /> : <MoonIcon className="h-3.5 w-3.5" />}
    </button>
  </header>
);
