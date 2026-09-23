"""
Hybrid Ranking Engine

Combines all ranking signals into a unified final ranking.
"""

import logging
from typing import Any, Dict, List, Optional

from app.hybrid.bm25 import BM25Engine
from app.hybrid.semantic import SemanticEngine
from app.hybrid.boosting import MetadataBooster
from app.hybrid.config import HybridSearchConfig
from app.hybrid.normalization import ScoreNormalizer

logger = logging.getLogger("nebula.hybrid.ranking")


class HybridRanker:
    """
    Unified ranking engine combining all signals.
    
    Ranking pipeline:
    1. BM25 keyword scoring
    2. Semantic vector scoring
    3. Score normalization
    4. Fusion
    5. Metadata boosting
    6. Final ranking
    """

    def __init__(self, config: Optional[HybridSearchConfig] = None):
        """
        Initialize hybrid ranker.
        
        Args:
            config: Hybrid search configuration
        """
        self.config = config or HybridSearchConfig()
        
        # Initialize components
        self.bm25_engine = BM25Engine(
            k1=self.config.bm25_k1,
            b=self.config.bm25_b,
        )
        self.semantic_engine = SemanticEngine()
        self.metadata_booster = MetadataBooster(
            title_boost=self.config.title_boost,
            heading_boost=self.config.heading_boost,
            tag_boost=self.config.tag_boost,
            category_boost=self.config.category_boost,
            recency_boost=self.config.recency_boost,
            popularity_boost=self.config.popularity_boost,
        )
        self.normalizer = ScoreNormalizer(method=self.config.normalization_method)

    def index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Index documents for ranking.
        
        Args:
            documents: List of documents to index
        """
        # Index for BM25
        self.bm25_engine.index_documents(documents)
        
        # Index for semantic search
        self.semantic_engine.index_documents(documents)
        
        logger.debug(f"Indexed {len(documents)} documents for hybrid ranking")

    def rank(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 20,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank documents using hybrid signals.
        
        Args:
            query: Search query
            query_vector: Query embedding vector
            documents: Documents to rank (None to use indexed documents)
            top_k: Number of results to return
            user_profile: Optional user profile for personalization
            
        Returns:
            Ranked list of documents with scores
        """
        if documents is None:
            documents = []
        
        # Index documents if provided
        if documents:
            self.index(documents)
        
        # Score documents
        scored_docs = []
        for doc in documents:
            scored_doc = self._score_document(query, query_vector, doc, user_profile)
            scored_docs.append(scored_doc)
        
        # Sort by final score
        scored_docs.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return scored_docs[:top_k]

    def _score_document(
        self,
        query: str,
        query_vector: Optional[List[float]],
        document: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Score a single document"""
        # BM25 score
        keyword_score = self.bm25_engine.score(query, document)
        
        # Semantic score
        semantic_score = 0.0
        if query_vector is not None and document.get("embedding") is not None:
            import numpy as np
            q_vec = np.array(query_vector)
            d_vec = np.array(document["embedding"])
            semantic_score = self.semantic_engine.score(q_vec, d_vec)
        
        # Normalize scores
        normalized_keyword = keyword_score
        normalized_semantic = semantic_score
        
        # Fusion: weighted combination
        fused_score = (
            self.config.bm25_weight * normalized_keyword
            + self.config.semantic_weight * normalized_semantic
        )
        
        # Create result with scores
        result = document.copy()
        result["keyword_score"] = keyword_score
        result["semantic_score"] = semantic_score
        result["fused_score"] = fused_score
        result["score"] = fused_score
        
        # Apply metadata boosting
        if self.config.enable_metadata_boost:
            query_terms = query.lower().split()
            boost_factors = []
            
            # Title boost
            title = result.get("title", "").lower()
            for term in query_terms:
                if term in title:
                    boost_factors.append(("title", self.config.title_boost))
                    break
            
            # Heading boost
            headings = result.get("headings", [])
            for heading in headings:
                if any(term in str(heading).lower() for term in query_terms):
                    boost_factors.append(("heading", self.config.heading_boost))
                    break
            
            # Tag boost
            tags = result.get("tags", [])
            for tag in tags:
                if any(term in str(tag).lower() for term in query_terms):
                    boost_factors.append(("tag", self.config.tag_boost))
                    break
            
            # Apply boosts
            boost_multiplier = 1.0
            for _, factor in boost_factors:
                boost_multiplier *= factor
            
            result["score"] = fused_score * boost_multiplier
            result["boost_factors"] = boost_factors
            result["boost_multiplier"] = boost_multiplier
        
        # Add score breakdown
        result["score_breakdown"] = {
            "keyword": {
                "raw": keyword_score,
                "weight": self.config.bm25_weight,
                "weighted": self.config.bm25_weight * keyword_score,
            },
            "semantic": {
                "raw": semantic_score,
                "weight": self.config.semantic_weight,
                "weighted": self.config.semantic_weight * semantic_score,
            },
            "boost_multiplier": result.get("boost_multiplier", 1.0),
            "final": result["score"],
        }
        
        return result

    def explain_ranking(
        self,
        query: str,
        document: Dict[str, Any],
        query_vector: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Explain why a document was ranked a certain way.
        
        Args:
            query: Search query
            document: Document to explain
            query_vector: Query embedding vector
            
        Returns:
            Explanation dictionary
        """
        explanation = {
            "query": query,
            "document_id": document.get("id", "unknown"),
            "document_title": document.get("title", "unknown"),
            "scores": {},
            "factors": [],
        }
        
        # Keyword score
        keyword_score = self.bm25_engine.score(query, document)
        explanation["scores"]["keyword"] = {
            "score": keyword_score,
            "weight": self.config.bm25_weight,
            "weighted_score": self.config.bm25_weight * keyword_score,
        }
        
        # Semantic score
        semantic_score = 0.0
        if query_vector and document.get("embedding"):
            import numpy as np
            q_vec = np.array(query_vector)
            d_vec = np.array(document["embedding"])
            semantic_score = self.semantic_engine.score(q_vec, d_vec)
        
        explanation["scores"]["semantic"] = {
            "score": semantic_score,
            "weight": self.config.semantic_weight,
            "weighted_score": self.config.semantic_weight * semantic_score,
        }
        
        # Boosts
        query_terms = query.lower().split()
        title = document.get("title", "").lower()
        for term in query_terms:
            if term in title:
                explanation["factors"].append({
                    "type": "title_match",
                    "term": term,
                    "boost": self.config.title_boost,
                })
        
        # Final score calculation
        fused_score = (
            self.config.bm25_weight * keyword_score
            + self.config.semantic_weight * semantic_score
        )
        
        explanation["final_score"] = fused_score
        explanation["calculation"] = (
            f"({self.config.bm25_weight} × {keyword_score:.3f}) + "
            f"({self.config.semantic_weight} × {semantic_score:.3f}) = {fused_score:.3f}"
        )
        
        return explanation

    def get_statistics(self) -> Dict[str, Any]:
        """Get ranking statistics"""
        return {
            "bm25": self.bm25_engine.get_statistics(),
            "semantic": self.semantic_engine.get_statistics(),
            "config": {
                "bm25_weight": self.config.bm25_weight,
                "semantic_weight": self.config.semantic_weight,
                "normalization_method": self.config.normalization_method,
            },
        }