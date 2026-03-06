from dataclasses import dataclass
from typing import Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from .embedder import get_text_embedder, get_embedder
from .hybrid_retriever import HybridMultiModalRetrieval
from .config import HybridSearchConfig
from .utils import create_multimodal_message


@dataclass
class MultiModalRetrieval:
    """
    Unified retrieval wrapper supporting hybrid (BM25 + dense) and dense-only search.

    text_faiss_store  — sentence-transformers FAISS (384-dim) for text chunks.
    image_faiss_store — CLIP FAISS (512-dim) for images; may be None.
    text_vectorStore may be None for image-only sessions.
    """
    query: str
    text_vectorStore: Optional[FAISS]
    image_data_store: Dict
    k: int = 5
    bm25_retriever: Optional[BM25Retriever] = None
    image_vectorStore: Optional[FAISS] = None
    use_hybrid: bool = True

    def retrieve_multimodal(self) -> Dict:
        """
        Retrieve documents using hybrid or dense-only search.

        Returns:
            Dict with keys "docs" (List[Document]) and "top_similarity" (float).
        """
        # Image-only session: no text index — use CLIP text encoder to cross-modal search
        if self.text_vectorStore is None:
            if self.image_vectorStore is None:
                return {"docs": [], "top_similarity": 0.0}
            img_emb = get_embedder().embed_text(self.query).tolist()
            scored = self.image_vectorStore.similarity_search_with_score_by_vector(
                embedding=img_emb, k=self.k
            )
            docs = [doc for doc, _ in scored]
            top_similarity = float(1 / (1 + scored[0][1])) if scored else 0.0
            return {"docs": docs, "top_similarity": top_similarity}

        if (
            self.use_hybrid
            and HybridSearchConfig.HYBRID_SEARCH_ENABLED
            and self.bm25_retriever is not None
        ):
            retriever = HybridMultiModalRetrieval(
                query=self.query,
                text_faiss_store=self.text_vectorStore,
                image_faiss_store=self.image_vectorStore,
                bm25_retriever=self.bm25_retriever,
                image_data_store=self.image_data_store,
                k=self.k,
                use_hybrid=True,
            )
            return retriever.retrieve_multimodal()

        # Fallback: dense-only search on the text index
        text_emb = get_text_embedder().encode(self.query, normalize_embeddings=True).tolist()
        scored = self.text_vectorStore.similarity_search_with_score_by_vector(
            embedding=text_emb, k=self.k
        )
        docs = [doc for doc, _ in scored]
        top_similarity = float(1 / (1 + scored[0][1])) if scored else 0.0
        return {"docs": docs, "top_similarity": top_similarity}

    def create_multimodal_message(self, retrieved_docs):
        """Create a multimodal message (text + images) for the LLM."""
        return create_multimodal_message(self.query, retrieved_docs, self.image_data_store)
