export const cn = (...classes: (string | boolean | undefined)[]) => {
  return classes.filter(Boolean).join(' ');
};

export const themeClasses = {
  background: (isDark: boolean) =>
    isDark
      ? 'bg-gradient-to-br from-slate-900 to-slate-800'
      : 'bg-gradient-to-br from-slate-50 to-blue-50',
  card: (isDark: boolean) =>
    isDark ? 'bg-slate-800' : 'bg-white',
  text: {
    primary: (isDark: boolean) =>
      isDark ? 'text-white' : 'text-slate-800',
    secondary: (isDark: boolean) =>
      isDark ? 'text-slate-300' : 'text-slate-600',
    tertiary: (isDark: boolean) =>
      isDark ? 'text-slate-400' : 'text-slate-500',
  },
  input: (isDark: boolean, disabled = false) =>
    cn(
      'flex-1 px-6 py-4 border-2 rounded-lg focus:ring-4 outline-none transition-all text-lg',
      isDark
        ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-green-500 focus:ring-green-900/50'
        : 'bg-white border-slate-200 text-slate-900 placeholder-slate-400 focus:border-green-400 focus:ring-green-100',
      disabled && (isDark ? 'disabled:bg-slate-800 disabled:text-slate-500' : 'disabled:bg-slate-50 disabled:text-slate-400')
    ),
  border: (isDark: boolean) =>
    isDark ? 'border-slate-600' : 'border-slate-200',
  divider: (isDark: boolean) =>
    isDark ? 'bg-slate-800 text-slate-400' : 'bg-white text-slate-500',
};
