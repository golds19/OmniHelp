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
      <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Document</p>

      <form onSubmit={onIngest} className="space-y-4">
        <label className="block cursor-pointer">
          <div className="border-2 border-dashed border-neutral-200 rounded-lg p-10 text-center hover:border-indigo-400 transition-colors">
            <UploadIcon className="mx-auto h-10 w-10 text-neutral-300 mb-3" />
            {file ? (
              <span className="inline-block bg-indigo-50 text-indigo-600 text-sm px-3 py-1 rounded-full">
                {file.name}
              </span>
            ) : (
              <p className="text-neutral-500 text-sm">Drop a PDF or click to browse</p>
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
            <p className={`text-sm ${ingested ? 'text-green-600' : 'text-red-500'}`}>
              {ingestStatus}
            </p>
          )}
        </div>
      </form>
    </div>
  );
};
