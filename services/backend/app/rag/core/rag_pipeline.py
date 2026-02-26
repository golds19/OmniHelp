import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
from .retriever import MultiModalRetrieval
from .utils import filter_documents_by_type
from .config import HybridSearchConfig
from .embedder import get_embedder
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever

logger = logging.getLogger(__name__)


def _compute_confidence(top_similarity: float, num_chunks: int) -> float:
    """
    Compute a confidence score blending retrieval similarity and chunk coverage.

    - Similarity component (70%): how well the top result matches the query
    - Coverage component (30%): how many chunks were retrieved (caps at k=5)

    Returns:
        float in [0, 1], rounded to 3 decimal places
    """
    sim_score = min(top_similarity, 1.0)
    chunk_score = min(num_chunks / 5.0, 1.0)
    return round(0.7 * sim_score + 0.3 * chunk_score, 3)


def _compute_answer_source_similarity(answer: str, text_docs) -> float:
    """
    Compute the maximum cosine similarity between the LLM answer and any
    retrieved text chunk.

    CLIP embeddings are L2-normalized unit vectors, so cosine similarity
    equals the dot product.

    Returns:
        float in [0, 1] — higher means the answer is better grounded in sources.
        Returns 0.0 if there are no text chunks or the answer is empty.
    """
    if not text_docs or not answer.strip():
        return 0.0
    embedder = get_embedder()
    answer_emb = embedder.embed_text(answer)
    max_sim = 0.0
    for doc in text_docs:
        doc_emb = embedder.embed_text(doc.page_content)
        sim = float(np.dot(answer_emb, doc_emb))
        if sim > max_sim:
            max_sim = sim
    return round(max_sim, 3)


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

        confidence = _compute_confidence(top_similarity, num_text_chunks)
        answer_source_similarity = _compute_answer_source_similarity(response.content, text_docs)
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
