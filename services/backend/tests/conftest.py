"""
Shared pytest fixtures for RAG system tests.
Provides mock embedders, documents, and retrievers for testing without GPU dependencies.
"""
import os
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-placeholder")

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict


# ========== Mock CLIP Embedder ==========

class MockCLIPEmbedder:
    """Mock CLIP embedder that returns fixed 512-dim vectors without loading the model."""

    model_name: str = "openai/clip-vit-base-patch32"

    def embed_text(self, text: str) -> np.ndarray:
        """Return a deterministic 512-dim normalized vector based on text hash."""
        np.random.seed(hash(text) % (2**32))
        vec = np.random.randn(512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)  # Normalize to unit length
        return vec

    def embed_image(self, image_data) -> np.ndarray:
        """Return a deterministic 512-dim normalized vector for images."""
        np.random.seed(42)
        vec = np.random.randn(512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        return vec


@pytest.fixture
def mock_embedder():
    """Fixture providing a mock CLIP embedder."""
    return MockCLIPEmbedder()


@pytest.fixture
def mock_get_embedder(mock_embedder):
    """Fixture that patches get_embedder to return the mock."""
    with patch('app.rag.core.embedder.get_embedder', return_value=mock_embedder):
        yield mock_embedder


# ========== Sample Documents ==========

@dataclass
class MockDocument:
    """Mock LangChain document for testing."""
    page_content: str
    metadata: Dict


@pytest.fixture
def sample_documents():
    """Fixture providing sample LangChain-style documents."""
    return [
        MockDocument(
            page_content="Machine learning is a subset of artificial intelligence.",
            metadata={"source": "test.pdf", "page": 1, "type": "text"}
        ),
        MockDocument(
            page_content="Neural networks are inspired by biological neurons.",
            metadata={"source": "test.pdf", "page": 2, "type": "text"}
        ),
        MockDocument(
            page_content="Deep learning uses multiple layers of neural networks.",
            metadata={"source": "test.pdf", "page": 3, "type": "text"}
        ),
        MockDocument(
            page_content="Transformers revolutionized natural language processing.",
            metadata={"source": "test.pdf", "page": 4, "type": "text"}
        ),
        MockDocument(
            page_content="CLIP connects images and text in a shared embedding space.",
            metadata={"source": "test.pdf", "page": 5, "type": "text"}
        ),
    ]


@pytest.fixture
def sample_embeddings(mock_embedder, sample_documents):
    """Fixture providing pre-computed embeddings for sample documents."""
    return [mock_embedder.embed_text(doc.page_content).tolist() for doc in sample_documents]


# ========== Sample PDF Bytes ==========

@pytest.fixture
def sample_pdf_bytes():
    """Fixture providing minimal valid PDF bytes for testing file uploads."""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test PDF content) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Root 1 0 R /Size 5 >>
startxref
306
%%EOF"""
    return pdf_content


# ========== Mock Vector Store ==========

@pytest.fixture
def mock_faiss_vectorstore(sample_documents, sample_embeddings):
    """Fixture providing a mock FAISS vector store."""
    mock_store = MagicMock()

    def similarity_search_by_vector(embedding, k=5):
        """Return top k documents (mocked)."""
        return sample_documents[:k]

    def similarity_search_with_score_by_vector(embedding, k=5):
        """Return top k (document, score) tuples with a fixed L2 distance of 0.25."""
        return [(doc, 0.25) for doc in sample_documents[:k]]

    def similarity_search(query, k=5):
        """Return top k documents for text query."""
        return sample_documents[:k]

    mock_store.similarity_search_by_vector = MagicMock(side_effect=similarity_search_by_vector)
    mock_store.similarity_search_with_score_by_vector = MagicMock(side_effect=similarity_search_with_score_by_vector)
    mock_store.similarity_search = MagicMock(side_effect=similarity_search)
    mock_store.as_retriever = MagicMock(return_value=MagicMock())

    return mock_store


# ========== Mock BM25 Retriever ==========

@pytest.fixture
def mock_bm25_retriever(sample_documents):
    """Fixture providing a mock BM25 retriever."""
    mock_retriever = MagicMock()
    mock_retriever.k = 10

    def invoke(query):
        """Return documents based on simple keyword matching."""
        return sample_documents[:5]

    mock_retriever.invoke = MagicMock(side_effect=invoke)
    mock_retriever.get_relevant_documents = MagicMock(side_effect=invoke)

    return mock_retriever


# ========== Image Data Store ==========

@pytest.fixture
def sample_image_data_store():
    """Fixture providing sample image data store with base64 images."""
    return {
        "img_page_1": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "img_page_2": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    }


# ========== API Test Client ==========

@pytest.fixture
def app_client():
    """Fixture providing a TestClient for FastAPI app testing."""
    from fastapi.testclient import TestClient
    from app.api.app import app

    # Reset global state before each test
    import app.api.app as app_module
    app_module.vectorstore = None
    app_module.bm25_retriever = None
    app_module.image_data_store = {}
    app_module.agentic_rag_system.reset()

    return TestClient(app)


# ========== Environment Fixtures ==========

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture for mocking environment variables."""
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, str(value))
    return _set_env
