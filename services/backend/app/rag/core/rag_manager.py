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
    Singleton class to manage the multimodal RAG system state.
    Prevents reloading models and embeddings on every query.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MultiModalRAGSystem, cls).__new__(cls)
        return cls._instance

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

        # Create vector stores (FAISS + BM25)
        vs = VectorStore(
            all_docs=self.all_docs,
            all_embeddings=self.all_embeddings,
            image_data_store=self.image_data_store,
            text_docs=self.text_docs
        )

        # Create hybrid retrievers if enabled
        if HybridSearchConfig.HYBRID_SEARCH_ENABLED:
            logger.info("Creating hybrid search retrievers (BM25 + FAISS)...")
            hybrid_stores = vs.create_hybrid_retrievers()
            self.vectorStore = hybrid_stores["faiss_store"]
            self.bm25_retriever = hybrid_stores["bm25_retriever"]
            logger.info(f"Hybrid search enabled (BM25 weight: {HybridSearchConfig.BM25_WEIGHT}, Dense weight: {HybridSearchConfig.DENSE_WEIGHT})")
        else:
            logger.info("Creating FAISS vector store only...")
            self.vectorStore = vs.create_vectorstore()
            self.bm25_retriever = None
            logger.info("Dense-only search enabled")

        # Store vision LLM
        self.vision_llm = vision_llm

        self._initialized = True
        logger.info(f"RAG system initialized with {len(self.all_docs)} documents ({len(self.text_docs)} text chunks)")

    def query(self, question: str, k: int = 5, use_hybrid: bool = True) -> Dict:
        """
        Query the multimodal RAG system.
        Supports both hybrid (BM25 + Dense) and dense-only search.

        Args:
            question: The query text
            k: Number of documents to retrieve
            use_hybrid: Whether to use hybrid search (if available)

        Returns:
            Dict containing retrieved_docs, sources, num_images, num_text_chunks
        """
        if not self._initialized:
            raise RuntimeError("RAG system not initialized. Please load a document first.")


        # Retrieve documents
        retriever = MultiModalRetrieval(
            query=question,
            vectorStore=self.vectorStore,
            image_data_store=self.image_data_store,
            k=k,
            bm25_retriever=self.bm25_retriever,
            use_hybrid=use_hybrid
        )
        retrieved_docs = retriever.retrieve_multimodal()

        # Prepare metadata
        sources = [
            {"page": doc.metadata["page"], "type": doc.metadata["type"]}
            for doc in retrieved_docs
        ]
        text_docs, image_docs = filter_documents_by_type(retrieved_docs)

        return {
            "retrieved_docs": retrieved_docs,
            "sources": sources,
            "num_images": len(image_docs),
            "num_text_chunks": len(text_docs)
        }

    def is_initialized(self) -> bool:
        """Check if the RAG system is initialized."""
        return self._initialized

    def reset(self):
        """Reset the RAG system state."""
        self._initialized = False
        self.vectorStore = None
        self.bm25_retriever = None
        self.all_docs = []
        self.all_embeddings = []
        self.text_docs = []
        self.image_data_store = {}
        self.vision_llm = None
        logger.info("RAG system reset.")
