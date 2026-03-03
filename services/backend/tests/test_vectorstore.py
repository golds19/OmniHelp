"""
Tests for vector store creation and management.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestVectorStore:
    """Tests for the VectorStore class."""

    def test_create_faiss_vectorstore(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that the text FAISS store is created from text documents."""
        with patch('app.rag.core.vectorstore.get_embedder'), \
             patch('app.rag.core.vectorstore.get_text_embedder'), \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS:

            mock_store = MagicMock()
            MockFAISS.from_embeddings.return_value = mock_store

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents,
            )

            result = vs.create_faiss_vectorstore()

            MockFAISS.from_embeddings.assert_called_once()
            assert result == mock_store

    def test_create_faiss_with_correct_text_embeddings(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that FAISS receives correct text-embedding pairs for text documents."""
        with patch('app.rag.core.vectorstore.get_embedder'), \
             patch('app.rag.core.vectorstore.get_text_embedder'), \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS:

            MockFAISS.from_embeddings.return_value = MagicMock()

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents,
            )

            vs.create_faiss_vectorstore()

            call_kwargs = MockFAISS.from_embeddings.call_args[1]
            text_embeddings = call_kwargs['text_embeddings']

            assert len(text_embeddings) == len(sample_documents)
            for (text, emb), doc in zip(text_embeddings, sample_documents):
                assert text == doc.page_content

    def test_create_bm25_retriever(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that BM25 retriever is created from text documents."""
        with patch('app.rag.core.vectorstore.get_embedder'), \
             patch('app.rag.core.vectorstore.get_text_embedder'), \
             patch('app.rag.core.vectorstore.BM25Retriever') as MockBM25:

            mock_retriever = MagicMock()
            MockBM25.from_documents.return_value = mock_retriever

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents,
            )

            result = vs.create_bm25_retriever()

            MockBM25.from_documents.assert_called_once_with(sample_documents)
            assert result == mock_retriever

    def test_create_bm25_returns_none_for_empty_docs(self, sample_embeddings, sample_image_data_store):
        """Test that BM25 creation returns None when no text documents."""
        with patch('app.rag.core.vectorstore.get_embedder'), \
             patch('app.rag.core.vectorstore.get_text_embedder'):

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=[],
                all_embeddings=[],
                image_data_store=sample_image_data_store,
                text_docs=[],
            )

            result = vs.create_bm25_retriever()

            assert result is None

    def test_create_hybrid_retrievers_returns_dict(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that create_hybrid_retrievers returns dict with all expected keys."""
        with patch('app.rag.core.vectorstore.get_embedder'), \
             patch('app.rag.core.vectorstore.get_text_embedder'), \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS, \
             patch('app.rag.core.vectorstore.BM25Retriever') as MockBM25:

            mock_faiss = MagicMock()
            MockFAISS.from_embeddings.return_value = mock_faiss

            mock_bm25 = MagicMock()
            MockBM25.from_documents.return_value = mock_bm25

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents,
            )

            result = vs.create_hybrid_retrievers()

            assert 'text_faiss_store' in result
            assert 'image_faiss_store' in result
            assert 'bm25_retriever' in result
            assert 'image_data_store' in result

            assert result['text_faiss_store'] == mock_faiss
            assert result['bm25_retriever'] == mock_bm25
            assert result['image_data_store'] == sample_image_data_store

    def test_create_vectorstore_backward_compat(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that create_vectorstore (old API) still works via the shim."""
        with patch('app.rag.core.vectorstore.get_embedder'), \
             patch('app.rag.core.vectorstore.get_text_embedder'), \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS:

            mock_store = MagicMock()
            MockFAISS.from_embeddings.return_value = mock_store

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents,
            )

            result = vs.create_vectorstore()

            assert result == mock_store


class TestCLIPEmbeddingWrapper:
    """Tests for the CLIPEmbeddingWrapper class (image FAISS queries)."""

    def test_wrapper_initializes_with_embedder(self):
        """Test that wrapper gets CLIP embedder on init."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import CLIPEmbeddingWrapper

            wrapper = CLIPEmbeddingWrapper()

            mock_get.assert_called_once()
            assert wrapper.embedder == mock_embedder

    def test_embed_documents_calls_embed_text_for_each(self):
        """Test that embed_documents calls embed_text for each document."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.zeros(512, dtype=np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import CLIPEmbeddingWrapper

            wrapper = CLIPEmbeddingWrapper()
            texts = ["text1", "text2", "text3"]
            wrapper.embed_documents(texts)

            assert mock_embedder.embed_text.call_count == 3

    def test_embed_query_uses_embed_text(self):
        """Test that embed_query uses CLIP embed_text."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.zeros(512, dtype=np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import CLIPEmbeddingWrapper

            wrapper = CLIPEmbeddingWrapper()
            wrapper.embed_query("test query")

            mock_embedder.embed_text.assert_called_once_with("test query")


class TestSentenceTransformerEmbeddingWrapper:
    """Tests for the SentenceTransformerEmbeddingWrapper class (text FAISS queries)."""

    def test_embed_query_returns_384_dim_list(self):
        """Test that embed_query returns a 384-dim float list."""
        with patch('app.rag.core.vectorstore.get_text_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.encode.return_value = np.zeros(384, dtype=np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import SentenceTransformerEmbeddingWrapper

            wrapper = SentenceTransformerEmbeddingWrapper()
            result = wrapper.embed_query("test query")

            assert isinstance(result, list)
            assert len(result) == 384
            mock_embedder.encode.assert_called_once_with("test query", normalize_embeddings=True)

    def test_embed_documents_calls_encode_batch(self):
        """Test that embed_documents uses encode_batch for efficiency."""
        with patch('app.rag.core.vectorstore.get_text_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.encode_batch.return_value = np.zeros((3, 384), dtype=np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import SentenceTransformerEmbeddingWrapper

            wrapper = SentenceTransformerEmbeddingWrapper()
            texts = ["text1", "text2", "text3"]
            result = wrapper.embed_documents(texts)

            mock_embedder.encode_batch.assert_called_once_with(texts, normalize_embeddings=True)
            assert len(result) == 3
