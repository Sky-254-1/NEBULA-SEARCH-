"""
Hybrid Search Configuration

Loads and validates hybrid search configuration from environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search"""

    # Feature flags
    enable_hybrid_search: bool = True
    enable_dynamic_weighting: bool = True
    enable_deduplication: bool = True
    enable_metadata_boost: bool = True
    enable_search_explain: bool = False

    # Scoring weights
    bm25_weight: float = 0.6
    semantic_weight: float = 0.4

    # Retrieval parameters
    top_k_keyword: int = 50
    top_k_vector: int = 50
    max_results: int = 20

    # Normalization
    normalization_method: str = "minmax"  # minmax, zscore, softmax, rank

    # BM25 parameters
    bm25_k1: float = 1.5
    bm25_b: float = 0.75

    # Freshness
    freshness_half_life_days: int = 7

    # Ranking weights
    keyword_weight: float = 0.35
    semantic_weight_final: float = 0.25
    freshness_weight: float = 0.10
    popularity_weight: float = 0.10
    personalization_weight: float = 0.10
    metadata_weight: float = 0.10

    # Thresholds
    min_keyword_score: float = 0.1
    min_semantic_score: float = 0.3

    # Metadata boost weights
    title_boost: float = 2.0
    heading_boost: float = 1.5
    tag_boost: float = 1.3
    category_boost: float = 1.2
    recency_boost: float = 1.4
    popularity_boost: float = 1.3

    # Intent-specific weights
    intent_weights: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Cache settings
    cache_embeddings: bool = True
    cache_ttl_seconds: int = 3600

    # Performance
    parallel_timeout_ms: int = 5000
    max_concurrent_requests: int = 100

    def __post_init__(self):
        """Initialize intent weights if not provided"""
        if not self.intent_weights:
            self.intent_weights = {
                "keyword": {"bm25": 0.8, "semantic": 0.2},
                "question": {"bm25": 0.3, "semantic": 0.7},
                "natural_language": {"bm25": 0.4, "semantic": 0.6},
                "phrase": {"bm25": 0.7, "semantic": 0.3},
                "code": {"bm25": 0.6, "semantic": 0.4},
                "document": {"bm25": 0.5, "semantic": 0.5},
                "mixed": {"bm25": 0.5, "semantic": 0.5},
            }

    @classmethod
    def from_env(cls) -> "HybridSearchConfig":
        """Load configuration from environment variables"""
        config = cls()

        # Feature flags
        config.enable_hybrid_search = cls._get_bool("ENABLE_HYBRID_SEARCH", config.enable_hybrid_search)
        config.enable_dynamic_weighting = cls._get_bool("ENABLE_DYNAMIC_WEIGHTING", config.enable_dynamic_weighting)
        config.enable_deduplication = cls._get_bool("ENABLE_RESULT_DEDUPLICATION", config.enable_deduplication)
        config.enable_metadata_boost = cls._get_bool("ENABLE_METADATA_BOOST", config.enable_metadata_boost)
        config.enable_search_explain = cls._get_bool("ENABLE_SEARCH_EXPLAIN", config.enable_search_explain)

        # Scoring weights
        bm25_weight = cls._get_float("BM25_WEIGHT", config.bm25_weight)
        semantic_weight = cls._get_float("SEMANTIC_WEIGHT", config.semantic_weight)
        
        # Normalize weights
        total = bm25_weight + semantic_weight
        config.bm25_weight = bm25_weight / total if total > 0 else 0.5
        config.semantic_weight = semantic_weight / total if total > 0 else 0.5

        # Retrieval parameters
        config.top_k_keyword = cls._get_int("TOP_K_KEYWORD", config.top_k_keyword)
        config.top_k_vector = cls._get_int("TOP_K_VECTOR", config.top_k_vector)
        config.max_results = cls._get_int("MAX_RESULTS", config.max_results)

        # Normalization
        config.normalization_method = os.getenv("NORMALIZATION_METHOD", config.normalization_method).lower()

        # BM25 parameters
        config.bm25_k1 = cls._get_float("BM25_K1", config.bm25_k1)
        config.bm25_b = cls._get_float("BM25_B", config.bm25_b)

        # Freshness
        config.freshness_half_life_days = cls._get_int("FRESHNESS_HALF_LIFE_DAYS", config.freshness_half_life_days)

        # Ranking weights
        config.keyword_weight = cls._get_float("KEYWORD_WEIGHT", config.keyword_weight)
        config.semantic_weight_final = cls._get_float("SEMANTIC_WEIGHT_FINAL", config.semantic_weight_final)
        config.freshness_weight = cls._get_float("FRESHNESS_WEIGHT", config.freshness_weight)
        config.popularity_weight = cls._get_float("POPULARITY_WEIGHT", config.popularity_weight)
        config.personalization_weight = cls._get_float("PERSONALIZATION_WEIGHT", config.personalization_weight)
        config.metadata_weight = cls._get_float("METADATA_WEIGHT", config.metadata_weight)

        # Thresholds
        config.min_keyword_score = cls._get_float("MIN_KEYWORD_SCORE", config.min_keyword_score)
        config.min_semantic_score = cls._get_float("MIN_SEMANTIC_SCORE", config.min_semantic_score)

        # Metadata boosts
        config.title_boost = cls._get_float("TITLE_BOOST", config.title_boost)
        config.heading_boost = cls._get_float("HEADING_BOOST", config.heading_boost)
        config.tag_boost = cls._get_float("TAG_BOOST", config.tag_boost)
        config.category_boost = cls._get_float("CATEGORY_BOOST", config.category_boost)
        config.recency_boost = cls._get_float("RECENCY_BOOST", config.recency_boost)
        config.popularity_boost = cls._get_float("POPULARITY_BOOST", config.popularity_boost)

        # Cache settings
        config.cache_embeddings = cls._get_bool("CACHE_EMBEDDINGS", config.cache_embeddings)
        config.cache_ttl_seconds = cls._get_int("CACHE_TTL_SECONDS", config.cache_ttl_seconds)

        # Performance
        config.parallel_timeout_ms = cls._get_int("PARALLEL_TIMEOUT_MS", config.parallel_timeout_ms)
        config.max_concurrent_requests = cls._get_int("MAX_CONCURRENT_REQUESTS", config.max_concurrent_requests)

        return config

    @staticmethod
    def _get_bool(key: str, default: bool) -> bool:
        """Get boolean from environment"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def _get_float(key: str, default: float) -> float:
        """Get float from environment"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    @staticmethod
    def _get_int(key: str, default: int) -> int:
        """Get int from environment"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "enable_hybrid_search": self.enable_hybrid_search,
            "enable_dynamic_weighting": self.enable_dynamic_weighting,
            "enable_deduplication": self.enable_deduplication,
            "enable_metadata_boost": self.enable_metadata_boost,
            "enable_search_explain": self.enable_search_explain,
            "bm25_weight": self.bm25_weight,
            "semantic_weight": self.semantic_weight,
            "top_k_keyword": self.top_k_keyword,
            "top_k_vector": self.top_k_vector,
            "max_results": self.max_results,
            "normalization_method": self.normalization_method,
            "bm25_k1": self.bm25_k1,
            "bm25_b": self.bm25_b,
            "freshness_half_life_days": self.freshness_half_life_days,
            "keyword_weight": self.keyword_weight,
            "semantic_weight_final": self.semantic_weight_final,
            "freshness_weight": self.freshness_weight,
            "popularity_weight": self.popularity_weight,
            "personalization_weight": self.personalization_weight,
            "metadata_weight": self.metadata_weight,
            "min_keyword_score": self.min_keyword_score,
            "min_semantic_score": self.min_semantic_score,
            "title_boost": self.title_boost,
            "heading_boost": self.heading_boost,
            "tag_boost": self.tag_boost,
            "category_boost": self.category_boost,
            "recency_boost": self.recency_boost,
            "popularity_boost": self.popularity_boost,
            "intent_weights": self.intent_weights,
            "cache_embeddings": self.cache_embeddings,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "parallel_timeout_ms": self.parallel_timeout_ms,
            "max_concurrent_requests": self.max_concurrent_requests,
        }


# Global config instance
hybrid_config = HybridSearchConfig.from_env()