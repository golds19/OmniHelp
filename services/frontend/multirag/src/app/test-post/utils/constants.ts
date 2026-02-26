export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  INGEST: `${API_BASE_URL}/ingest-agentic`,
  QUERY_STREAM: `${API_BASE_URL}/query-agentic-stream`,
  EVAL_LOGS: `${API_BASE_URL}/eval/logs`,
} as const;

export const MESSAGES = {
  INGEST_SUCCESS: 'Document ready',
  INGEST_ERROR: 'Could not reach backend',
  QUERY_ERROR: 'Could not reach backend',
} as const;
