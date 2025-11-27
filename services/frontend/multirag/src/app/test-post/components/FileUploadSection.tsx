import { StepHeader } from './StepHeader';
import { Button } from './Button';
import { UploadIcon, CheckCircleIcon, ErrorCircleIcon } from './Icons';

interface FileUploadSectionProps {
  file: File | null;
  isDark: boolean;
  isPending: boolean;
  ingested: boolean;
  ingestStatus: string;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onIngest: (e: React.FormEvent) => void;
}

export const FileUploadSection = ({
  file,
  isDark,
  isPending,
  ingested,
  ingestStatus,
  onFileChange,
  onIngest,
}: FileUploadSectionProps) => {
  return (
    <div className="space-y-4">
      <StepHeader stepNumber={1} title="Upload Document" isDark={isDark} />

      <form onSubmit={onIngest} className="space-y-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          <label className="flex-1 cursor-pointer">
            <div
              className={`flex items-center justify-center px-6 py-4 border-2 border-dashed rounded-lg transition-all ${
                isDark
                  ? 'border-slate-600 hover:border-blue-500 hover:bg-blue-900/20'
                  : 'border-slate-300 hover:border-blue-400 hover:bg-blue-50/50'
              }`}
            >
              <div className="text-center">
                <UploadIcon
                  className={`mx-auto h-12 w-12 mb-2 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}
                />
                <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                  {file ? (
                    <span className={`font-medium ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
                      {file.name}
                    </span>
                  ) : (
                    <span>Click to select a PDF file</span>
                  )}
                </p>
              </div>
            </div>
            <input type="file" accept="application/pdf" onChange={onFileChange} className="hidden" />
          </label>

          <Button type="submit" variant="primary" isLoading={isPending} loadingText="Processing..." disabled={!file}>
            Upload & Ingest
          </Button>
        </div>

        {ingestStatus && (
          <div
            className={`p-4 rounded-lg border ${
              ingested
                ? isDark
                  ? 'bg-green-900/30 border-green-700 text-green-400'
                  : 'bg-green-50 border-green-200 text-green-700'
                : isDark
                ? 'bg-red-900/30 border-red-700 text-red-400'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            <div className="flex items-center gap-2">
              {ingested ? (
                <CheckCircleIcon className="w-5 h-5" />
              ) : (
                <ErrorCircleIcon className="w-5 h-5" />
              )}
              <span className="font-medium">{ingestStatus}</span>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
