import type { HistoryEntry } from '../hooks/useDocumentQuery';

interface Props {
  history: HistoryEntry[];
  onClear: () => void;
}

const renderMarkdown = (text: string) => {
  const parts = text.split(/(\*\*[^*\n]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>
      : part
  );
};

export const ConversationHistory = ({ history, onClear }: Props) => {
  if (history.length === 0) return null;

  const pairs: { user: string; assistant: string }[] = [];
  for (let i = 0; i + 1 < history.length; i += 2) {
    if (history[i].role === 'user' && history[i + 1].role === 'assistant') {
      pairs.push({ user: history[i].content, assistant: history[i + 1].content });
    }
  }
  if (pairs.length === 0) return null;

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest text-foreground-dim">History</p>
        <button onClick={onClear}
          className="text-[10px] font-mono uppercase tracking-widest text-foreground-dim hover:text-foreground transition-colors">
          Clear
        </button>
      </div>

      <div className="space-y-5">
        {pairs.map((pair, idx) => (
          <div key={idx} className="space-y-2">
            {/* User bubble — right aligned */}
            <div className="flex justify-end">
              <div className="max-w-sm px-3.5 py-2 rounded-2xl rounded-tr-sm bg-surface-elevated border border-border text-sm text-foreground">
                {pair.user}
              </div>
            </div>
            {/* Assistant — left, no bubble */}
            <p className="text-sm leading-7 text-foreground-muted whitespace-pre-wrap max-w-prose">
              {renderMarkdown(pair.assistant)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
};
