interface Props {
  input: string;
  isPending: boolean;
  ingested: boolean;
  isStreaming: boolean;
  onInputChange: (value: string) => void;
  onQuery: (e: React.FormEvent) => void;
  onStop: () => void;
}

export const QuerySection = ({ input, isPending, ingested, isStreaming, onInputChange, onQuery, onStop }: Props) => {
  const canQuery = ingested && !isPending;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && canQuery && !isStreaming && input.trim()) {
      e.preventDefault();
      onQuery(e as unknown as React.FormEvent);
    }
  };

  return (
    <form onSubmit={onQuery}>
      <div className={`relative rounded-xl border bg-surface transition-all duration-200 ${
        canQuery
          ? 'border-border hover:border-border-hover focus-within:border-accent/50 focus-within:ring-2 focus-within:ring-accent/10'
          : 'border-border opacity-50'
      }`}>
        <textarea
          value={input}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!canQuery}
          placeholder={ingested ? 'Ask anything about your document… (⏎ to send)' : 'Upload a document first'}
          rows={1}
          style={{ maxHeight: '120px' }}
          className="w-full px-4 pt-3.5 pb-11 text-sm text-foreground placeholder:text-foreground-dim bg-transparent resize-none outline-none leading-6 overflow-y-auto"
        />
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          {input.trim() && (
            <span className="text-[10px] font-mono text-foreground-dim">{input.length}/2000</span>
          )}
          {isStreaming ? (
            <button type="button" onClick={onStop}
              className="h-7 px-3 rounded-lg bg-surface-elevated border border-border text-xs text-foreground-dim hover:text-foreground transition-colors">
              Stop
            </button>
          ) : (
            <button type="submit" disabled={!canQuery || !input.trim()}
              className="h-7 px-3 rounded-lg bg-accent text-white text-xs font-medium transition-all hover:bg-accent/90 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed">
              Ask
            </button>
          )}
        </div>
      </div>
    </form>
  );
};
