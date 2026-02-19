"use client";
import { useState, useEffect } from "react";
import { useDocumentIngest } from "./hooks/useDocumentIngest";
import { useDocumentQuery } from "./hooks/useDocumentQuery";
import { Header } from "./components/Header";
import { FileUploadSection } from "./components/FileUploadSection";
import { QuerySection } from "./components/QuerySection";
import { ResponseDisplay } from "./components/ResponseDisplay";
import { API_BASE_URL } from "./utils/constants";
import type { QueryResponse } from "@/types/api";

type BackendStatus = 'connecting' | 'online' | 'offline';

export default function TestPost() {
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<QueryResponse | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('connecting');

  useEffect(() => {
    fetch(`${API_BASE_URL}/ping`, { signal: AbortSignal.timeout(5000) })
      .then((res) => setBackendStatus(res.ok ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const { ingested, ingestStatus, isPending, ingestDocument, resetIngestStatus } = useDocumentIngest();
  const { response, isStreaming, queryDocument, stopQuery, clearResponse } = useDocumentQuery();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    resetIngestStatus();
    clearResponse();
    setMetadata(null);
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    clearResponse();
    setMetadata(null);
    await ingestDocument(file);
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    setMetadata(null);
    await queryDocument(input);
  };

  if (backendStatus === 'connecting') {
    return (
      <main className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-5 w-5 rounded-full border-2 border-neutral-200 border-t-indigo-600 animate-spin" />
          <p className="text-sm text-neutral-400">Connecting to backend...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-neutral-50 flex justify-center pt-20 pb-16 px-6">
      <div className="w-full max-w-2xl space-y-10">
        {backendStatus === 'offline' && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-500" />
            Backend unavailable — requests may fail
          </div>
        )}

        <Header />

        <FileUploadSection
          file={file}
          isPending={isPending}
          ingested={ingested}
          ingestStatus={ingestStatus}
          onFileChange={handleFileChange}
          onIngest={handleIngest}
        />

        <QuerySection
          input={input}
          isPending={isPending}
          ingested={ingested}
          isStreaming={isStreaming}
          onInputChange={setInput}
          onQuery={handleQuery}
          onStop={stopQuery}
        />

        <ResponseDisplay
          response={response}
          metadata={metadata}
          isStreaming={isStreaming}
          ingested={ingested}
        />
      </div>
    </main>
  );
}
