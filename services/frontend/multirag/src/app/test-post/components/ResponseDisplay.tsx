import { ChatIcon, InfoIcon } from './Icons';

interface QueryResponse {
  answer: string;
  sources: Array<{ page: number; type: string }>;
  num_images: number;
  num_text_chunks: number;
  agent_type?: string;
}

interface ResponseDisplayProps {
  response: string;
  metadata: QueryResponse | null;
  isDark: boolean;
  isStreaming: boolean;
  ingested: boolean;
}

export const ResponseDisplay = ({ response, metadata, isDark, isStreaming, ingested }: ResponseDisplayProps) => {
  if (!response && !ingested) return null;

  return (
    <div className="space-y-3">
      <h3 className={`text-lg font-semibold flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
        <ChatIcon className={`w-5 h-5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />
        Agent Response
        {isStreaming && (
          <span className={`ml-2 text-sm animate-pulse ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
            Streaming...
          </span>
        )}
      </h3>

      <div
        className={`min-h-[120px] p-6 rounded-lg border ${
          isDark
            ? 'bg-linear-to-br from-slate-700 to-slate-600 border-slate-600'
            : 'bg-linear-to-br from-slate-50 to-slate-100 border-slate-200'
        }`}
      >
        {response ? (
          <p className={`leading-relaxed whitespace-pre-wrap ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
            {response}
          </p>
        ) : (
          <p className={`italic ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
            Your answer will appear here...
          </p>
        )}
      </div>

      {metadata && (
        <div
          className={`p-4 rounded-lg border space-y-3 ${
            isDark ? 'bg-slate-700/50 border-slate-600' : 'bg-blue-50/50 border-blue-200'
          }`}
        >
          <h4
            className={`text-sm font-semibold flex items-center gap-2 ${
              isDark ? 'text-slate-300' : 'text-slate-700'
            }`}
          >
            <InfoIcon className="w-4 h-4" />
            Retrieval Metadata
          </h4>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetadataCard
              label="Text Chunks"
              value={metadata.num_text_chunks}
              colorClass={isDark ? 'text-blue-400' : 'text-blue-600'}
              isDark={isDark}
            />
            <MetadataCard
              label="Images"
              value={metadata.num_images}
              colorClass={isDark ? 'text-green-400' : 'text-green-600'}
              isDark={isDark}
            />
            <MetadataCard
              label="Total Sources"
              value={metadata.sources.length}
              colorClass={isDark ? 'text-purple-400' : 'text-purple-600'}
              isDark={isDark}
            />
            <MetadataCard
              label="Agent Type"
              value={metadata.agent_type || 'N/A'}
              colorClass={isDark ? 'text-orange-400' : 'text-orange-600'}
              isDark={isDark}
              isText
            />
          </div>

          {metadata.sources.length > 0 && (
            <div className="mt-3">
              <div className={`text-xs mb-2 font-medium ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                Sources Referenced:
              </div>
              <div className="flex flex-wrap gap-2">
                {metadata.sources.map((source, idx) => (
                  <span
                    key={idx}
                    className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${
                      source.type === 'image'
                        ? isDark
                          ? 'bg-green-900/30 text-green-400'
                          : 'bg-green-100 text-green-700'
                        : isDark
                        ? 'bg-blue-900/30 text-blue-400'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {source.type === 'image' ? '🖼️' : '📄'} Page {source.page}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface MetadataCardProps {
  label: string;
  value: string | number;
  colorClass: string;
  isDark: boolean;
  isText?: boolean;
}

const MetadataCard = ({ label, value, colorClass, isDark, isText = false }: MetadataCardProps) => (
  <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-600/50' : 'bg-white'}`}>
    <div className={`text-xs mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{label}</div>
    <div className={`${isText ? 'text-sm font-semibold' : 'text-lg font-bold'} ${colorClass}`}>{value}</div>
  </div>
);
