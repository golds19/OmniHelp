import { useState } from 'react';

export interface LibraryEntry {
  session_id: string;
  filename: string;
  ingested_at: string; // ISO timestamp
}

const STORAGE_KEY = 'lifeforge_docs';
const ACTIVE_KEY = 'lifeforge_active_session';

export const useDocumentLibrary = () => {
  const [documents, setDocuments] = useState<LibraryEntry[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]');
    } catch {
      return [];
    }
  });

  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(ACTIVE_KEY);
  });

  const addDocument = (session_id: string, filename: string) => {
    const entry: LibraryEntry = {
      session_id,
      filename,
      ingested_at: new Date().toISOString(),
    };
    setDocuments(prev => {
      const next = [...prev, entry];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
    localStorage.setItem(ACTIVE_KEY, session_id);
    setActiveSessionId(session_id);
  };

  const selectDocument = (session_id: string) => {
    localStorage.setItem(ACTIVE_KEY, session_id);
    setActiveSessionId(session_id);
  };

  const removeDocument = (session_id: string) => {
    setDocuments(prev => {
      const next = prev.filter(d => d.session_id !== session_id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
    if (activeSessionId === session_id) {
      localStorage.removeItem(ACTIVE_KEY);
      setActiveSessionId(null);
    }
  };

  return { documents, activeSessionId, addDocument, selectDocument, removeDocument };
};
