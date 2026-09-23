"""
Scoring Engine

Unified scoring system combining all ranking signals.
"""

import logging
from typing import Any, Dict, List, Optional

from app.hybrid.bm25 import BM25Engine
from app.hybrid.config import HybridSearchConfig

logger = logging.getLogger("nebula.hybrid.scoring")


class ScoringEngine:
    """
    Unified scoring engine that combines all ranking signals.
    
    Combines:
    - BM25 keyword score
    - Semantic vector score
    - Freshness score
    - Popularity score
    - Metadata quality score
    """

    def __init__(self, config: Optional[HybridSearchConfig] = None):
        """
        Initialize scoring engine.
        
        Args:
            config: Hybrid search configuration
        """
        self.config = config or HybridSearchConfig()
        self.bm25_engine = BM25Engine(
            k1=self.config.bm25_k1,
            b=self.config.bm25_b,
        )

    def score_document(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        document: Optional[Dict[str, Any]] = None,
        intent: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Score a single document with all signals.
        
        Args:
            query: Search query
            query_vector: Query embedding
            document: Document to score
            intent: Query intent analysis
            
        Returns:
            Scoring result with all components
        """
        if not document:
            return {"score": 0.0, "components": {}}
        
        # Get dynamic weights based on intent
        bm25_weight, semantic_weight = self._get_weights(intent)
        
        # Calculate BM25 score
        keyword_score = self.bm25_engine.score(query, document)
        
        # Calculate semantic score
        semantic_score = 0.0
        if query_vector and document.get("embedding"):
            import numpy as np
            q_vec = np.array(query_vector)
            d_vec = np.array(document["embedding"])
            
            # Cosine similarity
            dot = np.dot(q_vec, d_vec)
            norm1 = np.linalg.norm(q_vec)
            norm2 = np.linalg.norm(d_vec)
            if norm1 > 0 and norm2 > 0:
                semantic_score = float(dot / (norm1 * norm2))
        
        # Calculate freshness score
        freshness_score = self._calculate_freshness(document)
        
        # Calculate popularity score
        popularity_score = self._calculate_popularity(document)
        
        # Calculate metadata quality score
        metadata_score = self._calculate_metadata_quality(document)
        
        # Normalize scores
        keyword_score = min(1.0, keyword_score)
        semantic_score = min(1.0, max(0.0, semantic_score))
        freshness_score = min(1.0, freshness_score)
        popularity_score = min(1.0, popularity_score)
        metadata_score = min(1.0, metadata_score)
        
        # Calculate weighted final score
        final_score = (
            bm25_weight * keyword_score
            + semantic_weight * semantic_score
            + self.config.freshness_weight * freshness_score
            + self.config.popularity_weight * popularity_score
            + self.config.metadata_weight * metadata_score
        )
        
        return {
            "score": final_score,
            "components": {
                "keyword": {
                    "score": keyword_score,
                    "weight": bm25_weight,
                    "weighted_score": bm25_weight * keyword_score,
                },
                "semantic": {
                    "score": semantic_score,
                    "weight": semantic_weight,
                    "weighted_score": semantic_weight * semantic_score,
                },
                "freshness": {
                    "score": freshness_score,
                    "weight": self.config.freshness_weight,
                    "weighted_score": self.config.freshness_weight * freshness_score,
                },
                "popularity": {
                    "score": popularity_score,
                    "weight": self.config.popularity_weight,
                    "weighted_score": self.config.popularity_weight * popularity_score,
                },
                "metadata": {
                    "score": metadata_score,
                    "weight": self.config.metadata_weight,
                    "weighted_score": self.config.metadata_weight * metadata_score,
                },
            },
        }

    def _get_weights(self, intent: Optional[Dict[str, Any]]) -> tuple:
        """
        Get weights based on query intent.
        
        Args:
            intent: Query intent analysis
            
        Returns:
            Tuple of (keyword_weight, semantic_weight)
        """
        if not intent or not self.config.enable_dynamic_weighting:
            return self.config.bm25_weight, self.config.semantic_weight
        
        intent_type = intent.get("intent", "mixed")
        intent_weights = self.config.intent_weights.get(intent_type, {})
        
        keyword_weight = intent_weights.get("bm25", self.config.bm25_weight)
        semantic_weight = intent_weights.get("semantic", self.config.semantic_weight)
        
        # Normalize weights
        total = keyword_weight + semantic_weight
        if total > 0:
            keyword_weight /= total
            semantic_weight /= total
        
        return keyword_weight, semantic_weight

    def _calculate_freshness(self, document: Dict[str, Any]) -> float:
        """
        Calculate freshness score.
        
        Args:
            document: Document to score
            
        Returns:
            Freshness score (0-1)
        """
        updated_at = document.get("updated_at")
        if not updated_at:
            return 0.5  # Default score
        
        # Parse date
        if isinstance(updated_at, str):
            try:
                from datetime import datetime
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return 0.5
        
        # Calculate age in days
        from datetime import datetime
        now = datetime.utcnow()
        if hasattr(updated_at, 'tzinfo') and updated_at.tzinfo:
            from datetime import timezone
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        age_days = (now - updated_at).total_seconds() / 86400
        
        # Exponential decay (half-life of 7 days)
        half_life = self.config.freshness_half_life_days
        decay = 2 ** (-age_days / half_life)
        
        return decay

    def _calculate_popularity(self, document: Dict[str, Any]) -> float:
        """
        Calculate popularity score.
        
        Args:
            document: Document to score
            
        Returns:
            Popularity score (0-1)
        """
        views = document.get("views", 0)
        clicks = document.get("clicks", 0)
        
        if views == 0 and clicks == 0:
            return 0.0
        
        # Use log scale for views
        view_score = min(1.0, views / 1000.0) if views > 0 else 0.0
        click_score = min(1.0, clicks / 100.0) if clicks > 0 else 0.0
        
        # Weighted average (70% clicks, 30% views)
        return 0.7 * click_score + 0.3 * view_score

    def _calculate_metadata_quality(self, document: Dict[str, Any]) -> float:
        """
        Calculate metadata quality score.
        
        Args:
            document: Document to score
            
        Returns:
            Quality score (0-1)
        """
        score = 0.0
        
        # Title (20%)
        title = document.get("title", "")
        if title and len(title) > 5:
            score += 0.2
        
        # Author (10%)
        if document.get("author"):
            score += 0.1
        
        # Description (15%)
        desc = document.get("description", document.get("snippet", ""))
        if desc and len(desc) > 10:
            score += 0.15
        
        # Tags (15%)
        tags = document.get("tags", [])
        if tags and len(tags) > 0:
            score += 0.15
        
        # Categories (10%)
        categories = document.get("categories", [])
        if categories and len(categories) > 0:
            score += 0.1
        
        # Content length (30%)
        content = document.get("content", document.get("snippet", ""))
        word_count = len(str(content).split())
        if word_count >= 100:
            score += 0.3
        elif word_count >= 50:
            score += 0.2
        elif word_count > 0:
            score += 0.1
        
        return min(1.0, score)

    def batch_score(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
        intent: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score multiple documents.
        
        Args:
            query: Search query
            query_vector: Query embedding
            documents: Documents to score
            intent: Query intent analysis
            
        Returns:
            List of scored documents
        """
        if not documents:
            return []
        
        scored_docs = []
        for doc in documents:
            score_result = self.score_document(query, query_vector, doc, intent)
            
            result = doc.copy()
            result["score"] = score_result["score"]
            result["score_components"] = score_result["components"]
            
            scored_docs.append(result)
        
        return scored_docs