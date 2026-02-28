import type { StreamingMetadata } from '@/types/api';
import { ShieldCheckIcon, ShieldIcon } from './Icons';

interface ResponseDisplayProps {
  response: string;
  metadata: StreamingMetadata | null;
  isStreaming: boolean;
  ingested: boolean;
}

const ConfidenceGauge = ({ value }: { value: number }) => {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? 'bg-success' :
    pct >= 40 ? 'bg-warning' :
    'bg-danger';
  const textColor =
    pct >= 70 ? 'text-success' :
    pct >= 40 ? 'text-warning' :
    'text-danger';

  return (
    <div className="flex items-center gap-2.5">
      <span className="text-xs text-foreground-dim uppercase tracking-wide">Confidence</span>
      <div className="w-20 h-1.5 rounded-full bg-border overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-sm font-mono font-semibold ${textColor}`}>{pct}%</span>
    </div>
  );
};

const HallucinationBadge = ({ isHallucination }: { isHallucination: boolean }) => {
  if (isHallucination) {
    return (
      <div className="flex items-center gap-1.5 text-danger">
        <ShieldIcon className="h-4 w-4" />
        <span className="text-xs font-medium">Low Confidence</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5 text-success">
      <ShieldCheckIcon className="h-4 w-4" />
      <span className="text-xs font-medium">Grounded</span>
    </div>
  );
};

const MetricPill = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center gap-1.5">
    <span className="text-xs text-foreground-dim">{label}</span>
    <span className="text-xs font-mono text-foreground-muted">{value}</span>
  </div>
);

const MetricsBar = ({ metadata }: { metadata: StreamingMetadata }) => {
  return (
    <div className="rounded-xl border border-border bg-surface p-4 space-y-3">
      {/* Row 1: Key metrics */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <ConfidenceGauge value={metadata.confidence} />

        <div className="w-px h-4 bg-border" />

        <HallucinationBadge isHallucination={metadata.is_hallucination} />

        <div className="w-px h-4 bg-border" />

        <MetricPill label="Similarity" value={metadata.top_similarity.toFixed(3)} />

        <div className="w-px h-4 bg-border" />

        <MetricPill label="Ans-Src" value={metadata.answer_source_similarity.toFixed(3)} />

        <div className="w-px h-4 bg-border" />

        <MetricPill label="Chunks" value={String(metadata.num_text_chunks)} />
        <MetricPill label="Images" value={String(metadata.num_images)} />
      </div>

      {/* Row 2: Source pages */}
      {metadata.source_pages.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-foreground-dim">Sources</span>
          {metadata.source_pages.map((page) => (
            <span
              key={page}
              className="text-xs font-mono px-2 py-0.5 rounded-md bg-accent-muted text-accent font-medium"
            >
              p.{page}
            </span>
          ))}
          {metadata.latency_ms > 0 && (
            <>
              <div className="flex-1" />
              <span className="text-xs font-mono text-foreground-dim">
                {metadata.latency_ms < 1000
                  ? `${Math.round(metadata.latency_ms)}ms`
                  : `${(metadata.latency_ms / 1000).toFixed(1)}s`}
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export const ResponseDisplay = ({ response, metadata, isStreaming, ingested }: ResponseDisplayProps) => {
  if (!response && !ingested) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">Answer</p>
        {isStreaming && (
          <span className="text-accent text-sm animate-pulse">Streaming...</span>
        )}
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        {response ? (
          <p className="text-foreground leading-relaxed whitespace-pre-wrap">{response}</p>
        ) : (
          <p className="text-foreground-dim italic">Your answer will appear here...</p>
        )}
      </div>

      {metadata && !isStreaming && <MetricsBar metadata={metadata} />}
    </div>
  );
};
