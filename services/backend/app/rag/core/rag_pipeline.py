import logging
from dataclasses import dataclass
from typing import Dict, Optional
from .retriever import MultiModalRetrieval
from .utils import filter_documents_by_type
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever

logger = logging.getLogger(__name__)


@dataclass
class MultiModalRAG:
    """
    Main pipeline for multimodal RAG (Retrieval-Augmented Generation).
    Supports both dense-only and hybrid (BM25 + Dense) search modes.
    """
    query: str
    vectorStore: FAISS
    image_data_store: Dict
    llm: ChatOpenAI
    k: int = 5
    bm25_retriever: Optional[BM25Retriever] = None
    use_hybrid: bool = True

    def generate(self):
        """
        Main pipeline for multimodal RAG.
        Supports both hybrid (BM25 + Dense) and dense-only search.

        Returns:
            Dict: Contains answer, sources, and metadata
        """
        # Retrieve relevant documents
        retriever = MultiModalRetrieval(
            query=self.query,
            vectorStore=self.vectorStore,
            image_data_store=self.image_data_store,
            k=self.k,
            bm25_retriever=self.bm25_retriever,
            use_hybrid=self.use_hybrid
        )
        context_docs = retriever.retrieve_multimodal()

        # Create multimodal message
        message = retriever.create_multimodal_message(context_docs)

        # Get response from LLM
        response = self.llm.invoke([message])

        # Log retrieved context info
        logger.debug(f"Retrieved {len(context_docs)} documents for context")

        # Return both response and metadata
        text_docs, image_docs = filter_documents_by_type(context_docs)
        return {
            "answer": response.content,
            "sources": [{"page": doc.metadata["page"], "type": doc.metadata["type"]}
                       for doc in context_docs],
            "num_images": len(image_docs),
            "num_text_chunks": len(text_docs)
        }