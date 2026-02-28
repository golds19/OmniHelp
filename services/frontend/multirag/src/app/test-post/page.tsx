"use client";
import { useState, useEffect } from "react";
import { useDocumentIngest } from "./hooks/useDocumentIngest";
import { useDocumentQuery } from "./hooks/useDocumentQuery";
import { Header } from "./components/Header";
import { DocumentBar } from "./components/DocumentBar";
import { ChatThread } from "./components/ChatThread";
import { ChatInput } from "./components/ChatInput";
import { API_BASE_URL } from "./utils/constants";

type BackendStatus = 'connecting' | 'online' | 'offline';

export default function TestPost() {
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('connecting');
  const [isDark, setIsDark] = useState(true);
  const [pendingQuestion, setPendingQuestion] = useState("");

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

  const { ingested, ingestStatus, isPending, ingestDocument, resetIngestStatus } = useDocumentIngest();
  const { response, isStreaming, queryLog, conversationTurns, queryDocument, stopQuery, clearConversation } = useDocumentQuery();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    resetIngestStatus();
    clearConversation();
    if (selectedFile) {
      await ingestDocument(selectedFile);
    }
  };

  const handleQuery = async () => {
    if (!input.trim() || isStreaming || !ingested) return;
    const question = input.trim();
    setInput('');
    setPendingQuestion(question);
    await queryDocument(question);
    setPendingQuestion('');
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
      <div className="w-full max-w-3xl">
        <div className="bg-surface rounded-2xl shadow-md border border-border flex flex-col">
          <div className="px-6 pt-6 pb-4 border-b border-border">
            <Header backendStatus={backendStatus} isDark={isDark} onToggleTheme={toggleTheme} />
          </div>

          <div className="px-6 border-b border-border">
            <DocumentBar
              file={file}
              isPending={isPending}
              ingested={ingested}
              ingestStatus={ingestStatus}
              onFileChange={handleFileChange}
            />
          </div>

          <ChatThread
            conversationTurns={conversationTurns}
            response={response}
            queryLog={queryLog}
            isStreaming={isStreaming}
            pendingQuestion={pendingQuestion}
          />

          <div className="px-4 py-3 border-t border-border">
            <ChatInput
              input={input}
              ingested={ingested}
              isStreaming={isStreaming}
              onInputChange={setInput}
              onSubmit={handleQuery}
              onStop={stopQuery}
            />
          </div>
        </div>
      </div>
    </main>
  );
}
