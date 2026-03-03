import type { LibraryEntry } from '../hooks/useDocumentLibrary';

interface Props {
  documents: LibraryEntry[];
  activeSessionId: string | null;
  onSelect: (session_id: string) => void;
  onRemove: (session_id: string) => void;
  onNewUpload: () => void;
}

const formatDate = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
};

export const DocumentSidebar = ({ documents, activeSessionId, onSelect, onRemove, onNewUpload }: Props) => {
  return (
    <div className="flex-shrink-0 w-56 bg-surface rounded-2xl shadow-md border border-border p-4 flex flex-col gap-3">
      <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">Documents</p>

      {documents.length === 0 ? (
        <p className="text-xs text-foreground-dim italic">No documents yet</p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {documents.map(doc => (
            <li key={doc.session_id}>
              <button
                onClick={() => onSelect(doc.session_id)}
                className={`w-full text-left rounded-lg px-3 py-2 text-xs transition-colors group relative ${
                  doc.session_id === activeSessionId
                    ? 'bg-accent-muted text-accent font-medium'
                    : 'hover:bg-surface-elevated text-foreground'
                }`}
              >
                <span className="block truncate pr-5" title={doc.filename}>
                  {doc.filename}
                </span>
                <span className="block text-[10px] text-foreground-dim mt-0.5">
                  {formatDate(doc.ingested_at)}
                </span>
                <span
                  role="button"
                  aria-label={`Remove ${doc.filename}`}
                  onClick={e => { e.stopPropagation(); onRemove(doc.session_id); }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-foreground-dim hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity leading-none"
                >
                  ×
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <button
        onClick={onNewUpload}
        className="mt-auto text-xs text-accent hover:text-accent/80 font-medium transition-colors text-left"
      >
        + New document
      </button>
    </div>
  );
};
