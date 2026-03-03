import type { LibraryEntry } from '../hooks/useDocumentLibrary';

interface Props {
  documents: LibraryEntry[];
  activeSessionId: string | null;
  onSelect: (session_id: string) => void;
  onRemove: (session_id: string) => void;
  onNewUpload: () => void;
  isOpen: boolean;
}

const DocIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
);

const formatDate = (iso: string) => {
  try { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); }
  catch { return ''; }
};

export const DocumentSidebar = ({ documents, activeSessionId, onSelect, onRemove, onNewUpload, isOpen }: Props) => (
  <aside className={`${isOpen ? 'w-56' : 'w-0'} transition-[width] duration-300 ease-in-out border-r border-border bg-surface flex flex-col shrink-0 overflow-hidden`}>
    <div className="w-56 flex flex-col h-full overflow-hidden">
      <div className="px-4 pt-5 pb-3">
        <p className="text-[10px] font-mono uppercase tracking-widest text-foreground-dim">Library</p>
      </div>

      <div className="flex-1 overflow-y-auto px-2 space-y-0.5 min-h-0">
        {documents.length === 0 ? (
          <div className="px-2 py-8 flex flex-col items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-surface-elevated flex items-center justify-center">
              <DocIcon className="h-4 w-4 text-foreground-dim" />
            </div>
            <p className="text-[11px] text-foreground-dim text-center leading-relaxed">
              No documents yet<br />Upload one to begin
            </p>
          </div>
        ) : (
          documents.map(doc => {
            const isActive = doc.session_id === activeSessionId;
            return (
              <div
                key={doc.session_id}
                onClick={() => onSelect(doc.session_id)}
                className={`group relative flex items-start gap-2 px-2 py-2 rounded-md cursor-pointer transition-colors ${
                  isActive ? 'bg-accent-muted' : 'hover:bg-surface-elevated'
                }`}
              >
                <div className={`absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full transition-all ${
                  isActive ? 'bg-accent' : 'bg-transparent'
                }`} />
                <DocIcon className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${isActive ? 'text-accent' : 'text-foreground-dim'}`} />
                <div className="flex-1 min-w-0">
                  <p className={`text-[11px] font-mono truncate leading-tight ${isActive ? 'text-accent' : 'text-foreground'}`}
                     title={doc.filename}>
                    {doc.filename.length > 18 ? doc.filename.slice(0, 17) + '…' : doc.filename}
                  </p>
                  <p className="text-[10px] text-foreground-dim mt-0.5">{formatDate(doc.ingested_at)}</p>
                </div>
                <button
                  onClick={e => { e.stopPropagation(); onRemove(doc.session_id); }}
                  aria-label={`Remove ${doc.filename}`}
                  className="opacity-0 group-hover:opacity-100 mt-0.5 text-foreground-dim hover:text-foreground transition-all text-sm leading-none shrink-0"
                >×</button>
              </div>
            );
          })
        )}
      </div>

      <div className="px-4 py-4 border-t border-border">
        <button
          onClick={onNewUpload}
          className="flex items-center gap-1.5 text-[11px] font-medium text-foreground-dim hover:text-accent transition-colors"
        >
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New document
        </button>
      </div>
    </div>
  </aside>
);
