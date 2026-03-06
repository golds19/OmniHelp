import { useRef, useState } from 'react';
import { UploadIcon, SpinnerIcon, CheckCircleIcon, ErrorCircleIcon } from './Icons';

interface Props {
  file: File | null;
  isPending: boolean;
  ingested: boolean;
  ingestStatus: string;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFileDrop: (file: File) => void;
  onIngest: (e: React.FormEvent) => void;
}

const fmt = (bytes: number) => bytes < 1048576
  ? `${(bytes / 1024).toFixed(1)} KB`
  : `${(bytes / 1048576).toFixed(1)} MB`;

export const FileUploadSection = ({ file, isPending, ingested, ingestStatus, onFileChange, onFileDrop, onIngest }: Props) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  if (ingested) {
    return (
      <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surface border border-border">
        <CheckCircleIcon className="h-4 w-4 text-emerald-500 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-mono text-foreground truncate">{file?.name ?? 'Document loaded'}</p>
          {file && <p className="text-[11px] text-foreground-dim">{fmt(file.size)}</p>}
        </div>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="text-[11px] text-foreground-dim hover:text-foreground transition-colors shrink-0"
        >
          Change
        </button>
        <input ref={inputRef} type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={onFileChange} className="sr-only" />
      </div>
    );
  }

  const statusType = ingestStatus && !isPending ? 'error' : null;

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="font-mono text-[10px] text-accent tracking-widest">01</span>
        <p className="text-xs font-medium uppercase tracking-widest text-foreground-dim">Upload document</p>
      </div>

      <form onSubmit={onIngest} className="space-y-3">
        <div
          onClick={() => !isPending && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); !isPending && setDragActive(true); }}
          onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            if (isPending) return;
            const dropped = e.dataTransfer.files?.[0];
            if (dropped) onFileDrop(dropped);
          }}
          className={`rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200 group ${
            dragActive
              ? 'border-accent bg-accent-muted/50 scale-[1.01]'
              : file
              ? 'border-accent/40 bg-accent-muted'
              : 'border-border hover:border-accent/40 hover:bg-accent-muted/30'
          }`}
        >
          <input ref={inputRef} type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={onFileChange}
            disabled={isPending} className="sr-only" />

          <div className="px-6 py-8 flex flex-col items-center gap-3 text-center">
            <div className={`h-10 w-10 rounded-xl flex items-center justify-center transition-colors ${
              file
                ? 'bg-accent/15 text-accent'
                : 'bg-surface-elevated text-foreground-dim group-hover:bg-accent/10 group-hover:text-accent'
            }`}>
              <UploadIcon className="h-5 w-5" />
            </div>
            {file ? (
              <div>
                <p className="text-sm font-mono text-foreground">{file.name}</p>
                <p className="text-[11px] text-foreground-dim mt-0.5">{fmt(file.size)}</p>
              </div>
            ) : (
              <div>
                <p className="text-sm text-foreground">
                  {dragActive ? 'Release to upload' : 'Drop a PDF or image here'}
                </p>
                <p className="text-[11px] text-foreground-dim mt-0.5">or click to browse · PDF, PNG, JPG · max 10 MB</p>
              </div>
            )}
          </div>
        </div>

        {file && (
          <button type="submit" disabled={isPending}
            className="w-full h-9 rounded-lg bg-accent text-white text-sm font-medium transition-all hover:bg-accent/90 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            {isPending
              ? <><SpinnerIcon className="h-4 w-4 animate-spin" /> Processing…</>
              : 'Ingest document'}
          </button>
        )}

        {ingestStatus && (
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${
            statusType === 'error'
              ? 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400'
              : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400'
          }`}>
            {statusType === 'error'
              ? <ErrorCircleIcon className="h-3.5 w-3.5 shrink-0" />
              : <CheckCircleIcon className="h-3.5 w-3.5 shrink-0" />}
            {ingestStatus}
          </div>
        )}
      </form>
    </section>
  );
};
