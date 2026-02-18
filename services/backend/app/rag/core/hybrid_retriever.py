import logging
from dataclasses import dataclass
from typing import Dict, List
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from .embedder import get_embedder
from .config import HybridSearchConfig
from .utils import create_multimodal_message

logger = logging.getLogger(__name__)


@dataclass
class HybridMultiModalRetrieval:
    """
    Class for hybrid retrieval combining BM25 (sparse) and FAISS (dense) retrievers
    using EnsembleRetriever for automatic fusion.
    """
    query: str
    faiss_store: FAISS
    bm25_retriever: BM25Retriever
    image_data_store: Dict
    k: int = 5
    use_hybrid: bool = True

    def __post_init__(self):
        """Initialize the CLIPEmbedder instance after dataclass initialization."""
        self.embedder = get_embedder()

    def retrieve_dense_only(self):
        """
        Dense-only retrieval using FAISS with CLIP embeddings.
        (Fallback for when hybrid is disabled)

        Returns:
            List of retrieved documents
        """
        # Embed query using CLIP
        query_embedding = self.embedder.embed_text(self.query).tolist()

        # Search in unified vector store
        results = self.faiss_store.similarity_search_by_vector(
            embedding=query_embedding,
            k=self.k
        )
        return results

    def retrieve_hybrid(self):
        """
        Hybrid retrieval using EnsembleRetriever (BM25 + Dense).
        Uses LangChain's built-in Reciprocal Rank Fusion (RRF).

        Returns:
            List of retrieved documents
        """
        # Check if BM25 retriever is available
        if self.bm25_retriever is None:
            logger.warning("BM25 retriever not available, falling back to dense-only search")
            return self.retrieve_dense_only()

        # Create dense retriever from FAISS store
        dense_retriever = self.faiss_store.as_retriever(
            search_kwargs={"k": HybridSearchConfig.K_DENSE_CANDIDATES}
        )

        # Create ensemble retriever with both sparse and dense
        ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, dense_retriever],
            weights=[HybridSearchConfig.BM25_WEIGHT, HybridSearchConfig.DENSE_WEIGHT]
        )

        # Retrieve documents using hybrid search
        results = ensemble_retriever.invoke(self.query)

        # Limit to top-k results
        return results[:self.k]

    def retrieve_multimodal(self):
        """
        Main retrieval method that chooses between hybrid or dense-only search.

        Returns:
            List of retrieved documents
        """
        if self.use_hybrid and HybridSearchConfig.HYBRID_SEARCH_ENABLED:
            logger.info(f"Using hybrid search (BM25: {HybridSearchConfig.BM25_WEIGHT}, Dense: {HybridSearchConfig.DENSE_WEIGHT})")
            return self.retrieve_hybrid()
        else:
            logger.info("Using dense-only search")
            return self.retrieve_dense_only()

    def create_multimodal_message_for_docs(self, retrieved_docs):
        """
        Create a message with both text and images for GPT-4V.

        Args:
            retrieved_docs: List of retrieved documents

        Returns:
            HumanMessage: Formatted message for the LLM
        """
        return create_multimodal_message(self.query, retrieved_docs, self.image_data_store)
