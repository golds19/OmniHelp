import logging
from dataclasses import dataclass
from typing import Dict, Optional
from .retriever import MultiModalRetrieval
from .utils import filter_documents_by_type
from .config import HybridSearchConfig
from .metrics import compute_confidence, compute_answer_source_similarity
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
            Dict: Contains answer, sources, metadata, confidence, top_similarity,
                  answer_source_similarity, and is_hallucination
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
        retrieval_result = retriever.retrieve_multimodal()
        context_docs = retrieval_result["docs"]
        top_similarity = retrieval_result["top_similarity"]

        # Log retrieved context info
        logger.debug(f"Retrieved {len(context_docs)} documents for context (top_similarity={top_similarity:.3f})")

        text_docs, image_docs = filter_documents_by_type(context_docs)
        num_text_chunks = len(text_docs)

        # Guardrail: reject queries with insufficient context
        if top_similarity < HybridSearchConfig.MIN_SIMILARITY_THRESHOLD:
            logger.info(f"Query rejected: top_similarity {top_similarity:.3f} < threshold {HybridSearchConfig.MIN_SIMILARITY_THRESHOLD}")
            return {
                "answer": "I don't have enough information in the uploaded documents to answer this question.",
                "sources": [],
                "num_images": 0,
                "num_text_chunks": 0,
                "confidence": 0.0,
                "top_similarity": top_similarity,
                "answer_source_similarity": 0.0,
                "is_hallucination": False,
            }

        # Create multimodal message and call LLM
        message = retriever.create_multimodal_message(context_docs)
        response = self.llm.invoke([message])

        confidence = compute_confidence(top_similarity, num_text_chunks)
        answer_source_similarity = compute_answer_source_similarity(response.content, text_docs)
        is_hallucination = answer_source_similarity < HybridSearchConfig.HALLUCINATION_THRESHOLD

        if is_hallucination:
            logger.warning(
                f"Hallucination flagged: answer_source_similarity {answer_source_similarity:.3f} "
                f"< threshold {HybridSearchConfig.HALLUCINATION_THRESHOLD}"
            )

        return {
            "answer": response.content,
            "sources": [{"page": doc.metadata["page"], "type": doc.metadata["type"]}
                       for doc in context_docs],
            "num_images": len(image_docs),
            "num_text_chunks": num_text_chunks,
            "confidence": confidence,
            "top_similarity": top_similarity,
            "answer_source_similarity": answer_source_similarity,
            "is_hallucination": is_hallucination,
        }
