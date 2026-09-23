"""Vector and keyword retrieval with FAISS support."""

import math
import re
import logging
from typing import Optional

from vector.embeddings import load_vector
from vector.faiss_index import get_user_index, rebuild_user_index

logger = logging.getLogger("nebula.vector.retrieval")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def keyword_score(query: str, text: str) -> float:
    q_tokens = set(re.findall(r"\w+", query.lower()))
    if not q_tokens:
        return 0.0
    t_tokens = set(re.findall(r"\w+", text.lower()))
    if not t_tokens:
        return 0.0
    overlap = len(q_tokens & t_tokens)
    return overlap / len(q_tokens)


def retrieve_chunks(
    query_vector: list[float],
    candidates: list[dict],
    query: str,
    top_k: int = 10,
    vector_weight: float = 0.7,
    use_faiss: bool = True,
    user_id: Optional[int] = None,
) -> list[dict]:
    """Retrieve chunks using hybrid vector + keyword search.

    Uses FAISS for fast vector similarity when available,
    falls back to brute-force cosine similarity.

    Args:
        query_vector: Query embedding vector
        candidates: List of candidate chunks with vector_path, content, etc.
        query: Original search query for keyword scoring
        top_k: Number of results to return
        vector_weight: Weight for vector score (0-1), keyword = 1 - vector_weight
        use_faiss: Whether to attempt FAISS search
        user_id: User ID for FAISS index lookup

    Returns:
        Top-k scored results
    """
    if not candidates:
        return []

    # Try FAISS for fast vector search
    if use_faiss and user_id is not None:
        try:
            faiss_idx = get_user_index(user_id)
            if faiss_idx.is_loaded and faiss_idx.size > 0:
                # Map candidate chunk_ids to FAISS external_ids
                chunk_vectors = []
                for item in candidates:
                    vec = load_vector(item["vector_path"])
                    chunk_vectors.append((item["chunk_id"], vec))

                # Ensure FAISS index has these vectors
                if faiss_idx.size != len(chunk_vectors):
                    faiss_idx = rebuild_user_index(user_id, chunk_vectors)

                # Search with FAISS
                faiss_results = faiss_idx.search(query_vector, top_k=top_k)
                faiss_ids = {ext_id for ext_id, _ in faiss_results}

                # Build scored results
                scored = []
                for item in candidates:
                    chunk_id = item["chunk_id"]
                    if chunk_id in faiss_ids:
                        # Get FAISS score
                        v_score = next(
                            (s for eid, s in faiss_results if eid == chunk_id), 0.0
                        )
                    else:
                        # Fallback to brute-force for items not in FAISS
                        vec = load_vector(item["vector_path"])
                        v_score = cosine_similarity(query_vector, vec)

                    k_score = keyword_score(query, item["content"])
                    hybrid = vector_weight * v_score + (1 - vector_weight) * k_score
                    scored.append({
                        **item,
                        "vector_score": v_score,
                        "keyword_score": k_score,
                        "score": hybrid,
                    })

                scored.sort(key=lambda x: x["score"], reverse=True)
                return scored[:top_k]
        except Exception as exc:
            logger.debug("FAISS search failed, falling back to brute-force: %s", exc)

    # Brute-force cosine similarity (fallback)
    scored = []
    for item in candidates:
        vec = load_vector(item["vector_path"])
        v_score = cosine_similarity(query_vector, vec)
        k_score = keyword_score(query, item["content"])
        hybrid = vector_weight * v_score + (1 - vector_weight) * k_score
        scored.append({
            **item,
            "vector_score": v_score,
            "keyword_score": k_score,
            "score": hybrid,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]