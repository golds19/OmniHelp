import { SunIcon, MoonIcon } from './Icons';

interface ThemeToggleProps {
  isDark: boolean;
  onToggle: () => void;
}

export const ThemeToggle = ({ isDark, onToggle }: ThemeToggleProps) => {
  return (
    <div className="flex justify-end mb-6">
      <button
        onClick={onToggle}
        className={`p-3 rounded-full shadow-lg transition-all hover:scale-110 ${
          isDark
            ? 'bg-slate-700 text-yellow-400 hover:bg-slate-600'
            : 'bg-white text-slate-700 hover:bg-slate-50'
        }`}
        aria-label="Toggle theme"
      >
        {isDark ? <SunIcon className="w-6 h-6" /> : <MoonIcon className="w-6 h-6" />}
      </button>
    </div>
  );
};
