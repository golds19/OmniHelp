import { StepHeader } from './StepHeader';
import { Button } from './Button';
import { themeClasses } from '../utils/theme';

interface QuerySectionProps {
  input: string;
  isDark: boolean;
  isPending: boolean;
  ingested: boolean;
  isStreaming: boolean;
  onInputChange: (value: string) => void;
  onQuery: (e: React.FormEvent) => void;
  onStop: () => void;
}

export const QuerySection = ({
  input,
  isDark,
  isPending,
  ingested,
  isStreaming,
  onInputChange,
  onQuery,
  onStop,
}: QuerySectionProps) => {
  return (
    <div className="space-y-4">
      <StepHeader stepNumber={2} title="Ask Questions" isDark={isDark} isActive={ingested} />

      <form onSubmit={onQuery} className="space-y-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          <input
            type="text"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder={ingested ? 'What would you like to know?' : 'Upload a document first...'}
            className={themeClasses.input(isDark, !ingested)}
            disabled={!ingested}
          />
          {isStreaming ? (
            <Button type="button" variant="danger" onClick={onStop}>
              Stop
            </Button>
          ) : (
            <Button
              type="submit"
              variant="success"
              isLoading={isPending}
              loadingText="Thinking..."
              disabled={!ingested || !input}
            >
              Ask Question
            </Button>
          )}
        </div>
      </form>
    </div>
  );
};
