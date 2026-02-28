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
  confidence?: number;
  top_similarity?: number;
  answer_source_similarity?: number;
  is_hallucination?: boolean;
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

// Generic error response from API
export interface APIError {
  detail: string;
}

// A single entry from GET /eval/logs or parsed from streaming metadata
export interface QueryLog {
  id: number;
  document_id: number | null;
  timestamp: string;
  query: string;
  answer_length: number;
  num_text_chunks: number;
  num_images: number;
  top_similarity: number;
  confidence: number;
  answer_source_similarity: number;
  is_hallucination: boolean;
  rejected: boolean;
  source_pages: number[];
  latency_ms: number;
}

// Metadata yielded as the final streaming chunk from /query-agentic-stream
export interface StreamingMetadata {
  sources: DocumentSource[];
  num_images: number;
  num_text_chunks: number;
  top_similarity: number;
  confidence: number;
  answer_source_similarity: number;
  is_hallucination: boolean;
  source_pages: number[];
  agent_type: string;
  latency_ms: number;
}

export const METADATA_DELIMITER = '\n\n__METADATA__';

// Response from GET /eval/logs
export interface EvalLogsResponse {
  logs: QueryLog[];
}

// Response from GET /eval/summary
export interface EvalSummary {
  total_queries: number;
  hallucination_rate: number;
  rejection_rate: number;
  avg_confidence: number;
  avg_top_similarity: number;
  avg_answer_source_similarity: number;
  avg_latency_ms: number;
}

// File validation constraints
export const FILE_CONSTRAINTS = {
  MAX_FILE_SIZE_MB: 25,
  MAX_FILE_SIZE_BYTES: 25 * 1024 * 1024,
  SUPPORTED_FORMATS: ['pdf'] as const,
  MAX_QUERY_LENGTH: 4096,
} as const;
