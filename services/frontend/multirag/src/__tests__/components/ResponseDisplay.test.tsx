/**
 * Tests for ResponseDisplay component
 */
import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ResponseDisplay } from '../../app/test-post/components/ResponseDisplay';
import type { QueryLog } from '@/types/api';

const sampleLog: QueryLog = {
  id: 1,
  document_id: null,
  timestamp: '2024-01-01T00:00:00Z',
  query: 'What is machine learning?',
  answer_length: 120,
  num_text_chunks: 3,
  num_images: 1,
  top_similarity: 0.85,
  confidence: 0.82,
  answer_source_similarity: 0.75,
  is_hallucination: false,
  rejected: false,
  source_pages: [3, 7, 12],
  latency_ms: 1234,
};

describe('ResponseDisplay', () => {
  const defaultProps = {
    response: '',
    queryLog: null,
    isStreaming: false,
    ingested: false,
  };

  describe('rendering conditions', () => {
    it('should render nothing when response is empty and not ingested', () => {
      const { container } = render(<ResponseDisplay {...defaultProps} />);

      expect(container.firstChild).toBeNull();
    });

    it('should render when ingested is true even without response', () => {
      render(<ResponseDisplay {...defaultProps} ingested={true} />);

      expect(screen.getByText('Answer')).toBeInTheDocument();
    });

    it('should render when response is present', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="This is a test response"
        />
      );

      expect(screen.getByText('This is a test response')).toBeInTheDocument();
    });
  });

  describe('response display', () => {
    it('should display response text', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Machine learning is a subset of AI."
          ingested={true}
        />
      );

      expect(screen.getByText('Machine learning is a subset of AI.')).toBeInTheDocument();
    });

    it('should show placeholder when no response but ingested', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          ingested={true}
        />
      );

      expect(screen.getByText('Your answer will appear here...')).toBeInTheDocument();
    });
  });

  describe('streaming indicator', () => {
    it('should show streaming indicator when isStreaming is true', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Partial response..."
          isStreaming={true}
          ingested={true}
        />
      );

      expect(screen.getByTestId('streaming-indicator')).toBeInTheDocument();
    });

    it('should not show streaming indicator when isStreaming is false', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Complete response"
          isStreaming={false}
          ingested={true}
        />
      );

      expect(screen.queryByTestId('streaming-indicator')).not.toBeInTheDocument();
    });
  });

  describe('metadata display', () => {
    it('should not render metadata row when queryLog is null', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={null}
          ingested={true}
        />
      );

      expect(screen.queryByText(/82%/)).not.toBeInTheDocument();
      expect(screen.queryByText('Pages:')).not.toBeInTheDocument();
    });

    it('should not render metadata row while streaming', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={sampleLog}
          isStreaming={true}
          ingested={true}
        />
      );

      expect(screen.queryByText('82% confidence')).not.toBeInTheDocument();
    });

    it('should render confidence badge when queryLog is provided', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={sampleLog}
          isStreaming={false}
          ingested={true}
        />
      );

      expect(screen.getByText('82% confidence')).toBeInTheDocument();
    });

    it('should render source page chips', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={sampleLog}
          isStreaming={false}
          ingested={true}
        />
      );

      const pagesContainer = screen.getByTestId('source-pages');
      expect(within(pagesContainer).getByText('3')).toBeInTheDocument();
      expect(within(pagesContainer).getByText('7')).toBeInTheDocument();
      expect(within(pagesContainer).getByText('12')).toBeInTheDocument();
    });

    it('should render latency rounded to 1 decimal', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={sampleLog}
          isStreaming={false}
          ingested={true}
        />
      );

      expect(screen.getByText('1.2s')).toBeInTheDocument();
    });

    it('should render hallucination warning when is_hallucination is true', () => {
      const hallucinationLog = { ...sampleLog, is_hallucination: true };

      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={hallucinationLog}
          isStreaming={false}
          ingested={true}
        />
      );

      expect(screen.getByText(/Low groundedness/)).toBeInTheDocument();
    });

    it('should not render hallucination warning when is_hallucination is false', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={sampleLog}
          isStreaming={false}
          ingested={true}
        />
      );

      expect(screen.queryByText(/Low groundedness/)).not.toBeInTheDocument();
    });

    it('should not render source chips when source_pages is empty', () => {
      const logNoPages = { ...sampleLog, source_pages: [] };

      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={logNoPages}
          isStreaming={false}
          ingested={true}
        />
      );

      expect(screen.queryByText('Pages:')).not.toBeInTheDocument();
    });
  });

  describe('confidence color thresholds', () => {
    it('should render confidence for high confidence (>=0.7)', () => {
      const highConfLog = { ...sampleLog, confidence: 0.85 };

      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={highConfLog}
          ingested={true}
        />
      );

      expect(screen.getByText('85% confidence')).toBeInTheDocument();
    });

    it('should render confidence for medium confidence (0.4-0.7)', () => {
      const midConfLog = { ...sampleLog, confidence: 0.55 };

      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={midConfLog}
          ingested={true}
        />
      );

      expect(screen.getByText('55% confidence')).toBeInTheDocument();
    });

    it('should render confidence for low confidence (<0.4)', () => {
      const lowConfLog = { ...sampleLog, confidence: 0.25 };

      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          queryLog={lowConfLog}
          ingested={true}
        />
      );

      expect(screen.getByText('25% confidence')).toBeInTheDocument();
    });
  });
});
