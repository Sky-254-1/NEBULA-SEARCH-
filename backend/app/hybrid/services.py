"""
Hybrid Search Service

Main service layer orchestrating the hybrid search pipeline.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.hybrid.config import HybridSearchConfig, hybrid_config
from app.hybrid.retriever import ParallelRetriever
from app.hybrid.fusion import FusionEngine
from app.hybrid.dedupe import Deduplicator
from app.hybrid.boosting import MetadataBooster
from app.hybrid.intent import IntentDetector
from app.hybrid.filters import FilterEngine
from app.hybrid.scoring import ScoringEngine
from app.hybrid.explain import ExplanationGenerator
from app.hybrid.metrics import HybridMetrics, SearchMetrics

logger = logging.getLogger("nebula.hybrid.service")


class HybridSearchService:
    """
    Main hybrid search service.
    
    Orchestrates the complete search pipeline:
    1. Detect query intent
    2. Parallel retrieval (BM25 + semantic)
    3. Score normalization
    4. Fusion
    5. Deduplication
    6. Filtering
    7. Metadata boosting
    8. Final ranking
    """

    def __init__(self, config: Optional[HybridSearchConfig] = None):
        """
        Initialize hybrid search service.
        
        Args:
            config: Hybrid search configuration
        """
        self.config = config or hybrid_config
        
        # Initialize components
        self.retriever = ParallelRetriever(
            top_k_keyword=self.config.top_k_keyword,
            top_k_vector=self.config.top_k_vector,
            timeout_ms=self.config.parallel_timeout_ms,
        )
        
        self.fusion_engine = FusionEngine(
            lexical_weight=self.config.bm25_weight,
            semantic_weight=self.config.semantic_weight,
        )
        
        self.deduplicator = Deduplicator()
        self.metadata_booster = MetadataBooster(
            title_boost=self.config.title_boost,
            heading_boost=self.config.heading_boost,
            tag_boost=self.config.tag_boost,
            category_boost=self.config.category_boost,
            recency_boost=self.config.recency_boost,
            popularity_boost=self.config.popularity_boost,
        )
        self.intent_detector = IntentDetector()
        self.filter_engine = FilterEngine()
        self.scoring_engine = ScoringEngine(self.config)
        self.explanation_generator = ExplanationGenerator()
        self.metrics = HybridMetrics()

    async def search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        query_vector: Optional[List[float]] = None,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        explain: bool = False,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            documents: Documents to search
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters
            explain: Whether to generate explanations
            user_id: User ID for personalization
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        intent_result = None
        error_msg = None
        
        try:
            # Step 1: Detect query intent
            if self.config.enable_dynamic_weighting:
                intent_result = self.intent_detector.detect(query)
                
                # Adjust fusion weights based on intent
                if intent_result["confidence"] > 0.6:
                    strategy = self.intent_detector.get_search_strategy(intent_result)
                    self.fusion_engine.update_weights(
                        strategy["keyword_weight"],
                        strategy["semantic_weight"],
                    )
            
            # Step 2: Parallel retrieval
            retrieval_start = time.time()
            bm25_results, vector_results = await self.retriever.retrieve(
                query, query_vector, documents
            )
            bm25_latency = (time.time() - retrieval_start) * 1000
            
            # Step 3: Fusion
            fusion_start = time.time()
            fused_results = self.fusion_engine.fuse(
                bm25_results, vector_results, top_k=top_k * 2
            )
            fusion_latency = (time.time() - fusion_start) * 1000
            
            # Step 4: Deduplication
            dedup_start = time.time()
            if self.config.enable_deduplication:
                deduped_results = self.deduplicator.deduplicate(fused_results)
            else:
                deduped_results = fused_results
            dedup_latency = (time.time() - dedup_start) * 1000
            
            # Step 5: Apply filters
            filtered_results = self.filter_engine.apply_filters(deduped_results, filters)
            
            # Step 6: Metadata boosting
            if self.config.enable_metadata_boost:
                boosted_results = self.metadata_booster.boost(filtered_results, query)
            else:
                boosted_results = filtered_results
            
            # Step 7: Final ranking
            final_results = boosted_results[:top_k]
            
            # Step 8: Generate explanations if requested
            result_explanations = None
            if explain or self.config.enable_search_explain:
                result_explanations = [
                    self.explanation_generator.explain_result(result, query, final_results)
                    for result in final_results
                ]
            
            # Calculate total latency
            total_latency = (time.time() - start_time) * 1000
            
            # Prepare response
            response = {
                "query": query,
                "results": final_results,
                "result_count": len(final_results),
                "intent": intent_result,
                "latency_ms": total_latency,
                "bm25_latency_ms": bm25_latency,
                "vector_latency_ms": 0,  # Included in bm25 for now
                "fusion_latency_ms": fusion_latency,
                "deduplication_latency_ms": dedup_latency,
                "explainations": result_explanations,
            }
            
            # Record metrics
            avg_score = (
                sum(r.get("score", 0.0) for r in final_results) / len(final_results)
                if final_results
                else 0.0
            )
            
            metrics = SearchMetrics(
                query=query,
                total_latency_ms=total_latency,
                bm25_latency_ms=bm25_latency,
                vector_latency_ms=0,
                fusion_latency_ms=fusion_latency,
                deduplication_latency_ms=dedup_latency,
                result_count=len(final_results),
                bm25_result_count=len(bm25_results),
                vector_result_count=len(vector_results),
                duplicates_removed=len(fused_results) - len(deduped_results),
                average_score=avg_score,
                max_score=final_results[0].get("score", 0.0) if final_results else 0.0,
                min_score=final_results[-1].get("score", 0.0) if final_results else 0.0,
                intent=intent_result.get("intent") if intent_result else None,
                intent_confidence=intent_result.get("confidence", 0.0) if intent_result else 0.0,
                success=True,
            )
            self.metrics.record_search(metrics)
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Hybrid search error: {e}", exc_info=True)
            
            # Record failed search
            total_latency = (time.time() - start_time) * 1000
            metrics = SearchMetrics(
                query=query,
                total_latency_ms=total_latency,
                success=False,
                error=error_msg,
            )
            self.metrics.record_search(metrics)
            
            raise

    def explain_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        query_vector: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Generate detailed explanation of search process.
        
        Args:
            query: Search query
            documents: Documents to search
            query_vector: Query embedding
            
        Returns:
            Detailed explanation
        """
        # Detect intent
        intent = self.intent_detector.detect(query)
        
        # Get strategy
        strategy = self.intent_detector.get_search_strategy(intent)
        
        # Score documents
        scored_docs = self.scoring_engine.batch_score(
            query, query_vector, documents, intent
        )
        
        # Rank documents
        ranked_docs = sorted(scored_docs, key=lambda x: x.get("score", 0.0), reverse=True)
        
        return {
            "query": query,
            "intent": intent,
            "strategy": strategy,
            "configuration": {
                "weights": strategy,
                "config_enabled": self.config.enable_hybrid_search,
            },
            "top_documents": ranked_docs[:10],
            "bm25_params": {
                "k1": self.config.bm25_k1,
                "b": self.config.bm25_b,
            },
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get search metrics"""
        return self.metrics.get_summary()

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "retriever": self.retriever.get_statistics(),
            "fusion": self.fusion_engine.get_statistics(),
            "deduplicator": self.deduplicator.get_statistics([]),
            "metrics": self.get_metrics(),
        }

    def update_config(self, config_updates: Dict[str, Any]):
        """
        Update configuration.
        
        Args:
            config_updates: Dictionary of config updates
        """
        # Update config object
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Update components
        self.fusion_engine.update_weights(
            self.config.bm25_weight,
            self.config.semantic_weight,
        )
        self.retriever.set_top_k(
            self.config.top_k_keyword,
            self.config.top_k_vector,
        )
        
        logger.info(f"Updated hybrid search configuration: {config_updates}")

    def reset_metrics(self):
        """Reset metrics"""
        self.metrics.reset()


# Global service instance
hybrid_search_service = HybridSearchService()