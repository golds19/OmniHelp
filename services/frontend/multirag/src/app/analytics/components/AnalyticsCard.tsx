interface AnalyticsCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: 'default' | 'green' | 'amber' | 'red';
}

const accentClasses = {
  default: 'text-accent',
  green: 'text-emerald-500 dark:text-emerald-400',
  amber: 'text-amber-500 dark:text-amber-400',
  red: 'text-red-500 dark:text-red-400',
};

export const AnalyticsCard = ({ label, value, sub, accent = 'default' }: AnalyticsCardProps) => (
  <div className="rounded-xl border border-border bg-surface px-5 py-4 flex flex-col gap-1">
    <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">{label}</p>
    <p className={`text-3xl font-semibold tabular-nums ${accentClasses[accent]}`}>{value}</p>
    {sub && <p className="text-xs text-foreground-dim">{sub}</p>}
  </div>
);
