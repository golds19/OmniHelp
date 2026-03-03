import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
import numpy as np
from .config import HybridSearchConfig
from .embedder import get_embedder, get_text_embedder

logger = logging.getLogger(__name__)


class CLIPEmbeddingWrapper(Embeddings):
    """
    LangChain Embeddings adapter backed by CLIP.

    Attached to the IMAGE FAISS index so that text queries are embedded with
    CLIP's text encoder — keeping them in the same 512-dim space as the stored
    image embeddings (cross-modal retrieval).
    """

    def __init__(self):
        self.embedder = get_embedder()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embedder.embed_text(text).tolist() for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embedder.embed_text(text).tolist()


class SentenceTransformerEmbeddingWrapper(Embeddings):
    """
    LangChain Embeddings adapter backed by sentence-transformers/all-MiniLM-L6-v2.

    Attached to the TEXT FAISS index so that both chunk indexing and query-time
    embedding use the same 384-dim model. Handles long text chunks correctly
    (no 77-token truncation).
    """

    def __init__(self):
        self.embedder = get_text_embedder()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.encode_batch(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embedder.encode(text, normalize_embeddings=True).tolist()


@dataclass
class VectorStore:
    """
    Creates and manages two FAISS vector stores — one for text, one for images —
    plus a BM25 retriever for hybrid search.

    Text chunks are embedded with sentence-transformers (384-dim).
    Images are embedded with CLIP (512-dim).
    Keeping them in separate indexes avoids dimension mismatch and lets each
    index use the optimal query-time embedding model.
    """
    all_docs: List
    all_embeddings: List
    image_data_store: Dict
    text_docs: List  # Text documents only for BM25

    def create_faiss_vectorstores(self) -> Tuple[Optional[FAISS], Optional[FAISS]]:
        """
        Build separate FAISS indexes for text chunks and image placeholders.

        Returns:
            (text_faiss_store, image_faiss_store)
            Either may be None if no documents of that type were provided.
        """
        text_pairs = [
            (doc, emb)
            for doc, emb in zip(self.all_docs, self.all_embeddings)
            if doc.metadata.get("type") != "image"
        ]
        image_pairs = [
            (doc, emb)
            for doc, emb in zip(self.all_docs, self.all_embeddings)
            if doc.metadata.get("type") == "image"
        ]

        text_store = None
        if text_pairs:
            text_docs, text_embs = zip(*text_pairs)
            text_store = FAISS.from_embeddings(
                text_embeddings=[(doc.page_content, emb) for doc, emb in zip(text_docs, text_embs)],
                embedding=SentenceTransformerEmbeddingWrapper(),
                metadatas=[doc.metadata for doc in text_docs],
            )
            logger.info(f"Created text FAISS index with {len(text_pairs)} chunks (384-dim)")

        image_store = None
        if image_pairs:
            img_docs, img_embs = zip(*image_pairs)
            image_store = FAISS.from_embeddings(
                text_embeddings=[(doc.page_content, emb) for doc, emb in zip(img_docs, img_embs)],
                embedding=CLIPEmbeddingWrapper(),
                metadatas=[doc.metadata for doc in img_docs],
            )
            logger.info(f"Created image FAISS index with {len(image_pairs)} images (512-dim)")

        return text_store, image_store

    def create_bm25_retriever(self) -> Optional[BM25Retriever]:
        """
        Create BM25 retriever for sparse (keyword-based) search over text documents.
        Images are excluded — BM25 cannot meaningfully index image placeholders.
        """
        if not self.text_docs:
            logger.warning("No text documents available for BM25 retriever")
            return None

        bm25_retriever = BM25Retriever.from_documents(self.text_docs)
        bm25_retriever.k = HybridSearchConfig.K_BM25_CANDIDATES
        return bm25_retriever

    def create_hybrid_retrievers(self) -> Dict:
        """
        Create all retrievers needed for hybrid multimodal search.

        Returns:
            Dict with keys:
                - text_faiss_store:  FAISS over text chunks (sentence-transformers, 384-dim)
                - image_faiss_store: FAISS over images (CLIP, 512-dim) — may be None
                - bm25_retriever:    BM25 over text chunks — may be None
                - image_data_store:  base64 image data
        """
        text_store, image_store = self.create_faiss_vectorstores()
        bm25_retriever = self.create_bm25_retriever()

        return {
            "text_faiss_store": text_store,
            "image_faiss_store": image_store,
            "bm25_retriever": bm25_retriever,
            "image_data_store": self.image_data_store,
        }

    # ------------------------------------------------------------------
    # Backward-compatibility shim (used by tests and the standard path)
    # ------------------------------------------------------------------

    def create_faiss_vectorstore(self) -> Optional[FAISS]:
        """Return the text FAISS store only (backward-compatible alias)."""
        text_store, _ = self.create_faiss_vectorstores()
        return text_store

    def create_vectorstore(self) -> Optional[FAISS]:
        """Alias for create_faiss_vectorstore (kept for backward compatibility)."""
        return self.create_faiss_vectorstore()
