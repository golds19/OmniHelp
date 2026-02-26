import type { QueryLog } from '@/types/api';

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
            ? 'bg-green-100 text-green-600 dark:bg-emerald-500/15 dark:text-emerald-400'
            : 'bg-indigo-100 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-400'
        }`}>
          3
        </span>
        <p className="text-xs font-medium text-neutral-400 dark:text-zinc-500 uppercase tracking-wider">Answer</p>
        {isStreaming && (
          <span data-testid="streaming-indicator" className="ml-1 inline-flex items-center gap-1 text-indigo-500 dark:text-indigo-400 text-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse [animation-delay:0.2s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse [animation-delay:0.4s]" />
          </span>
        )}
      </div>

      <div className={response || isStreaming ? 'bg-white rounded-lg px-4 py-3 border border-slate-100 dark:bg-zinc-800/50 dark:border-zinc-700/50' : ''}>
        {response ? (
          <p className="text-slate-800 dark:text-zinc-100 leading-7 whitespace-pre-wrap">
            {renderMarkdown(response)}
            {isStreaming && (
              <span className="inline-block w-0.5 h-[1em] ml-0.5 bg-indigo-500 dark:bg-indigo-400 animate-pulse align-middle" />
            )}
          </p>
        ) : (
          <p className="text-neutral-400 dark:text-zinc-600 italic">Your answer will appear here...</p>
        )}
      </div>

      {queryLog && !isStreaming && (
        <div className="pt-2 border-t border-neutral-100 dark:border-zinc-800 space-y-2">
          <div className="flex items-center gap-2 flex-wrap text-sm">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${confidenceColor(queryLog.confidence)}`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {Math.round(queryLog.confidence * 100)}% confidence
            </span>
            {queryLog.source_pages.length > 0 && (
              <span data-testid="source-pages" className="flex items-center gap-1 flex-wrap">
                <span className="text-neutral-400 text-xs">Pages:</span>
                {[...new Set(queryLog.source_pages)].sort((a, b) => a - b).map(p => (
                  <span key={p} className="px-1.5 py-0.5 text-xs font-mono bg-neutral-100 text-neutral-600 dark:bg-zinc-700 dark:text-zinc-300 rounded">
                    {p}
                  </span>
                ))}
              </span>
            )}
            <span className="ml-auto text-xs text-neutral-400 dark:text-zinc-500">{(queryLog.latency_ms / 1000).toFixed(1)}s</span>
          </div>
          {!!queryLog.is_hallucination && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-700 dark:bg-amber-500/10 dark:border-amber-500/20 dark:text-amber-300 px-3 py-2 flex items-center gap-2 text-xs">
              <span>⚠</span>
              <span>Low groundedness — verify against the document</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
