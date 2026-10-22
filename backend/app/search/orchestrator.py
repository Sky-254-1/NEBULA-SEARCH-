"""Search orchestration pipeline."""

import asyncio
import hashlib
import logging
import time
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.database import get_db
from app.database.repositories.analytics_repository import AnalyticsRepository
from app.services.cache import cache_service
from app.services.search import ALLOWED_BACKENDS, run_web_search, sanitize_query
from app.search.query_understanding.pipeline import get_query_preprocessor

logger = logging.getLogger("nebula.search.orchestrator")
settings = get_settings()

# Initialize query preprocessor
_query_preprocessor = get_query_preprocessor()


def expand_query(query: str) -> list[str]:
    """Generate lightweight query variants for broader recall."""
    base = sanitize_query(query)
    if not base:
        return []
    variants = [base]
    words = base.split()
    if len(words) > 2:
        variants.append(" ".join(words[:3]))
    return list(dict.fromkeys(variants))


def _dedupe_results(results: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for item in results:
        url = item.get("url", "").strip().lower()
        key = url or hashlib.md5(item.get("title", "").encode(), usedforsecurity=False).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _rank_results(results: list[dict], query: str) -> list[dict]:
    # OPTIMIZATION: pre-calculating unique query terms and using a manual loop
    # instead of a generator within sum() reduces overhead for large result sets.
    query_terms = {term.lower() for term in query.split() if term}
    if not query_terms:
        return results

    scored = []
    for item in results:
        score = 0.0
        content = item.get("content", "").lower()
        title = item.get("title", "").lower()
        url = item.get("url", "").lower()

        for term in query_terms:
            if term in content:
                score += 1.0
            if term in title:
                score += 2.0
            if term in url:
                score += 1.5

        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


async def _user_id(db, email: str) -> Optional[int]:
    """Get user ID by email."""
    from app.database.repositories.user import UserRepository
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    return user["id"] if user else None


async def _track_search_analytics(
    user_id: int,
    query: str,
    search_type: str,
    result_count: int
):
    """Track search analytics asynchronously."""
    try:
        from app.database.engine import connect

        db = await connect()
        try:
            analytics_repo = AnalyticsRepository(db)
            await analytics_repo.record_search_event(
                query=query,
                user_id=user_id,
                session_id="background",
                search_backend=",".join(settings.default_backends)
                if hasattr(settings, "default_backends")
                else "web",
                search_type=search_type,
                results_count=result_count,
                response_time_ms=0.0,
                clicked_result=None,
                device=None,
            )
        finally:
            await db.close()
    except Exception as e:
        logger.debug(f"Failed to track search analytics: {e}")


async def orchestrate_search(
    query: str,
    user_email: Optional[str] = None,
    backends: List[str] = None,
    include_ai_answer: bool = True,
    include_suggestions: bool = True,
    enable_semantic: bool = True,
    enable_personalization: bool = True,
    enable_spell_check: bool = True,
    enable_diversity: bool = True,
    page: int = 1,
    page_size: int = 20,
    include_highlights: bool = True,
    facets: List[str] = None,
    filters: Dict[str, Any] = None,
    max_results: int = 100,
) -> Dict[str, Any]:
    """Orchestrate multi-backend search with deduplication and ranking."""
    _request_start = time.time()

    backends = backends or settings.default_backends
    backends = [b.strip().lower() for b in backends if b.strip().lower() in ALLOWED_BACKENDS]

    if not backends:
        backends = ["wikipedia"]

    logger.info(f"Orchestrating search: query={query}, backends={backends}")

    # Preprocess query
    query = sanitize_query(query)
    if not query:
        return {
            "query": query,
            "backends": backends,
            "results": [],
            "total": 0,
            "suggestions": [],
            "ai_answer": None,
            "facets": None,
            "response_time_ms": round((time.time() - _request_start) * 1000, 2),
        }

    # Expand query for broader recall
    query_variants = expand_query(query) if enable_personalization else [query]

    # Run searches in parallel
    tasks = []
    for variant in query_variants:
        for backend in backends:
            tasks.append(run_web_search(variant, backend))

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect and deduplicate results
    all_results = []
    for results in results_list:
        if isinstance(results, Exception):
            logger.warning(f"Backend error: {results}")
            continue
        if isinstance(results, list):
            all_results.extend(results)

    # Deduplicate
    unique_results = _dedupe_results(all_results)

    # Rank results
    ranked_results = _rank_results(unique_results, query)

    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = ranked_results[start_idx:end_idx]

    total = len(ranked_results)

    # AI answer synthesis
    ai_answer = None
    if include_ai_answer and ranked_results:
        snippets = [r.get("snippet", "") for r in ranked_results[:5] if r.get("snippet")]
        ai_answer = await generate_ai_answer(query, snippets)

    # Suggestions
    suggestions = []
    if include_suggestions:
        suggestions = await get_suggestions(query)

    # Compute facets
    facets_out = _compute_facets(paginated_results, facets) if facets and paginated_results else None

    # Track analytics (async, fire and forget)
    if user_email:
        asyncio.create_task(
            _track_search_analytics(
                user_id=0,
                query=query,
                search_type="orchestrated",
                result_count=total,
            )
        )

    return {
        "query": query,
        "mode": "orchestrated",
        "backends": backends,
        "results": paginated_results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "suggestions": suggestions,
        "ai_answer": ai_answer,
        "facets": facets_out,
        "response_time_ms": round((time.time() - _request_start) * 1000, 2),
    }


async def generate_ai_answer(query: str, snippets: List[str]) -> Optional[Dict[str, Any]]:
    """Generate AI answer from search snippets."""
    if not snippets:
        return None

    # Use OpenAI if configured, otherwise fallback to DuckDuckGo AI
    try:
        from app.services.ai import generate_answer
        answer = await generate_answer(query, snippets)
        return {
            "answer": answer,
            "provider": "openai" if settings.ai_provider == "openai" else "fallback",
            "citations": [],
        }
    except Exception as e:
        logger.warning(f"AI answer generation failed: {e}")
        return {
            "answer": f"I found some results for '{query}' but couldn't generate a summary.",
            "provider": "fallback",
            "citations": [],
        }


async def get_suggestions(query: str) -> List[str]:
    """Get search suggestions based on the query."""
    try:
        # Use query expansion engine if available
        from app.search.intelligence import query_suggestion_engine
        suggestions = await query_suggestion_engine.get_suggestions(query)
        return [s.suggestion for s in suggestions[:5]]
    except Exception as e:
        logger.warning(f"Suggestions generation failed: {e}")
        return []


def _compute_facets(results: List[Dict], facet_fields: List[str]) -> List[Dict]:
    """Compute facet counts for search results."""
    facets = {}
    for field in facet_fields:
        field_counts: Dict[str, int] = {}
        for result in results:
            value = result.get(field, "unknown")
            field_counts[value] = field_counts.get(value, 0) + 1
        facets[field] = [
            {"value": k, "count": v} for k, v in sorted(field_counts.items(), key=lambda x: -x[1])
        ]
    return [{"field": k, "values": v} for k, v in facets.items()]
