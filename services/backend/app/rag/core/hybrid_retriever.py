import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from .embedder import get_embedder
from .config import HybridSearchConfig
from .utils import create_multimodal_message

logger = logging.getLogger(__name__)


@dataclass
class HybridMultiModalRetrieval:
    """
    Class for hybrid retrieval combining BM25 (sparse) and FAISS (dense) retrievers
    using Reciprocal Rank Fusion (RRF).
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

    def retrieve_dense_only(self) -> List[Tuple[Document, float]]:
        """
        Dense-only retrieval using FAISS with CLIP embeddings.
        (Fallback for when hybrid is disabled)

        Returns:
            List of (Document, score) tuples where score is an L2 distance
        """
        query_embedding = self.embedder.embed_text(self.query).tolist()
        results = self.faiss_store.similarity_search_with_score_by_vector(
            embedding=query_embedding,
            k=self.k
        )
        return results

    def retrieve_hybrid(self) -> List[Document]:
        """
        Hybrid retrieval using BM25 + Dense with inline Reciprocal Rank Fusion (RRF).

        Returns:
            List of retrieved documents
        """
        if self.bm25_retriever is None:
            logger.warning("BM25 retriever not available, falling back to dense-only search")
            return [doc for doc, _ in self.retrieve_dense_only()]

        # Create dense retriever from FAISS store
        dense_retriever = self.faiss_store.as_retriever(
            search_kwargs={"k": HybridSearchConfig.K_DENSE_CANDIDATES}
        )

        bm25_docs = self.bm25_retriever.invoke(self.query)
        dense_docs = dense_retriever.invoke(self.query)

        # Reciprocal Rank Fusion with configured weights
        rrf_scores: dict = {}
        doc_map: dict = {}
        for rank, doc in enumerate(bm25_docs):
            key = doc.page_content[:200]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + HybridSearchConfig.BM25_WEIGHT / (HybridSearchConfig.RRF_K_CONSTANT + rank + 1)
            doc_map[key] = doc
        for rank, doc in enumerate(dense_docs):
            key = doc.page_content[:200]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + HybridSearchConfig.DENSE_WEIGHT / (HybridSearchConfig.RRF_K_CONSTANT + rank + 1)
            doc_map[key] = doc

        sorted_keys = sorted(rrf_scores, key=lambda k: rrf_scores[k], reverse=True)
        return [doc_map[k] for k in sorted_keys[:self.k]]

    def _get_top_similarity(self, docs: List[Document]) -> float:
        """
        Get the top similarity score by re-querying FAISS for the single best match.
        Used for the hybrid path where RRF doesn't expose raw scores.

        L2 distance is converted to a 0–1 similarity via 1 / (1 + distance).

        Returns:
            float in [0, 1] — higher means more similar
        """
        if not docs:
            return 0.0
        query_embedding = self.embedder.embed_text(self.query).tolist()
        scored = self.faiss_store.similarity_search_with_score_by_vector(
            embedding=query_embedding, k=1
        )
        if scored:
            distance = scored[0][1]
            return float(1 / (1 + distance))
        return 0.0

    def retrieve_multimodal(self) -> Dict:
        """
        Main retrieval method that chooses between hybrid or dense-only search.

        Returns:
            Dict with keys:
              - "docs": List[Document]
              - "top_similarity": float in [0, 1]
        """
        if self.use_hybrid and HybridSearchConfig.HYBRID_SEARCH_ENABLED:
            logger.info(f"Using hybrid search (BM25: {HybridSearchConfig.BM25_WEIGHT}, Dense: {HybridSearchConfig.DENSE_WEIGHT})")
            docs = self.retrieve_hybrid()
            top_similarity = self._get_top_similarity(docs)
        else:
            logger.info("Using dense-only search")
            scored = self.retrieve_dense_only()
            docs = [doc for doc, _ in scored]
            top_similarity = float(1 / (1 + scored[0][1])) if scored else 0.0

        return {"docs": docs, "top_similarity": top_similarity}

    def create_multimodal_message_for_docs(self, retrieved_docs):
        """
        Create a message with both text and images for GPT-4V.

        Args:
            retrieved_docs: List of retrieved documents

        Returns:
            HumanMessage: Formatted message for the LLM
        """
        return create_multimodal_message(self.query, retrieved_docs, self.image_data_store)
