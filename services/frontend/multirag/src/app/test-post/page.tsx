"use client";
import { useState, useEffect } from "react";
import { useDocumentIngest } from "./hooks/useDocumentIngest";
import { useDocumentQuery } from "./hooks/useDocumentQuery";
import { Header } from "./components/Header";
import { FileUploadSection } from "./components/FileUploadSection";
import { QuerySection } from "./components/QuerySection";
import { ResponseDisplay } from "./components/ResponseDisplay";
import { API_BASE_URL } from "./utils/constants";

type BackendStatus = 'connecting' | 'online' | 'offline';

export default function TestPost() {
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('connecting');
  const [isDark, setIsDark] = useState(true);

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
  const { response, isStreaming, queryLog, queryDocument, stopQuery, clearResponse } = useDocumentQuery();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    resetIngestStatus();
    clearResponse();
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    clearResponse();
    await ingestDocument(file);
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    await queryDocument(input);
  };

  if (backendStatus === 'connecting') {
    return (
      <main className="min-h-screen bg-neutral-50 dark:bg-zinc-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-5 w-5 rounded-full border-2 border-neutral-200 border-t-indigo-600 dark:border-zinc-700 dark:border-t-indigo-400 animate-spin" />
          <p className="text-sm text-neutral-400 dark:text-zinc-500">Connecting to backend...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 dark:bg-none dark:bg-zinc-950 flex justify-center pt-12 pb-20 px-4">
      <div className="w-full max-w-3xl">
        <div className="bg-slate-50 rounded-2xl shadow-md border border-slate-200 dark:bg-zinc-900 dark:shadow-xl dark:border-zinc-800 p-8 space-y-8">
          <Header backendStatus={backendStatus} isDark={isDark} onToggleTheme={toggleTheme} />

          <div className="border-t border-slate-200/60 dark:border-zinc-800" />

          <FileUploadSection
            file={file}
            isPending={isPending}
            ingested={ingested}
            ingestStatus={ingestStatus}
            onFileChange={handleFileChange}
            onIngest={handleIngest}
          />

          <div className="border-t border-slate-200/60 dark:border-zinc-800" />

          <QuerySection
            input={input}
            isPending={isPending}
            ingested={ingested}
            isStreaming={isStreaming}
            onInputChange={setInput}
            onQuery={handleQuery}
            onStop={stopQuery}
          />

          {(response || ingested) && (
            <>
              <div className="border-t border-slate-200/60 dark:border-zinc-800" />
              <ResponseDisplay
                response={response}
                queryLog={queryLog}
                isStreaming={isStreaming}
                ingested={ingested}
              />
            </>
          )}
        </div>
      </div>
    </main>
  );
}
