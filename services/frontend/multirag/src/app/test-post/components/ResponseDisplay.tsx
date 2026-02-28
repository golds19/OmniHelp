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

interface ResponseDisplayProps {
  response: string;
  queryLog: QueryLog | null;
  isStreaming: boolean;
  ingested: boolean;
}

const confidenceColor = (confidence: number) => {
  if (confidence >= 0.7) return 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-500/10';
  if (confidence >= 0.4) return 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-500/10';
  return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-500/10';
};

export const ResponseDisplay = ({ response, queryLog, isStreaming, ingested }: ResponseDisplayProps) => {
  if (!response && !ingested) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className={`h-5 w-5 rounded-full text-xs font-bold flex items-center justify-center flex-shrink-0 ${
          queryLog && !isStreaming
            ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400'
            : 'bg-accent-muted text-accent'
        }`}>
          3
        </span>
        <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">Answer</p>
        {isStreaming && (
          <span data-testid="streaming-indicator" className="ml-1 inline-flex items-center gap-1 text-accent text-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse [animation-delay:0.2s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse [animation-delay:0.4s]" />
          </span>
        )}
      </div>

      <div className={response || isStreaming ? 'rounded-xl border border-border bg-surface px-5 py-4' : ''}>
        {response ? (
          <p className="text-foreground leading-7 whitespace-pre-wrap">
            {renderMarkdown(response)}
            {isStreaming && (
              <span className="inline-block w-0.5 h-[1em] ml-0.5 bg-accent animate-pulse align-middle" />
            )}
          </p>
        ) : (
          <p className="text-foreground-dim italic">Your answer will appear here...</p>
        )}
      </div>

      {queryLog && !isStreaming && (
        <div className="rounded-xl border border-border bg-surface p-4 space-y-2">
          <div className="flex items-center gap-2 flex-wrap text-sm">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${confidenceColor(queryLog.confidence)}`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {Math.round(queryLog.confidence * 100)}% confidence
            </span>

            {!queryLog.is_hallucination ? (
              <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 text-xs">
                <ShieldCheckIcon className="h-3.5 w-3.5" />
                Grounded
              </span>
            ) : null}

            {queryLog.source_pages.length > 0 && (
              <span data-testid="source-pages" className="flex items-center gap-1 flex-wrap">
                <span className="text-foreground-dim text-xs">Pages:</span>
                {[...new Set(queryLog.source_pages)].sort((a, b) => a - b).map(p => (
                  <span key={p} className="px-1.5 py-0.5 text-xs font-mono bg-accent-muted text-accent rounded">
                    {p}
                  </span>
                ))}
              </span>
            )}

            <span className="ml-auto text-xs font-mono text-foreground-dim">{(queryLog.latency_ms / 1000).toFixed(1)}s</span>
          </div>

          {!!queryLog.is_hallucination && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-700 dark:bg-amber-500/10 dark:border-amber-500/20 dark:text-amber-300 px-3 py-2 flex items-center gap-2 text-xs">
              <ShieldIcon className="h-3.5 w-3.5 flex-shrink-0" />
              <span>Low groundedness — verify against the document</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
