"""
Shared metric helpers used by both the standard RAG pipeline and the agentic path.
"""
import numpy as np
from .embedder import get_text_embedder


def compute_confidence(top_similarity: float, num_chunks: int) -> float:
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


def compute_answer_source_similarity(answer: str, text_docs: list) -> float:
    """
    Compute the maximum cosine similarity between the LLM answer and any
    retrieved text chunk using sentence-transformers (384-dim).

    sentence-transformers produces L2-normalized unit vectors, so cosine
    similarity equals the dot product. Unlike CLIP, this model has no token
    limit — long answers and long chunks are embedded correctly.

    Returns:
        float in [0, 1] — higher means the answer is better grounded in sources.
        Returns 0.0 if there are no text chunks or the answer is empty.
    """
    if not text_docs or not answer.strip():
        return 0.0

    text_embedder = get_text_embedder()
    answer_emb = text_embedder.encode(answer, normalize_embeddings=True)
    max_sim = 0.0
    for doc in text_docs:
        doc_emb = text_embedder.encode(doc.page_content, normalize_embeddings=True)
        sim = float(np.dot(answer_emb, doc_emb))
        if sim > max_sim:
            max_sim = sim
    return round(max_sim, 3)
