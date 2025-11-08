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
  const [isDark, setIsDark] = useState(false);
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
    <main className={`min-h-screen flex flex-col items-center justify-center p-8 transition-colors ${
      isDark
        ? "bg-gradient-to-br from-slate-900 to-slate-800"
        : "bg-gradient-to-br from-slate-50 to-blue-50"
    }`}>
      <div className="w-full max-w-4xl">
        {/* Theme Toggle Button */}
        <div className="flex justify-end mb-6">
          <button
            onClick={() => setIsDark(!isDark)}
            className={`p-3 rounded-full shadow-lg transition-all hover:scale-110 ${
              isDark
                ? "bg-slate-700 text-yellow-400 hover:bg-slate-600"
                : "bg-white text-slate-700 hover:bg-slate-50"
            }`}
            aria-label="Toggle theme"
          >
            {isDark ? (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
          </button>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className={`text-4xl font-bold mb-3 ${
            isDark ? "text-white" : "text-slate-800"
          }`}>
            Document Intelligence
          </h1>
          <p className={`text-lg ${
            isDark ? "text-slate-300" : "text-slate-600"
          }`}>
            Upload documents and query them with AI-powered insights
          </p>
        </div>

        {/* Main Card */}
        <div className={`rounded-2xl shadow-xl p-8 space-y-8 ${
          isDark ? "bg-slate-800" : "bg-white"
        }`}>

          {/* Step 1: Document Upload */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                isDark
                  ? "bg-blue-900/50 text-blue-400"
                  : "bg-blue-100 text-blue-600"
              }`}>
                1
              </div>
              <h2 className={`text-xl font-semibold ${
                isDark ? "text-slate-200" : "text-slate-700"
              }`}>Upload Document</h2>
            </div>

            <form onSubmit={handleIngest} className="space-y-4">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                <label className="flex-1 cursor-pointer">
                  <div className={`flex items-center justify-center px-6 py-4 border-2 border-dashed rounded-lg transition-all ${
                    isDark
                      ? "border-slate-600 hover:border-blue-500 hover:bg-blue-900/20"
                      : "border-slate-300 hover:border-blue-400 hover:bg-blue-50/50"
                  }`}>
                    <div className="text-center">
                      <svg className={`mx-auto h-12 w-12 mb-2 ${
                        isDark ? "text-slate-500" : "text-slate-400"
                      }`} stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <p className={`text-sm ${
                        isDark ? "text-slate-400" : "text-slate-600"
                      }`}>
                        {file ? (
                          <span className={`font-medium ${
                            isDark ? "text-blue-400" : "text-blue-600"
                          }`}>{file.name}</span>
                        ) : (
                          <span>Click to select a PDF file</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>

                <button
                  type="submit"
                  className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-medium hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed shadow-md hover:shadow-lg transition-all disabled:shadow-none"
                  disabled={isPending || !file}
                >
                  {isPending ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    "Upload & Ingest"
                  )}
                </button>
              </div>

              {ingestStatus && (
                <div className={`p-4 rounded-lg border ${
                  ingested
                    ? isDark
                      ? "bg-green-900/30 border-green-700 text-green-400"
                      : "bg-green-50 border-green-200 text-green-700"
                    : isDark
                    ? "bg-red-900/30 border-red-700 text-red-400"
                    : "bg-red-50 border-red-200 text-red-700"
                }`}>
                  <div className="flex items-center gap-2">
                    {ingested ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    )}
                    <span className="font-medium">{ingestStatus}</span>
                  </div>
                </div>
              )}
            </form>
          </div>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className={`w-full border-t ${
                isDark ? "border-slate-600" : "border-slate-200"
              }`}></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className={`px-4 ${
                isDark ? "bg-slate-800 text-slate-400" : "bg-white text-slate-500"
              }`}>Then ask questions</span>
            </div>
          </div>

          {/* Step 2: Query */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                ingested
                  ? isDark
                    ? "bg-green-900/50 text-green-400"
                    : "bg-green-100 text-green-600"
                  : isDark
                  ? "bg-slate-700 text-slate-500"
                  : "bg-slate-100 text-slate-400"
              }`}>
                2
              </div>
              <h2 className={`text-xl font-semibold ${
                isDark ? "text-slate-200" : "text-slate-700"
              }`}>Ask Questions</h2>
            </div>

            <form onSubmit={handleQuery} className="space-y-4">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={ingested ? "What would you like to know?" : "Upload a document first..."}
                  className={`flex-1 px-6 py-4 border-2 rounded-lg focus:ring-4 outline-none transition-all text-lg ${
                    isDark
                      ? "bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-green-500 focus:ring-green-900/50 disabled:bg-slate-800 disabled:text-slate-500"
                      : "bg-white border-slate-200 text-slate-900 placeholder-slate-400 focus:border-green-400 focus:ring-green-100 disabled:bg-slate-50 disabled:text-slate-400"
                  }`}
                  disabled={!ingested}
                />
                <button
                  type="submit"
                  className="px-8 py-4 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg font-medium hover:from-green-700 hover:to-green-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed shadow-md hover:shadow-lg transition-all disabled:shadow-none"
                  disabled={isPending || !ingested || !input}
                >
                  {isPending ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Thinking...
                    </span>
                  ) : (
                    "Ask Question"
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Response Section */}
          {(response || ingested) && (
            <div className="space-y-3">
              <h3 className={`text-lg font-semibold flex items-center gap-2 ${
                isDark ? "text-slate-200" : "text-slate-700"
              }`}>
                <svg className={`w-5 h-5 ${
                  isDark ? "text-slate-400" : "text-slate-500"
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                Response
              </h3>
              <div className={`min-h-[120px] p-6 rounded-lg border ${
                isDark
                  ? "bg-gradient-to-br from-slate-700 to-slate-600 border-slate-600"
                  : "bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200"
              }`}>
                {response ? (
                  <p className={`leading-relaxed whitespace-pre-wrap ${
                    isDark ? "text-slate-200" : "text-slate-700"
                  }`}>{response}</p>
                ) : (
                  <p className={`italic ${
                    isDark ? "text-slate-500" : "text-slate-400"
                  }`}>Your answer will appear here...</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={`text-center mt-8 text-sm ${
          isDark ? "text-slate-400" : "text-slate-500"
        }`}>
          Powered by AI-driven document understanding
        </div>
      </div>
    </main>
  );
}