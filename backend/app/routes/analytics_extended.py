"""Extended analytics endpoints for production-grade search analytics dashboard."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_db
from app.database.engine import DatabaseConnection
from app.database.repositories.user import UserRepository
from app.services.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.schemas import APIResponse
from app.services.analytics_service import AnalyticsService
from app.services.cache import cache_service

logger = logging.getLogger("nebula.analytics")

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SearchEventRequest(BaseModel):
    """Search event recording request."""
    query: str = Field(..., min_length=1, max_length=1000)
    search_type: str = Field(..., pattern=r"^(keyword|semantic|hybrid)$")
    results_count: int = Field(..., ge=0)
    response_time_ms: float = Field(..., ge=0)
    clicked_result: int | None = None
    device: str | None = None


class ClickEventRequest(BaseModel):
    """Click event recording request."""
    search_event_id: int = Field(..., ge=1)
    document_id: int = Field(..., ge=1)
    rank_position: int = Field(..., ge=1)
    time_to_click: float | None = None


class PopularQueryResponse(BaseModel):
    """Popular query response."""
    query: str
    count: int


class ZeroResultQueryResponse(BaseModel):
    """Zero result query response."""
    query: str
    count: int


class ResponseTimeStats(BaseModel):
    """Response time statistics."""
    average: float
    median: float
    p95: float
    p99: float
    max: float


class QueryTrend(BaseModel):
    """Query trend data."""
    date: str
    queries: int
    unique_users: int | None = None
    zero_results: int | None = None


class DashboardOverview(BaseModel):
    """Dashboard overview statistics."""
    total_queries: int
    unique_users: int
    average_response_time_ms: float
    zero_result_rate: float
    click_through_rate: float


class DashboardResponse(BaseModel):
    """Full dashboard response."""
    overview: DashboardOverview
    popular_searches: list[PopularQueryResponse]
    response_times: ResponseTimeStats
    zero_result_queries: list[ZeroResultQueryResponse]
    query_trends: list[QueryTrend]


class UserAnalyticsResponse(BaseModel):
    """User analytics response."""
    searches: int
    avg_session_duration_ms: float
    preferred_search_type: str
    most_clicked_documents: list[dict[str, Any]]


class ClickAnalyticsResponse(BaseModel):
    """Click analytics response."""
    total_clicks: int
    avg_click_position: float
    most_clicked_documents: list[dict[str, Any]]


class SearchQualityMetrics(BaseModel):
    """Search quality metrics."""
    zero_result_rate: float
    avg_response_time: float
    semantic_search_usage: int
    hybrid_search_usage: int


# ---------------------------------------------------------------------------
# Admin authorization guard
# ---------------------------------------------------------------------------

async def _require_admin(email: str = Depends(get_current_user), db: DatabaseConnection = Depends(get_db)) -> str:
    """Require admin role for analytics endpoints."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return email


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=DashboardResponse, dependencies=[Depends(rate_limit)])
async def get_dashboard(
    period: str = Query("24h", description="Time period: 24h, 7d, 30d, 90d"),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get analytics dashboard overview."""
    if period not in ("24h", "7d", "30d", "90d"):
        raise HTTPException(status_code=400, detail="Invalid period. Use: 24h, 7d, 30d, 90d")
    
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_dashboard(period=period)


@router.get("/popular", response_model=list[PopularQueryResponse], dependencies=[Depends(rate_limit)])
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get popular search queries."""
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_popular(limit=limit, days=days)


@router.get("/zero-results", response_model=list[ZeroResultQueryResponse], dependencies=[Depends(rate_limit)])
async def get_zero_result_searches(
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get queries that returned zero results."""
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_zero_results(limit=limit, days=days)


@router.get("/response-times", response_model=ResponseTimeStats, dependencies=[Depends(rate_limit)])
async def get_response_times(
    days: int = Query(7, ge=1, le=90),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get response time analytics."""
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_response_times(days=days)


@router.get("/query-trends", response_model=list[QueryTrend], dependencies=[Depends(rate_limit)])
async def get_query_trends(
    period: str = Query("daily", description="Period: hourly, daily, weekly, monthly"),
    days: int = Query(30, ge=1, le=365),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get search query trends over time."""
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_query_trends(period=period, days=days)


@router.get("/clicks", response_model=ClickAnalyticsResponse, dependencies=[Depends(rate_limit)])
async def get_click_analytics(
    days: int = Query(7, ge=1, le=90),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get click-through analytics."""
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_click_analytics(days=days)


@router.post("/record-click", dependencies=[Depends(rate_limit)])
async def record_click(
    payload: ClickEventRequest,
    email: str = Depends(get_current_user),
    db: DatabaseConnection = Depends(get_db),
):
    """Record a click event from a search result."""
    # Look up the search event
    from app.database.repositories.search import SearchRepository
    search_repo = SearchRepository(db)
    await search_repo.recent_for_user(user_id=0, limit=1)  # placeholder
    
    # In production, fetch actual search event from DB
    # For now, we just store the click
    service = AnalyticsService(db, redis_client=cache_service._redis)
    await service.record_click(
        search_event_id=payload.search_event_id,
        query="",  # Would be populated from search_event record
        document_id=payload.document_id,
        rank_position=payload.rank_position,
        time_to_click=payload.time_to_click,
        user_id=None,  # Would be resolved from current user
    )
    return APIResponse(message="Click recorded")


@router.get("/users/{user_id}", response_model=UserAnalyticsResponse, dependencies=[Depends(rate_limit)])
async def get_user_analytics(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get analytics for a specific user."""
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_user_analytics(user_id=user_id, days=days)


@router.get("/quality", response_model=SearchQualityMetrics, dependencies=[Depends(rate_limit)])
async def get_search_quality(
    days: int = Query(30, ge=1, le=365),
    _admin: str = Depends(_require_admin),
    db: DatabaseConnection = Depends(get_db),
):
    """Get search quality metrics."""
    service = AnalyticsService(db, redis_client=cache_service._redis)
    return await service.get_search_quality_metrics(days=days)


@router.post("/record-search", response_model=APIResponse, dependencies=[Depends(rate_limit)])
async def record_search(
    payload: SearchEventRequest,
    email: str = Depends(get_current_user),
    db: DatabaseConnection = Depends(get_db),
):
    """Record a search event."""
    # Resolve user_id from email
    from app.database.repositories.user import UserRepository
    users = UserRepository(db)
    user = await users.get_by_email(email)
    user_id = user.get("id") if user else None
    
    # Generate a session ID (in production, from cookie or header)
    import uuid
    session_id = str(uuid.uuid4())
    
    service = AnalyticsService(db, redis_client=cache_service._redis)
    await service.record_search(
        query=payload.query,
        user_id=user_id,
        session_id=session_id,
        search_backend="unified",
        search_type=payload.search_type,
        results_count=payload.results_count,
        response_time_ms=payload.response_time_ms,
        clicked_result=payload.clicked_result,
        device=payload.device,
    )
    return APIResponse(message="Search event recorded")