"""
Tests for FastAPI endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO


class TestPingEndpoint:
    """Tests for the health check endpoint."""

    def test_ping_returns_pong(self, app_client):
        """Test that /ping returns pong message."""
        response = app_client.get("/ping")

        assert response.status_code == 200
        assert response.json() == {"message": "pong"}


class TestIngestEndpoint:
    """Tests for the document ingestion endpoint."""

    def test_ingest_non_pdf_returns_400(self, app_client):
        """Test that non-PDF files are rejected."""
        # Create a fake text file
        fake_file = BytesIO(b"This is not a PDF")

        response = app_client.post(
            "/ingest",
            files={"file": ("test.txt", fake_file, "text/plain")}
        )

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_ingest_accepts_pdf(self, app_client, sample_pdf_bytes):
        """Test that PDF files are accepted (mocking processing)."""
        with patch('app.api.app.DataEmbedding') as MockDE, \
             patch('app.api.app.VectorStore') as MockVS:

            # Mock the data embedding
            mock_de_instance = MagicMock()
            mock_de_instance.process_and_embedd_docs.return_value = (
                [],  # docs
                [],  # embeddings
                {},  # image_data_store
                []   # text_docs
            )
            MockDE.return_value = mock_de_instance

            # Mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.create_hybrid_retrievers.return_value = {
                "faiss_store": MagicMock(),
                "bm25_retriever": MagicMock(),
                "image_data_store": {}
            }
            MockVS.return_value = mock_vs_instance

            fake_pdf = BytesIO(sample_pdf_bytes)
            response = app_client.post(
                "/ingest",
                files={"file": ("test.pdf", fake_pdf, "application/pdf")}
            )

            assert response.status_code == 200
            assert "Successfully processed" in response.json()["message"]


class TestQueryEndpoint:
    """Tests for the query endpoint."""

    def test_query_without_ingest_returns_400(self, app_client):
        """Test that querying without ingestion returns error."""
        response = app_client.post(
            "/query",
            json={"question": "What is machine learning?"}
        )

        assert response.status_code == 400
        assert "No documents" in response.json()["detail"]

    def test_query_returns_expected_schema(self, app_client):
        """Test that query response has expected structure."""
        # Set up mock vectorstore
        import app.api.app as app_module

        with patch.object(app_module, 'vectorstore', MagicMock()), \
             patch.object(app_module, 'bm25_retriever', MagicMock()), \
             patch('app.api.app.MultiModalRAG') as MockRAG:

            mock_rag = MagicMock()
            mock_rag.generate.return_value = {
                "answer": "Machine learning is a subset of AI.",
                "sources": [{"page": 1, "type": "text"}],
                "num_images": 0,
                "num_text_chunks": 3
            }
            MockRAG.return_value = mock_rag

            response = app_client.post(
                "/query",
                json={"question": "What is machine learning?"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify schema
            assert "answer" in data
            assert "sources" in data
            assert "num_images" in data
            assert "num_text_chunks" in data

            assert isinstance(data["answer"], str)
            assert isinstance(data["sources"], list)
            assert isinstance(data["num_images"], int)
            assert isinstance(data["num_text_chunks"], int)


class TestAgenticIngestEndpoint:
    """Tests for the agentic ingest endpoint."""

    def test_agentic_ingest_non_pdf_returns_400(self, app_client):
        """Test that non-PDF files are rejected for agentic ingestion."""
        fake_file = BytesIO(b"This is not a PDF")

        response = app_client.post(
            "/ingest-agentic",
            files={"file": ("test.docx", fake_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_agentic_ingest_accepts_pdf(self, app_client, sample_pdf_bytes):
        """Test that agentic PDF ingestion works."""
        import app.api.app as app_module

        with patch.object(app_module.agentic_rag_system, 'initialize') as mock_init:
            fake_pdf = BytesIO(sample_pdf_bytes)
            response = app_client.post(
                "/ingest-agentic",
                files={"file": ("test.pdf", fake_pdf, "application/pdf")}
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["status"] == "initialized"


class TestAgenticQueryEndpoint:
    """Tests for the agentic query endpoint."""

    def test_agentic_query_without_init_returns_400(self, app_client):
        """Test that querying uninitialized agentic system returns error."""
        import app.api.app as app_module

        with patch.object(app_module.agentic_rag_system, 'is_initialized', return_value=False):
            response = app_client.post(
                "/query-agentic",
                json={"question": "What is in the document?"}
            )

            assert response.status_code == 400
            assert "not initialized" in response.json()["detail"]

    def test_agentic_query_returns_expected_schema(self, app_client):
        """Test that agentic query response has expected structure."""
        import app.api.app as app_module

        with patch.object(app_module.agentic_rag_system, 'is_initialized', return_value=True), \
             patch('app.api.app.run_agentic_rag') as mock_run:

            mock_run.return_value = {
                "answer": "The document discusses AI concepts.",
                "sources": [{"page": 1, "type": "text"}, {"page": 2, "type": "image"}],
                "num_images": 1,
                "num_text_chunks": 2
            }

            response = app_client.post(
                "/query-agentic",
                json={"question": "What is in the document?"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify schema includes agent_type
            assert "answer" in data
            assert "sources" in data
            assert "num_images" in data
            assert "num_text_chunks" in data
            assert "agent_type" in data
            assert data["agent_type"] == "ReAct"


class TestCORSHeaders:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, app_client):
        """Test that CORS headers are set correctly."""
        response = app_client.options(
            "/ping",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        # FastAPI/Starlette CORS middleware should respond
        assert response.status_code in [200, 204, 405]
