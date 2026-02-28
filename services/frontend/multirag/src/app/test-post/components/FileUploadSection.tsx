import { Button } from './Button';
import { UploadIcon } from './Icons';

interface FileUploadSectionProps {
  file: File | null;
  isPending: boolean;
  ingested: boolean;
  ingestStatus: string;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onIngest: (e: React.FormEvent) => void;
}

export const FileUploadSection = ({
  file,
  isPending,
  ingested,
  ingestStatus,
  onFileChange,
  onIngest,
}: FileUploadSectionProps) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className={`h-5 w-5 rounded-full text-xs font-bold flex items-center justify-center flex-shrink-0 ${
          ingested
            ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400'
            : 'bg-accent-muted text-accent'
        }`}>
          1
        </span>
        <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">Document</p>
      </div>

      <form onSubmit={onIngest} className="space-y-4">
        <label className="block cursor-pointer">
          <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
            ingested
              ? 'border-emerald-200 bg-emerald-50/40 dark:border-emerald-500/30 dark:bg-emerald-500/5'
              : 'border-border bg-surface hover:border-accent/50 dark:hover:border-accent/40'
          }`}>
            <UploadIcon className="mx-auto h-10 w-10 text-foreground-dim mb-3" />
            {file ? (
              <div className="space-y-1">
                <span className="inline-block bg-accent-muted text-accent text-sm px-3 py-1 rounded-full font-medium">
                  {file.name}
                </span>
                <p className="text-xs text-foreground-dim">{(file.size / 1024).toFixed(0)} KB</p>
              </div>
            ) : (
              <p className="text-foreground-muted text-sm">Drop a PDF or click to browse</p>
            )}
          </div>
          <input type="file" accept="application/pdf" onChange={onFileChange} className="hidden" />
        </label>

        <div className="flex items-center gap-4">
          <Button
            type="submit"
            variant="primary"
            isLoading={isPending}
            loadingText="Processing..."
            disabled={!file}
          >
            Ingest document
          </Button>

          {ingestStatus && (
            <p className={`text-sm ${ingested ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'}`}>
              {ingestStatus}
            </p>
          )}
        </div>
      </form>
    </div>
  );
};
