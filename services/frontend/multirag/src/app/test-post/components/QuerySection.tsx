import { Button } from './Button';

interface QuerySectionProps {
  input: string;
  isPending: boolean;
  ingested: boolean;
  isStreaming: boolean;
  onInputChange: (value: string) => void;
  onQuery: (e: React.FormEvent) => void;
  onStop: () => void;
}

export const QuerySection = ({
  input,
  isPending,
  ingested,
  isStreaming,
  onInputChange,
  onQuery,
  onStop,
}: QuerySectionProps) => {
  return (
    <div className="space-y-3">
      <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">Question</p>

      <form onSubmit={onQuery} className="space-y-3">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder={ingested ? 'What would you like to know?' : 'Upload a document first...'}
          rows={3}
          className="border border-border rounded-xl px-4 py-3 w-full bg-surface text-foreground placeholder:text-foreground-dim focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent/50 disabled:opacity-40 disabled:cursor-not-allowed resize-none transition-colors"
          disabled={!ingested}
        />
        <div className="flex justify-end">
          {isStreaming ? (
            <Button type="button" variant="danger" onClick={onStop}>
              Stop
            </Button>
          ) : (
            <Button
              type="submit"
              variant="primary"
              isLoading={isPending}
              loadingText="Thinking..."
              disabled={!ingested || !input}
            >
              Ask
            </Button>
          )}
        </div>
      </form>
    </div>
  );
};
