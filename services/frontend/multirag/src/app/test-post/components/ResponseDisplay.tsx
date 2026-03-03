import type { QueryLog } from '@/types/api';
import { ShieldCheckIcon, ShieldIcon } from './Icons';

const renderMarkdown = (text: string) => {
  const parts = text.split(/(\*\*[^*\n]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>
      : part
  );
};

interface Props {
  response: string;
  queryLog: QueryLog | null;
  isStreaming: boolean;
  ingested: boolean;
}

const conf = (v: number) => ({
  color: v >= 0.7 ? 'text-emerald-600 dark:text-emerald-400'
       : v >= 0.4 ? 'text-amber-600 dark:text-amber-400'
       : 'text-red-500 dark:text-red-400',
  dot: v >= 0.7 ? 'bg-emerald-500' : v >= 0.4 ? 'bg-amber-500' : 'bg-red-500',
});

export const ResponseDisplay = ({ response, queryLog, isStreaming, ingested }: Props) => {
  if (!response && !ingested) return null;

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden animate-[var(--animate-fade-in)]">
      <div className="px-5 py-4 min-h-[3rem]">
        {response ? (
          <p className="text-sm leading-7 text-foreground whitespace-pre-wrap">
            {renderMarkdown(response)}
            {isStreaming && (
              <span className="inline-block w-0.5 h-[0.9em] ml-0.5 bg-accent animate-pulse align-middle" />
            )}
          </p>
        ) : (
          <p className="text-sm text-foreground-dim italic">Thinking…</p>
        )}
        {isStreaming && (
          <div data-testid="streaming-indicator" className="flex items-center gap-1 mt-2">
            {[0, 150, 300].map(d => (
              <span key={d} className="h-1 w-1 rounded-full bg-accent animate-pulse"
                style={{ animationDelay: `${d}ms` }} />
            ))}
          </div>
        )}
      </div>

      {/* Metadata footer */}
      {queryLog && !isStreaming && (
        <div className="border-t border-border px-5 py-2.5 bg-surface-elevated flex items-center gap-2.5 flex-wrap">
          <span className={`flex items-center gap-1.5 font-mono text-xs ${conf(queryLog.confidence).color}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${conf(queryLog.confidence).dot}`} />
            {Math.round(queryLog.confidence * 100)}%
          </span>

          {queryLog.source_pages.length > 0 && (
            <>
              <span className="text-foreground-dim font-mono text-xs select-none">·</span>
              <span data-testid="source-pages" className="flex items-center gap-1 flex-wrap">
                {[...new Set(queryLog.source_pages)].sort((a, b) => a - b).map(p => (
                  <span key={p} className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-accent-muted text-accent">
                    p.{p}
                  </span>
                ))}
              </span>
            </>
          )}

          {!queryLog.is_hallucination && (
            <>
              <span className="text-foreground-dim font-mono text-xs select-none">·</span>
              <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-600 dark:text-emerald-400">
                <ShieldCheckIcon className="h-3 w-3" />
                grounded
              </span>
            </>
          )}

          <span className="ml-auto font-mono text-[10px] text-foreground-dim">
            {(queryLog.latency_ms / 1000).toFixed(1)}s
          </span>
        </div>
      )}

      {/* Hallucination warning */}
      {queryLog && !isStreaming && queryLog.is_hallucination && (
        <div className="border-t border-amber-200 dark:border-amber-500/20 px-5 py-2.5 bg-amber-50 dark:bg-amber-500/10 flex items-center gap-2">
          <ShieldIcon className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
          <p className="text-[11px] text-amber-700 dark:text-amber-300">
            Low groundedness — verify this answer against the document
          </p>
        </div>
      )}
    </div>
  );
};
