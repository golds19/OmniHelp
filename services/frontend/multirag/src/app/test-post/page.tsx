"use client";
import { useState, useEffect, useRef } from "react";
import { useDocumentIngest } from "./hooks/useDocumentIngest";
import { useDocumentQuery } from "./hooks/useDocumentQuery";
import { useDocumentLibrary } from "./hooks/useDocumentLibrary";
import { Header } from "./components/Header";
import { FileUploadSection } from "./components/FileUploadSection";
import { QuerySection } from "./components/QuerySection";
import { ResponseDisplay } from "./components/ResponseDisplay";
import { DocumentSidebar } from "./components/DocumentSidebar";
import { API_BASE_URL } from "./utils/constants";

type BackendStatus = 'connecting' | 'online' | 'offline';

const renderMd = (text: string) => {
  const parts = text.split(/(\*\*[^*\n]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  );
};

export default function TestPost() {
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('connecting');
  const [isDark, setIsDark] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const uploadSectionRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastQuestionRef = useRef('');

  useEffect(() => {
    const dark = localStorage.getItem('theme') !== 'light';
    setIsDark(dark);
    document.documentElement.classList.toggle('dark', dark);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem('sidebar');
    if (stored !== null) setSidebarOpen(stored !== 'closed');
  }, []);

  const toggleTheme = () => {
    const d = !isDark;
    setIsDark(d);
    document.documentElement.classList.toggle('dark', d);
    localStorage.setItem('theme', d ? 'dark' : 'light');
  };

  const toggleSidebar = () =>
    setSidebarOpen(prev => {
      localStorage.setItem('sidebar', prev ? 'closed' : 'open');
      return !prev;
    });

  useEffect(() => {
    fetch(`${API_BASE_URL}/ping`, { signal: AbortSignal.timeout(5000) })
      .then(r => setBackendStatus(r.ok ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const { ingested, ingestStatus, isPending, sessionId, ingestDocument, resetIngestStatus } = useDocumentIngest();
  const { response, isStreaming, queryLog, conversationHistory, queryDocument, stopQuery, clearResponse, clearHistory } = useDocumentQuery();
  const library = useDocumentLibrary();

  const activeSessionId = library.activeSessionId ?? sessionId;
  const prevSessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (sessionId && sessionId !== prevSessionIdRef.current && file) {
      library.addDocument(sessionId, file.name);
      prevSessionIdRef.current = sessionId;
    }
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll to bottom when streaming starts or new content arrives
  useEffect(() => {
    if (isStreaming) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [isStreaming, response]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
    resetIngestStatus();
    clearResponse();
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    clearResponse();
    clearHistory();
    await ingestDocument(file);
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSessionId || !input.trim()) return;
    lastQuestionRef.current = input;
    setInput('');
    await queryDocument(lastQuestionRef.current, activeSessionId);
  };

  const handleSelectDocument = (session_id: string) => {
    library.selectDocument(session_id);
    clearResponse();
    clearHistory();
  };

  // Derive past Q&A pairs from conversation history
  const historyPairs: { user: string; assistant: string }[] = [];
  for (let i = 0; i + 1 < conversationHistory.length; i += 2) {
    if (conversationHistory[i].role === 'user' && conversationHistory[i + 1].role === 'assistant') {
      historyPairs.push({
        user: conversationHistory[i].content,
        assistant: conversationHistory[i + 1].content,
      });
    }
  }

  if (backendStatus === 'connecting') {
    return (
      <div className="h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-6 w-6 rounded-full border-2 border-border border-t-accent animate-spin" />
          <p className="text-[10px] font-mono uppercase tracking-widest text-foreground-dim">Connecting</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header
        backendStatus={backendStatus}
        isDark={isDark}
        onToggleTheme={toggleTheme}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={toggleSidebar}
      />

      <div className="flex-1 flex overflow-hidden">
        <DocumentSidebar
          documents={library.documents}
          activeSessionId={library.activeSessionId}
          onSelect={handleSelectDocument}
          onRemove={library.removeDocument}
          onNewUpload={() => uploadSectionRef.current?.scrollIntoView({ behavior: 'smooth' })}
          isOpen={sidebarOpen}
        />

        {/* Main content: scrollable thread + sticky input */}
        <div className="flex-1 flex flex-col overflow-hidden bg-background">

          {/* Scrollable area */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-2xl mx-auto px-6 pt-6 pb-2 space-y-6">

              {/* Upload card — compact when ingested */}
              <div ref={uploadSectionRef}>
                <FileUploadSection
                  file={file}
                  isPending={isPending}
                  ingested={ingested}
                  ingestStatus={ingestStatus}
                  onFileChange={handleFileChange}
                  onIngest={handleIngest}
                />
              </div>

              {/* Empty state — document loaded but no questions yet */}
              {!!activeSessionId && !response && historyPairs.length === 0 && !isStreaming && (
                <div className="py-16 flex flex-col items-center gap-3 text-center">
                  <p className="text-sm text-foreground-dim">
                    Document ready — ask anything below
                  </p>
                </div>
              )}

              {/* Chat thread */}
              {(historyPairs.length > 0 || response || isStreaming) && (
                <div className="space-y-8">
                  {/* Past Q&A pairs */}
                  {historyPairs.map((pair, idx) => (
                    <div key={idx} className="space-y-3 animate-[var(--animate-fade-in)]"
                      style={{ animationDelay: `${idx * 40}ms` }}>
                      {/* User bubble */}
                      <div className="flex justify-end">
                        <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-surface-elevated border border-border text-sm text-foreground">
                          {pair.user}
                        </div>
                      </div>
                      {/* Assistant prose */}
                      <p className="text-sm leading-7 text-foreground whitespace-pre-wrap">
                        {renderMd(pair.assistant)}
                      </p>
                    </div>
                  ))}

                  {/* Current answer (streaming or just completed) */}
                  {(response || isStreaming) && (
                    <div className="space-y-3">
                      {/* Current user question bubble */}
                      {lastQuestionRef.current && (
                        <div className="flex justify-end">
                          <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-surface-elevated border border-border text-sm text-foreground">
                            {lastQuestionRef.current}
                          </div>
                        </div>
                      )}
                      <ResponseDisplay
                        response={response}
                        queryLog={queryLog}
                        isStreaming={isStreaming}
                        ingested={!!activeSessionId}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={bottomRef} className="h-2" />
            </div>
          </div>

          {/* Sticky input bar */}
          <div className="shrink-0 border-t border-border bg-surface/90 backdrop-blur-sm px-6 py-4">
            <div className="max-w-2xl mx-auto">
              <QuerySection
                input={input}
                isPending={isPending}
                ingested={!!activeSessionId}
                isStreaming={isStreaming}
                onInputChange={setInput}
                onQuery={handleQuery}
                onStop={stopQuery}
              />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
