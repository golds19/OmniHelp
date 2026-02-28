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
      <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">Document</p>

      <form onSubmit={onIngest} className="space-y-4">
        <label className="block cursor-pointer">
          <div className="border-2 border-dashed border-border rounded-xl p-10 text-center hover:border-accent/50 transition-colors bg-surface">
            <UploadIcon className="mx-auto h-10 w-10 text-foreground-dim mb-3" />
            {file ? (
              <span className="inline-block bg-accent-muted text-accent text-sm px-3 py-1 rounded-full font-medium">
                {file.name}
              </span>
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
            <p className={`text-sm ${ingested ? 'text-success' : 'text-danger'}`}>
              {ingestStatus}
            </p>
          )}
        </div>
      </form>
    </div>
  );
};
