"""
Hybrid Search Engine

Combines keyword and semantic search with intelligent result merging:
- Parallel retrieval from multiple sources
- Score normalization
- Intelligent result merging
- Configurable weighting between lexical and semantic signals
"""

import logging
from typing import Any, Dict, List, Optional

from app.search.ranking_service import ranking_service

logger = logging.getLogger("nebula.search.hybrid")


class HybridSearchEngine:
    """
    Hybrid search combining keyword and semantic retrieval.
    
    Features:
    - Parallel web and vector search
    - Score normalization across different sources
    - Intelligent result merging and deduplication
    - Configurable lexical/semantic weighting
    - Low-latency response times
    """
    
    def __init__(
        self,
        lexical_weight: float = 0.5,
        semantic_weight: float = 0.5,
        enable_deduplication: bool = True,
        enable_reranking: bool = True,
    ):
        """
        Initialize hybrid search engine.
        
        Args:
            lexical_weight: Weight for keyword search results (0.0-1.0)
            semantic_weight: Weight for semantic search results (0.0-1.0)
            enable_deduplication: Remove duplicate results
            enable_reranking: Apply ranking service to final results
        """
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        self.enable_deduplication = enable_deduplication
        self.enable_reranking = enable_reranking
        
        # Normalize weights
        total = lexical_weight + semantic_weight
        self.lexical_weight /= total
        self.semantic_weight /= total
    
    async def search(
        self,
        query: str,
        db: Any = None,
        user_id: Optional[int] = None,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            db: Database connection
            user_id: User ID for personalization
            top_k: Number of results to return
            filters: Optional filters
            
        Returns:
            List of search results with scores
        """
        web_results = []
        vector_results = []
        
        # Fetch web results (keyword search)
        try:
            from app.services.search import run_web_search
            web_raw = await run_web_search(query, backend="wikipedia", page=1, page_size=top_k)
            
            web_results = [
                {
                    "id": f"web_{i}",
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "content": r.get("snippet", ""),
                    "url": r.get("url", ""),
                    "source": "web",
                    "lexical_score": r.get("score", 0.5),
                    "semantic_score": 0.0,
                }
                for i, r in enumerate(web_raw, 1)
            ]
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
        
        # Fetch vector results (semantic search)
        try:
            from vector.pipeline import hybrid_search as vector_hybrid_search
            vector_raw = await vector_hybrid_search(db, user_id, query, top_k=top_k)
            
            vector_results = [
                {
                    "id": r.get("chunk_id", f"vec_{i}"),
                    "title": r.get("filename", ""),
                    "snippet": r.get("content", "")[:200],
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "source": "vector",
                    "lexical_score": r.get("keyword_score", 0.0),
                    "semantic_score": r.get("vector_score", 0.5),
                }
                for i, r in enumerate(vector_raw, 1)
            ]
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
        
        # Merge results
        merged = self._merge_results(web_results, vector_results, top_k)
        
        # Apply ranking
        if self.enable_reranking:
            user_profile = None
            if user_id:
                try:
                    from app.search.intelligence import personalization_engine
                    user_profile = await personalization_engine.get_user_profile(user_id)
                except Exception as exc:
                    logger.debug("Personalization profile fetch failed: %s", exc)
            
            merged = await ranking_service.rank(query, merged, user_profile)
        
        return merged[:top_k]
    
    def _merge_results(
        self,
        web_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Merge and normalize results from different sources.
        
        Args:
            web_results: Web search results
            vector_results: Vector search results
            top_k: Target number of results
            
        Returns:
            Merged and normalized results
        """
        # Normalize scores to 0-1 range
        web_results = self._normalize_scores(web_results, "lexical_score")
        vector_results = self._normalize_scores(vector_results, "semantic_score")
        
        # Combine results
        all_results = []
        
        # Add web results with lexical weight
        for result in web_results:
            result = result.copy()
            lexical_score = result.get("lexical_score", 0.0)
            semantic_score = result.get("semantic_score", 0.0)
            
            # Calculate combined score
            result["score"] = (
                self.lexical_weight * lexical_score
                + self.semantic_weight * semantic_score
            )
            result["scores"] = {
                "lexical": lexical_score,
                "semantic": semantic_score,
            }
            
            all_results.append(result)
        
        # Add vector results with semantic weight
        for result in vector_results:
            result = result.copy()
            lexical_score = result.get("lexical_score", 0.0)
            semantic_score = result.get("semantic_score", 0.0)
            
            # Calculate combined score
            result["score"] = (
                self.lexical_weight * lexical_score
                + self.semantic_weight * semantic_score
            )
            result["scores"] = {
                "lexical": lexical_score,
                "semantic": semantic_score,
            }
            
            all_results.append(result)
        
        # Deduplicate if enabled
        if self.enable_deduplication:
            all_results = self._deduplicate(all_results)
        
        # Sort by score
        all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return all_results[:top_k]
    
    def _normalize_scores(
        self, results: List[Dict[str, Any]], score_key: str
    ) -> List[Dict[str, Any]]:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            results: Search results
            score_key: Key containing the score to normalize
            
        Returns:
            Results with normalized scores
        """
        if not results:
            return results
        
        scores = [r.get(score_key, 0.0) for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        # Avoid division by zero
        if max_score == min_score:
            for result in results:
                result[score_key] = 0.5
            return results
        
        # Normalize
        for result in results:
            score = result.get(score_key, 0.0)
            normalized = (score - min_score) / (max_score - min_score)
            result[score_key] = normalized
        
        return results
    
    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate results based on URL or content similarity.
        
        Args:
            results: Search results
            
        Returns:
            Deduplicated results
        """
        seen_urls = set()
        seen_content = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "").strip().lower()
            content = result.get("content", "")[:100].strip().lower()
            
            # Skip if URL or content already seen
            if url and url in seen_urls:
                continue
            
            if content and content in seen_content:
                continue
            
            # Add to unique results
            unique_results.append(result)
            
            if url:
                seen_urls.add(url)
            if content:
                seen_content.add(content)
        
        return unique_results
    
    def update_weights(self, lexical_weight: float, semantic_weight: float):
        """
        Update search weights.
        
        Args:
            lexical_weight: New lexical weight
            semantic_weight: New semantic weight
        """
        total = lexical_weight + semantic_weight
        self.lexical_weight = lexical_weight / total
        self.semantic_weight = semantic_weight / total
        
        logger.info(
            f"Updated weights: lexical={self.lexical_weight:.2f}, "
            f"semantic={self.semantic_weight:.2f}"
        )


# Global instance
hybrid_search_engine = HybridSearchEngine()