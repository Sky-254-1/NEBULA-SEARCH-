"""Result reranking with BM25, vector scores, and fusion strategies."""

import logging
from typing import Optional

from vector.bm25 import BM25Okapi, tokenize
from vector.fusion import reciprocal_rank_fusion, linear_fusion, adaptive_fusion

logger = logging.getLogger("nebula.vector.ranking")


def rerank(
    results: list[dict],
    query: Optional[str] = None,
    boost_recent: bool = True,
    fusion_method: str = "linear",
    bm25_weight: float = 0.3,
    vector_weight: float = 0.7,
) -> list[dict]:
    """Rerank search results using hybrid scoring.

    Args:
        results: List of result dicts with 'content', 'score', 'vector_score', 'keyword_score'
        query: Original search query (for BM25 scoring)
        boost_recent: Whether to apply recency boost
        fusion_method: 'linear', 'rrf', or 'adaptive'
        bm25_weight: Weight for BM25 scores (linear fusion only)
        vector_weight: Weight for vector scores (linear fusion only)

    Returns:
        Reranked results list
    """
    if not results:
        return results

    # Apply BM25 scoring if query is provided
    if query and len(results) > 1:
        try:
            corpus = [r.get("content", "") for r in results]
            bm25 = BM25Okapi(corpus)
            bm25_scores = bm25.scores(query)

            for i, r in enumerate(results):
                r["bm25_score"] = bm25_scores[i]
        except Exception as exc:
            logger.debug("BM25 scoring failed: %s", exc)

    # Apply fusion strategy
    if query and len(results) > 1:
        try:
            bm25_pairs = [(i, r.get("bm25_score", 0)) for i, r in enumerate(results)]
            vector_pairs = [(i, r.get("vector_score", r.get("score", 0))) for i, r in enumerate(results)]

            query_length = len(tokenize(query))

            if fusion_method == "rrf":
                fused = reciprocal_rank_fusion(bm25_pairs, vector_pairs, top_n=len(results))
            elif fusion_method == "adaptive":
                fused = adaptive_fusion(bm25_pairs, vector_pairs, query_length, top_n=len(results))
            else:
                fused = linear_fusion(bm25_pairs, vector_pairs, bm25_weight, vector_weight, top_n=len(results))

            # Apply fused scores
            score_map = dict(fused)
            for i, r in enumerate(results):
                r["fused_score"] = score_map.get(i, 0)
                r["score"] = r["fused_score"]
        except Exception as exc:
            logger.debug("Fusion failed: %s", exc)

    # Apply recency boost
    if boost_recent:
        for i, item in enumerate(results):
            recency = 1.0 / (1 + i * 0.01)
            item["score"] = item.get("score", 0) * recency

    # Sort by final score
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results


def rerank_with_explanations(
    results: list[dict],
    query: str,
) -> list[dict]:
    """Rerank and add explanation for each result's score."""
    results = rerank(results, query, fusion_method="adaptive")

    for r in results:
        parts = []
        if "bm25_score" in r:
            parts.append(f"BM25={r['bm25_score']:.3f}")
        if "vector_score" in r:
            parts.append(f"Vector={r['vector_score']:.3f}")
        if "keyword_score" in r:
            parts.append(f"Keyword={r['keyword_score']:.3f}")
        r["score_explanation"] = " + ".join(parts) if parts else ""

    return results