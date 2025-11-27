interface StepHeaderProps {
  stepNumber: number;
  title: string;
  isDark: boolean;
  isActive?: boolean;
}

export const StepHeader = ({ stepNumber, title, isDark, isActive = false }: StepHeaderProps) => {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
          isActive
            ? isDark
              ? 'bg-green-900/50 text-green-400'
              : 'bg-green-100 text-green-600'
            : isDark
            ? stepNumber === 1
              ? 'bg-blue-900/50 text-blue-400'
              : 'bg-slate-700 text-slate-500'
            : stepNumber === 1
            ? 'bg-blue-100 text-blue-600'
            : 'bg-slate-100 text-slate-400'
        }`}
      >
        {stepNumber}
      </div>
      <h2 className={`text-xl font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{title}</h2>
    </div>
  );
};
