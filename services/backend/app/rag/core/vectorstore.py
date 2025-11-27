from dataclasses import dataclass
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
import numpy as np
from .config import HybridSearchConfig
from .data_ingestion import CLIPEmbedder


class CLIPEmbeddingWrapper(Embeddings):
    """Wrapper to make CLIPEmbedder compatible with LangChain's Embeddings interface."""

    def __init__(self):
        self.embedder = CLIPEmbedder()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return [self.embedder.embed_text(text).tolist() for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a query text."""
        return self.embedder.embed_text(text).tolist()


@dataclass
class VectorStore:
    """
    Class for creating and managing FAISS vector stores with CLIP embeddings
    and BM25 retriever for hybrid search.
    """
    all_docs: List
    all_embeddings: List
    image_data_store: Dict
    text_docs: List  # Text documents only for BM25

    def create_faiss_vectorstore(self):
        """
        Create unified FAISS vector store with CLIP embeddings.

        Returns:
            FAISS: Vector store instance
        """
        embedding_array = np.array(self.all_embeddings)

        # Create CLIP embedding wrapper for query-time embedding
        clip_embeddings = CLIPEmbeddingWrapper()

        vector_store = FAISS.from_embeddings(
            text_embeddings=[(doc.page_content, emb) for doc, emb in zip(self.all_docs, embedding_array)],
            embedding=clip_embeddings,  # Now FAISS can embed queries!
            metadatas=[doc.metadata for doc in self.all_docs]
        )
        return vector_store

    def create_bm25_retriever(self):
        """
        Create BM25 retriever for sparse (keyword-based) search.
        Only uses text documents (images excluded).

        Returns:
            BM25Retriever: BM25 retriever instance
        """
        if not self.text_docs:
            print("Warning: No text documents available for BM25 retriever")
            return None

        bm25_retriever = BM25Retriever.from_documents(self.text_docs)
        bm25_retriever.k = HybridSearchConfig.K_BM25_CANDIDATES
        return bm25_retriever

    def create_hybrid_retrievers(self):
        """
        Create both FAISS vector store and BM25 retriever for hybrid search.

        Returns:
            Dict containing:
                - faiss_store: FAISS vector store
                - bm25_retriever: BM25 retriever
                - image_data_store: Base64 image data
        """
        faiss_store = self.create_faiss_vectorstore()
        bm25_retriever = self.create_bm25_retriever()

        return {
            "faiss_store": faiss_store,
            "bm25_retriever": bm25_retriever,
            "image_data_store": self.image_data_store
        }

    # Backward compatibility - keep old method
    def create_vectorstore(self):
        """
        Create unified FAISS vector store with CLIP embeddings.
        (Kept for backward compatibility)

        Returns:
            FAISS: Vector store instance
        """
        return self.create_faiss_vectorstore()


if __name__ == "__main__":
    print("Testing")