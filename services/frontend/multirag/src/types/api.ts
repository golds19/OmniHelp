/**
 * Shared API types for Lifeforge RAG system
 */

// Source information from document retrieval
export interface DocumentSource {
  page: number;
  type: 'text' | 'image';
}

// Response from /query-agentic endpoint
export interface QueryResponse {
  answer: string;
  sources: DocumentSource[];
  num_images: number;
  num_text_chunks: number;
  agent_type?: string;
}

// Response from /ingest-agentic endpoint
export interface IngestResponse {
  message: string;
  status: 'initialized' | 'error';
}

// Request payload for query endpoints
export interface QueryRequest {
  question: string;
}

// Voice transcription response
export interface TranscribeResponse {
  transcript: string;
  language: string;
  filename: string;
}

// Voice query result with audio
export interface VoiceQueryResult {
  transcript: string;
  answer: string;
  audioUrl: string;
  sources: DocumentSource[];
  num_images: number;
  num_text_chunks: number;
}

// Generic error response from API
export interface APIError {
  detail: string;
}

// Streaming state for query responses
export interface StreamingState {
  isStreaming: boolean;
  response: string;
  error: string | null;
}

// Document ingest state
export interface IngestState {
  ingested: boolean;
  status: string;
  isPending: boolean;
}

// File validation constraints
export const FILE_CONSTRAINTS = {
  MAX_FILE_SIZE_MB: 25,
  MAX_FILE_SIZE_BYTES: 25 * 1024 * 1024,
  SUPPORTED_FORMATS: ['pdf'] as const,
  MAX_QUERY_LENGTH: 4096,
} as const;

// Audio constraints for voice features
export const AUDIO_CONSTRAINTS = {
  MAX_AUDIO_SIZE_MB: 25,
  MAX_AUDIO_SIZE_BYTES: 25 * 1024 * 1024,
  SUPPORTED_FORMATS: ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'] as const,
} as const;
