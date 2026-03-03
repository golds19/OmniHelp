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

  // Group into pairs: [user, assistant], [user, assistant], ...
  const pairs: Array<{ user: string; assistant: string }> = [];
  for (let i = 0; i < history.length - 1; i += 2) {
    if (history[i].role === 'user' && history[i + 1]?.role === 'assistant') {
      pairs.push({ user: history[i].content, assistant: history[i + 1].content });
    }
  }

  if (pairs.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider flex-1">
          Conversation history
        </p>
        <button
          onClick={onClear}
          className="text-xs text-foreground-dim hover:text-foreground transition-colors"
        >
          Clear
        </button>
      </div>

      <div className="space-y-4">
        {pairs.map((pair, idx) => (
          <div key={idx} className="space-y-2">
            <div className="inline-block max-w-full rounded-full bg-surface-elevated px-3 py-1 text-sm text-foreground">
              {pair.user}
            </div>
            <p className="text-sm text-foreground-dim leading-6 whitespace-pre-wrap">
              {renderMarkdown(pair.assistant)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
