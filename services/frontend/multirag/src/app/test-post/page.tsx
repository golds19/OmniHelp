"use client";
import { useState } from "react";
import { useDocumentIngest } from "./hooks/useDocumentIngest";
import { useDocumentQuery } from "./hooks/useDocumentQuery";
import { ThemeToggle } from "./components/ThemeToggle";
import { Header } from "./components/Header";
import { FileUploadSection } from "./components/FileUploadSection";
import { QuerySection } from "./components/QuerySection";
import { ResponseDisplay } from "./components/ResponseDisplay";
import { themeClasses } from "./utils/theme";

interface QueryResponse {
  answer: string;
  sources: Array<{ page: number; type: string }>;
  num_images: number;
  num_text_chunks: number;
  agent_type?: string;
}

export default function TestPost() {
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<QueryResponse | null>(null);
  const [isDark, setIsDark] = useState(false);

  const { ingested, ingestStatus, isPending, ingestDocument, resetIngestStatus } = useDocumentIngest();
  const { response, isStreaming, queryDocument, stopQuery, clearResponse } = useDocumentQuery();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    console.log("📁 File selected:", selectedFile?.name);
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

  return (
    <main className={`min-h-screen flex flex-col items-center justify-center p-8 transition-colors ${themeClasses.background(isDark)}`}>
      <div className="w-full max-w-4xl">
        <ThemeToggle isDark={isDark} onToggle={() => setIsDark(!isDark)} />

        <Header isDark={isDark} />

        <div className={`rounded-2xl shadow-xl p-8 space-y-8 ${themeClasses.card(isDark)}`}>
          <FileUploadSection
            file={file}
            isDark={isDark}
            isPending={isPending}
            ingested={ingested}
            ingestStatus={ingestStatus}
            onFileChange={handleFileChange}
            onIngest={handleIngest}
          />

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className={`w-full border-t ${themeClasses.border(isDark)}`}></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className={`px-4 ${themeClasses.divider(isDark)}`}>Then ask questions</span>
            </div>
          </div>

          <QuerySection
            input={input}
            isDark={isDark}
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
            isDark={isDark}
            isStreaming={isStreaming}
            ingested={ingested}
          />
        </div>

        {/* Footer */}
        <div className={`text-center mt-8 text-sm ${themeClasses.text.tertiary(isDark)}`}>
          Powered by Agentic RAG with ReAct Agent & CLIP Embeddings
        </div>
      </div>
    </main>
  );
}
