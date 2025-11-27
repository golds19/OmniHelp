import { useState, useRef } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';

export const useDocumentQuery = () => {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const queryDocument = async (question: string) => {
    console.log('🔍 Querying with input:', question);
    setResponse('');
    setIsStreaming(true);

    abortControllerRef.current = new AbortController();

    try {
      console.log('📤 Sending POST request to /query-agentic-stream');
      const res = await fetch(API_ENDPOINTS.QUERY_STREAM, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: abortControllerRef.current.signal,
      });

      console.log('📥 Stream response status:', res.status);

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
        setResponse(fullAnswer);
      }

      console.log('✅ Streaming complete');
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log(MESSAGES.STREAM_ABORTED);
      } else {
        console.error('🔥 Query error:', err);
        setResponse(MESSAGES.QUERY_ERROR);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
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
