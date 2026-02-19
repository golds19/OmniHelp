export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  INGEST: `${API_BASE_URL}/ingest-agentic`,
  QUERY_STREAM: `${API_BASE_URL}/query-agentic-stream`,
} as const;

export const MESSAGES = {
  INGEST_SUCCESS: 'Document ingested successfully with Agentic RAG 🤖',
  INGEST_ERROR: 'Error contacting backend',
  QUERY_ERROR: 'Error contacting backend',
  NO_FILE: '⚠️ No file selected',
  STREAM_ABORTED: '🛑 Stream aborted by user',
} as const;
