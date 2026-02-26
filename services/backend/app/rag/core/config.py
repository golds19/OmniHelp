"""
Centralized configuration for the RAG system.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """Application-level configuration"""

    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost,http://localhost:3000"
    ).split(",")

    # Temporary directory for file uploads
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")


class PDFConfig:
    """Configuration for PDF processing"""

    CHUNK_SIZE: int = int(os.getenv("PDF_CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("PDF_CHUNK_OVERLAP", "200"))

    @classmethod
    def validate(cls):
        """Validate PDF configuration parameters"""
        assert cls.CHUNK_SIZE > 0, "PDF_CHUNK_SIZE must be positive"
        assert cls.CHUNK_OVERLAP >= 0, "PDF_CHUNK_OVERLAP must be non-negative"
        assert cls.CHUNK_OVERLAP < cls.CHUNK_SIZE, "PDF_CHUNK_OVERLAP must be less than PDF_CHUNK_SIZE"


class LLMConfig:
    """Configuration parameters for LLM models"""

    # Main LLM model for RAG responses
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    # Query enhancement LLM (can be different/cheaper model)
    QUERY_ENHANCER_MODEL = os.getenv("QUERY_ENHANCER_MODEL", "gpt-4o-mini")
    QUERY_ENHANCER_TEMPERATURE = float(os.getenv("QUERY_ENHANCER_TEMPERATURE", "0.7"))

    @classmethod
    def validate(cls):
        """Validate LLM configuration parameters"""
        assert 0 <= cls.LLM_TEMPERATURE <= 2, "LLM_TEMPERATURE must be between 0 and 2"
        assert 0 <= cls.QUERY_ENHANCER_TEMPERATURE <= 2, "QUERY_ENHANCER_TEMPERATURE must be between 0 and 2"
        assert cls.LLM_MODEL, "LLM_MODEL must be specified"
        assert cls.QUERY_ENHANCER_MODEL, "QUERY_ENHANCER_MODEL must be specified"

    @classmethod
    def get_config_dict(cls):
        """Get configuration as dictionary"""
        return {
            "llm_model": cls.LLM_MODEL,
            "llm_temperature": cls.LLM_TEMPERATURE,
            "query_enhancer_model": cls.QUERY_ENHANCER_MODEL,
            "query_enhancer_temperature": cls.QUERY_ENHANCER_TEMPERATURE,
        }


class HybridSearchConfig:
    """Configuration parameters for hybrid search"""

    # Enable/Disable hybrid search
    HYBRID_SEARCH_ENABLED = os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() == "true"

    # Fusion weights (should sum to ~1.0)
    BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "0.4"))
    DENSE_WEIGHT = float(os.getenv("DENSE_WEIGHT", "0.6"))

    # Number of results
    K_TOTAL = int(os.getenv("K_TOTAL", "5"))  # Final results to return
    K_BM25_CANDIDATES = int(os.getenv("K_BM25_CANDIDATES", "10"))  # BM25 candidates to fetch
    K_DENSE_CANDIDATES = int(os.getenv("K_DENSE_CANDIDATES", "10"))  # Dense candidates to fetch

    # RRF (Reciprocal Rank Fusion) constant
    # Higher values make the fusion less aggressive
    RRF_K_CONSTANT = int(os.getenv("RRF_K_CONSTANT", "60"))

    # BM25 Parameters
    BM25_K1 = float(os.getenv("BM25_K1", "1.5"))  # Term frequency saturation
    BM25_B = float(os.getenv("BM25_B", "0.75"))  # Length normalization

    # Tokenization settings
    TOKENIZER = os.getenv("TOKENIZER", "nltk")  # Options: nltk, spacy
    REMOVE_STOPWORDS = os.getenv("REMOVE_STOPWORDS", "false").lower() == "true"
    LOWERCASE = os.getenv("LOWERCASE", "true").lower() == "true"

    # Query Expansion settings
    QUERY_EXPANSION_ENABLED = os.getenv("QUERY_EXPANSION_ENABLED", "true").lower() == "true"
    NUM_QUERY_VARIATIONS = int(os.getenv("NUM_QUERY_VARIATIONS", "3"))

    # Similarity threshold below which queries are rejected as out-of-context
    MIN_SIMILARITY_THRESHOLD: float = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.3"))

    @classmethod
    def validate(cls):
        """Validate configuration parameters"""
        assert 0 <= cls.BM25_WEIGHT <= 1, "BM25_WEIGHT must be between 0 and 1"
        assert 0 <= cls.DENSE_WEIGHT <= 1, "DENSE_WEIGHT must be between 0 and 1"
        assert cls.K_TOTAL > 0, "K_TOTAL must be positive"
        assert cls.K_BM25_CANDIDATES >= cls.K_TOTAL, "K_BM25_CANDIDATES should be >= K_TOTAL"
        assert cls.K_DENSE_CANDIDATES >= cls.K_TOTAL, "K_DENSE_CANDIDATES should be >= K_TOTAL"
        assert 0 <= cls.MIN_SIMILARITY_THRESHOLD <= 1, "MIN_SIMILARITY_THRESHOLD must be between 0 and 1"

    @classmethod
    def get_config_dict(cls):
        """Get configuration as dictionary"""
        return {
            "hybrid_search_enabled": cls.HYBRID_SEARCH_ENABLED,
            "bm25_weight": cls.BM25_WEIGHT,
            "dense_weight": cls.DENSE_WEIGHT,
            "k_total": cls.K_TOTAL,
            "k_bm25_candidates": cls.K_BM25_CANDIDATES,
            "k_dense_candidates": cls.K_DENSE_CANDIDATES,
            "rrf_k_constant": cls.RRF_K_CONSTANT,
            "bm25_k1": cls.BM25_K1,
            "bm25_b": cls.BM25_B,
            "tokenizer": cls.TOKENIZER,
            "remove_stopwords": cls.REMOVE_STOPWORDS,
            "lowercase": cls.LOWERCASE,
            "query_expansion_enabled": cls.QUERY_EXPANSION_ENABLED,
            "num_query_variations": cls.NUM_QUERY_VARIATIONS,
            "min_similarity_threshold": cls.MIN_SIMILARITY_THRESHOLD,
        }


# Validate configuration on import
PDFConfig.validate()
LLMConfig.validate()
HybridSearchConfig.validate()
