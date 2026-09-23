"""Analytics endpoints for usage tracking and metrics."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any

from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.user import UserRepository
from app.services.auth import get_current_user
from app.search.intelligence import search_analytics

logger = logging.getLogger("nebula.analytics")

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


async def _user_id(db, email: str) -> int:
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user["id"]


class UsageStats(BaseModel):
    """Usage statistics model."""
    total_searches: int
    total_documents: int
    total_ai_queries: int
    period_days: int
    daily_average: float


class SearchAnalytics(BaseModel):
    """Search analytics model."""
    total_queries: int
    unique_queries: int
    avg_response_time_ms: float
    backends_used: Dict[str, int]
    top_queries: List[Dict[str, Any]]
    period_days: int


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    cache_hit_ratio: float
    error_rate: float
    period_days: int


class AnalyticsExport(BaseModel):
    """Analytics export model."""
    export_id: int
    export_type: str
    download_url: str
    created_at: str


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    period_days: int = Query(30, ge=1, le=365),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get user usage statistics."""
    user_id = await _user_id(db, email)

    # Use DB-backed analytics
    search_analytics._set_db(db)
    history = await search_analytics.get_user_search_history(user_id, limit=10000)

    total_searches = len(history)
    daily_average = total_searches / period_days if period_days > 0 else 0.0

    docs_repo = DocumentRepository(db)
    docs = await docs_repo.list_for_user(user_id, limit=10000)
    total_documents = len(docs)

    return UsageStats(
        total_searches=total_searches,
        total_documents=total_documents,
        total_ai_queries=0,
        period_days=period_days,
        daily_average=round(daily_average, 2),
    )


@router.get("/search", response_model=SearchAnalytics)
async def get_search_analytics(
    period_days: int = Query(30, ge=1, le=365),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get search analytics for user."""
    user_id = await _user_id(db, email)

    search_analytics._set_db(db)
    history = await search_analytics.get_user_search_history(user_id, limit=10000)

    total_queries = len(history)
    unique_queries = len(set(item.get("query", "") for item in history))

    backends_used: Dict[str, int] = {}
    for item in history:
        backend = item.get("backend", "unknown")
        backends_used[backend] = backends_used.get(backend, 0) + 1

    query_counts: Dict[str, int] = {}
    for item in history:
        query = item.get("query", "")
        query_counts[query] = query_counts.get(query, 0) + 1

    top_queries = [
        {"query": q, "count": c}
        for q, c in sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return SearchAnalytics(
        total_queries=total_queries,
        unique_queries=unique_queries,
        avg_response_time_ms=0.0,
        backends_used=backends_used,
        top_queries=top_queries,
        period_days=period_days,
    )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    period_days: int = Query(7, ge=1, le=90),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get performance metrics."""
    from app.services.monitoring import metrics
    return PerformanceMetrics(
        avg_latency_ms=round(metrics.get_avg_response_time(), 2),
        p95_latency_ms=round(metrics.get_avg_response_time() * 1.5, 2),
        p99_latency_ms=round(metrics.get_avg_response_time() * 2.0, 2),
        cache_hit_ratio=round(metrics.get_cache_hit_ratio(), 4),
        error_rate=round(metrics.get_error_rate(), 4),
        period_days=period_days,
    )


@router.get("/export")
async def export_analytics(
    export_type: str = Query("json", description="Export format (json, csv)"),
    period_days: int = Query(30, ge=1, le=365),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Export analytics data."""
    user_id = await _user_id(db, email)

    import json
    import uuid

    search_analytics._set_db(db)
    history = await search_analytics.get_user_search_history(user_id, limit=10000)

    from app.config import get_settings
    settings = get_settings()
    export_dir = settings.storage_exports / str(user_id)
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = f"analytics_{uuid.uuid4().hex}.{export_type}"
    dest = export_dir / filename

    export_data = {
        "user_id": user_id,
        "email": email,
        "period_days": period_days,
        "exported_at": datetime.now().isoformat(),
        "search_history": history,
    }

    dest.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
    export_id = 1

    return AnalyticsExport(
        export_id=export_id,
        export_type=export_type,
        download_url=f"/exports/{filename}",
        created_at=datetime.now().isoformat(),
    )
