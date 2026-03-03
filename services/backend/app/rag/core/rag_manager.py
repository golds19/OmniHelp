"""
Singleton class to manage the multimodal RAG system state.
This ensures we don't rebuild embeddings on every query.
"""
import logging
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from .data_ingestion import DataEmbedding
from .vectorstore import VectorStore
from .config import HybridSearchConfig
from .retriever import MultiModalRetrieval
from .utils import filter_documents_by_type

logger = logging.getLogger(__name__)


class MultiModalRAGSystem:
    """
    Per-session manager for the multimodal RAG system state.
    Each instance is independent, enabling per-session isolation.
    """

    def __init__(self):
        self._initialized: bool = False
        self.text_vectorStore = None
        self.image_vectorStore = None
        self.bm25_retriever = None
        self.all_docs = []
        self.all_embeddings = []
        self.text_docs = []
        self.image_data_store = {}
        self.vision_llm = None

    def initialize(self, pdf_path: str, vision_llm: Optional[ChatOpenAI] = None):
        """
        Initialize the RAG system with a PDF document.

        Args:
            pdf_path: Path to the PDF file to process
            vision_llm: Optional vision LLM for multimodal processing
        """
        if self._initialized:
            logger.info("RAG system already initialized. Resetting for new document...")
            self.reset()

        logger.info(f"Initializing multimodal RAG system with {pdf_path}...")

        # Load and embed data
        data_embedder = DataEmbedding(pdf_path=pdf_path)
        self.all_docs, self.all_embeddings, self.image_data_store, self.text_docs = \
            data_embedder.process_and_embedd_docs()

        # Create vector stores (FAISS text + image, BM25)
        vs = VectorStore(
            all_docs=self.all_docs,
            all_embeddings=self.all_embeddings,
            image_data_store=self.image_data_store,
            text_docs=self.text_docs,
        )

        if HybridSearchConfig.HYBRID_SEARCH_ENABLED:
            logger.info("Creating hybrid search retrievers (BM25 + FAISS)...")
            hybrid_stores = vs.create_hybrid_retrievers()
            self.text_vectorStore = hybrid_stores["text_faiss_store"]
            self.image_vectorStore = hybrid_stores["image_faiss_store"]
            self.bm25_retriever = hybrid_stores["bm25_retriever"]
            logger.info(
                f"Hybrid search enabled (BM25 weight: {HybridSearchConfig.BM25_WEIGHT}, "
                f"Dense weight: {HybridSearchConfig.DENSE_WEIGHT})"
            )
        else:
            logger.info("Creating FAISS vector stores only (dense search)...")
            text_store, image_store = vs.create_faiss_vectorstores()
            self.text_vectorStore = text_store
            self.image_vectorStore = image_store
            self.bm25_retriever = None

        self.vision_llm = vision_llm
        self._initialized = True
        logger.info(
            f"RAG system initialized with {len(self.all_docs)} documents "
            f"({len(self.text_docs)} text chunks)"
        )

    def query(self, question: str, k: int = 5, use_hybrid: bool = True) -> Dict:
        """
        Query the multimodal RAG system.

        Returns:
            Dict with retrieved_docs, sources, num_images, num_text_chunks, top_similarity.
        """
        if not self._initialized:
            raise RuntimeError("RAG system not initialized. Please load a document first.")

        retriever = MultiModalRetrieval(
            query=question,
            text_vectorStore=self.text_vectorStore,
            image_vectorStore=self.image_vectorStore,
            image_data_store=self.image_data_store,
            k=k,
            bm25_retriever=self.bm25_retriever,
            use_hybrid=use_hybrid,
        )
        retrieval_result = retriever.retrieve_multimodal()
        retrieved_docs = retrieval_result["docs"]
        top_similarity = retrieval_result["top_similarity"]

        sources = [
            {"page": doc.metadata["page"], "type": doc.metadata["type"]}
            for doc in retrieved_docs
        ]
        text_docs, image_docs = filter_documents_by_type(retrieved_docs)

        return {
            "retrieved_docs": retrieved_docs,
            "sources": sources,
            "num_images": len(image_docs),
            "num_text_chunks": len(text_docs),
            "top_similarity": top_similarity,
        }

    def is_initialized(self) -> bool:
        """Check if the RAG system is initialized."""
        return self._initialized

    def reset(self):
        """Reset the RAG system state."""
        self._initialized = False
        self.text_vectorStore = None
        self.image_vectorStore = None
        self.bm25_retriever = None
        self.all_docs = []
        self.all_embeddings = []
        self.text_docs = []
        self.image_data_store = {}
        self.vision_llm = None
        logger.info("RAG system reset.")
