from dataclasses import dataclass
from typing import Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from .embedder import get_embedder
from .hybrid_retriever import HybridMultiModalRetrieval
from .config import HybridSearchConfig
from .utils import create_multimodal_message


@dataclass
class MultiModalRetrieval:
    """
    Class for unified retrieval of text and images using CLIP embeddings.
    Supports both dense-only and hybrid (BM25 + Dense) search modes.
    """
    query: str
    vectorStore: FAISS
    image_data_store: Dict
    k: int = 5
    bm25_retriever: Optional[BM25Retriever] = None
    use_hybrid: bool = True

    def __post_init__(self):
        """Initialize the CLIPEmbedder instance after dataclass initialization."""
        self.embedder = get_embedder()

    def retrieve_multimodal(self):
        """
        Unified retrieval for text and images.
        Automatically chooses between hybrid and dense-only based on configuration.

        Returns:
            List of retrieved documents
        """
        # Use hybrid search if enabled and BM25 retriever is available
        if self.use_hybrid and HybridSearchConfig.HYBRID_SEARCH_ENABLED and self.bm25_retriever is not None:
            hybrid_retriever = HybridMultiModalRetrieval(
                query=self.query,
                faiss_store=self.vectorStore,
                bm25_retriever=self.bm25_retriever,
                image_data_store=self.image_data_store,
                k=self.k,
                use_hybrid=True
            )
            return hybrid_retriever.retrieve_multimodal()
        else:
            # Fallback to dense-only search
            query_embedding = self.embedder.embed_text(self.query).tolist()
            results = self.vectorStore.similarity_search_by_vector(
                embedding=query_embedding,
                k=self.k
            )
            return results

    def create_multimodal_message(self, retrieved_docs):
        """
        Create a message with both text and images for GPT-4V.

        Args:
            retrieved_docs: List of retrieved documents

        Returns:
            HumanMessage: Formatted message for the LLM
        """
        return create_multimodal_message(self.query, retrieved_docs, self.image_data_store)
