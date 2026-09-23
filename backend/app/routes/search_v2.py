"""
Enhanced Search Routes (v2)
Includes semantic search, spell correction, autocomplete, personalization,
and advanced ranking.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.database.repositories.search import SearchRepository
from app.database.repositories.user import UserRepository
from app.middleware.rate_limit import rate_limit
from app.search.intelligence import (
    autocomplete_engine,
    personalization_engine,
    query_suggestion_engine,
    search_analytics,
    spell_corrector,
)
from app.search.orchestrator import orchestrate_search
from app.search.query_understanding.intent_classifier import intent_classifier
from app.search.ranking import hybrid_ranker
from app.search.semantic.engine import semantic_engine
from app.services.auth import get_current_user

logger = logging.getLogger("nebula.search.v2")

router = APIRouter(prefix="/api/v2/search", tags=["Search v2"])


async def _inject_db(db):
    """Inject database connection into intelligence singletons for DB-backed operations."""
    search_analytics._set_db(db)
    query_suggestion_engine.analytics._set_db(db)


@router.get("/suggest", dependencies=[Depends(rate_limit)])
async def get_suggestions(
    q: str = Query(..., min_length=2, max_length=100, description="Partial query"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions"),
    email: Optional[str] = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get intelligent query suggestions including:
    - Autocomplete
    - Spell corrections
    - User history
    - Trending queries
    """
    await _inject_db(db)

    user_id = None
    if email:
        users = UserRepository(db)
        user_id = await users.get_id_by_email(email)

    suggestions = await query_suggestion_engine.get_suggestions(q, user_id, limit, db=db)

    return {
        "query": q,
        "suggestions": [
            {
                "text": s.suggestion,
                "score": s.score,
                "source": s.source,
                "metadata": s.metadata or {},
            }
            for s in suggestions
        ],
    }


@router.get("/autocomplete", dependencies=[Depends(rate_limit)])
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=20),
    db=Depends(get_db),
):
    """Fast autocomplete suggestions"""
    await _inject_db(db)
    suggestions = await autocomplete_engine.suggest(q, limit)

    return {
        "query": q,
        "completions": [s.suggestion for s in suggestions],
    }


@router.get("/spell-check", dependencies=[Depends(rate_limit)])
async def spell_check(
    q: str = Query(..., min_length=1, max_length=500),
):
    """Check spelling and suggest corrections"""
    corrected, was_corrected = await spell_corrector.correct_query(q)

    return {
        "original": q,
        "corrected": corrected,
        "was_corrected": was_corrected,
    }


@router.get("/", response_model=dict, dependencies=[Depends(rate_limit)])
async def intelligent_search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    backends: str = Query("wikipedia", description="Comma-separated backends"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Results per page"),
    enable_semantic: bool = Query(True, description="Enable semantic reranking"),
    enable_personalization: bool = Query(True, description="Enable personalization"),
    enable_spell_check: bool = Query(True, description="Auto spell correction"),
    enable_diversity: bool = Query(True, description="Promote diverse results"),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Intelligent search with all enhancements:
    - Spell correction
    - Semantic search
    - Advanced ranking (BM25, TF-IDF, ML)
    - Personalization
    - Diversity promotion
    - Intent classification
    """
    await _inject_db(db)

    # Get user
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)

    original_query = q

    # 1. Spell correction
    if enable_spell_check:
        corrected_query, was_corrected = await spell_corrector.correct_query(q)
        if was_corrected:
            logger.info(f"Query corrected: '{q}' -> '{corrected_query}'")
            q = corrected_query

    # 2. Get initial results from orchestrator
    backend_list = [b.strip() for b in backends.split(",") if b.strip()]
    search_response = await orchestrate_search(q, backend_list, 1, page_size * 2)

    results = search_response.get("results", [])

    if not results:
        # Log and return empty
        search_repo = SearchRepository(db)
        await search_repo.log_search(user_id, q, backends, 0)

        return {
            "query": q,
            "original_query": original_query,
            "results": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "spell_corrected": original_query != q,
            "intent": intent_classifier.classify(q),
        }

    # 3. Classify query intent
    intent = intent_classifier.classify(q)
    logger.info(f"Query intent: {intent}")

    # 4. Apply advanced ranking
    user_profile = None
    if enable_personalization and user_id:
        user_profile = await personalization_engine.get_user_profile(user_id)

    ranked_results = await hybrid_ranker.rank(
        query=q,
        results=results,
        user_profile=user_profile,
        enable_diversity=enable_diversity,
    )

    # 5. Semantic reranking
    if enable_semantic:
        try:
            ranked_results = await semantic_engine.rerank(
                query=q,
                documents=ranked_results,
                alpha=0.3,  # 30% semantic, 70% keyword
            )
        except Exception as e:
            logger.warning(f"Semantic reranking failed: {e}")

    # 6. Apply intent-based boosts
    for result in ranked_results:
        intent_boost = intent_classifier.get_intent_boost(q, result)
        if 'combined_score' in result:
            result['combined_score'] *= intent_boost

    # Re-sort after intent boost
    ranked_results.sort(
        key=lambda x: x.get('combined_score', x.get('semantic_score', 0)),
        reverse=True
    )

    # 7. Personalization
    if enable_personalization and user_profile:
        ranked_results = await personalization_engine.personalize_results(
            user_id, q, ranked_results
        )

    # 8. Pagination
    start = (page - 1) * page_size
    page_results = ranked_results[start : start + page_size]

    # 9. Log search
    search_repo = SearchRepository(db)
    await search_repo.log_search(user_id, q, backends, len(page_results))

    # 10. Log analytics
    await search_analytics.log_search_event(
        user_id=user_id,
        query=q,
        results_count=len(page_results),
    )

    return {
        "query": q,
        "original_query": original_query,
        "results": page_results,
        "total": len(ranked_results),
        "page": page,
        "page_size": page_size,
        "spell_corrected": original_query != q,
        "intent": intent,
        "backends": backend_list,
        "features": {
            "semantic_enabled": enable_semantic,
            "personalization_enabled": enable_personalization and user_profile is not None,
            "diversity_enabled": enable_diversity,
        },
    }


@router.get("/semantic", dependencies=[Depends(rate_limit)])
async def semantic_search(
    q: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Min similarity"),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Pure semantic search using embeddings.
    Returns results based on semantic similarity only.
    """
    # Get base results first
    search_response = await orchestrate_search(q, ["wikipedia"], 1, top_k * 2)
    results = search_response.get("results", [])

    if not results:
        return {
            "query": q,
            "results": [],
            "total": 0,
        }

    # Index and search semantically
    await semantic_engine.index_documents(results)
    semantic_results = await semantic_engine.search(q, top_k, threshold)

    return {
        "query": q,
        "results": semantic_results,
        "total": len(semantic_results),
        "mode": "semantic",
    }


@router.get("/trending", dependencies=[Depends(rate_limit)])
async def get_trending(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    db=Depends(get_db),
):
    """Get trending search queries"""
    await _inject_db(db)
    trending = await search_analytics.get_trending_queries(limit, hours)

    return {
        "trending": trending,
        "period_hours": hours,
    }


@router.get("/popular", dependencies=[Depends(rate_limit)])
async def get_popular(
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
):
    """Get most popular search queries"""
    await _inject_db(db)
    popular = await search_analytics.get_popular_queries(limit)

    return {
        "popular": popular,
    }


@router.post("/click", dependencies=[Depends(rate_limit)])
async def log_click(
    query: str = Query(...),
    position: int = Query(..., ge=0),
    url: str = Query(...),
    session_id: Optional[str] = Query(None),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Log click event for analytics and personalization.
    Call this when user clicks on a search result.
    """
    await _inject_db(db)

    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)

    # Log for analytics
    await search_analytics.log_search_event(
        user_id=user_id,
        query=query,
        results_count=0,  # Not relevant for click
        clicked_position=position,
        clicked_url=url,
        session_id=session_id,
    )

    # Update personalization profile
    await personalization_engine.update_profile_from_click(
        user_id=user_id,
        query=query,
        clicked_position=position,
        clicked_url=url,
    )

    return {
        "message": "Click logged",
        "query": query,
        "position": position,
    }


@router.get("/profile", dependencies=[Depends(rate_limit)])
async def get_search_profile(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get user's search profile and preferences"""
    await _inject_db(db)

    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)

    profile = await personalization_engine.get_user_profile(user_id)
    history = await search_analytics.get_user_search_history(user_id, limit=20)

    return {
        "profile": profile,
        "recent_searches": history,
    }


@router.get("/analytics", dependencies=[Depends(rate_limit)])
async def get_analytics(
    query: Optional[str] = Query(None),
    db=Depends(get_db),
):
    """Get analytics for a query or overall stats"""
    await _inject_db(db)

    if query:
        ctr = await search_analytics.calculate_ctr(query)
        return {
            "query": query,
            "ctr": ctr,
        }

    # Overall stats
    trending = await search_analytics.get_trending_queries(10, 24)
    popular = await search_analytics.get_popular_queries(10)

    return {
        "trending_24h": trending,
        "popular_overall": popular,
    }
