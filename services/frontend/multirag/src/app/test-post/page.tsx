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
import { ConversationHistory } from "./components/ConversationHistory";
import { API_BASE_URL } from "./utils/constants";

type BackendStatus = 'connecting' | 'online' | 'offline';

export default function TestPost() {
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('connecting');
  const [isDark, setIsDark] = useState(true);
  const uploadSectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    const dark = saved !== 'light';
    setIsDark(dark);
    document.documentElement.classList.toggle('dark', dark);
  }, []);

  const toggleTheme = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    document.documentElement.classList.toggle('dark', newDark);
    localStorage.setItem('theme', newDark ? 'dark' : 'light');
  };

  useEffect(() => {
    fetch(`${API_BASE_URL}/ping`, { signal: AbortSignal.timeout(5000) })
      .then((res) => setBackendStatus(res.ok ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const { ingested, ingestStatus, isPending, sessionId, ingestDocument, resetIngestStatus } = useDocumentIngest();
  const { response, isStreaming, queryLog, conversationHistory, queryDocument, stopQuery, clearResponse, clearHistory } = useDocumentQuery();
  const library = useDocumentLibrary();

  // Active session: prefer library's activeSessionId, fall back to freshly ingested sessionId
  const activeSessionId = library.activeSessionId ?? sessionId;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    resetIngestStatus();
    clearResponse();
  };

  // When a new sessionId is assigned after ingest, register it in the library
  const prevSessionIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (sessionId && sessionId !== prevSessionIdRef.current && file) {
      library.addDocument(sessionId, file.name);
      prevSessionIdRef.current = sessionId;
    }
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    clearResponse();
    clearHistory();
    await ingestDocument(file);
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSessionId) return;
    await queryDocument(input, activeSessionId);
  };

  const handleSelectDocument = (session_id: string) => {
    library.selectDocument(session_id);
    clearResponse();
    clearHistory();
  };

  const handleNewUpload = () => {
    uploadSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  if (backendStatus === 'connecting') {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-5 w-5 rounded-full border-2 border-border border-t-accent animate-spin" />
          <p className="text-sm text-foreground-dim">Connecting to backend...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background flex justify-center pt-12 pb-20 px-4">
      <div className="w-full max-w-5xl flex gap-6 items-start">
        <DocumentSidebar
          documents={library.documents}
          activeSessionId={library.activeSessionId}
          onSelect={handleSelectDocument}
          onRemove={library.removeDocument}
          onNewUpload={handleNewUpload}
        />

        <div className="flex-1 min-w-0">
          <div className="bg-surface rounded-2xl shadow-md border border-border p-8 space-y-8">
            <Header backendStatus={backendStatus} isDark={isDark} onToggleTheme={toggleTheme} />

            <div className="border-t border-border" />

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

            <div className="border-t border-border" />

            <QuerySection
              input={input}
              isPending={isPending}
              ingested={!!activeSessionId}
              isStreaming={isStreaming}
              onInputChange={setInput}
              onQuery={handleQuery}
              onStop={stopQuery}
            />

            {conversationHistory.length > 0 && (
              <>
                <div className="border-t border-border" />
                <ConversationHistory history={conversationHistory} onClear={clearHistory} />
              </>
            )}

            {(response || !!activeSessionId) && (
              <>
                <div className="border-t border-border" />
                <ResponseDisplay
                  response={response}
                  queryLog={queryLog}
                  isStreaming={isStreaming}
                  ingested={!!activeSessionId}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
