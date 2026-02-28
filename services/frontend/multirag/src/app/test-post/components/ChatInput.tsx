import { useRef, useEffect } from 'react';
import { SendIcon, StopSquareIcon } from './Icons';

interface ChatInputProps {
  input: string;
  ingested: boolean;
  isStreaming: boolean;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  onStop: () => void;
}

export const ChatInput = ({
  input,
  ingested,
  isStreaming,
  onInputChange,
  onSubmit,
  onStop,
}: ChatInputProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming && ingested && input.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="border border-border rounded-2xl flex items-end gap-2 px-4 py-3">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={ingested ? 'Type a follow-up...' : 'Upload a document to start chatting'}
        rows={1}
        disabled={!ingested}
        className="flex-1 resize-none bg-transparent text-foreground placeholder:text-foreground-dim focus:outline-none text-sm leading-6 disabled:opacity-40 disabled:cursor-not-allowed overflow-y-auto"
        style={{ maxHeight: '160px' }}
      />
      {isStreaming ? (
        <button
          type="button"
          onClick={onStop}
          className="flex-shrink-0 p-1.5 rounded-lg bg-accent text-white hover:bg-accent/90 transition-colors"
          aria-label="Stop streaming"
        >
          <StopSquareIcon className="h-4 w-4" />
        </button>
      ) : (
        <button
          type="button"
          onClick={onSubmit}
          disabled={!ingested || !input.trim()}
          className="flex-shrink-0 p-1.5 rounded-lg bg-accent text-white hover:bg-accent/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Send message"
        >
          <SendIcon className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};
