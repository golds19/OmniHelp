/**
 * Tests for FileUploadSection component.
 * Covers drag-and-drop behaviour, accept attribute, and ingested state rendering.
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { FileUploadSection } from '../../app/test-post/components/FileUploadSection';

const defaultProps = {
  file: null,
  isPending: false,
  ingested: false,
  ingestStatus: '',
  onFileChange: jest.fn(),
  onFileDrop: jest.fn(),
  onIngest: jest.fn(),
};

describe('FileUploadSection', () => {
  beforeEach(() => jest.clearAllMocks());

  // ── Initial render ────────────────────────────────────────────────────────

  describe('initial render', () => {
    it('shows drop zone placeholder text', () => {
      render(<FileUploadSection {...defaultProps} />);
      expect(screen.getByText('Drop a PDF or image here')).toBeInTheDocument();
    });

    it('file input accepts pdf, png, jpg, and jpeg', () => {
      render(<FileUploadSection {...defaultProps} />);
      const inputs = document.querySelectorAll('input[type="file"]');
      // There is one input in the pre-ingestion form
      expect(inputs.length).toBeGreaterThanOrEqual(1);
      inputs.forEach((input) => {
        expect((input as HTMLInputElement).accept).toBe('.pdf,.png,.jpg,.jpeg');
      });
    });

    it('does not show ingest button when no file selected', () => {
      render(<FileUploadSection {...defaultProps} />);
      expect(screen.queryByText('Ingest document')).not.toBeInTheDocument();
    });
  });

  // ── Drag-and-drop ────────────────────────────────────────────────────────

  describe('drag-and-drop behaviour', () => {
    function getDropZone() {
      // The dashed-border div wraps the upload content
      return document.querySelector('.border-dashed') as HTMLElement;
    }

    it('changes text to "Release to upload" on dragOver', () => {
      render(<FileUploadSection {...defaultProps} />);
      fireEvent.dragOver(getDropZone());
      expect(screen.getByText('Release to upload')).toBeInTheDocument();
    });

    it('reverts to default text on dragLeave', () => {
      render(<FileUploadSection {...defaultProps} />);
      fireEvent.dragOver(getDropZone());
      fireEvent.dragLeave(getDropZone());
      expect(screen.getByText('Drop a PDF or image here')).toBeInTheDocument();
    });

    it('calls onFileDrop with the dropped file', () => {
      const onFileDrop = jest.fn();
      render(<FileUploadSection {...defaultProps} onFileDrop={onFileDrop} />);

      const mockFile = new File(['content'], 'figure.png', { type: 'image/png' });
      fireEvent.drop(getDropZone(), {
        dataTransfer: { files: [mockFile] },
      });

      expect(onFileDrop).toHaveBeenCalledTimes(1);
      expect(onFileDrop).toHaveBeenCalledWith(mockFile);
    });

    it('does not call onFileDrop when isPending is true', () => {
      const onFileDrop = jest.fn();
      render(<FileUploadSection {...defaultProps} isPending={true} onFileDrop={onFileDrop} />);

      const mockFile = new File(['content'], 'figure.png', { type: 'image/png' });
      fireEvent.drop(getDropZone(), {
        dataTransfer: { files: [mockFile] },
      });

      expect(onFileDrop).not.toHaveBeenCalled();
    });

    it('reverts dragActive after drop', () => {
      render(<FileUploadSection {...defaultProps} />);
      fireEvent.dragOver(getDropZone());
      expect(screen.getByText('Release to upload')).toBeInTheDocument();

      const mockFile = new File(['x'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.drop(getDropZone(), { dataTransfer: { files: [mockFile] } });

      // After drop dragActive should be false — text should not show "Release to upload"
      // (note: after drop the file prop hasn't changed since onFileDrop is mocked,
      //  so the placeholder is visible again)
      expect(screen.queryByText('Release to upload')).not.toBeInTheDocument();
    });
  });

  // ── Ingested state ───────────────────────────────────────────────────────

  describe('ingested state', () => {
    it('renders compact filename strip when ingested=true', () => {
      const file = new File(['x'], 'paper.pdf', { type: 'application/pdf' });
      render(<FileUploadSection {...defaultProps} ingested={true} file={file} />);

      expect(screen.getByText('paper.pdf')).toBeInTheDocument();
      expect(screen.getByText('Change')).toBeInTheDocument();
    });

    it('does not show the drop zone when ingested=true', () => {
      const file = new File(['x'], 'paper.pdf', { type: 'application/pdf' });
      render(<FileUploadSection {...defaultProps} ingested={true} file={file} />);

      expect(screen.queryByText('Drop a PDF or image here')).not.toBeInTheDocument();
      expect(document.querySelector('.border-dashed')).not.toBeInTheDocument();
    });
  });
});
