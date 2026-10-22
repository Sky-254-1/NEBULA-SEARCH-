"""Ranking models for search results."""

import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RankingFeatures:
    """Features extracted from a document for ranking."""
    bm25_score: float = 0.0
    tfidf_score: float = 0.0
    position_score: float = 0.0
    title_match: bool = False
    snippet_match: bool = False
    url_match: bool = False
    freshness_score: float = 0.0
    domain_authority: float = 0.0
    personalization_score: float = 0.0


class BM25Ranker:
    """BM25 ranking model."""

    def __init__(self, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.indexed_docs: List[Dict[str, Any]] = []

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Index documents for BM25 scoring."""
        self.indexed_docs = documents

    def score(self, query: str, doc: Dict[str, Any]) -> float:
        """Score a single document for a query."""
        if not self.indexed_docs or not doc:
            return 0.0
        query_terms = query.lower().split()
        return self._bm25_score(doc, query_terms)

    def rank(self, documents: List[Dict[str, Any]], query_terms: List[str]) -> List[Tuple[int, float]]:
        """Rank documents based on BM25 score."""
        if not documents or not query_terms:
            return []

        scores = []
        for idx, doc in enumerate(documents):
            score = self._bm25_score(doc, query_terms)
            scores.append((idx, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _bm25_score(self, doc: Dict[str, Any], query_terms: List[str]) -> float:
        """Calculate BM25 score for a document."""
        # Build content from title, snippet, and url if content is not available
        title = doc.get("title", "")
        snippet = doc.get("snippet", "")
        url = doc.get("url", "")
        content = doc.get("content", "")
        
        # Fallback: combine title, snippet, url if no content field
        if not content and (title or snippet or url):
            content = f"{title} {snippet} {url}"
        
        content = content.lower()
        if not content or not query_terms:
            return 0.0

        # Get document length
        doc_len = len(content.split())
        avg_doc_len = sum(
            len((d.get("content", "") or f"{d.get('title', '')} {d.get('snippet', '')} {d.get('url', '')}").split()) 
            for d in self.indexed_docs
        ) / max(len(self.indexed_docs), 1)

        score = 0.0
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in content:
                # Term frequency
                tf = content.count(term_lower)
                # Document frequency (simplified - use 1 for unique terms)
                df = sum(
                    1 for d in self.indexed_docs 
                    if term_lower in ((d.get("content", "") or f"{d.get('title', '')} {d.get('snippet', '')} {d.get('url', '')}").lower())
                )
                if df == 0:
                    df = 1

                # BM25 formula: IDF * (TF * (k1 + 1)) / (TF + k1 * (1 - b + b * doc_len / avg_len))
                # Avoid division by zero by using a small epsilon for avg_doc_len
                avg_doc_len_safe = avg_doc_len if avg_doc_len > 0 else 1.0
                idf = np.log((len(self.indexed_docs) - df + 0.5) / (df + 0.5) + 1.0)
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len_safe))

        return score


class TFIDFRanker:
    """TF-IDF ranking model."""

    def __init__(self):
        self.idf: Dict[str, float] = {}
        self.df: Dict[str, int] = {}

    def calculate_tf(self, term: str, content: str) -> float:
        """Calculate term frequency."""
        content_lower = content.lower()
        term_lower = term.lower()
        words = content_lower.split()
        if not words:
            return 0.0
        return content_lower.count(term_lower) / len(words)

    def calculate_idf(self, term: str, documents: List[Dict[str, Any]]) -> float:
        """Calculate inverse document frequency."""
        n_docs = len(documents)
        if n_docs == 0:
            return 0.0
        
        def get_doc_text(doc):
            """Get combined text from doc for term matching."""
            content = doc.get("content", "")
            if not content:
                content = f"{doc.get('title', '')} {doc.get('snippet', '')} {doc.get('url', '')}"
            return content.lower()
        
        doc_freq = sum(1 for doc in documents if term.lower() in get_doc_text(doc))
        if doc_freq == 0:
            return 0.0
        return np.log((n_docs + 1) / (doc_freq + 1)) + 1

    def fit(self, documents: List[Dict[str, Any]]) -> "TFIDFRanker":
        """Fit the model on documents to compute IDF."""
        n_docs = len(documents)
        if n_docs == 0:
            return self

        def get_doc_terms(doc):
            """Get terms from document content."""
            content = doc.get("content", "")
            if not content:
                content = f"{doc.get('title', '')} {doc.get('snippet', '')} {doc.get('url', '')}"
            return set(content.lower().split())
        
        doc_freq: Dict[str, int] = {}
        for doc in documents:
            terms = get_doc_terms(doc)
            for term in terms:
                doc_freq[term] = doc_freq.get(term, 0) + 1

        self.df = doc_freq
        self.idf = {term: np.log((n_docs + 1) / (df + 1)) + 1 for term, df in doc_freq.items()}
        return self

    def transform(self, documents: List[Dict[str, Any]], query_terms: List[str]) -> List[Tuple[int, float]]:
        """Transform documents to TF-IDF scores."""
        if not documents or not query_terms:
            return []

        scores = []
        for idx, doc in enumerate(documents):
            score = self._tfidf_score(doc, query_terms)
            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def score(self, query: str, doc: Dict[str, Any], documents: List[Dict[str, Any]]) -> float:
        """Score a single document for a query."""
        query_terms = query.lower().split()
        self.fit(documents)
        return self._tfidf_score(doc, query_terms)

    def _tfidf_score(self, doc: Dict[str, Any], query_terms: List[str]) -> float:
        content = doc.get("content", "")
        if not content:
            content = f"{doc.get('title', '')} {doc.get('snippet', '')} {doc.get('url', '')}"
        content = content.lower()
        score = 0.0
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in content:
                tf = content.count(term_lower) / max(len(content.split()), 1)
                idf = self.idf.get(term_lower, 0)
                score += tf * idf
        return score


class PositionAwareRanker:
    """Ranker that considers term position for better scoring."""

    def __init__(self, position_bonus: float = 0.1):
        self.position_bonus = position_bonus

    def score(self, query: str, doc: Dict[str, Any]) -> float:
        """Score a single document for a query."""
        content = doc.get("content", "").lower()
        title = doc.get("title", "").lower()
        url = doc.get("url", "").lower()
        score = 0.0
        
        for term in query.lower().split():
            term_lower = term.lower()
            # Content match
            if term_lower in content:
                pos = content.find(term_lower)
                bonus = self.position_bonus * (1.0 / (1.0 + pos / 100.0))
                score += 1.0 + bonus
            # Title match
            if term_lower in title:
                pos = title.find(term_lower)
                bonus = self.position_bonus * (1.0 / (1.0 + pos / 100.0))
                score += 2.0 + bonus  # Title matches are more important
            # URL match
            if term_lower in url:
                score += 1.5  # URL matches get a bonus
        
        return score

    def rank(self, documents: List[Dict[str, Any]], query_terms: List[str]) -> List[Tuple[int, float]]:
        """Rank documents considering term position."""
        if not documents or not query_terms:
            return []

        scores = []
        for idx, doc in enumerate(documents):
            content = doc.get("content", "").lower()
            score = 0.0

            for term in query_terms:
                term_lower = term.lower()
                if term_lower in content:
                    pos = content.find(term_lower)
                    # First position gets full bonus, decays with position
                    bonus = self.position_bonus * (1.0 / (1.0 + pos / 100.0))
                    score += 1.0 + bonus

            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class MLRanker:
    """Machine learning-based ranking using simple heuristics."""

    def __init__(self):
        self.weights = {
            "term_frequency": 1.0,
            "position": 0.1,
            "length_norm": 0.5,
            "title_boost": 1.5,
            "bm25": 0.5,
        }

    def extract_features(
        self,
        query: str,
        doc: Dict[str, Any],
        documents: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> RankingFeatures:
        """Extract features for ML ranking."""
        # Build content from title, snippet, url if content is not available
        content = doc.get("content", "")
        if not content:
            content = f"{doc.get('title', '')} {doc.get('snippet', '')} {doc.get('url', '')}"
        content = content.lower()
        title = doc.get("title", "").lower()
        snippet = doc.get("snippet", "").lower()
        url = doc.get("url", "").lower()
        query_terms = query.lower().split()

        # Calculate BM25-like score using actual BM25 ranker
        bm25_ranker = BM25Ranker()
        bm25_ranker.index_documents(documents)
        bm25_score = bm25_ranker.score(query, doc)

        # Title match
        title_match = any(term in title for term in query_terms)

        # Snippet match
        snippet_match = any(term in snippet for term in query_terms)

        # URL match
        url_match = any(term in url for term in query_terms)

        # Freshness score
        freshness_score = self._calculate_freshness(doc)

        # Domain authority
        domain_authority = self._calculate_domain_authority(doc)

        # Personalization score
        personalization_score = 0.0
        if user_profile and "interests" in user_profile:
            user_interests = set(interest.lower() for interest in user_profile["interests"])
            all_text = content + title + snippet + url
            matches = sum(1 for interest in user_interests if interest in all_text)
            personalization_score = matches / max(len(user_interests), 1)

        return RankingFeatures(
            bm25_score=bm25_score,
            title_match=title_match,
            snippet_match=snippet_match,
            url_match=url_match,
            freshness_score=freshness_score,
            domain_authority=domain_authority,
            personalization_score=personalization_score
        )

    def _calculate_freshness(self, doc: Dict[str, Any]) -> float:
        """Calculate freshness score based on published date."""
        published_date = doc.get("published_date")
        if not published_date:
            return 0.5  # Neutral score for unknown dates

        try:
            doc_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            days_old = (datetime.now() - doc_date.replace(tzinfo=None)).days
            # Decay: newer is better, score from 0 to 1
            if days_old < 7:
                return 1.0
            elif days_old < 30:
                return 0.8
            elif days_old < 90:
                return 0.6
            elif days_old < 365:
                return 0.4
            else:
                return 0.2
        except (ValueError, TypeError):
            return 0.5

    def _calculate_domain_authority(self, doc: Dict[str, Any]) -> float:
        """Calculate domain authority based on URL."""
        url = doc.get("url", "")
        url_lower = url.lower()

        # Known high-authority domains
        if "wikipedia.org" in url_lower:
            return 0.9
        elif ".edu" in url_lower:
            return 0.8
        elif ".gov" in url_lower:
            return 0.85
        elif "medium.com" in url_lower or "github.com" in url_lower:
            return 0.7
        else:
            return 0.5  # Default for unknown domains

    def normalize_scores(self, scores: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """Normalize scores to [0, 1] range."""
        if not scores:
            return []

        max_score = max(score for _, score in scores)
        min_score = min(score for _, score in scores)

        if max_score == min_score:
            return [(idx, 0.5) for idx, _ in scores]

        normalized = []
        for idx, score in scores:
            norm_score = (score - min_score) / (max_score - min_score)
            normalized.append((idx, norm_score))

        return normalized

    def score(self, query: str, doc: Dict[str, Any], documents: List[Dict[str, Any]]) -> float:
        """Score a single document for a query."""
        query_terms = query.lower().split()
        return self._ml_score(doc, query_terms)

    def rank(self, documents: List[Dict[str, Any]], query_terms: List[str]) -> List[Tuple[int, float]]:
        """Rank documents using ML-style heuristics."""
        if not documents or not query_terms:
            return []

        scores = []
        for idx, doc in enumerate(documents):
            score = self._ml_score(doc, query_terms)
            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _ml_score(self, doc: Dict[str, Any], query_terms: List[str]) -> float:
        content = doc.get("content", "").lower()
        title = doc.get("title", "").lower()
        score = 0.0

        for term in query_terms:
            term_lower = term.lower()
            if term_lower in content:
                tf = content.count(term_lower) / max(len(content.split()), 1)
                score += self.weights["term_frequency"] * tf

                # Position bonus
                pos = content.find(term_lower)
                score += self.weights["position"] * (1.0 / (1.0 + pos / 100.0))

        # Title boost
        if title:
            for term in query_terms:
                if term.lower() in title:
                    score += self.weights["title_boost"]

        # Length normalization
        content_len = len(content.split())
        score *= self.weights["length_norm"] / np.sqrt(content_len + 1)

        return score


class DiversityRanker:
    """Ranker that promotes result diversity."""

    def __init__(self, diversity_weight: float = 0.3):
        self.diversity_weight = diversity_weight

    def _similarity(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> float:
        """Calculate similarity between two documents based on title/content overlap."""
        text1 = (doc1.get("title", "") + " " + doc1.get("snippet", "")).lower()
        text2 = (doc2.get("title", "") + " " + doc2.get("snippet", "")).lower()

        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2
        if not union:
            return 0.0
        return len(intersection) / len(union)

    def diversify(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Diversify search results to reduce redundancy."""
        if not results:
            return []

        if len(results) == 1:
            return results

        diversified = [results[0]]
        remaining = results[1:]

        while remaining:
            best_idx = 0
            best_score = float("-inf")

            for idx, doc in enumerate(remaining):
                # Calculate min similarity to already selected docs
                min_similarity = min(
                    self._similarity(doc, selected) for selected in diversified
                )
                score = self.diversity_weight - min_similarity
                if score > best_score:
                    best_score = score
                    best_idx = idx

            diversified.append(remaining.pop(best_idx))

        return diversified

    def rank(self, documents: List[Dict[str, Any]], query_terms: List[str]) -> List[Tuple[int, float]]:
        """Rank documents with diversity consideration."""
        if not documents or not query_terms:
            return []

        base_scores = BM25Ranker().rank(documents, query_terms)

        # Calculate diversity penalty
        scored_docs = []
        seen_sources = set()
        for idx, score in base_scores:
            source = documents[idx].get("source", "unknown")
            diversity_penalty = self.diversity_weight if source in seen_sources else 0.0
            seen_sources.add(source)
            scored_docs.append((idx, max(0, score - diversity_penalty)))

        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs


class HybridRanker:
    """Combined BM25 + TF-IDF + Position ranking."""

    def __init__(
        self,
        bm25_weight: float = 0.5,
        tfidf_weight: float = 0.3,
        position_weight: float = 0.2,
    ):
        self.bm25_weight = bm25_weight
        self.tfidf_weight = tfidf_weight
        self.position_weight = position_weight

        self.tfidf_ranker = TFIDFRanker()
        self.position_ranker = PositionAwareRanker()
        self.feature_stats: Dict[str, int] = {"total_ranked": 0}

    def fit(self, documents: List[Dict[str, Any]]) -> "HybridRanker":
        """Fit the ranker on documents."""
        self.tfidf_ranker.fit(documents)
        return self

    async def rank_async(
        self,
        query: str,
        results: List[Dict[str, Any]],
        enable_diversity: bool = True,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rank using hybrid approach asynchronously."""
        if not results:
            self.feature_stats["total_ranked"] = 0
            return []

        # Get scores from each ranker
        documents = results
        query_terms = query.lower().split()

        bm25_scores = BM25Ranker().rank(documents, query_terms)
        tfidf_scores = self.tfidf_ranker.transform(documents, query_terms)
        position_scores = self.position_ranker.rank(documents, query_terms)

        # Combine scores
        combined_scores: Dict[int, float] = {}
        for idx, score in bm25_scores:
            combined_scores[idx] = combined_scores.get(idx, 0.0) + self.bm25_weight * score

        for idx, score in tfidf_scores:
            combined_scores[idx] = combined_scores.get(idx, 0.0) + self.tfidf_weight * score

        for idx, score in position_scores:
            combined_scores[idx] = combined_scores.get(idx, 0.0) + self.position_weight * score

        # Normalize scores to [0, 1]
        if combined_scores:
            max_score = max(combined_scores.values())
            min_score = min(combined_scores.values())
            if max_score > min_score:
                for idx in combined_scores:
                    combined_scores[idx] = (combined_scores[idx] - min_score) / (max_score - min_score)

        # Apply diversity if enabled
        if enable_diversity:
            diversity_ranker = DiversityRanker(diversity_weight=0.3)
            for idx in combined_scores:
                combined_scores[idx] *= (1 - diversity_ranker.diversity_weight)

        # Create ranked results
        ranked_results = []
        sorted_indices = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        for position, (idx, score) in enumerate(sorted_indices):
            result = results[idx].copy()
            result["final_score"] = round(score, 4)
            result["rank_position"] = position + 1
            ranked_results.append(result)

        self.feature_stats["total_ranked"] += len(ranked_results)
        return ranked_results

    def rank_hybrid(self, documents: List[Dict[str, Any]], query_terms: List[str]) -> List[Tuple[int, float]]:
        """Rank using hybrid approach (synchronous version)."""
        if not documents or not query_terms:
            return []

        bm25_scores = BM25Ranker().rank(documents, query_terms)
        tfidf_scores = self.tfidf_ranker.transform(documents, query_terms)
        position_scores = self.position_ranker.rank(documents, query_terms)

        # Combine scores
        combined: Dict[int, float] = {}
        for idx, score in bm25_scores:
            combined[idx] = combined.get(idx, 0.0) + self.bm25_weight * score

        for idx, score in tfidf_scores:
            combined[idx] = combined.get(idx, 0.0) + self.tfidf_weight * score

        for idx, score in position_scores:
            combined[idx] = combined.get(idx, 0.0) + self.position_weight * score

        result = [(idx, score) for idx, score in combined.items()]
        result.sort(key=lambda x: x[1], reverse=True)
        return result


class RankingModelManager:
    """Manager for ranking models."""

    def __init__(self, ranker: Optional[MLRanker] = None):
        self.ranker = ranker or MLRanker()
        self.models: Dict[str, Callable] = {
            "bm25": lambda docs, query: BM25Ranker().rank(docs, query),
            "tfidf": lambda docs, query: TFIDFRanker().transform(docs, query),
            "position": lambda docs, query: PositionAwareRanker().rank(docs, query),
            "ml": lambda docs, query: self.ranker.rank(docs, query),
            "diversity": lambda docs, query: DiversityRanker().rank(docs, query),
        }
        self.hybrid = HybridRanker()
        self._default_model = "bm25"
        self.training_data: List[Dict[str, Any]] = []
        self._version = "1.0.0"
        self._feature_weights: Dict[str, float] = {
            "bm25": 0.5,
            "tfidf": 0.3,
            "position": 0.2
        }
        self.model_metadata: Dict[str, Any] = {
            "last_training_date": None,
            "model_version": self._version,
            "training_count": 0
        }

    def register_model(self, name: str, model_fn: Callable) -> None:
        """Register a custom ranking model."""
        self.models[name] = model_fn

    def rank(self, model_name: str, documents: List[Dict[str, Any]], query_terms: List[str]) -> List[Tuple[int, float]]:
        """Rank documents using specified model."""
        if model_name == "hybrid":
            return self.hybrid.rank_hybrid(documents, query_terms)

        if model_name not in self.models:
            logger.warning(f"Unknown model '{model_name}', using default: {self._default_model}")
            model_name = self._default_model

        return self.models[model_name](documents, query_terms)

    def get_available_models(self) -> List[str]:
        """Return list of available model names."""
        return list(self.models.keys())

    def record_training_sample(self, query: str, doc: Dict[str, Any], features: Dict[str, Any], clicked: bool) -> None:
        """Record a training sample for ML ranking."""
        sample = {
            "query": query,
            "doc": doc,
            "features": features,
            "clicked": clicked,
            "timestamp": datetime.now().isoformat()
        }
        self.training_data.append(sample)

    def should_retrain(self, sample_threshold: int = 1000) -> bool:
        """Check if model should be retrained based on training data size."""
        return len(self.training_data) >= sample_threshold

    def clear_training_data(self) -> None:
        """Clear all training data."""
        self.training_data = []

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "version": self._version,
            "feature_weights": self._feature_weights,
            "training_samples": len(self.training_data),
            "available_models": self.get_available_models()
        }

    def update_weights(self, weights: Dict[str, float]) -> None:
        """Update feature weights for ranking."""
        for key, value in weights.items():
            if key in self._feature_weights:
                self._feature_weights[key] = value
        # Update metadata when weights are changed
        self.model_metadata['last_training_date'] = datetime.now().isoformat()


# Global instance for easy access
global_hybrid_ranker = HybridRanker()

# Alias for backward compatibility
hybrid_ranker = global_hybrid_ranker
