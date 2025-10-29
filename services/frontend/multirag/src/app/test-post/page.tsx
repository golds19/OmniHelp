"use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

export default function TestPost() {
  const [response, setResponse] = useState("");
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [ingested, setIngested] = useState(false);
  const [ingestStatus, setIngestStatus] = useState("");
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    console.log("📁 File selected:", selectedFile?.name);
    setFile(selectedFile);
    setIngested(false);
    setIngestStatus("");
    setResponse("");
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      console.warn("⚠️ No file selected");
      return;
    }

    console.log("🚀 Starting ingestion for:", file.name);
    setIngestStatus("");
    setResponse("");

    startTransition(async () => {
      try {
        const formData = new FormData();
        formData.append("file", file);
        
        console.log("📤 Sending POST request to /ingest");
        const res = await fetch("http://localhost:8000/ingest", {
          method: "POST",
          body: formData,
        });

        console.log("📥 Response status:", res.status);
        const data = await res.json();
        console.log("📦 Response data:", data);

        if (res.ok) {
          setIngested(true);
          setIngestStatus("Document ingested successfully.");
          console.log("✅ Ingestion successful");
        } else {
          setIngestStatus(data.detail || "Ingestion failed.");
          console.error("❌ Ingestion failed:", data.detail);
        }
      } catch (err) {
        console.error("🔥 Ingestion error:", err);
        setIngestStatus("Error contacting backend");
      }
    });
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("🔍 Querying with input:", input);
    setResponse("");

    startTransition(async () => {
      try {
        console.log("📤 Sending POST request to /query");
        const res = await fetch("http://localhost:8000/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: input }),
        });

        console.log("📥 Query response status:", res.status);
        const data = await res.json();
        console.log("📦 Query response data:", data);

        setResponse(data.answer || JSON.stringify(data));
        console.log("✅ Query successful");
      } catch (err) {
        console.error("🔥 Query error:", err);
        setResponse("Error contacting backend");
      }
    });
  };

  console.log("🎨 Rendering - ingested:", ingested, "isPending:", isPending);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4">
      <h1 className="text-2xl font-bold mb-6">Test Document Ingestion and Query</h1>
      
      <form onSubmit={handleIngest} className="mb-4 flex items-center gap-4">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          disabled={isPending || !file}
        >
          {isPending ? "Uploading..." : "Upload & Ingest"}
        </button>
      </form>

      {ingestStatus && (
        <div className={`mb-8 ${ingested ? "text-green-600" : "text-red-600"}`}>
          {ingestStatus}
        </div>
      )}

      <form onSubmit={handleQuery} className="mb-4 flex items-center gap-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your question"
          className="px-4 py-2 w-80 border rounded disabled:bg-gray-100"
          disabled={!ingested}
        />
        <button
          type="submit"
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          disabled={isPending || !ingested || !input}
        >
          {isPending ? "Sending..." : "Send"}
        </button>
      </form>

      <div className="w-full max-w-2xl">
        <b>Response:</b>
        <div className="mt-2 min-h-8 p-4 bg-gray-50 rounded">{response}</div>
      </div>
    </main>
  );
}