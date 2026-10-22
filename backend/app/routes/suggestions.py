"""Search suggestions API routes."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.database.engine import DatabaseConnection
from app.database.repositories.user import UserRepository
from app.services.auth import get_current_user
from app.services.suggestion_service import SuggestionService

logger = logging.getLogger("nebula.suggestions")

router = APIRouter(prefix="/api/v1/search/suggestions", tags=["Suggestions"])


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class SuggestionItem(BaseModel):
    """Single search suggestion."""
    model_config = ConfigDict(json_schema_extra={"examples": {"text": "machine learning", "type": "trending", "score": 0.98}})
    text: str
    type: str
    score: float


class SuggestionsResponse(BaseModel):
    """Search suggestions response."""
    model_config = ConfigDict(json_schema_extra={"examples": {"query": "machine", "suggestions": [], "cache_hit": False, "latency_ms": 45}})
    query: str
    suggestions: list[SuggestionItem]
    cache_hit: bool
    latency_ms: int


class TrendingResponse(BaseModel):
    """Trending queries response."""
    query: str
    suggestions: list[SuggestionItem]


class RelatedResponse(BaseModel):
    """Related searches response."""
    query: str
    suggestions: list[SuggestionItem]


class RebuildResponse(BaseModel):
    """Rebuild operation response."""
    status: str
    details: dict[str, Any]


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _get_suggestion_service(db: DatabaseConnection = Depends(get_db)) -> SuggestionService:
    return SuggestionService(db)


def _sanitize_query(query: str) -> str:
    """Sanitize and validate query input."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    query = query.strip()
    if len(query) > 100:
        raise HTTPException(status_code=400, detail="Query must be 100 characters or less")
    return query


# ------------------------------------------------------------------ #
# Endpoints
# ------------------------------------------------------------------ #

@router.get(
    "",
    response_model=SuggestionsResponse,
    summary="Get search suggestions",
    description="Get AI-powered search suggestions combining trending, semantic, and related searches.",
    responses={
        200: {"description": "Suggestions retrieved successfully"},
        400: {"description": "Invalid query parameter"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def get_suggestions(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100, examples={"default": {"value": "machine"}}),
    limit: int = Query(5, ge=1, le=10),
    service: SuggestionService = Depends(_get_suggestion_service),
) -> SuggestionsResponse:
    """Get search suggestions for a query."""
    query = _sanitize_query(q)

    # Extract user email if authenticated
    email = None
    try:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from starlette.requests import Request as StarletteRequest
            req = StarletteRequest(request.scope)
            email = await get_current_user(req)
    except Exception as exc:
        logger.debug("Suggestions auth extraction failed: %s", exc)
        pass  # Anonymous access is fine

    # Generate session ID from request
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = getattr(request.state, "request_id", None)
    if not session_id:
        import uuid as uuid_module
        session_id = str(uuid_module.uuid4())

    result = await service.get_suggestions(
        query=query,
        limit=limit,
        user_id=email,
        session_id=session_id,
    )

    return SuggestionsResponse(**result)


@router.get(
    "/trending",
    response_model=TrendingResponse,
    summary="Get trending suggestions",
    description="Get trending searches matching the query prefix.",
)
async def get_trending(
    q: str = Query(..., min_length=1, max_length=100, examples={"default": {"value": "machine"}}),
    limit: int = Query(10, ge=1, le=10),
    service: SuggestionService = Depends(_get_suggestion_service),
) -> TrendingResponse:
    """Get trending suggestions."""
    query = _sanitize_query(q)
    suggestions = await service.get_trending_suggestions(query, limit=limit)

    return TrendingResponse(
        query=query,
        suggestions=[SuggestionItem(**s) for s in suggestions],
    )


@router.get(
    "/related",
    response_model=RelatedResponse,
    summary="Get related searches",
    description="Get related searches based on user behavior and co-occurrence.",
)
async def get_related(
    q: str = Query(..., min_length=1, max_length=100, examples={"default": {"value": "python"}}),
    limit: int = Query(10, ge=1, le=10),
    service: SuggestionService = Depends(_get_suggestion_service),
) -> RelatedResponse:
    """Get related searches."""
    query = _sanitize_query(q)
    suggestions = await service.get_related_suggestions(query, limit=limit)

    return RelatedResponse(
        query=query,
        suggestions=[SuggestionItem(**s) for s in suggestions],
    )


@router.post(
    "/rebuild",
    response_model=RebuildResponse,
    summary="Rebuild suggestion indexes",
    description="Rebuild trending metrics, related searches, and semantic suggestions. Requires admin privileges.",
    responses={
        200: {"description": "Rebuild completed successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - admin access required"},
    },
)
async def rebuild_suggestions(
    email: str = Depends(get_current_user),
    service: SuggestionService = Depends(_get_suggestion_service),
    db: DatabaseConnection = Depends(get_db),
) -> RebuildResponse:
    """Rebuild all suggestion indexes. Admin only."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info("User %s initiated suggestion rebuild", email)

    # Run all rebuilds in parallel
    trending_result, related_result, semantic_result = await asyncio.gather(
        service.refresh_trending(),
        service.refresh_related_searches(),
        service.refresh_semantic_suggestions(),
    )

    return RebuildResponse(
        status="success",
        details={
            "trending": trending_result,
            "related_searches": related_result,
            "semantic_suggestions": semantic_result,
        },
    )


# ------------------------------------------------------------------ #
# Background task integration
# ------------------------------------------------------------------ #

async def record_search_analytics(
    query: str,
    user_id: int | None,
    session_id: str,
    clicked_result_id: int | None = None,
    response_time_ms: int | None = None,
    result_count: int = 0,
) -> None:
    """Record search analytics (called from search routes)."""
    from app.database.engine import connect

    db = await connect()
    try:
        service = SuggestionService(db)
        await service.record_search(
            query=query,
            user_id=user_id,
            session_id=session_id,
            clicked_result_id=clicked_result_id,
            response_time_ms=response_time_ms,
            result_count=result_count,
        )
    except Exception:
        logger.exception("Failed to record search analytics for query '%s'", query)
    finally:
        await db.close()