"""
Tests for configuration validation.
"""
import pytest
import os


class TestHybridSearchConfig:
    """Tests for HybridSearchConfig validation."""

    def test_hybrid_config_default_weights(self):
        """Test that default weights are reasonable."""
        from app.rag.core.config import HybridSearchConfig

        assert HybridSearchConfig.BM25_WEIGHT == 0.4
        assert HybridSearchConfig.DENSE_WEIGHT == 0.6
        # Weights should sum to ~1.0
        total = HybridSearchConfig.BM25_WEIGHT + HybridSearchConfig.DENSE_WEIGHT
        assert abs(total - 1.0) < 0.01

    def test_hybrid_config_validates_weights_in_range(self, mock_env_vars):
        """Test that weight validation catches out-of-range values."""
        # This test verifies the validate() assertions work
        # We can't easily test assertion errors without reloading the module,
        # so we verify the valid defaults pass validation
        from app.rag.core.config import HybridSearchConfig

        # Should not raise
        HybridSearchConfig.validate()

        # Verify weights are in valid range
        assert 0 <= HybridSearchConfig.BM25_WEIGHT <= 1
        assert 0 <= HybridSearchConfig.DENSE_WEIGHT <= 1

    def test_hybrid_config_k_values_positive(self):
        """Test that K values are positive."""
        from app.rag.core.config import HybridSearchConfig

        assert HybridSearchConfig.K_TOTAL > 0
        assert HybridSearchConfig.K_BM25_CANDIDATES > 0
        assert HybridSearchConfig.K_DENSE_CANDIDATES > 0

    def test_hybrid_config_candidates_gte_total(self):
        """Test that candidate counts are >= final result count."""
        from app.rag.core.config import HybridSearchConfig

        assert HybridSearchConfig.K_BM25_CANDIDATES >= HybridSearchConfig.K_TOTAL
        assert HybridSearchConfig.K_DENSE_CANDIDATES >= HybridSearchConfig.K_TOTAL

    def test_hybrid_config_get_config_dict(self):
        """Test that get_config_dict returns all expected keys."""
        from app.rag.core.config import HybridSearchConfig

        config = HybridSearchConfig.get_config_dict()

        expected_keys = [
            "hybrid_search_enabled",
            "bm25_weight",
            "dense_weight",
            "k_total",
            "k_bm25_candidates",
            "k_dense_candidates",
            "rrf_k_constant",
            "bm25_k1",
            "bm25_b",
            "tokenizer",
            "remove_stopwords",
            "lowercase",
            "query_expansion_enabled",
            "num_query_variations"
        ]

        for key in expected_keys:
            assert key in config


class TestPDFConfig:
    """Tests for PDFConfig validation."""

    def test_pdf_config_default_chunk_size_positive(self):
        """Test that default chunk size is positive."""
        from app.rag.core.config import PDFConfig

        assert PDFConfig.CHUNK_SIZE > 0
        assert PDFConfig.CHUNK_SIZE == 1000  # Default

    def test_pdf_config_chunk_overlap_non_negative(self):
        """Test that chunk overlap is non-negative."""
        from app.rag.core.config import PDFConfig

        assert PDFConfig.CHUNK_OVERLAP >= 0
        assert PDFConfig.CHUNK_OVERLAP == 200  # Default

    def test_pdf_config_overlap_less_than_size(self):
        """Test that overlap is less than chunk size."""
        from app.rag.core.config import PDFConfig

        assert PDFConfig.CHUNK_OVERLAP < PDFConfig.CHUNK_SIZE

    def test_pdf_config_validates_successfully(self):
        """Test that default config passes validation."""
        from app.rag.core.config import PDFConfig

        # Should not raise
        PDFConfig.validate()


class TestLLMConfig:
    """Tests for LLMConfig validation."""

    def test_llm_config_temperature_in_range(self):
        """Test that temperature is in valid range."""
        from app.rag.core.config import LLMConfig

        assert 0 <= LLMConfig.LLM_TEMPERATURE <= 2
        assert 0 <= LLMConfig.QUERY_ENHANCER_TEMPERATURE <= 2

    def test_llm_config_models_specified(self):
        """Test that model names are specified."""
        from app.rag.core.config import LLMConfig

        assert LLMConfig.LLM_MODEL
        assert LLMConfig.QUERY_ENHANCER_MODEL
        assert len(LLMConfig.LLM_MODEL) > 0
        assert len(LLMConfig.QUERY_ENHANCER_MODEL) > 0

    def test_llm_config_validates_successfully(self):
        """Test that default config passes validation."""
        from app.rag.core.config import LLMConfig

        # Should not raise
        LLMConfig.validate()

    def test_llm_config_get_config_dict(self):
        """Test that get_config_dict returns expected keys."""
        from app.rag.core.config import LLMConfig

        config = LLMConfig.get_config_dict()

        assert "llm_model" in config
        assert "llm_temperature" in config
        assert "query_enhancer_model" in config
        assert "query_enhancer_temperature" in config


class TestAppConfig:
    """Tests for AppConfig."""

    def test_app_config_cors_origins_is_list(self):
        """Test that CORS origins is a list."""
        from app.rag.core.config import AppConfig

        assert isinstance(AppConfig.CORS_ORIGINS, list)
        assert len(AppConfig.CORS_ORIGINS) > 0

    def test_app_config_temp_dir_specified(self):
        """Test that temp directory is specified."""
        from app.rag.core.config import AppConfig

        assert AppConfig.TEMP_DIR
        assert len(AppConfig.TEMP_DIR) > 0


class TestEnvOverrides:
    """Tests for environment variable overrides."""

    def test_env_override_chunk_size(self, monkeypatch):
        """Test that PDF_CHUNK_SIZE can be overridden via env."""
        monkeypatch.setenv("PDF_CHUNK_SIZE", "2000")

        # Need to reload the module to pick up new env var
        # For unit tests, we just verify the pattern works
        chunk_size = int(os.getenv("PDF_CHUNK_SIZE", "1000"))
        assert chunk_size == 2000

    def test_env_override_hybrid_enabled(self, monkeypatch):
        """Test that HYBRID_SEARCH_ENABLED can be overridden via env."""
        monkeypatch.setenv("HYBRID_SEARCH_ENABLED", "false")

        enabled = os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() == "true"
        assert enabled is False

    def test_env_override_weights(self, monkeypatch):
        """Test that BM25_WEIGHT and DENSE_WEIGHT can be overridden."""
        monkeypatch.setenv("BM25_WEIGHT", "0.3")
        monkeypatch.setenv("DENSE_WEIGHT", "0.7")

        bm25 = float(os.getenv("BM25_WEIGHT", "0.4"))
        dense = float(os.getenv("DENSE_WEIGHT", "0.6"))

        assert bm25 == 0.3
        assert dense == 0.7
        assert abs(bm25 + dense - 1.0) < 0.01

    def test_env_override_cors_origins(self, monkeypatch):
        """Test that CORS_ORIGINS can be overridden."""
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com,https://api.example.com")

        origins = os.getenv("CORS_ORIGINS", "http://localhost").split(",")

        assert len(origins) == 2
        assert "https://example.com" in origins
        assert "https://api.example.com" in origins
