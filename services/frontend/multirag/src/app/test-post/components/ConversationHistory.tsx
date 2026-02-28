import type { ConversationTurn } from '../hooks/useDocumentQuery';

const renderMarkdown = (text: string) => {
  const parts = text.split(/(\*\*[^*\n]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>
      : part
  );
};

interface ConversationHistoryProps {
  turns: ConversationTurn[];
  onClear: () => void;
}

export const ConversationHistory = ({ turns, onClear }: ConversationHistoryProps) => {
  if (turns.length === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">
          Conversation
        </p>
        <button
          onClick={onClear}
          className="text-xs text-foreground-dim hover:text-foreground transition-colors"
        >
          Clear
        </button>
      </div>

      {turns.map((turn, i) => (
        <div key={i} className="space-y-2">
          {/* User question */}
          <div className="flex items-start gap-2">
            <span className="mt-0.5 h-5 w-5 rounded-full bg-accent-muted text-accent text-xs font-bold flex items-center justify-center flex-shrink-0">
              Q
            </span>
            <p className="text-sm text-foreground-muted leading-6">{turn.question}</p>
          </div>

          {/* Assistant answer */}
          <div className="flex items-start gap-2">
            <span className="mt-0.5 h-5 w-5 rounded-full bg-surface-elevated text-foreground-dim text-xs font-bold flex items-center justify-center flex-shrink-0">
              A
            </span>
            <p className="text-sm text-foreground leading-6 whitespace-pre-wrap">
              {renderMarkdown(turn.answer)}
            </p>
          </div>
        </div>
      ))}

      <div className="border-t border-border" />
    </div>
  );
};
