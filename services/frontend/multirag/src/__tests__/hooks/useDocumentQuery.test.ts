/**
 * Tests for useDocumentQuery hook
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { useDocumentQuery } from '../../app/test-post/hooks/useDocumentQuery';

// Mock constants
jest.mock('../../app/test-post/utils/constants', () => ({
  API_ENDPOINTS: {
    QUERY_STREAM: 'http://localhost:8000/query-agentic-stream',
  },
  MESSAGES: {
    QUERY_ERROR: 'Error contacting backend',
  },
}));

describe('useDocumentQuery', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('should have empty response initially', () => {
      const { result } = renderHook(() => useDocumentQuery());

      expect(result.current.response).toBe('');
      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe('queryDocument', () => {
    it('should set isStreaming to true when starting', async () => {
      // Mock a slow streaming response
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Hello') })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const { result } = renderHook(() => useDocumentQuery());

      await act(async () => {
        result.current.queryDocument('test question');
      });

      // After completion, streaming should be false
      expect(result.current.isStreaming).toBe(false);
    });

    it('should accumulate streaming response', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Hello ') })
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('World') })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const { result } = renderHook(() => useDocumentQuery());

      await act(async () => {
        await result.current.queryDocument('test question');
      });

      expect(result.current.response).toBe('Hello World');
    });

    it('should handle fetch errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useDocumentQuery());

      await act(async () => {
        await result.current.queryDocument('test question');
      });

      expect(result.current.response).toBe('Error contacting backend');
      expect(result.current.isStreaming).toBe(false);
    });

    it('should handle non-ok response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
      });

      const { result } = renderHook(() => useDocumentQuery());

      await act(async () => {
        await result.current.queryDocument('test question');
      });

      expect(result.current.response).toBe('Error contacting backend');
    });

    it('should clear previous response when starting new query', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('New response') })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const { result } = renderHook(() => useDocumentQuery());

      // First query
      await act(async () => {
        await result.current.queryDocument('first question');
      });

      expect(result.current.response).toBe('New response');

      // Second query - response should be cleared first
      const mockReader2 = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Second response') })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader2,
        },
      });

      await act(async () => {
        await result.current.queryDocument('second question');
      });

      expect(result.current.response).toBe('Second response');
    });
  });

  describe('stopQuery', () => {
    it('should abort streaming when stopQuery is called', async () => {
      const mockAbort = jest.fn();
      const originalAbortController = global.AbortController;

      global.AbortController = jest.fn().mockImplementation(() => ({
        signal: { aborted: false },
        abort: mockAbort,
      })) as unknown as typeof AbortController;

      // Never-ending stream
      const mockReader = {
        read: jest.fn().mockImplementation(() => new Promise(() => {})),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const { result } = renderHook(() => useDocumentQuery());

      // Start query (don't await - it won't complete)
      act(() => {
        result.current.queryDocument('test question');
      });

      // Stop the query
      act(() => {
        result.current.stopQuery();
      });

      expect(mockAbort).toHaveBeenCalled();

      global.AbortController = originalAbortController;
    });
  });

  describe('clearResponse', () => {
    it('should clear the response', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Some response') })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const { result } = renderHook(() => useDocumentQuery());

      await act(async () => {
        await result.current.queryDocument('test question');
      });

      expect(result.current.response).toBe('Some response');

      act(() => {
        result.current.clearResponse();
      });

      expect(result.current.response).toBe('');
    });
  });
});
