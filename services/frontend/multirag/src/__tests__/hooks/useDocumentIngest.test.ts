/**
 * Tests for useDocumentIngest hook
 */
import { renderHook, act } from '@testing-library/react';
import { useDocumentIngest } from '../../app/test-post/hooks/useDocumentIngest';

// Mock constants
jest.mock('../../app/test-post/utils/constants', () => ({
  API_ENDPOINTS: {
    INGEST: 'http://localhost:8000/ingest-agentic',
  },
  MESSAGES: {
    INGEST_SUCCESS: 'Document ingested successfully',
    INGEST_ERROR: 'Error contacting backend',
  },
}));

describe('useDocumentIngest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useDocumentIngest());

      expect(result.current.ingested).toBe(false);
      expect(result.current.ingestStatus).toBe('');
      expect(result.current.isPending).toBe(false);
    });
  });

  describe('ingestDocument', () => {
    it('should do nothing if file is null', async () => {
      const { result } = renderHook(() => useDocumentIngest());

      await act(async () => {
        await result.current.ingestDocument(null);
      });

      expect(global.fetch).not.toHaveBeenCalled();
      expect(result.current.ingested).toBe(false);
    });

    it('should set isPending during upload', async () => {
      let resolvePromise: (value: unknown) => void;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      (global.fetch as jest.Mock).mockReturnValue(pendingPromise);

      const { result } = renderHook(() => useDocumentIngest());
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      // Start ingest (don't await)
      act(() => {
        result.current.ingestDocument(mockFile);
      });

      expect(result.current.isPending).toBe(true);

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: () => Promise.resolve({ message: 'Success' }),
        });
      });

      expect(result.current.isPending).toBe(false);
    });

    it('should set ingested to true on success', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'Document processed' }),
      });

      const { result } = renderHook(() => useDocumentIngest());
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        await result.current.ingestDocument(mockFile);
      });

      expect(result.current.ingested).toBe(true);
      expect(result.current.ingestStatus).toBe('Document ingested successfully');
    });

    it('should set error status on failure', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Only PDF files are supported' }),
      });

      const { result } = renderHook(() => useDocumentIngest());
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

      await act(async () => {
        await result.current.ingestDocument(mockFile);
      });

      expect(result.current.ingested).toBe(false);
      expect(result.current.ingestStatus).toBe('Only PDF files are supported');
    });

    it('should set generic error on network failure', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useDocumentIngest());
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        await result.current.ingestDocument(mockFile);
      });

      expect(result.current.ingested).toBe(false);
      expect(result.current.ingestStatus).toBe('Error contacting backend');
    });

    it('should send file as FormData', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'Success' }),
      });

      const { result } = renderHook(() => useDocumentIngest());
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        await result.current.ingestDocument(mockFile);
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/ingest-agentic',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
    });
  });

  describe('resetIngestStatus', () => {
    it('should reset ingested and status', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'Success' }),
      });

      const { result } = renderHook(() => useDocumentIngest());
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      // First, ingest a document
      await act(async () => {
        await result.current.ingestDocument(mockFile);
      });

      expect(result.current.ingested).toBe(true);

      // Then reset
      act(() => {
        result.current.resetIngestStatus();
      });

      expect(result.current.ingested).toBe(false);
      expect(result.current.ingestStatus).toBe('');
    });
  });
});
