"""
Advanced Ranking Service

Implements production-ready ranking with:
- BM25 scoring
- TF-IDF weighting
- Metadata boosting
- Freshness scoring
- Popularity scoring
- Configurable ranking pipeline
"""

import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nebula.search.ranking")


@dataclass
class RankingConfig:
    """Ranking configuration"""
    # BM25 parameters
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    
    # Feature weights
    keyword_weight: float = 0.35
    semantic_weight: float = 0.25
    freshness_weight: float = 0.10
    popularity_weight: float = 0.10
    personalization_weight: float = 0.10
    metadata_weight: float = 0.10
    
    # Freshness decay (half-life in days)
    freshness_half_life: int = 7
    
    # Minimum scores
    min_keyword_score: float = 0.1
    min_semantic_score: float = 0.3


@dataclass
class DocumentFeatures:
    """Document ranking features"""
    document_id: str
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    freshness_score: float = 0.0
    popularity_score: float = 0.0
    personalization_score: float = 0.0
    metadata_score: float = 0.0
    final_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BM25Scorer:
    """BM25 ranking algorithm implementation"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_count = 0
        self.avg_doc_length = 0.0
        self.doc_freq = Counter()
        self.doc_lengths = {}
    
    def index_documents(self, documents: List[Dict[str, Any]]):
        """Index documents for BM25 scoring"""
        total_length = 0
        
        for doc in documents:
            doc_id = doc.get("id", "")
            text = f"{doc.get('title', '')} {doc.get('content', '')} {doc.get('snippet', '')}".lower()
            words = text.split()
            doc_length = len(words)
            
            self.doc_lengths[doc_id] = doc_length
            total_length += doc_length
            
            # Count document frequency
            unique_terms = set(words)
            for term in unique_terms:
                self.doc_freq[term] += 1
        
        self.doc_count = len(documents)
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0
    
    def score(self, query: str, document: Dict[str, Any]) -> float:
        """Calculate BM25 score for document"""
        if self.doc_count == 0:
            return 0.0
        
        query_terms = query.lower().split()
        document.get("id", "")
        doc_text = f"{document.get('title', '')} {document.get('content', '')} {document.get('snippet', '')}".lower()
        doc_terms = doc_text.split()
        doc_length = len(doc_terms)
        
        # Count term frequencies
        term_freq = Counter(doc_terms)
        
        score = 0.0
        for term in query_terms:
            if term not in term_freq:
                continue
            
            tf = term_freq[term]
            df = self.doc_freq.get(term, 0)
            
            if df == 0:
                continue
            
            # IDF component
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)
            
            # Length normalization
            norm = 1 - self.b + self.b * (doc_length / self.avg_doc_length) if self.avg_doc_length > 0 else 1
            
            # BM25 formula
            score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * norm)
        
        return score


class FreshnessScorer:
    """Score documents based on freshness"""
    
    def __init__(self, half_life_days: int = 7):
        self.half_life_days = half_life_days
    
    def score(self, document: Dict[str, Any]) -> float:
        """Calculate freshness score (0-1)"""
        updated_at = document.get("updated_at")
        if not updated_at:
            return 0.5  # Default score
        
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return 0.5
        
        # Calculate age in days
        now = datetime.now(timezone.utc)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age_days = (now - updated_at).total_seconds() / 86400
        
        # Exponential decay based on half-life
        decay = math.pow(2, -age_days / self.half_life_days)
        
        return min(1.0, max(0.0, decay))


class PopularityScorer:
    """Score documents based on popularity"""
    
    def __init__(self):
        self.view_counts = {}
        self.click_through_rates = {}
    
    def update_metrics(self, document_id: str, views: int, ctr: float):
        """Update popularity metrics"""
        self.view_counts[document_id] = views
        self.click_through_rates[document_id] = ctr
    
    def score(self, document: Dict[str, Any]) -> float:
        """Calculate popularity score (0-1)"""
        doc_id = document.get("id", "")
        
        views = self.view_counts.get(doc_id, 0)
        ctr = self.click_through_rates.get(doc_id, 0.0)
        
        # Normalize views (log scale, max at 1000 views)
        view_score = min(1.0, math.log(views + 1) / math.log(1001)) if views > 0 else 0.0
        
        # CTR is already 0-1
        ctr_score = min(1.0, ctr)
        
        # Combine (70% CTR, 30% views)
        return 0.7 * ctr_score + 0.3 * view_score


class MetadataScorer:
    """Score documents based on metadata quality"""
    
    def __init__(self):
        self.weights = {
            "has_title": 0.2,
            "has_author": 0.15,
            "has_description": 0.2,
            "has_tags": 0.15,
            "has_categories": 0.15,
            "content_length": 0.15,
        }
    
    def score(self, document: Dict[str, Any]) -> float:
        """Calculate metadata score (0-1)"""
        score = 0.0
        
        # Title
        if document.get("title") and len(document.get("title", "")) > 5:
            score += self.weights["has_title"]
        
        # Author
        if document.get("author"):
            score += self.weights["has_author"]
        
        # Description/snippet
        if document.get("snippet") or document.get("description"):
            score += self.weights["has_description"]
        
        # Tags
        if document.get("tags") and len(document.get("tags", [])) > 0:
            score += self.weights["has_tags"]
        
        # Categories
        if document.get("categories") and len(document.get("categories", [])) > 0:
            score += self.weights["has_categories"]
        
        # Content length (optimal range 100-5000 words)
        content_length = len(document.get("content", "").split())
        if 100 <= content_length <= 5000:
            score += self.weights["content_length"]
        elif content_length > 50:
            score += self.weights["content_length"] * 0.5
        
        return min(1.0, score)


class RankingService:
    """
    Advanced ranking service combining multiple signals.
    """
    
    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()
        self.bm25_scorer = BM25Scorer(k1=self.config.bm25_k1, b=self.config.bm25_b)
        self.freshness_scorer = FreshnessScorer(half_life_days=self.config.freshness_half_life)
        self.popularity_scorer = PopularityScorer()
        self.metadata_scorer = MetadataScorer()
    
    async def rank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank search results using multiple signals.
        
        Args:
            query: Search query
            results: Search results to rank
            user_profile: Optional user profile for personalization
            
        Returns:
            Ranked results with scores
        """
        if not results:
            return []
        
        # Index documents for BM25
        self.bm25_scorer.index_documents(results)
        
        # Score each document
        scored_results = []
        for doc in results:
            features = await self._score_document(query, doc, user_profile)
            
            # Add scores to document
            doc_copy = doc.copy()
            doc_copy["score"] = features.final_score
            doc_copy["scores"] = {
                "keyword": features.keyword_score,
                "semantic": features.semantic_score,
                "freshness": features.freshness_score,
                "popularity": features.popularity_score,
                "personalization": features.personalization_score,
                "metadata": features.metadata_score,
            }
            
            scored_results.append((features.final_score, doc_copy))
        
        # Sort by final score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for _, doc in scored_results]
    
    async def _score_document(
        self,
        query: str,
        document: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]],
    ) -> DocumentFeatures:
        """Score a single document"""
        features = DocumentFeatures(document_id=document.get("id", ""))
        
        # Keyword score (BM25)
        features.keyword_score = self.bm25_scorer.score(query, document)
        if features.keyword_score < self.config.min_keyword_score:
            features.keyword_score = 0.0
        
        # Semantic score (from document or calculate)
        features.semantic_score = document.get("semantic_score", 0.0)
        if features.semantic_score < self.config.min_semantic_score:
            features.semantic_score = 0.0
        
        # Freshness score
        features.freshness_score = self.freshness_scorer.score(document)
        
        # Popularity score
        features.popularity_score = self.popularity_scorer.score(document)
        
        # Personalization score
        if user_profile:
            features.personalization_score = self._calculate_personalization(
                document, user_profile
            )
        
        # Metadata score
        features.metadata_score = self.metadata_scorer.score(document)
        
        # Calculate final score
        features.final_score = (
            self.config.keyword_weight * features.keyword_score
            + self.config.semantic_weight * features.semantic_score
            + self.config.freshness_weight * features.freshness_score
            + self.config.popularity_weight * features.popularity_score
            + self.config.personalization_weight * features.personalization_score
            + self.config.metadata_weight * features.metadata_score
        )
        
        return features
    
    def _calculate_personalization(
        self, document: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> float:
        """Calculate personalization score"""
        score = 0.0
        
        # Match user interests
        interests = user_profile.get("interests", [])
        doc_text = f"{document.get('title', '')} {document.get('content', '')}".lower()
        
        for interest in interests:
            if interest.lower() in doc_text:
                score += 0.2
        
        # Match preferred sources
        preferred_sources = user_profile.get("preferred_sources", [])
        doc_url = document.get("url", "")
        
        for source in preferred_sources:
            if source in doc_url:
                score += 0.3
        
        return min(1.0, score)
    
    def update_popularity_metrics(
        self, document_id: str, views: int, click_through_rate: float
    ):
        """Update popularity metrics for a document"""
        self.popularity_scorer.update_metrics(document_id, views, click_through_rate)


# Global instance
ranking_service = RankingService()