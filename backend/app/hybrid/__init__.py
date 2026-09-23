"""
Hybrid Search Module

Production-grade hybrid search combining BM25 keyword ranking with semantic vector search.
"""

from app.hybrid.bm25 import BM25Engine
from app.hybrid.semantic import SemanticEngine
from app.hybrid.fusion import FusionEngine
from app.hybrid.dedupe import Deduplicator
from app.hybrid.ranking import HybridRanker
from app.hybrid.retriever import ParallelRetriever
from app.hybrid.intent import IntentDetector
from app.hybrid.boosting import MetadataBooster
from app.hybrid.normalization import ScoreNormalizer
from app.hybrid.filters import FilterEngine
from app.hybrid.scoring import ScoringEngine
from app.hybrid.metadata import MetadataExtractor
from app.hybrid.explain import ExplanationGenerator
from app.hybrid.metrics import HybridMetrics
from app.hybrid.services import HybridSearchService
from app.hybrid.config import HybridSearchConfig
from app.hybrid.routes import router as hybrid_router

__all__ = [
    "BM25Engine",
    "SemanticEngine",
    "FusionEngine",
    "Deduplicator",
    "HybridRanker",
    "ParallelRetriever",
    "IntentDetector",
    "MetadataBooster",
    "ScoreNormalizer",
    "FilterEngine",
    "ScoringEngine",
    "MetadataExtractor",
    "ExplanationGenerator",
    "HybridMetrics",
    "HybridSearchService",
    "HybridSearchConfig",
    "hybrid_router",
]