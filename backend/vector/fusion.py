"""Score fusion strategies for hybrid search.

Implements Reciprocal Rank Fusion (RRF), linear combination,
and normalized score merging for combining BM25 and vector scores.
"""

import math
import logging
from typing import Optional

logger = logging.getLogger("nebula.vector.fusion")


def reciprocal_rank_fusion(
    bm25_results: list[tuple[int, float]],
    vector_results: list[tuple[int, float]],
    k: int = 60,
    top_n: int = 10,
) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion (RRF) for combining two ranked result sets.

    The RRF score for each item is: sum(1 / (k + rank))
    where rank is the position in each ranked list.

    Args:
        bm25_results: List of (doc_id, score) from BM25, sorted by score descending
        vector_results: List of (doc_id, score) from vector search, sorted by score descending
        k: RRF constant (typically 60)
        top_n: Number of results to return

    Returns:
        Top-n (doc_id, fused_score) pairs sorted by fused score descending
    """
    bm25_ranks = {doc_id: rank for rank, (doc_id, _) in enumerate(bm25_results)}
    vector_ranks = {doc_id: rank for rank, (doc_id, _) in enumerate(vector_results)}

    all_doc_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())

    rrf_scores: dict[int, float] = {}
    for doc_id in all_doc_ids:
        score = 0.0
        if doc_id in bm25_ranks:
            score += 1.0 / (k + bm25_ranks[doc_id])
        if doc_id in vector_ranks:
            score += 1.0 / (k + vector_ranks[doc_id])
        rrf_scores[doc_id] = score

    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]


def linear_fusion(
    bm25_results: list[tuple[int, float]],
    vector_results: list[tuple[int, float]],
    bm25_weight: float = 0.3,
    vector_weight: float = 0.7,
    top_n: int = 10,
) -> list[tuple[int, float]]:
    """Linear combination of normalized BM25 and vector scores."""
    bm25_norm = _minmax_normalize(dict(bm25_results))
    vector_norm = _minmax_normalize(dict(vector_results))

    combined: dict[int, float] = {}
    for doc_id in set(list(bm25_norm.keys()) + list(vector_norm.keys())):
        score = 0.0
        score += bm25_weight * bm25_norm.get(doc_id, 0.0)
        score += vector_weight * vector_norm.get(doc_id, 0.0)
        if score > 0:
            combined[doc_id] = score

    ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]


def adaptive_fusion(
    bm25_results: list[tuple[int, float]],
    vector_results: list[tuple[int, float]],
    query_length: int,
    top_n: int = 10,
) -> list[tuple[int, float]]:
    """Adaptive fusion that adjusts weights based on query length.

    Short queries (< 3 words): Favor BM25
    Long queries (>= 5 words): Favor vector search
    Medium queries: Balanced
    """
    if query_length <= 2:
        bm25_w, vec_w = 0.7, 0.3
    elif query_length >= 5:
        bm25_w, vec_w = 0.2, 0.8
    else:
        t = (query_length - 2) / 3.0
        bm25_w = 0.7 - t * 0.5
        vec_w = 0.3 + t * 0.5

    return linear_fusion(bm25_results, vector_results, bm25_w, vec_w, top_n)


def _minmax_normalize(scores: dict[int, float]) -> dict[int, float]:
    """Min-max normalize scores to [0, 1]."""
    if not scores:
        return {}
    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return {k: 1.0 for k in scores}
    return {k: (v - min_val) / (max_val - min_val) for k, v in scores.items()}


def score_normalize(
    score: float,
    method: str = "minmax",
    min_score: float = 0.0,
    max_score: float = 1.0,
) -> float:
    """Normalize a single score using various methods."""
    if method == "sigmoid":
        return 1.0 / (1.0 + math.exp(-score))
    elif method == "tanh":
        return math.tanh(score)
    else:
        if max_score == min_score:
            return 0.5
        return (score - min_score) / (max_score - min_score)