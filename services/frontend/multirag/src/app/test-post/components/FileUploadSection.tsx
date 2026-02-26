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
            ? 'bg-green-100 text-green-600 dark:bg-emerald-500/15 dark:text-emerald-400'
            : 'bg-indigo-100 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-400'
        }`}>
          1
        </span>
        <p className="text-xs font-medium text-neutral-400 dark:text-zinc-500 uppercase tracking-wider">Document</p>
      </div>

      <form onSubmit={onIngest} className="space-y-4">
        <label className="block cursor-pointer">
          <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
            ingested
              ? 'border-green-200 bg-green-50/40 dark:border-emerald-500/30 dark:bg-emerald-500/5'
              : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-indigo-50/30 dark:border-zinc-700 dark:bg-zinc-800/50 dark:hover:border-indigo-500/40 dark:hover:bg-indigo-500/5'
          }`}>
            <UploadIcon className="mx-auto h-10 w-10 text-neutral-300 dark:text-zinc-600 mb-3" />
            {file ? (
              <div className="space-y-1">
                <span className="inline-block bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-300 dark:border dark:border-indigo-500/20 text-sm px-3 py-1 rounded-full">
                  {file.name}
                </span>
                <p className="text-xs text-neutral-400 dark:text-zinc-500">{(file.size / 1024).toFixed(0)} KB</p>
              </div>
            ) : (
              <p className="text-neutral-500 dark:text-zinc-400 text-sm">Drop a PDF or click to browse</p>
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
            <p className={`text-sm ${ingested ? 'text-green-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'}`}>
              {ingestStatus}
            </p>
          )}
        </div>
      </form>
    </div>
  );
};
