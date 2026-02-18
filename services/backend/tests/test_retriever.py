"""
Tests for the retrieval logic - the most critical RAG component.
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
    """Tests for the main MultiModalRetrieval class."""

    def test_dense_only_retrieval_when_bm25_is_none(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that retrieval works with FAISS only when BM25 is None."""
        with patch('app.rag.core.retriever.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.retriever import MultiModalRetrieval

            retriever = MultiModalRetrieval(
                query="test query",
                vectorStore=mock_faiss_vectorstore,
                image_data_store=sample_image_data_store,
                k=3,
                bm25_retriever=None,
                use_hybrid=True
            )

            results = retriever.retrieve_multimodal()

            # Should still return results from FAISS
            assert results is not None
            assert len(results) <= 3
            mock_faiss_vectorstore.similarity_search_by_vector.assert_called_once()

    def test_retrieval_respects_k_parameter(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that retrieval respects the k parameter."""
        with patch('app.rag.core.retriever.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            from app.rag.core.retriever import MultiModalRetrieval

            for k in [1, 3, 5]:
                mock_faiss_vectorstore.similarity_search_by_vector.reset_mock()

                retriever = MultiModalRetrieval(
                    query="test query",
                    vectorStore=mock_faiss_vectorstore,
                    image_data_store=sample_image_data_store,
                    k=k,
                    bm25_retriever=None,
                    use_hybrid=False
                )

                results = retriever.retrieve_multimodal()

                # Verify k was passed to FAISS
                call_kwargs = mock_faiss_vectorstore.similarity_search_by_vector.call_args[1]
                assert call_kwargs['k'] == k

    def test_embedding_converted_to_list(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that numpy embedding is converted to list for FAISS compatibility."""
        with patch('app.rag.core.retriever.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            np_embedding = np.random.randn(512).astype(np.float32)
            mock_embedder.embed_text.return_value = np_embedding
            mock_get.return_value = mock_embedder

            from app.rag.core.retriever import MultiModalRetrieval

            retriever = MultiModalRetrieval(
                query="test query",
                vectorStore=mock_faiss_vectorstore,
                image_data_store=sample_image_data_store,
                k=5,
                bm25_retriever=None,
                use_hybrid=False
            )

            retriever.retrieve_multimodal()

            # Verify embedding was converted to list
            call_kwargs = mock_faiss_vectorstore.similarity_search_by_vector.call_args[1]
            embedding_arg = call_kwargs['embedding']
            assert isinstance(embedding_arg, list)
            assert len(embedding_arg) == 512


class TestHybridMultiModalRetrieval:
    """Tests for the hybrid (BM25 + Dense) retrieval class."""

    def test_hybrid_retrieval_uses_ensemble(
        self, mock_faiss_vectorstore, mock_bm25_retriever, sample_image_data_store
    ):
        """Test that hybrid retrieval uses EnsembleRetriever."""
        with patch('app.rag.core.hybrid_retriever.get_embedder') as mock_get, \
             patch('app.rag.core.hybrid_retriever.EnsembleRetriever') as MockEnsemble, \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            MockConfig.HYBRID_SEARCH_ENABLED = True
            MockConfig.BM25_WEIGHT = 0.4
            MockConfig.DENSE_WEIGHT = 0.6
            MockConfig.K_DENSE_CANDIDATES = 10

            # Mock ensemble retriever
            mock_ensemble = MagicMock()
            mock_ensemble.invoke.return_value = [
                MockDocument("result 1", {"page": 1}),
                MockDocument("result 2", {"page": 2}),
            ]
            MockEnsemble.return_value = mock_ensemble

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            retriever = HybridMultiModalRetrieval(
                query="hybrid test query",
                faiss_store=mock_faiss_vectorstore,
                bm25_retriever=mock_bm25_retriever,
                image_data_store=sample_image_data_store,
                k=5,
                use_hybrid=True
            )

            results = retriever.retrieve_hybrid()

            # Ensemble retriever should be created with correct weights
            MockEnsemble.assert_called_once()
            call_kwargs = MockEnsemble.call_args[1]
            assert call_kwargs['weights'] == [0.4, 0.6]

    def test_hybrid_fallback_to_dense_when_bm25_none(
        self, mock_faiss_vectorstore, sample_image_data_store
    ):
        """Test that hybrid falls back to dense-only when BM25 is None."""
        with patch('app.rag.core.hybrid_retriever.get_embedder') as mock_get, \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            MockConfig.HYBRID_SEARCH_ENABLED = True

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            retriever = HybridMultiModalRetrieval(
                query="test query",
                faiss_store=mock_faiss_vectorstore,
                bm25_retriever=None,  # No BM25
                image_data_store=sample_image_data_store,
                k=5,
                use_hybrid=True
            )

            results = retriever.retrieve_hybrid()

            # Should fall back to dense-only (FAISS)
            mock_faiss_vectorstore.similarity_search_by_vector.assert_called_once()

    def test_retrieve_multimodal_respects_hybrid_config(
        self, mock_faiss_vectorstore, mock_bm25_retriever, sample_image_data_store
    ):
        """Test that retrieve_multimodal respects HYBRID_SEARCH_ENABLED config."""
        with patch('app.rag.core.hybrid_retriever.get_embedder') as mock_get, \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            # Disable hybrid search
            MockConfig.HYBRID_SEARCH_ENABLED = False

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            retriever = HybridMultiModalRetrieval(
                query="test query",
                faiss_store=mock_faiss_vectorstore,
                bm25_retriever=mock_bm25_retriever,
                image_data_store=sample_image_data_store,
                k=5,
                use_hybrid=True
            )

            results = retriever.retrieve_multimodal()

            # Should use dense-only since hybrid is disabled
            mock_faiss_vectorstore.similarity_search_by_vector.assert_called_once()

    def test_hybrid_limits_results_to_k(
        self, mock_faiss_vectorstore, mock_bm25_retriever, sample_image_data_store
    ):
        """Test that hybrid retrieval limits results to k."""
        with patch('app.rag.core.hybrid_retriever.get_embedder') as mock_get, \
             patch('app.rag.core.hybrid_retriever.EnsembleRetriever') as MockEnsemble, \
             patch('app.rag.core.hybrid_retriever.HybridSearchConfig') as MockConfig:

            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            MockConfig.HYBRID_SEARCH_ENABLED = True
            MockConfig.BM25_WEIGHT = 0.4
            MockConfig.DENSE_WEIGHT = 0.6
            MockConfig.K_DENSE_CANDIDATES = 10

            # Return more results than k
            mock_ensemble = MagicMock()
            mock_ensemble.invoke.return_value = [
                MockDocument(f"result {i}", {"page": i}) for i in range(10)
            ]
            MockEnsemble.return_value = mock_ensemble

            from app.rag.core.hybrid_retriever import HybridMultiModalRetrieval

            k = 3
            retriever = HybridMultiModalRetrieval(
                query="test query",
                faiss_store=mock_faiss_vectorstore,
                bm25_retriever=mock_bm25_retriever,
                image_data_store=sample_image_data_store,
                k=k,
                use_hybrid=True
            )

            results = retriever.retrieve_hybrid()

            # Results should be limited to k
            assert len(results) == k
