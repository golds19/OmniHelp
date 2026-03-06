"""
Tests for DataEmbedding.process_and_embed_image_file().

Covers standalone PNG/JPG ingestion — no text extraction, image-only FAISS index.
Uses conftest fixtures: mock_embedder (CLIP, 512-dim) and mock_get_embedder.
"""
import os
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-placeholder")

import io
import base64
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from PIL import Image


def _make_tiny_png_bytes() -> bytes:
    """Return valid 1×1 red PNG bytes for use as a test image file."""
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _patch_embedders(mock_embedder):
    """Context manager that patches both get_embedder and get_text_embedder in data_ingestion."""
    return patch.multiple(
        'app.rag.core.data_ingestion',
        get_embedder=lambda: mock_embedder,
        get_text_embedder=lambda: MagicMock(),
    )


class TestProcessAndEmbedImageFile:

    def test_returns_single_image_doc(self, tmp_path, mock_embedder, mock_get_embedder):
        """Returns exactly 1 Document with type='image' and correct metadata."""
        from app.rag.core.data_ingestion import DataEmbedding

        img_path = tmp_path / "test.png"
        img_path.write_bytes(_make_tiny_png_bytes())

        with _patch_embedders(mock_embedder):
            embedder = DataEmbedding(pdf_path=str(img_path))
            docs, _, _, _ = embedder.process_and_embed_image_file()

        assert len(docs) == 1
        assert docs[0].metadata["type"] == "image"
        assert docs[0].metadata["image_id"] == "page_0_img_0"
        assert docs[0].metadata["page"] == 0

    def test_stores_valid_base64_png_in_image_data_store(self, tmp_path, mock_embedder, mock_get_embedder):
        """image_data_store contains the image as a valid base64-encoded PNG."""
        from app.rag.core.data_ingestion import DataEmbedding

        img_path = tmp_path / "test.png"
        img_path.write_bytes(_make_tiny_png_bytes())

        with _patch_embedders(mock_embedder):
            embedder = DataEmbedding(pdf_path=str(img_path))
            _, _, img_store, _ = embedder.process_and_embed_image_file()

        assert "page_0_img_0" in img_store
        raw = base64.b64decode(img_store["page_0_img_0"])
        assert raw[:4] == b"\x89PNG"  # PNG magic bytes — valid PNG

    def test_embedding_is_512_dim(self, tmp_path, mock_embedder, mock_get_embedder):
        """CLIP embedding is 512-dimensional (matches image FAISS index dimension)."""
        from app.rag.core.data_ingestion import DataEmbedding

        img_path = tmp_path / "test.png"
        img_path.write_bytes(_make_tiny_png_bytes())

        with _patch_embedders(mock_embedder):
            embedder = DataEmbedding(pdf_path=str(img_path))
            _, embeddings, _, _ = embedder.process_and_embed_image_file()

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 512

    def test_text_docs_is_empty(self, tmp_path, mock_embedder, mock_get_embedder):
        """No text documents are produced — BM25 retriever will receive an empty list."""
        from app.rag.core.data_ingestion import DataEmbedding

        img_path = tmp_path / "test.png"
        img_path.write_bytes(_make_tiny_png_bytes())

        with _patch_embedders(mock_embedder):
            embedder = DataEmbedding(pdf_path=str(img_path))
            _, _, _, text_docs = embedder.process_and_embed_image_file()

        assert text_docs == []

    def test_all_docs_contains_image_doc(self, tmp_path, mock_embedder, mock_get_embedder):
        """all_docs list contains the image document (used for FAISS index construction)."""
        from app.rag.core.data_ingestion import DataEmbedding

        img_path = tmp_path / "test.png"
        img_path.write_bytes(_make_tiny_png_bytes())

        with _patch_embedders(mock_embedder):
            embedder = DataEmbedding(pdf_path=str(img_path))
            docs, embeddings, img_store, _ = embedder.process_and_embed_image_file()

        # all_docs and embeddings must be parallel lists
        assert len(docs) == len(embeddings)
        assert docs[0].page_content == "[Image: page_0_img_0]"
