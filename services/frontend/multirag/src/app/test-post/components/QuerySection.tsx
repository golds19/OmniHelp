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
      <div className="flex items-center gap-2">
        <span className="h-5 w-5 rounded-full bg-indigo-100 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-400 text-xs font-bold flex items-center justify-center flex-shrink-0">
          2
        </span>
        <p className="text-xs font-medium text-neutral-400 dark:text-zinc-500 uppercase tracking-wider">Question</p>
      </div>

      <form onSubmit={onQuery} className="space-y-3">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder={ingested ? 'What would you like to know?' : 'Upload a document first...'}
          rows={4}
          className="border border-neutral-200 dark:border-zinc-700 rounded-lg px-4 py-3 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:focus:ring-indigo-500/30 dark:focus:border-indigo-500/50 text-base text-neutral-900 dark:text-zinc-100 placeholder:text-neutral-400 dark:placeholder:text-zinc-600 disabled:opacity-40 disabled:cursor-not-allowed resize-none bg-white dark:bg-zinc-800 transition-colors"
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
