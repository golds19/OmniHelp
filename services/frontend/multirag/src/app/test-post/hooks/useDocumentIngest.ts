import { useState, useTransition } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';

export const useDocumentIngest = () => {
  const [ingested, setIngested] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  const [isPending, startTransition] = useTransition();

  const ingestDocument = async (file: File | null) => {
    if (!file) {
      console.warn(MESSAGES.NO_FILE);
      return;
    }

    console.log('🚀 Starting ingestion for:', file.name);
    setIngestStatus('');

    startTransition(async () => {
      try {
        const formData = new FormData();
        formData.append('file', file);

        console.log('📤 Sending POST request to /ingest-agentic');
        const res = await fetch(API_ENDPOINTS.INGEST, {
          method: 'POST',
          body: formData,
        });

        console.log('📥 Response status:', res.status);
        const data = await res.json();
        console.log('📦 Response data:', data);

        if (res.ok) {
          setIngested(true);
          setIngestStatus(MESSAGES.INGEST_SUCCESS);
          console.log('✅ Ingestion successful');
        } else {
          setIngestStatus(data.detail || 'Ingestion failed.');
          console.error('❌ Ingestion failed:', data.detail);
        }
      } catch (err) {
        console.error('🔥 Ingestion error:', err);
        setIngestStatus(MESSAGES.INGEST_ERROR);
      }
    });
  };

  const resetIngestStatus = () => {
    setIngested(false);
    setIngestStatus('');
  };

  return {
    ingested,
    ingestStatus,
    isPending,
    ingestDocument,
    resetIngestStatus,
  };
};
