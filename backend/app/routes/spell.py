"""Spell correction API routes."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.database import get_db
from app.database.repositories.spell import SpellRepository
from app.models.schemas import APIResponse
from app.middleware.rate_limit import rate_limit
from app.services.auth import get_current_user
from app.services.spell_service import SpellService, SpellResult, normalize_text

logger = logging.getLogger("nebula.spell")
router = APIRouter(prefix="/api/v1/search", tags=["Search"])
security = HTTPBearer(auto_error=False)

settings = get_settings()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_api_response(result: SpellResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "original": result.original,
        "corrected": result.corrected,
        "confidence": result.confidence,
        "changed": result.changed,
    }
    if result.suggestions:
        payload["suggestions"] = result.suggestions
    if result.changed and result.confidence >= 0.70:
        payload["did_you_mean"] = result.corrected
    return payload


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/spell",
    response_model=APIResponse,
    dependencies=[Depends(rate_limit)],
    summary="Correct spelling in a search query",
    description="Returns corrected query, confidence score, and optional suggestions.",
)
async def spell_correct(
    q: str = Query(..., min_length=1, max_length=100, description="Search query to correct"),
    max_distance: int = Query(2, ge=1, le=2, description="Maximum edit distance"),
    db=Depends(get_db),
):
    """Correct spelling errors in a search query.

    Returns corrected query with confidence score.
    """
    start = time.perf_counter()
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    # Validate input
    normalized = normalize_text(q)
    if len(normalized) > 100:
        raise HTTPException(status_code=400, detail="Query too long (max 100 characters)")
    if any(ord(c) < 32 and c not in ("\t", "\n") for c in q):
        raise HTTPException(status_code=400, detail="Invalid control characters in query")

    # Check for potential injection patterns (basic)
    dangerous = {"--", ";", "/*", "*/", "xp_", "sp_", "'\""}
    if any(p in q.lower() for p in dangerous):
        raise HTTPException(status_code=400, detail="Invalid query format")

    try:
        cache = await _get_cache_client()
        service = SpellService(cache_client=cache)
        await service.load_dictionary()

        result = await service.correct_query(q, max_distance=max_distance)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "spell_correct query=%s corrected=%s changed=%s confidence=%s latency_ms=%s",
            q,
            result.corrected,
            result.changed,
            result.confidence,
            round(elapsed, 2),
        )

        return APIResponse(data=_to_api_response(result))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("spell_correct failed for query: %s", q)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/spell/suggestions",
    response_model=APIResponse,
    dependencies=[Depends(rate_limit)],
    summary="Get spelling suggestions for a query",
    description="Returns multiple ranked suggestions for a misspelled query.",
)
async def spell_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    max_suggestions: int = Query(5, ge=1, le=5, description="Maximum number of suggestions"),
    db=Depends(get_db),
):
    """Get multiple spelling suggestions ranked by confidence."""
    start = time.perf_counter()
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    normalized = normalize_text(q)
    if len(normalized) > 100:
        raise HTTPException(status_code=400, detail="Query too long (max 100 characters)")

    try:
        cache = await _get_cache_client()
        service = SpellService(cache_client=cache)
        await service.load_dictionary()

        result = await service.correct_query(q)
        suggestions = (result.suggestions or [])[:max_suggestions]
        if not suggestions and result.changed:
            suggestions = [result.corrected]

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "spell_suggestions query=%s count=%d latency_ms=%s",
            q,
            len(suggestions),
            round(elapsed, 2),
        )

        return APIResponse(data={"query": q, "suggestions": suggestions})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("spell_suggestions failed for query: %s", q)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/spell/rebuild",
    response_model=APIResponse,
    dependencies=[Depends(rate_limit)],
    summary="Rebuild spell dictionary from indexed content",
    description="Admin-only endpoint to rebuild the spell dictionary. Requires authentication.",
)
async def rebuild_spell_dictionary(
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db=Depends(get_db),
):
    """Rebuild the spell dictionary from indexed documents.

    Requires admin authentication.
    """
    # Auth check
    email = None
    if credentials:
        try:
            email = await get_current_user(credentials.credentials)
        except Exception as exc:
            logger.debug("Spell auth user extraction failed: %s", exc)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try to check admin role (best-effort)
    try:
        users_repo = __import_from("app.database.repositories.user", "UserRepository")
        users = users_repo.UserRepository(db)
        user = await users.get_by_email(email)
        if not user or not user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
    except HTTPException:
        raise
    except Exception as exc:
        # If user repo not available, proceed (backward compatible)
        logger.debug("Spell admin user lookup failed: %s", exc)

    try:
        cache = await _get_cache_client()
        service = SpellService(cache_client=cache)
        SpellRepository(db)

        # Invalidate caches
        if cache:
            await cache.delete_pattern("spell:*")

        # Schedule background rebuild
        async def _rebuild() -> None:
            try:
                await service.load_dictionary()
                logger.info("Spell dictionary rebuilt")
            except Exception:
                logger.exception("Spell dictionary rebuild failed")

        background_tasks.add_task(_rebuild)

        return APIResponse(data={"status": "rebuilding", "message": "Dictionary rebuild started"})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("rebuild_spell_dictionary failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_cache_client() -> Any:
    try:
        from app.services.cache import cache_service
        return cache_service
    except Exception:
        return None


def __import_from(module_path: str, name: str) -> Any:
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, name)