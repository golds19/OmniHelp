"""
Tests for the CLIP embedder singleton pattern and embedding functionality.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestGetEmbedder:
    """Tests for the singleton get_embedder function."""

    def test_get_embedder_returns_singleton(self):
        """Test that get_embedder returns the same instance on multiple calls."""
        # Clear the lru_cache to ensure fresh state
        from app.rag.core.embedder import get_embedder
        get_embedder.cache_clear()

        # Mock CLIPEmbedder to avoid loading the actual model
        with patch('app.rag.core.embedder.CLIPEmbedder') as MockCLIPEmbedder:
            mock_instance = MagicMock()
            MockCLIPEmbedder.return_value = mock_instance

            # Get embedder twice
            embedder1 = get_embedder()
            embedder2 = get_embedder()

            # Should be the same instance
            assert embedder1 is embedder2

            # CLIPEmbedder should only be instantiated once
            assert MockCLIPEmbedder.call_count == 1

        # Clean up cache after test
        get_embedder.cache_clear()

    def test_get_embedder_cache_cleared_creates_new_instance(self):
        """Test that clearing cache creates a new embedder instance."""
        from app.rag.core.embedder import get_embedder
        get_embedder.cache_clear()

        with patch('app.rag.core.embedder.CLIPEmbedder') as MockCLIPEmbedder:
            mock_instance1 = MagicMock()
            mock_instance2 = MagicMock()
            MockCLIPEmbedder.side_effect = [mock_instance1, mock_instance2]

            # Get first instance
            embedder1 = get_embedder()

            # Clear cache
            get_embedder.cache_clear()

            # Get second instance
            embedder2 = get_embedder()

            # Should be different instances
            assert embedder1 is not embedder2
            assert MockCLIPEmbedder.call_count == 2

        get_embedder.cache_clear()


class TestCLIPEmbedder:
    """Tests for CLIPEmbedder embedding functionality using mock."""

    def test_embed_text_returns_correct_shape(self, mock_embedder):
        """Test that embed_text returns a 512-dimensional vector."""
        embedding = mock_embedder.embed_text("test query")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
        assert embedding.dtype == np.float32

    def test_embed_text_is_normalized(self, mock_embedder):
        """Test that text embeddings are L2 normalized (norm = 1.0)."""
        embedding = mock_embedder.embed_text("test query for normalization")

        l2_norm = np.linalg.norm(embedding)
        assert np.isclose(l2_norm, 1.0, atol=1e-5)

    def test_embed_text_deterministic(self, mock_embedder):
        """Test that same text produces same embedding."""
        text = "deterministic test"
        embedding1 = mock_embedder.embed_text(text)
        embedding2 = mock_embedder.embed_text(text)

        np.testing.assert_array_almost_equal(embedding1, embedding2)

    def test_embed_text_different_texts_produce_different_embeddings(self, mock_embedder):
        """Test that different texts produce different embeddings."""
        embedding1 = mock_embedder.embed_text("machine learning")
        embedding2 = mock_embedder.embed_text("deep learning")

        # Should be different vectors
        assert not np.allclose(embedding1, embedding2)

    def test_embed_image_returns_correct_shape(self, mock_embedder):
        """Test that embed_image returns a 512-dimensional vector."""
        embedding = mock_embedder.embed_image("dummy_image_path")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
        assert embedding.dtype == np.float32

    def test_embed_image_is_normalized(self, mock_embedder):
        """Test that image embeddings are L2 normalized."""
        embedding = mock_embedder.embed_image("dummy_image_path")

        l2_norm = np.linalg.norm(embedding)
        assert np.isclose(l2_norm, 1.0, atol=1e-5)


class TestGetTextEmbedder:
    """Tests for the singleton get_text_embedder function."""

    def test_get_text_embedder_returns_singleton(self):
        """Test that get_text_embedder returns the same instance on multiple calls."""
        from app.rag.core.embedder import get_text_embedder
        get_text_embedder.cache_clear()

        with patch('app.rag.core.embedder.TextEmbedder') as MockTextEmbedder:
            mock_instance = MagicMock()
            MockTextEmbedder.return_value = mock_instance

            embedder1 = get_text_embedder()
            embedder2 = get_text_embedder()

            assert embedder1 is embedder2
            assert MockTextEmbedder.call_count == 1

        get_text_embedder.cache_clear()


class TestTextEmbedder:
    """Tests for TextEmbedder via the MockTextEmbedder fixture."""

    def test_encode_returns_384_dim(self, mock_text_embedder):
        """Test that encode returns a 384-dimensional vector."""
        embedding = mock_text_embedder.encode("test query")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32

    def test_encode_is_normalized(self, mock_text_embedder):
        """Test that encoded vectors are L2 normalized."""
        embedding = mock_text_embedder.encode("test query for normalization")
        assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5)

    def test_encode_deterministic(self, mock_text_embedder):
        """Test that the same text produces the same embedding."""
        text = "deterministic test"
        e1 = mock_text_embedder.encode(text)
        e2 = mock_text_embedder.encode(text)
        np.testing.assert_array_almost_equal(e1, e2)

    def test_encode_different_texts_differ(self, mock_text_embedder):
        """Test that different texts produce different embeddings."""
        e1 = mock_text_embedder.encode("machine learning")
        e2 = mock_text_embedder.encode("deep learning")
        assert not np.allclose(e1, e2)

    def test_encode_batch_returns_correct_shape(self, mock_text_embedder):
        """Test that encode_batch returns (N, 384) array."""
        texts = ["text one", "text two", "text three"]
        batch = mock_text_embedder.encode_batch(texts)
        assert isinstance(batch, np.ndarray)
        assert batch.shape == (3, 384)


class TestCLIPEmbeddingWrapper:
    """Tests for the LangChain-compatible CLIP embedding wrapper."""

    def test_embed_documents_returns_list_of_lists(self):
        """Test that embed_documents returns list of float lists for LangChain compatibility."""
        from app.rag.core.vectorstore import CLIPEmbeddingWrapper

        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            mock_embedder.embed_text.return_value = np.random.randn(512).astype(np.float32)
            mock_get.return_value = mock_embedder

            wrapper = CLIPEmbeddingWrapper()
            texts = ["text1", "text2", "text3"]
            embeddings = wrapper.embed_documents(texts)

            assert isinstance(embeddings, list)
            assert len(embeddings) == 3
            assert all(isinstance(emb, list) for emb in embeddings)
            assert all(len(emb) == 512 for emb in embeddings)

    def test_embed_query_returns_list(self):
        """Test that embed_query returns a float list for LangChain compatibility."""
        from app.rag.core.vectorstore import CLIPEmbeddingWrapper

        with patch('app.rag.core.vectorstore.get_embedder') as mock_get:
            mock_embedder = MagicMock()
            vec = np.random.randn(512).astype(np.float32)
            mock_embedder.embed_text.return_value = vec
            mock_get.return_value = mock_embedder

            wrapper = CLIPEmbeddingWrapper()
            embedding = wrapper.embed_query("test query")

            assert isinstance(embedding, list)
            assert len(embedding) == 512
            assert all(isinstance(x, float) for x in embedding)
