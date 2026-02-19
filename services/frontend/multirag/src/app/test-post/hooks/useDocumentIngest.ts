import { useState, useCallback } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';

export const useDocumentIngest = () => {
  const [ingested, setIngested] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  const [isPending, setIsPending] = useState(false);

  const ingestDocument = useCallback(async (file: File | null) => {
    if (!file) {
      return;
    }

    setIngestStatus('');
    setIsPending(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(API_ENDPOINTS.INGEST, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setIngested(true);
        setIngestStatus(MESSAGES.INGEST_SUCCESS);
      } else {
        setIngestStatus(data.detail || 'Ingestion failed.');
      }
    } catch {
      setIngestStatus(MESSAGES.INGEST_ERROR);
    } finally {
      setIsPending(false);
    }
  }, []);

  const resetIngestStatus = useCallback(() => {
    setIngested(false);
    setIngestStatus('');
  }, []);

  return {
    ingested,
    ingestStatus,
    isPending,
    ingestDocument,
    resetIngestStatus,
  };
};
