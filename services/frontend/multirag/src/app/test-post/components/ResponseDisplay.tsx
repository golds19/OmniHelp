import type { QueryResponse } from '@/types/api';

interface ResponseDisplayProps {
  response: string;
  metadata: QueryResponse | null;
  isStreaming: boolean;
  ingested: boolean;
}

export const ResponseDisplay = ({ response, metadata, isStreaming, ingested }: ResponseDisplayProps) => {
  if (!response && !ingested) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Answer</p>
        {isStreaming && (
          <span className="text-indigo-500 text-sm animate-pulse">Streaming...</span>
        )}
      </div>

      <div>
        {response ? (
          <p className="text-neutral-900 leading-relaxed whitespace-pre-wrap">{response}</p>
        ) : (
          <p className="text-neutral-400 italic">Your answer will appear here...</p>
        )}
      </div>

      {metadata && (
        <div className="space-y-3 pt-2">
          <p className="text-xs text-neutral-500">
            <span>{metadata.num_text_chunks} text chunks</span>
            {' · '}
            <span>{metadata.num_images} images</span>
            {' · '}
            <span>{metadata.sources.length} sources</span>
            {' · '}
            <span>{metadata.agent_type || 'N/A'}</span>
          </p>

          {metadata.sources.length > 0 && (
            <ol className="space-y-1">
              {metadata.sources.map((source, idx) => (
                <li key={idx} className="flex items-center gap-2 text-sm text-neutral-600">
                  <span>{idx + 1}.</span>
                  <span>Page {source.page}</span>
                  <span className="text-xs bg-neutral-100 text-neutral-500 px-1.5 py-0.5 rounded">
                    {source.type}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  );
};
