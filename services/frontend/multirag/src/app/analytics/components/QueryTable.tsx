import type { QueryLog } from '@/types/api';

const confidenceBadge = (confidence: number) => {
  if (confidence >= 0.7) return 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-500/10';
  if (confidence >= 0.4) return 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-500/10';
  return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-500/10';
};

const formatTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
};

interface QueryTableProps {
  logs: QueryLog[];
}

export const QueryTable = ({ logs }: QueryTableProps) => {
  if (logs.length === 0) {
    return (
      <p className="text-sm text-foreground-dim italic text-center py-6">
        No queries logged yet
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left">
            <th className="pb-2 pr-4 text-xs font-medium text-foreground-dim uppercase tracking-wider">Time</th>
            <th className="pb-2 pr-4 text-xs font-medium text-foreground-dim uppercase tracking-wider">Query</th>
            <th className="pb-2 pr-4 text-xs font-medium text-foreground-dim uppercase tracking-wider">Confidence</th>
            <th className="pb-2 pr-4 text-xs font-medium text-foreground-dim uppercase tracking-wider">Grounded</th>
            <th className="pb-2 text-xs font-medium text-foreground-dim uppercase tracking-wider">Latency</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-b border-border last:border-0 hover:bg-surface-elevated transition-colors">
              <td className="py-2.5 pr-4 font-mono text-xs text-foreground-dim whitespace-nowrap">
                {formatTime(log.timestamp)}
              </td>
              <td className="py-2.5 pr-4 text-foreground max-w-[280px]">
                <span className="block truncate" title={log.query}>{log.query || '—'}</span>
              </td>
              <td className="py-2.5 pr-4">
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${confidenceBadge(log.confidence)}`}>
                  <span className="h-1.5 w-1.5 rounded-full bg-current" />
                  {Math.round(log.confidence * 100)}%
                </span>
              </td>
              <td className="py-2.5 pr-4 text-xs">
                {log.is_hallucination ? (
                  <span className="text-amber-500 dark:text-amber-400">Low</span>
                ) : (
                  <span className="text-emerald-600 dark:text-emerald-400">Yes</span>
                )}
              </td>
              <td className="py-2.5 font-mono text-xs text-foreground-dim">
                {(log.latency_ms / 1000).toFixed(1)}s
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
