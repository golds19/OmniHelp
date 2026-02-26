import { useState, useRef, useCallback } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';
import type { QueryLog, EvalLogsResponse } from '@/types/api';

const DEBOUNCE_MS = 50;

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
      setResponse(pendingUpdateRef.current);
    }
    rafIdRef.current = null;
  }, []);

  // Fire-and-forget: fetches the latest eval log after a short delay to allow
  // the backend's finally block to write to SQLite before we read it back.
  const fetchQueryLog = useCallback(async (question: string) => {
    await new Promise<void>(r => setTimeout(r, 300));
    try {
      const logRes = await fetch(`${API_ENDPOINTS.EVAL_LOGS}?limit=1`);
      if (logRes.ok) {
        const data: EvalLogsResponse = await logRes.json();
        if (data.logs.length > 0 && data.logs[0].query === question) {
          setQueryLog(data.logs[0]);
        }
      }
    } catch {
      // Non-fatal — metadata display is best-effort
    }
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

        // Debounce state updates to reduce re-renders during fast streams
        const now = Date.now();
        if (now - lastUpdateRef.current >= DEBOUNCE_MS) {
          lastUpdateRef.current = now;
          setResponse(fullAnswer);
        } else if (!rafIdRef.current) {
          rafIdRef.current = requestAnimationFrame(flushUpdate);
        }
      }

      // Ensure final content is rendered
      setResponse(fullAnswer);

      // Fetch eval log asynchronously — does not block isStreaming reset
      void fetchQueryLog(question);
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
