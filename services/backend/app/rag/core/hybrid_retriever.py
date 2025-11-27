from dataclasses import dataclass
from typing import Dict, List
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.schema.messages import HumanMessage
from .data_ingestion import CLIPEmbedder
from .config import HybridSearchConfig


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
        self.embedder = CLIPEmbedder()

    def retrieve_dense_only(self):
        """
        Dense-only retrieval using FAISS with CLIP embeddings.
        (Fallback for when hybrid is disabled)

        Returns:
            List of retrieved documents
        """
        # Embed query using CLIP
        query_embedding = self.embedder.embed_text(self.query)

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
            print("BM25 retriever not available, falling back to dense-only search")
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
            print(f"🔍 Using hybrid search (BM25: {HybridSearchConfig.BM25_WEIGHT}, Dense: {HybridSearchConfig.DENSE_WEIGHT})")
            return self.retrieve_hybrid()
        else:
            print("🔍 Using dense-only search")
            return self.retrieve_dense_only()

    def create_multimodal_message(self, retrieved_docs):
        """
        Create a message with both text and images for GPT-4V.

        Args:
            retrieved_docs: List of retrieved documents

        Returns:
            HumanMessage: Formatted message for the LLM
        """
        content = []

        # Add the query
        content.append({
            "type": "text",
            "text": f"Question: {self.query}\n\nContext:\n"
        })

        # Separate text and image documents
        text_docs = [doc for doc in retrieved_docs if doc.metadata.get("type") == "text"]
        image_docs = [doc for doc in retrieved_docs if doc.metadata.get("type") == "image"]

        # Add text context
        if text_docs:
            text_context = "\n\n".join([
                f"[Page {doc.metadata['page']}]: {doc.page_content}"
                for doc in text_docs
            ])
            content.append({
                "type": "text",
                "text": f"Text excerpts:\n{text_context}\n"
            })

        # Add images context
        for doc in image_docs:
            image_id = doc.metadata.get("image_id")
            if image_id and image_id in self.image_data_store:
                content.append({
                    "type": "text",
                    "text": f"\n[Image from page {doc.metadata['page']}]\n"
                })
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{self.image_data_store[image_id]}",
                        "alt_text": f"Image from page {doc.metadata['page']}"
                    }
                })

        # Add instruction
        content.append({
            "type": "text",
            "text": "\nAnswer the question based on the provided context. If the context does not contain the answer, say 'I don't know'."
        })

        return HumanMessage(content=content)
