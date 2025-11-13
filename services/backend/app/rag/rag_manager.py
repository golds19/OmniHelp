"""
Singleton class to manage the multimodal RAG system state.
This ensures we don't rebuild embeddings on every query.
"""

from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from .data_ingestion import DataEmbedding
from .vectorstore import VectorStore


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
            print("RAG system already initialized. Skipping...")
            return

        print(f"Initializing multimodal RAG system with {pdf_path}...")

        # Load and embed data
        data_embedder = DataEmbedding(pdf_path=pdf_path)
        self.all_docs, self.all_embeddings, self.image_data_store = \
            data_embedder.process_and_embedd_docs()

        # Create vector store
        vs = VectorStore(
            all_docs=self.all_docs,
            all_embeddings=self.all_embeddings,
            image_data_store=self.image_data_store
        )
        self.vectorStore = vs.create_vectorstore()

        # Store vision LLM
        self.vision_llm = vision_llm

        self._initialized = True
        print(f"✓ RAG system initialized with {len(self.all_docs)} documents")

    def query(self, question: str, k: int = 5) -> Dict:
        """
        Query the multimodal RAG system.

        Args:
            question: The query text
            k: Number of documents to retrieve

        Returns:
            Dict containing retrieved_docs, sources, num_images, num_text_chunks
        """
        if not self._initialized:
            raise RuntimeError("RAG system not initialized. Please load a document first.")

        from .retriever import MultiModalRetrieval

        # Retrieve documents
        retriever = MultiModalRetrieval(
            query=question,
            vectorStore=self.vectorStore,
            image_data_store=self.image_data_store,
            k=k
        )
        retrieved_docs = retriever.retrieve_multimodal()

        # Prepare metadata
        sources = [
            {"page": doc.metadata["page"], "type": doc.metadata["type"]}
            for doc in retrieved_docs
        ]
        num_images = len([doc for doc in retrieved_docs if doc.metadata.get("type") == "image"])
        num_text_chunks = len([doc for doc in retrieved_docs if doc.metadata.get("type") == "text"])

        return {
            "retrieved_docs": retrieved_docs,
            "sources": sources,
            "num_images": num_images,
            "num_text_chunks": num_text_chunks
        }

    def is_initialized(self) -> bool:
        """Check if the RAG system is initialized."""
        return self._initialized

    def reset(self):
        """Reset the RAG system state."""
        self._initialized = False
        self.vectorStore = None
        self.all_docs = []
        self.all_embeddings = []
        self.image_data_store = {}
        self.vision_llm = None
        print("RAG system reset.")
