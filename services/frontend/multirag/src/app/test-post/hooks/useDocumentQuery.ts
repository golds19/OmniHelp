import { useState, useRef, useCallback } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';

const DEBOUNCE_MS = 50;

export const useDocumentQuery = () => {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
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

  const queryDocument = async (question: string) => {
    setResponse('');
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

        // Debounce updates to reduce re-renders
        const now = Date.now();
        if (now - lastUpdateRef.current >= DEBOUNCE_MS) {
          lastUpdateRef.current = now;
          setResponse(fullAnswer);
        } else if (!rafIdRef.current) {
          rafIdRef.current = requestAnimationFrame(flushUpdate);
        }
      }

      // Ensure final content is displayed
      setResponse(fullAnswer);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Stream was aborted by user - no action needed
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
  };

  return {
    response,
    isStreaming,
    queryDocument,
    stopQuery,
    clearResponse,
  };
};
