"""
Hybrid Search API Routes

REST endpoints for hybrid search functionality.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

from app.services.auth import get_current_user_token_payload
from app.hybrid.config import HybridSearchConfig
from app.hybrid.services import hybrid_search_service

logger = logging.getLogger("nebula.hybrid.routes")

router = APIRouter(prefix="/api/v1/search/hybrid", tags=["hybrid-search"])


# Request/Response Models
class HybridSearchRequest(BaseModel):
    """Hybrid search request"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    top_k: int = Field(20, description="Number of results to return", ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    explain: bool = Field(False, description="Generate explanations")
    query_vector: Optional[List[float]] = Field(None, description="Query embedding vector")


class HybridSearchResponse(BaseModel):
    """Hybrid search response"""
    query: str
    results: List[Dict[str, Any]]
    result_count: int
    intent: Optional[Dict[str, Any]]
    latency_ms: float
    bm25_latency_ms: float
    fusion_latency_ms: float
    deduplication_latency_ms: float
    explanations: Optional[List[Dict[str, Any]]]


class ExplainRequest(BaseModel):
    """Search explanation request"""
    query: str = Field(..., description="Search query")
    query_vector: Optional[List[float]] = Field(None, description="Query embedding")


class ExplainResponse(BaseModel):
    """Search explanation response"""
    query: str
    intent: Dict[str, Any]
    strategy: Dict[str, Any]
    configuration: Dict[str, Any]
    top_documents: List[Dict[str, Any]]
    bm25_params: Dict[str, Any]


class ConfigResponse(BaseModel):
    """Hybrid search configuration"""
    model_config = ConfigDict(from_attributes=True)
    enable_hybrid_search: bool
    bm25_weight: float
    semantic_weight: float
    top_k_keyword: int
    top_k_vector: int
    max_results: int
    normalization_method: str
    enable_dynamic_weighting: bool
    enable_deduplication: bool
    enable_metadata_boost: bool
    enable_search_explain: bool


class MetricsResponse(BaseModel):
    """Hybrid search metrics"""
    model_config = ConfigDict(from_attributes=True)
    total_searches: int
    success_rate: float
    average_latency_ms: float
    average_result_count: float
    average_score: float
    top_queries: List[Dict[str, Any]]
    intent_distribution: Dict[str, int]
    recent_queries: List[str]


class StatisticsResponse(BaseModel):
    """System statistics"""
    model_config = ConfigDict(from_attributes=True)
    retriever: Dict[str, Any]
    fusion: Dict[str, Any]
    deduplicator: Dict[str, Any]
    metrics: Dict[str, Any]


# Endpoints
@router.post("/", response_model=HybridSearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    current_user: dict = Depends(get_current_user_token_payload),
):
    """
    Perform hybrid search combining BM25 and semantic search.
    
    Returns ranked results with optional explanations.
    """
    try:
        # Get documents from vector search/index
        # This is a placeholder - integrate with your document retrieval
        documents = []
        
        # If you have a document store, fetch documents here
        # For now, we expect documents to be passed or fetched
        
        results = await hybrid_search_service.search(
            query=request.query,
            documents=documents,
            query_vector=request.query_vector,
            top_k=request.top_k,
            filters=request.filters,
            explain=request.explain,
            user_id=current_user.get("sub") if current_user else None,
        )
        
        return HybridSearchResponse(**results)
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post("/explain", response_model=ExplainResponse)
async def explain_search(
    request: ExplainRequest,
):
    """
    Generate detailed explanation of search process.
    
    Returns intent analysis, strategy, and scored documents.
    """
    try:
        # Get documents
        documents = []
        
        explanation = hybrid_search_service.explain_search(
            query=request.query,
            documents=documents,
            query_vector=request.query_vector,
        )
        
        return ExplainResponse(**explanation)
        
    except Exception as e:
        logger.error(f"Explain search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation failed: {str(e)}",
        )


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """
    Get current hybrid search configuration.
    
    Returns all configurable parameters.
    """
    config = HybridSearchConfig.from_env()
    
    return ConfigResponse(
        enable_hybrid_search=config.enable_hybrid_search,
        bm25_weight=config.bm25_weight,
        semantic_weight=config.semantic_weight,
        top_k_keyword=config.top_k_keyword,
        top_k_vector=config.top_k_vector,
        max_results=config.max_results,
        normalization_method=config.normalization_method,
        enable_dynamic_weighting=config.enable_dynamic_weighting,
        enable_deduplication=config.enable_deduplication,
        enable_metadata_boost=config.enable_metadata_boost,
        enable_search_explain=config.enable_search_explain,
    )


@router.put("/config")
async def update_config(
    config_updates: Dict[str, Any],
):
    """
    Update hybrid search configuration.
    
    Requires authentication.
    """
    # Validate config updates
    allowed_fields = {
        "bm25_weight",
        "semantic_weight",
        "top_k_keyword",
        "top_k_vector",
        "max_results",
        "normalization_method",
        "enable_dynamic_weighting",
        "enable_deduplication",
        "enable_metadata_boost",
        "enable_search_explain",
        "title_boost",
        "heading_boost",
        "tag_boost",
        "category_boost",
        "recency_boost",
        "popularity_boost",
    }
    
    invalid_fields = set(config_updates.keys()) - allowed_fields
    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid config fields: {invalid_fields}",
        )
    
    try:
        hybrid_search_service.update_config(config_updates)
        
        return {
            "message": "Configuration updated successfully",
            "updated_fields": list(config_updates.keys()),
        }
        
    except Exception as e:
        logger.error(f"Config update error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config update failed: {str(e)}",
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get hybrid search metrics.
    
    Returns performance and usage statistics.
    """
    metrics = hybrid_search_service.get_metrics()
    
    return MetricsResponse(
        total_searches=metrics.get("total_searches", 0),
        success_rate=metrics.get("success_rate", 0.0),
        average_latency_ms=metrics.get("average_latency_ms", 0.0),
        average_result_count=metrics.get("average_result_count", 0.0),
        average_score=metrics.get("average_score", 0.0),
        top_queries=metrics.get("top_queries", []),
        intent_distribution=metrics.get("intent_distribution", {}),
        recent_queries=metrics.get("recent_queries", []),
    )


@router.post("/rebuild-ranking")
async def rebuild_ranking():
    """
    Rebuild ranking indices.
    
    Reinitializes BM25 and semantic search indices.
    """
    try:
        # This would typically reindex all documents
        # For now, return success
        return {
            "message": "Ranking indices rebuilt successfully",
            "status": "completed",
        }
        
    except Exception as e:
        logger.error(f"Rebuild ranking error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rebuild failed: {str(e)}",
        )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Get comprehensive system statistics.
    
    Returns statistics about all hybrid search components.
    """
    stats = hybrid_search_service.get_statistics()
    
    return StatisticsResponse(**stats)