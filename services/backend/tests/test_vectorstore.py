"""
Tests for vector store creation and management.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestVectorStore:
    """Tests for the VectorStore class."""

    def test_create_faiss_vectorstore(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that FAISS vector store is created successfully."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get, \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS:

            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            mock_store = MagicMock()
            MockFAISS.from_embeddings.return_value = mock_store

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents
            )

            result = vs.create_faiss_vectorstore()

            # FAISS.from_embeddings should be called
            MockFAISS.from_embeddings.assert_called_once()
            assert result == mock_store

    def test_create_faiss_with_correct_text_embeddings(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that FAISS receives correct text-embedding pairs."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get, \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS:

            mock_embedder = MagicMock()
            mock_get.return_value = mock_embedder

            MockFAISS.from_embeddings.return_value = MagicMock()

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents
            )

            vs.create_faiss_vectorstore()

            # Verify text_embeddings argument
            call_kwargs = MockFAISS.from_embeddings.call_args[1]
            text_embeddings = call_kwargs['text_embeddings']

            assert len(text_embeddings) == len(sample_documents)
            for (text, emb), doc in zip(text_embeddings, sample_documents):
                assert text == doc.page_content

    def test_create_bm25_retriever(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that BM25 retriever is created from text documents."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get, \
             patch('app.rag.core.vectorstore.BM25Retriever') as MockBM25:

            mock_embedder = MagicMock()
            mock_get.return_value = mock_embedder

            mock_retriever = MagicMock()
            MockBM25.from_documents.return_value = mock_retriever

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents
            )

            result = vs.create_bm25_retriever()

            MockBM25.from_documents.assert_called_once_with(sample_documents)
            assert result == mock_retriever

    def test_create_bm25_returns_none_for_empty_docs(self, sample_embeddings, sample_image_data_store):
        """Test that BM25 creation returns None when no text documents."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=[],
                all_embeddings=[],
                image_data_store=sample_image_data_store,
                text_docs=[]  # Empty text docs
            )

            result = vs.create_bm25_retriever()

            assert result is None

    def test_create_hybrid_retrievers_returns_dict(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that create_hybrid_retrievers returns dict with all components."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get, \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS, \
             patch('app.rag.core.vectorstore.BM25Retriever') as MockBM25:

            mock_embedder = MagicMock()
            mock_get.return_value = mock_embedder

            mock_faiss = MagicMock()
            MockFAISS.from_embeddings.return_value = mock_faiss

            mock_bm25 = MagicMock()
            MockBM25.from_documents.return_value = mock_bm25

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents
            )

            result = vs.create_hybrid_retrievers()

            # Verify all keys present
            assert 'faiss_store' in result
            assert 'bm25_retriever' in result
            assert 'image_data_store' in result

            assert result['faiss_store'] == mock_faiss
            assert result['bm25_retriever'] == mock_bm25
            assert result['image_data_store'] == sample_image_data_store

    def test_create_vectorstore_backward_compat(self, sample_documents, sample_embeddings, sample_image_data_store):
        """Test that create_vectorstore (old API) still works."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get, \
             patch('app.rag.core.vectorstore.FAISS') as MockFAISS:

            mock_embedder = MagicMock()
            mock_get.return_value = mock_embedder

            mock_store = MagicMock()
            MockFAISS.from_embeddings.return_value = mock_store

            from app.rag.core.vectorstore import VectorStore

            vs = VectorStore(
                all_docs=sample_documents,
                all_embeddings=sample_embeddings,
                image_data_store=sample_image_data_store,
                text_docs=sample_documents
            )

            # Old method should still work
            result = vs.create_vectorstore()

            assert result == mock_store


class TestCLIPEmbeddingWrapper:
    """Tests for the CLIPEmbeddingWrapper class."""

    def test_wrapper_initializes_with_embedder(self):
        """Test that wrapper gets embedder on init."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import CLIPEmbeddingWrapper

            wrapper = CLIPEmbeddingWrapper()

            mock_get.assert_called_once()
            assert wrapper.embedder == mock_embedder

    def test_embed_documents_calls_embed_text_for_each(self):
        """Test that embed_documents processes each text."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.zeros(512, dtype=np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import CLIPEmbeddingWrapper

            wrapper = CLIPEmbeddingWrapper()
            texts = ["text1", "text2", "text3"]
            wrapper.embed_documents(texts)

            # Should call embed_text for each document
            assert mock_embedder.embed_text.call_count == 3

    def test_embed_query_uses_embed_text(self):
        """Test that embed_query uses embed_text method."""
        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.zeros(512, dtype=np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.vectorstore import CLIPEmbeddingWrapper

            wrapper = CLIPEmbeddingWrapper()
            wrapper.embed_query("test query")

            mock_embedder.embed_text.assert_called_once_with("test query")
