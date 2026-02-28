import { useState, useRef, useCallback } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';
import type { QueryLog, StreamingMetadata } from '@/types/api';
import { METADATA_DELIMITER } from '@/types/api';

const DEBOUNCE_MS = 50;

/** Map streaming metadata into a QueryLog-compatible shape for display. */
const toQueryLog = (meta: StreamingMetadata): QueryLog => ({
  id: 0,
  document_id: null,
  timestamp: new Date().toISOString(),
  query: '',
  answer_length: 0,
  num_text_chunks: meta.num_text_chunks,
  num_images: meta.num_images,
  top_similarity: meta.top_similarity,
  confidence: meta.confidence,
  answer_source_similarity: meta.answer_source_similarity,
  is_hallucination: meta.is_hallucination,
  rejected: false,
  source_pages: meta.source_pages,
  latency_ms: meta.latency_ms,
});

export const useDocumentQuery = () => {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [queryLog, setQueryLog] = useState<QueryLog | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastUpdateRef = useRef<number>(0);
  const pendingUpdateRef = useRef<string>('');
  const rafIdRef = useRef<number | null>(null);

  const flushUpdate = useCallback(() => {
    if (pendingUpdateRef.current) {
      const display = pendingUpdateRef.current.split(METADATA_DELIMITER)[0];
      setResponse(display);
    }
    rafIdRef.current = null;
  }, []);

  const queryDocument = async (question: string) => {
    setResponse('');
    setQueryLog(null);
    setIsStreaming(true);
    lastUpdateRef.current = 0;
    pendingUpdateRef.current = '';

    abortControllerRef.current = new AbortController();

    try {
      const res = await fetch(API_ENDPOINTS.QUERY_STREAM, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: abortControllerRef.current.signal,
      });

      if (!res.ok) {
        throw new Error('Failed to query');
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let fullAnswer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullAnswer += chunk;
        pendingUpdateRef.current = fullAnswer;

        // Strip metadata from display during streaming
        const displayText = fullAnswer.split(METADATA_DELIMITER)[0];

        // Debounce state updates to reduce re-renders during fast streams
        const now = Date.now();
        if (now - lastUpdateRef.current >= DEBOUNCE_MS) {
          lastUpdateRef.current = now;
          setResponse(displayText);
        } else if (!rafIdRef.current) {
          rafIdRef.current = requestAnimationFrame(flushUpdate);
        }
      }

      // Parse metadata from the final content
      const delimIdx = fullAnswer.indexOf(METADATA_DELIMITER);
      if (delimIdx !== -1) {
        const answerText = fullAnswer.substring(0, delimIdx);
        const metaJson = fullAnswer.substring(delimIdx + METADATA_DELIMITER.length);
        setResponse(answerText);
        try {
          const parsed: StreamingMetadata = JSON.parse(metaJson);
          setQueryLog(toQueryLog(parsed));
        } catch {
          // Metadata parse failed — show answer without metrics
        }
      } else {
        setResponse(fullAnswer);
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Stream cancelled by user — no action needed
      } else {
        setResponse(MESSAGES.QUERY_ERROR);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    }
  };

  const stopQuery = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const clearResponse = () => {
    setResponse('');
    setQueryLog(null);
  };

  return {
    response,
    isStreaming,
    queryLog,
    queryDocument,
    stopQuery,
    clearResponse,
  };
};
