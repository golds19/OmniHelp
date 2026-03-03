"""
Tests for the retrieval logic — the most critical RAG component.
Tests both dense-only and hybrid retrieval paths.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import Dict


@dataclass
class MockDocument:
    """Mock LangChain document for testing."""
    page_content: str
    metadata: Dict


class TestMultiModalRetrieval:
    """Tests for the MultiModalRetrieval wrapper class."""

    def test_dense_only_retrieval_when_bm25_is_none(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that retrieval works with text FAISS only when BM25 is None."""
        with patch('app.rag.core.retriever.get_text_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.encode.return_value = np.random.randn(384).astype(np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.retriever import MultiModalRetrieval

            retriever = MultiModalRetrieval(
                query="test query",
                text_vectorStore=mock_faiss_vectorstore,
                image_data_store=sample_image_data_store,
                k=3,
                bm25_retriever=None,
                use_hybrid=True,
            )

            results = retriever.retrieve_multimodal()

            assert results is not None
            assert "docs" in results
            assert "top_similarity" in results
            assert len(results["docs"]) <= 3
            mock_faiss_vectorstore.similarity_search_with_score_by_vector.assert_called_once()

    def test_retrieval_respects_k_parameter(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that retrieval respects the k parameter."""
        with patch('app.rag.core.retriever.get_text_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.encode.return_value = np.random.randn(384).astype(np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.retriever import MultiModalRetrieval

            for k in [1, 3, 5]:
                mock_faiss_vectorstore.similarity_search_with_score_by_vector.reset_mock()

                retriever = MultiModalRetrieval(
                    query="test query",
                    text_vectorStore=mock_faiss_vectorstore,
                    image_data_store=sample_image_data_store,
                    k=k,
                    bm25_retriever=None,
                    use_hybrid=False,
                )

                retriever.retrieve_multimodal()

                call_kwargs = mock_faiss_vectorstore.similarity_search_with_score_by_vector.call_args[1]
                assert call_kwargs['k'] == k

    def test_embedding_converted_to_list(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that the numpy embedding is converted to list for FAISS compatibility."""
        with patch('app.rag.core.retriever.get_text_embedder') as mock_get:
            mock_embedder = MagicMock()
            np_embedding = np.random.randn(384).astype(np.float32)
            mock_embedder.encode.return_value = np_embedding
            mock_get.return_value = mock_embedder

            from app.rag.core.retriever import MultiModalRetrieval

            retriever = MultiModalRetrieval(
                query="test query",
                text_vectorStore=mock_faiss_vectorstore,
                image_data_store=sample_image_data_store,
                k=5,
                bm25_retriever=None,
                use_hybrid=False,
            )

            retriever.retrieve_multimodal()

            call_kwargs = mock_faiss_vectorstore.similarity_search_with_score_by_vector.call_args[1]
            embedding_arg = call_kwargs['embedding']
            assert isinstance(embedding_arg, list)
            assert len(embedding_arg) == 384


class TestHybridMultiModalRetrieval:
    """Tests for the hybrid (BM25 + Dense) retrieval class."""

    def test_hybrid_retrieval_combines_bm25_and_dense(
        self, mock_faiss_vectorstore, mock_bm25_retriever, sample_image_data_store
    ):
        """Test that hybrid retrieval invokes both BM25 and the text FAISS retriever."""
        with patch('app.rag.core.hybrid_retriever.get_embedder'), \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            MockConfig.HYBRID_SEARCH_ENABLED = True
            MockConfig.BM25_WEIGHT = 0.4
            MockConfig.DENSE_WEIGHT = 0.6
            MockConfig.K_DENSE_CANDIDATES = 10
            MockConfig.RRF_K_CONSTANT = 60

            mock_dense_retriever = MagicMock()
            mock_dense_retriever.invoke.return_value = [
                MockDocument("result 1", {"page": 1, "type": "text"}),
            ]
            mock_faiss_vectorstore.as_retriever.return_value = mock_dense_retriever

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            retriever = HybridMultiModalRetrieval(
                query="hybrid test query",
                text_faiss_store=mock_faiss_vectorstore,
                bm25_retriever=mock_bm25_retriever,
                image_data_store=sample_image_data_store,
                k=5,
                use_hybrid=True,
            )

            results = retriever.retrieve_hybrid()

            mock_bm25_retriever.invoke.assert_called_once_with("hybrid test query")
            mock_faiss_vectorstore.as_retriever.assert_called_once()
            mock_dense_retriever.invoke.assert_called_once_with("hybrid test query")

    def test_hybrid_fallback_to_dense_when_bm25_none(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that hybrid falls back to dense-only when BM25 is None."""
        with patch('app.rag.core.hybrid_retriever.get_embedder'), \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            MockConfig.HYBRID_SEARCH_ENABLED = True

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            retriever = HybridMultiModalRetrieval(
                query="test query",
                text_faiss_store=mock_faiss_vectorstore,
                bm25_retriever=None,
                image_data_store=sample_image_data_store,
                k=5,
                use_hybrid=True,
            )

            results = retriever.retrieve_hybrid()

            # Should fall back to dense-only (similarity_search_with_score)
            mock_faiss_vectorstore.similarity_search_with_score.assert_called_once()

    def test_retrieve_multimodal_respects_hybrid_config(
        self, mock_faiss_vectorstore, mock_bm25_retriever, sample_image_data_store
    ):
        """Test that retrieve_multimodal respects HYBRID_SEARCH_ENABLED=False."""
        with patch('app.rag.core.hybrid_retriever.get_embedder'), \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            MockConfig.HYBRID_SEARCH_ENABLED = False

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            retriever = HybridMultiModalRetrieval(
                query="test query",
                text_faiss_store=mock_faiss_vectorstore,
                bm25_retriever=mock_bm25_retriever,
                image_data_store=sample_image_data_store,
                k=5,
                use_hybrid=True,
            )

            results = retriever.retrieve_multimodal()

            # Dense-only: similarity_search_with_score (not as_retriever)
            mock_faiss_vectorstore.similarity_search_with_score.assert_called_once()
            mock_bm25_retriever.invoke.assert_not_called()

    def test_hybrid_limits_results_to_k(
        self, mock_faiss_vectorstore, mock_bm25_retriever, sample_image_data_store
    ):
        """Test that hybrid retrieval limits results to k."""
        with patch('app.rag.core.hybrid_retriever.get_embedder'), \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            MockConfig.HYBRID_SEARCH_ENABLED = True
            MockConfig.BM25_WEIGHT = 0.4
            MockConfig.DENSE_WEIGHT = 0.6
            MockConfig.K_DENSE_CANDIDATES = 10
            MockConfig.RRF_K_CONSTANT = 60

            # Both BM25 and dense return 10 results each
            many_docs = [MockDocument(f"result {i}", {"page": i, "type": "text"}) for i in range(10)]
            mock_bm25_retriever.invoke.return_value = many_docs

            mock_dense_retriever = MagicMock()
            mock_dense_retriever.invoke.return_value = many_docs
            mock_faiss_vectorstore.as_retriever.return_value = mock_dense_retriever

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            k = 3
            retriever = HybridMultiModalRetrieval(
                query="test query",
                text_faiss_store=mock_faiss_vectorstore,
                bm25_retriever=mock_bm25_retriever,
                image_data_store=sample_image_data_store,
                k=k,
                use_hybrid=True,
            )

            results = retriever.retrieve_hybrid()

            assert len(results) == k
