import { useRef } from 'react';
import { PaperclipIcon, FileTextIcon, SpinnerIcon } from './Icons';

interface DocumentBarProps {
  file: File | null;
  isPending: boolean;
  ingested: boolean;
  ingestStatus: string;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export const DocumentBar = ({ file, isPending, ingested, ingestStatus, onFileChange }: DocumentBarProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const openPicker = () => fileInputRef.current?.click();

  return (
    <div className="flex items-center gap-3 py-2.5 min-h-[40px]">
      {isPending ? (
        <>
          <SpinnerIcon className="h-4 w-4 text-accent animate-spin flex-shrink-0" />
          <span className="text-sm text-foreground-dim">Processing…</span>
        </>
      ) : ingested && file ? (
        <>
          <FileTextIcon className="h-4 w-4 text-accent flex-shrink-0" />
          <span className="text-sm text-foreground truncate flex-1">{file.name}</span>
          <button
            onClick={openPicker}
            className="text-xs text-foreground-dim hover:text-foreground transition-colors flex-shrink-0"
          >
            Change ↑
          </button>
        </>
      ) : (
        <div className="flex items-center gap-2 flex-1">
          <button
            onClick={openPicker}
            className="flex items-center gap-2 text-sm text-foreground-dim hover:text-foreground transition-colors"
          >
            <PaperclipIcon className="h-4 w-4 flex-shrink-0" />
            Drop a PDF or click to upload
          </button>
          {ingestStatus && !ingested && (
            <span className="text-xs text-red-500 dark:text-red-400 ml-2">{ingestStatus}</span>
          )}
        </div>
      )}
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        onChange={onFileChange}
        className="hidden"
      />
    </div>
  );
};
