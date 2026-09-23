"""Autocomplete API routes."""

import html
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.database.repositories.user import UserRepository
from app.middleware.rate_limit import rate_limit
from app.models.schemas import APIResponse
from app.services.auth import get_current_user
from app.services.autocomplete_service import AutocompleteService

logger = logging.getLogger("nebula.autocomplete")
router = APIRouter(prefix="/api/v1/search", tags=["Search"])


def _escape_output(value: str) -> str:
    """Escape HTML/JS special characters for safe output."""
    return html.escape(value, quote=True)


@router.get("/autocomplete", response_model=APIResponse, dependencies=[Depends(rate_limit)])
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=50, description="Search query prefix"),
    db=Depends(get_db),
    user_id: int | None = None,
):
    """Get autocomplete suggestions based on recent and popular searches."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    service = AutocompleteService(db)
    try:
        suggestions = await service.get_autocomplete(q, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Autocomplete failed for query: %s", q)
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    # Escape output to prevent XSS
    escaped = [_escape_output(s) for s in suggestions]
    return APIResponse(data={"suggestions": escaped})


@router.get(
    "/recent",
    response_model=APIResponse,
    dependencies=[Depends(rate_limit)],
    summary="Get user's recent searches",
)
async def get_recent_searches(
    limit: int = Query(20, ge=1, le=100),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get the authenticated user's recent searches."""
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        return APIResponse(data={"recent": []})

    service = AutocompleteService(db)
    recent = await service.get_recent(user_id, limit)
    return APIResponse(data={"recent": recent})


@router.delete(
    "/recent",
    response_model=APIResponse,
    dependencies=[Depends(rate_limit)],
    summary="Clear user's recent searches",
)
async def clear_recent_searches(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Clear the authenticated user's recent search history."""
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        return APIResponse(data={"cleared": False})

    service = AutocompleteService(db)
    await service.clear_recent(user_id)
    return APIResponse(data={"cleared": True})


@router.get(
    "/popular",
    response_model=APIResponse,
    dependencies=[Depends(rate_limit)],
    summary="Get popular queries across all users",
)
async def get_popular_queries(
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """Get the most popular search queries."""
    service = AutocompleteService(db)
    popular = await service.get_popular(limit)
    return APIResponse(data={"queries": popular})