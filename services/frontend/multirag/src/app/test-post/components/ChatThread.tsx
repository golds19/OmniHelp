import { useRef, useEffect } from 'react';
import type { ConversationTurn } from '../hooks/useDocumentQuery';
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

const confidenceColor = (confidence: number) => {
  if (confidence >= 0.7) return 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-500/10';
  if (confidence >= 0.4) return 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-500/10';
  return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-500/10';
};

const MetricsRow = ({ queryLog }: { queryLog: QueryLog }) => (
  <div className="mt-3 space-y-2">
    <div className="flex items-center gap-2 flex-wrap">
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${confidenceColor(queryLog.confidence)}`}>
        <span className="h-1.5 w-1.5 rounded-full bg-current" />
        {Math.round(queryLog.confidence * 100)}% confidence
      </span>
      {!queryLog.is_hallucination && (
        <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 text-xs">
          <ShieldCheckIcon className="h-3.5 w-3.5" />
          Grounded
        </span>
      )}
      {queryLog.source_pages.length > 0 && (
        <span className="flex items-center gap-1 flex-wrap">
          <span className="text-foreground-dim text-xs">Pages:</span>
          {[...new Set(queryLog.source_pages)].sort((a, b) => a - b).map(p => (
            <span key={p} className="px-1.5 py-0.5 text-xs font-mono bg-accent-muted text-accent rounded">
              {p}
            </span>
          ))}
        </span>
      )}
      <span className="ml-auto text-xs font-mono text-foreground-dim">
        {(queryLog.latency_ms / 1000).toFixed(1)}s
      </span>
    </div>
    {!!queryLog.is_hallucination && (
      <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-700 dark:bg-amber-500/10 dark:border-amber-500/20 dark:text-amber-300 px-3 py-2 flex items-center gap-2 text-xs">
        <ShieldIcon className="h-3.5 w-3.5 flex-shrink-0" />
        <span>Low groundedness — verify against the document</span>
      </div>
    )}
  </div>
);

interface ChatThreadProps {
  conversationTurns: ConversationTurn[];
  response: string;
  queryLog: QueryLog | null;
  isStreaming: boolean;
  pendingQuestion: string;
}

export const ChatThread = ({
  conversationTurns,
  response,
  queryLog,
  isStreaming,
  pendingQuestion,
}: ChatThreadProps) => {
  const anchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    anchorRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [response, conversationTurns.length]);

  const isEmpty = conversationTurns.length === 0 && !isStreaming && !response;

  return (
    <div className="overflow-y-auto max-h-[56vh] px-6 py-4">
      {isEmpty ? (
        <div className="flex items-center justify-center h-32 text-foreground-dim text-sm">
          Ask a question to get started
        </div>
      ) : (
        <div className="space-y-6">
          {conversationTurns.map((turn, i) => {
            const isLastTurn = i === conversationTurns.length - 1;
            const showMetrics = isLastTurn && !isStreaming && queryLog !== null;
            return (
              <div key={i} className="space-y-3">
                <div className="flex justify-end">
                  <div className="ml-auto max-w-[75%] bg-accent-muted text-foreground rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-6">
                    {turn.question}
                  </div>
                </div>
                <div className="text-sm text-foreground leading-7 whitespace-pre-wrap">
                  {renderMarkdown(turn.answer)}
                  {showMetrics && <MetricsRow queryLog={queryLog} />}
                </div>
              </div>
            );
          })}

          {isStreaming && (
            <div className="space-y-3">
              <div className="flex justify-end">
                <div className="ml-auto max-w-[75%] bg-accent-muted text-foreground rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-6">
                  {pendingQuestion}
                </div>
              </div>
              <div className="text-sm text-foreground leading-7 whitespace-pre-wrap">
                {renderMarkdown(response)}
                <span className="inline-block w-0.5 h-[1em] ml-0.5 bg-accent animate-pulse align-middle" />
              </div>
            </div>
          )}
        </div>
      )}
      <div ref={anchorRef} />
    </div>
  );
};
