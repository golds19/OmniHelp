/**
 * Tests for ResponseDisplay component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { ResponseDisplay } from '../../app/test-post/components/ResponseDisplay';
import type { QueryResponse } from '@/types/api';

describe('ResponseDisplay', () => {
  const defaultProps = {
    response: '',
    metadata: null,
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

      expect(screen.getByText('Streaming...')).toBeInTheDocument();
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

      expect(screen.queryByText('Streaming...')).not.toBeInTheDocument();
    });
  });

  describe('metadata display', () => {
    const sampleMetadata: QueryResponse = {
      answer: 'Test answer',
      sources: [
        { page: 1, type: 'text' },
        { page: 2, type: 'image' },
      ],
      num_images: 1,
      num_text_chunks: 3,
      agent_type: 'ReAct',
    };

    it('should display metadata when present', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={sampleMetadata}
          ingested={true}
        />
      );

      expect(screen.getByText('3 text chunks')).toBeInTheDocument();
    });

    it('should display text chunks count', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={sampleMetadata}
          ingested={true}
        />
      );

      expect(screen.getByText('3 text chunks')).toBeInTheDocument();
    });

    it('should display images count', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={sampleMetadata}
          ingested={true}
        />
      );

      expect(screen.getByText('1 images')).toBeInTheDocument();
    });

    it('should display total sources count', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={sampleMetadata}
          ingested={true}
        />
      );

      expect(screen.getByText('2 sources')).toBeInTheDocument();
    });

    it('should display agent type', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={sampleMetadata}
          ingested={true}
        />
      );

      expect(screen.getByText('ReAct')).toBeInTheDocument();
    });

    it('should display source references', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={sampleMetadata}
          ingested={true}
        />
      );

      expect(screen.getByText(/Page 1/)).toBeInTheDocument();
      expect(screen.getByText(/Page 2/)).toBeInTheDocument();
    });

    it('should not display metadata section when metadata is null', () => {
      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={null}
          ingested={true}
        />
      );

      expect(screen.queryByText(/text chunks/)).not.toBeInTheDocument();
    });
  });

  describe('empty sources handling', () => {
    it('should not show sources section when sources array is empty', () => {
      const metadataNoSources: QueryResponse = {
        answer: 'Test answer',
        sources: [],
        num_images: 0,
        num_text_chunks: 0,
        agent_type: 'ReAct',
      };

      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={metadataNoSources}
          ingested={true}
        />
      );

      expect(screen.queryByText(/Page/)).not.toBeInTheDocument();
    });
  });

  describe('agent type fallback', () => {
    it('should show N/A when agent_type is undefined', () => {
      const metadataNoAgent: QueryResponse = {
        answer: 'Test answer',
        sources: [],
        num_images: 0,
        num_text_chunks: 0,
      };

      render(
        <ResponseDisplay
          {...defaultProps}
          response="Test response"
          metadata={metadataNoAgent}
          ingested={true}
        />
      );

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });
});
