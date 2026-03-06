import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
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
    Hybrid retrieval combining BM25 (sparse) and two FAISS indexes (dense) via RRF.

    text_faiss_store  — 384-dim sentence-transformers index over text chunks.
                        Query embedding is handled automatically by the attached
                        SentenceTransformerEmbeddingWrapper.
    image_faiss_store — 512-dim CLIP index over images (optional).
                        Queried with CLIP's text encoder for cross-modal retrieval.
    """
    query: str
    text_faiss_store: Optional[FAISS]
    image_data_store: Dict
    bm25_retriever: Optional[BM25Retriever] = None
    image_faiss_store: Optional[FAISS] = None
    k: int = 5
    use_hybrid: bool = True

    def retrieve_dense_only(self) -> List[Tuple[Document, float]]:
        """
        Dense-only retrieval from the text FAISS index.
        The SentenceTransformerEmbeddingWrapper handles query embedding automatically.

        Returns:
            List of (Document, L2-distance) tuples
        """
        if self.text_faiss_store is None:
            return []
        results = self.text_faiss_store.similarity_search_with_score(self.query, k=self.k)
        return results

    def retrieve_hybrid(self) -> List[Document]:
        """
        Hybrid retrieval: BM25 + text FAISS + (optionally) image FAISS via RRF.

        Returns:
            List of retrieved documents (text and/or image), ranked by RRF score.
        """
        if self.bm25_retriever is None:
            logger.warning("BM25 retriever not available, falling back to dense-only search")
            return [doc for doc, _ in self.retrieve_dense_only()]

        # --- Text retrieval: BM25 + text FAISS ---
        text_dense_retriever = self.text_faiss_store.as_retriever(
            search_kwargs={"k": HybridSearchConfig.K_DENSE_CANDIDATES}
        )
        bm25_docs = self.bm25_retriever.invoke(self.query)
        text_dense_docs = text_dense_retriever.invoke(self.query)

        # --- Image retrieval: CLIP cross-modal ---
        image_docs: List[Document] = []
        if self.image_faiss_store is not None:
            try:
                clip_embed = get_embedder().embed_text(self.query).tolist()
                image_results = self.image_faiss_store.similarity_search_with_score_by_vector(
                    clip_embed, k=HybridSearchConfig.K_DENSE_CANDIDATES
                )
                image_docs = [doc for doc, _ in image_results]
            except Exception as e:
                logger.warning(f"Image FAISS search failed: {e}")

        # --- RRF fusion ---
        rrf_scores: dict = {}
        doc_map: dict = {}

        def _add(docs: List[Document], weight: float):
            for rank, doc in enumerate(docs):
                key = doc.page_content[:200]
                rrf_scores[key] = rrf_scores.get(key, 0.0) + weight / (
                    HybridSearchConfig.RRF_K_CONSTANT + rank + 1
                )
                doc_map[key] = doc

        _add(bm25_docs, HybridSearchConfig.BM25_WEIGHT)
        _add(text_dense_docs, HybridSearchConfig.DENSE_WEIGHT)
        # Images get the dense weight — they are a parallel dense retrieval path
        _add(image_docs, HybridSearchConfig.DENSE_WEIGHT)

        sorted_keys = sorted(rrf_scores, key=lambda k: rrf_scores[k], reverse=True)
        return [doc_map[k] for k in sorted_keys[: self.k]]

    def _get_top_similarity(self, docs: List[Document]) -> float:
        """
        Top similarity score from the text FAISS index (L2 → [0,1] similarity).
        Image docs are excluded — their L2 distance is in a different space.
        """
        if not docs or self.text_faiss_store is None:
            return 0.0
        scored = self.text_faiss_store.similarity_search_with_score(self.query, k=1)
        if scored:
            distance = scored[0][1]
            return float(1 / (1 + distance))
        return 0.0

    def retrieve_multimodal(self) -> Dict:
        """
        Main entry point. Chooses hybrid or dense-only based on configuration.

        Returns:
            Dict with keys:
              - "docs":           List[Document]
              - "top_similarity": float in [0, 1]
        """
        if self.use_hybrid and HybridSearchConfig.HYBRID_SEARCH_ENABLED:
            logger.info(
                f"Using hybrid search (BM25: {HybridSearchConfig.BM25_WEIGHT}, "
                f"Dense: {HybridSearchConfig.DENSE_WEIGHT})"
            )
            docs = self.retrieve_hybrid()
            top_similarity = self._get_top_similarity(docs)
        else:
            logger.info("Using dense-only search")
            scored = self.retrieve_dense_only()
            docs = [doc for doc, _ in scored]
            top_similarity = float(1 / (1 + scored[0][1])) if scored else 0.0

        return {"docs": docs, "top_similarity": top_similarity}

    def create_multimodal_message_for_docs(self, retrieved_docs):
        """Create a multimodal message (text + images) for the LLM."""
        return create_multimodal_message(self.query, retrieved_docs, self.image_data_store)
