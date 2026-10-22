"""
Score Fusion Engine

Combines scores from multiple retrieval sources using weighted fusion.
Supports configurable fusion strategies.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger("nebula.hybrid.fusion")


class FusionEngine:
    """
    Fuse scores from multiple retrieval sources.
    
    Features:
    - Weighted linear combination
    - Reciprocal rank fusion (RRF)
    - Configurable source weights
    - Score interpolation
    """

    def __init__(
        self,
        lexical_weight: float = 0.6,
        semantic_weight: float = 0.4,
        fusion_method: str = "linear",
        rrf_k: int = 60,
    ):
        """
        Initialize fusion engine.
        
        Args:
            lexical_weight: Weight for keyword/BM25 scores
            semantic_weight: Weight for semantic/vector scores
            fusion_method: Fusion method (linear, rrf, interpolate)
            rrf_k: RRF smoothing parameter
        """
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        self.fusion_method = fusion_method.lower()
        self.rrf_k = rrf_k
        
        # Normalize weights
        total = lexical_weight + semantic_weight
        self.lexical_weight = lexical_weight / total if total > 0 else 0.5
        self.semantic_weight = semantic_weight / total if total > 0 else 0.5
        
        self.supported_methods = {"linear", "rrf", "interpolate"}

    def fuse(
        self,
        lexical_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fuse results from lexical and semantic retrieval.
        
        Args:
            lexical_results: Results from BM25/keyword search
            semantic_results: Results from vector/semantic search
            top_k: Number of results to return
            
        Returns:
            Fused and ranked results
        """
        if self.fusion_method == "rrf":
            return self._fuse_rrf(lexical_results, semantic_results, top_k)
        elif self.fusion_method == "interpolate":
            return self._fuse_interpolate(lexical_results, semantic_results, top_k)
        else:
            return self._fuse_linear(lexical_results, semantic_results, top_k)

    def _fuse_linear(
        self,
        lexical_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Linear fusion: weighted sum of normalized scores.
        
        score = lexical_weight * lexical_score + semantic_weight * semantic_score
        """
        # Create lookup for quick access
        all_results = {}
        
        # Process lexical results
        for result in lexical_results:
            doc_id = result.get("id")
            lexical_score = result.get("lexical_score", result.get("score", 0.0))
            
            if doc_id not in all_results:
                all_results[doc_id] = result.copy()
                all_results[doc_id]["scores"] = {}
            
            all_results[doc_id]["scores"]["lexical"] = lexical_score
            all_results[doc_id]["lexical_score"] = lexical_score
        
        # Process semantic results
        for result in semantic_results:
            doc_id = result.get("id")
            semantic_score = result.get("semantic_score", result.get("score", 0.0))
            
            if doc_id not in all_results:
                all_results[doc_id] = result.copy()
                all_results[doc_id]["scores"] = {}
            
            all_results[doc_id]["scores"]["semantic"] = semantic_score
            all_results[doc_id]["semantic_score"] = semantic_score
        
        # Calculate fused scores
        fused_results = []
        for doc_id, result in all_results.items():
            lexical_score = result.get("lexical_score", 0.0)
            semantic_score = result.get("semantic_score", 0.0)
            
            # Linear combination
            fused_score = (
                self.lexical_weight * lexical_score
                + self.semantic_weight * semantic_score
            )
            
            result["score"] = fused_score
            result["score_breakdown"] = {
                "lexical": {
                    "raw": lexical_score,
                    "weight": self.lexical_weight,
                    "weighted": self.lexical_weight * lexical_score,
                },
                "semantic": {
                    "raw": semantic_score,
                    "weight": self.semantic_weight,
                    "weighted": self.semantic_weight * semantic_score,
                },
                "fusion_method": "linear",
            }
            
            fused_results.append(result)
        
        # Sort by fused score
        fused_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return fused_results[:top_k]

    def _fuse_rrf(
        self,
        lexical_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF).
        
        RRF score = sum(1 / (k + rank)) for each source
        """
        all_results = {}
        
        # Process lexical results with RRF
        for rank, result in enumerate(lexical_results, 1):
            doc_id = result.get("id")
            rrf_score = 1.0 / (self.rrf_k + rank)
            
            if doc_id not in all_results:
                all_results[doc_id] = result.copy()
                all_results[doc_id]["scores"] = {}
            
            all_results[doc_id]["scores"]["lexical_rrf"] = rrf_score
            all_results[doc_id]["lexical_rank"] = rank
        
        # Process semantic results with RRF
        for rank, result in enumerate(semantic_results, 1):
            doc_id = result.get("id")
            rrf_score = 1.0 / (self.rrf_k + rank)
            
            if doc_id not in all_results:
                all_results[doc_id] = result.copy()
                all_results[doc_id]["scores"] = {}
            
            all_results[doc_id]["scores"]["semantic_rrf"] = rrf_score
            all_results[doc_id]["semantic_rank"] = rank
        
        # Calculate RRF scores
        fused_results = []
        for doc_id, result in all_results.items():
            lexical_rrf = result.get("scores", {}).get("lexical_rrf", 0.0)
            semantic_rrf = result.get("scores", {}).get("semantic_rrf", 0.0)
            
            # Weighted RRF combination
            rrf_score = (
                self.lexical_weight * lexical_rrf
                + self.semantic_weight * semantic_rrf
            )
            
            result["score"] = rrf_score
            result["score_breakdown"] = {
                "lexical_rrf": lexical_rrf,
                "semantic_rrf": semantic_rrf,
                "fusion_method": "rrf",
                "rrf_k": self.rrf_k,
            }
            
            fused_results.append(result)
        
        # Sort by RRF score
        fused_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return fused_results[:top_k]

    def _fuse_interpolate(
        self,
        lexical_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Interpolation fusion with score boundary handling.
        
        Uses linear interpolation but handles cases where one source has no score.
        """
        all_results = {}
        
        # Process lexical results
        for result in lexical_results:
            doc_id = result.get("id")
            lexical_score = result.get("lexical_score", result.get("score", 0.0))
            
            if doc_id not in all_results:
                all_results[doc_id] = result.copy()
                all_results[doc_id]["scores"] = {}
            
            all_results[doc_id]["scores"]["lexical"] = lexical_score
            all_results[doc_id]["lexical_score"] = lexical_score
        
        # Process semantic results
        for result in semantic_results:
            doc_id = result.get("id")
            semantic_score = result.get("semantic_score", result.get("score", 0.0))
            
            if doc_id not in all_results:
                all_results[doc_id] = result.copy()
                all_results[doc_id]["scores"] = {}
            
            all_results[doc_id]["scores"]["semantic"] = semantic_score
            all_results[doc_id]["semantic_score"] = semantic_score
        
        # Calculate interpolated scores
        fused_results = []
        for doc_id, result in all_results.items():
            lexical_score = result.get("lexical_score", 0.0)
            semantic_score = result.get("semantic_score", 0.0)
            
            # Normalize weights based on availability
            has_lexical = lexical_score > 0
            has_semantic = semantic_score > 0
            
            if has_lexical and has_semantic:
                # Both scores available
                lexical_w = self.lexical_weight
                semantic_w = self.semantic_weight
            elif has_lexical:
                # Only lexical score
                lexical_w = 1.0
                semantic_w = 0.0
            elif has_semantic:
                # Only semantic score
                lexical_w = 0.0
                semantic_w = 1.0
            else:
                # No scores
                continue
            
            interpolated_score = (
                lexical_w * lexical_score + semantic_w * semantic_score
            )
            
            result["score"] = interpolated_score
            result["score_breakdown"] = {
                "lexical": {
                    "raw": lexical_score,
                    "weight": lexical_w,
                    "weighted": lexical_w * lexical_score,
                },
                "semantic": {
                    "raw": semantic_score,
                    "weight": semantic_w,
                    "weighted": semantic_w * semantic_score,
                },
                "fusion_method": "interpolate",
            }
            
            fused_results.append(result)
        
        # Sort by interpolated score
        fused_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return fused_results[:top_k]

    def update_weights(self, lexical_weight: float, semantic_weight: float):
        """
        Update fusion weights.
        
        Args:
            lexical_weight: New lexical weight
            semantic_weight: New semantic weight
        """
        total = lexical_weight + semantic_weight
        self.lexical_weight = lexical_weight / total if total > 0 else 0.5
        self.semantic_weight = semantic_weight / total if total > 0 else 0.5
        
        logger.info(
            f"Updated fusion weights: lexical={self.lexical_weight:.2f}, "
            f"semantic={self.semantic_weight:.2f}"
        )

    def set_fusion_method(self, method: str):
        """
        Set fusion method.
        
        Args:
            method: Fusion method name (linear, rrf, interpolate)
        """
        if method in self.supported_methods:
            self.fusion_method = method
            logger.info(f"Fusion method set to: {method}")
        else:
            logger.warning(
                f"Unsupported fusion method: {method}, "
                f"keeping current: {self.fusion_method}"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get fusion engine statistics"""
        return {
            "lexical_weight": self.lexical_weight,
            "semantic_weight": self.semantic_weight,
            "fusion_method": self.fusion_method,
            "rrf_k": self.rrf_k,
            "supported_methods": list(self.supported_methods),
        }