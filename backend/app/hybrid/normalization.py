"""
Score Normalization

Normalizes scores from different sources into a common range.
Supports multiple normalization methods.
"""

import logging
import math
from typing import Any, Dict, List, Optional


logger = logging.getLogger("nebula.hybrid.normalization")


class ScoreNormalizer:
    """
    Normalize scores from different retrieval systems into a common range.
    
    Supported methods:
    - minmax: Min-max normalization to [0, 1]
    - zscore: Z-score normalization (mean=0, std=1)
    - softmax: Softmax normalization
    - rank: Rank-based normalization
    """

    def __init__(self, method: str = "minmax"):
        """
        Initialize normalizer.
        
        Args:
            method: Normalization method (minmax, zscore, softmax, rank)
        """
        self.method = method.lower()
        self.supported_methods = {"minmax", "zscore", "softmax", "rank"}
        
        if self.method not in self.supported_methods:
            logger.warning(
                f"Unsupported normalization method: {method}, "
                f"falling back to minmax"
            )
            self.method = "minmax"

    def normalize(
        self,
        scores: List[float],
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
    ) -> List[float]:
        """
        Normalize a list of scores.
        
        Args:
            scores: List of raw scores
            min_score: Optional minimum score (computed if not provided)
            max_score: Optional maximum score (computed if not provided)
            
        Returns:
            List of normalized scores
        """
        if not scores:
            return []
        
        if self.method == "minmax":
            return self._normalize_minmax(scores, min_score, max_score)
        elif self.method == "zscore":
            return self._normalize_zscore(scores)
        elif self.method == "softmax":
            return self._normalize_softmax(scores)
        elif self.method == "rank":
            return self._normalize_rank(scores)
        else:
            return self._normalize_minmax(scores, min_score, max_score)

    def _normalize_minmax(
        self,
        scores: List[float],
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
    ) -> List[float]:
        """Min-max normalization to [0, 1]"""
        if min_score is None:
            min_score = min(scores)
        if max_score is None:
            max_score = max(scores)
        
        # Avoid division by zero
        score_range = max_score - min_score
        if score_range == 0:
            return [0.5] * len(scores)
        
        return [(score - min_score) / score_range for score in scores]

    def _normalize_zscore(self, scores: List[float]) -> List[float]:
        """Z-score normalization (mean=0, std=1)"""
        if len(scores) < 2:
            return [0.0] * len(scores)
        
        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        std = math.sqrt(variance)
        
        if std == 0:
            return [0.0] * len(scores)
        
        # Convert to [0, 1] range using sigmoid
        z_scores = [(score - mean) / std for score in scores]
        normalized = [1 / (1 + math.exp(-z)) for z in z_scores]
        
        return normalized

    def _normalize_softmax(self, scores: List[float]) -> List[float]:
        """Softmax normalization"""
        if not scores:
            return []
        
        # Shift scores for numerical stability
        max_score = max(scores)
        exp_scores = [math.exp(score - max_score) for score in scores]
        sum_exp = sum(exp_scores)
        
        if sum_exp == 0:
            return [0.0] * len(scores)
        
        return [exp_score / sum_exp for exp_score in exp_scores]

    def _normalize_rank(self, scores: List[float]) -> List[float]:
        """Rank-based normalization"""
        if not scores:
            return []
        
        # Sort scores with indices
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign ranks
        n = len(scores)
        ranks = [0.0] * n
        for rank, (idx, _) in enumerate(indexed_scores, 1):
            ranks[idx] = rank / n
        
        # Invert so higher scores get higher normalized values
        return [1.0 - rank for rank in ranks]

    def normalize_results(
        self,
        results: List[Dict[str, Any]],
        score_key: str = "score",
    ) -> List[Dict[str, Any]]:
        """
        Normalize scores in a list of result dictionaries.
        
        Args:
            results: List of result dictionaries
            score_key: Key containing the score to normalize
            
        Returns:
            Results with normalized scores
        """
        if not results:
            return results
        
        scores = [r.get(score_key, 0.0) for r in results]
        normalized = self.normalize(scores)
        
        for i, result in enumerate(results):
            result[f"{score_key}_normalized"] = normalized[i]
        
        return results

    def normalize_multi_source(
        self,
        source_scores: Dict[str, List[float]],
    ) -> Dict[str, List[float]]:
        """
        Normalize scores from multiple sources independently.
        
        Args:
            source_scores: Dictionary mapping source name to list of scores
            
        Returns:
            Dictionary mapping source name to list of normalized scores
        """
        normalized = {}
        
        for source, scores in source_scores.items():
            normalized[source] = self.normalize(scores)
        
        return normalized

    def set_method(self, method: str):
        """
        Set normalization method.
        
        Args:
            method: Normalization method name
        """
        if method in self.supported_methods:
            self.method = method
            logger.info(f"Normalization method set to: {method}")
        else:
            logger.warning(
                f"Unsupported normalization method: {method}, "
                f"keeping current: {self.method}"
            )

    def get_method(self) -> str:
        """Get current normalization method"""
        return self.method

    def get_statistics(self, scores: List[float]) -> Dict[str, float]:
        """
        Calculate statistics for a list of scores.
        
        Args:
            scores: List of scores
            
        Returns:
            Dictionary with statistics
        """
        if not scores:
            return {}
        
        n = len(scores)
        mean = sum(scores) / n
        variance = sum((score - mean) ** 2 for score in scores) / n
        std = math.sqrt(variance)
        
        return {
            "count": n,
            "min": min(scores),
            "max": max(scores),
            "mean": mean,
            "std": std,
            "variance": variance,
        }