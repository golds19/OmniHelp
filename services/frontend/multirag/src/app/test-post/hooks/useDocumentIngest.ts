import { useState, useCallback } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';

export const useDocumentIngest = () => {
  const [ingested, setIngested] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  const [isPending, setIsPending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const ingestDocument = useCallback(async (file: File | null) => {
    if (!file) {
      return;
    }

    setIngestStatus('');
    setIsPending(true);

    try {
      const MAX_SIZE_MB = 10;
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        throw new Error(`File too large. Maximum size is ${MAX_SIZE_MB} MB.`);
      }

      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(API_ENDPOINTS.INGEST, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setIngested(true);
        setSessionId(data.session_id ?? null);
        setIngestStatus(MESSAGES.INGEST_SUCCESS);
      } else {
        setIngestStatus(data.detail || 'Ingestion failed.');
      }
    } catch (err) {
      setIngestStatus(err instanceof Error ? err.message : MESSAGES.INGEST_ERROR);
    } finally {
      setIsPending(false);
    }
  }, []);

  const resetIngestStatus = useCallback(() => {
    setIngested(false);
    setIngestStatus('');
    setSessionId(null);
  }, []);

  return {
    ingested,
    ingestStatus,
    isPending,
    sessionId,
    ingestDocument,
    resetIngestStatus,
  };
};
