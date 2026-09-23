"""Autocomplete service with caching and ranking."""

import logging
import re
import time

from app.config import get_settings
from app.database.engine import DatabaseConnection
from app.database.repositories.autocomplete import AutocompleteRepository
from app.services.cache import cache_service

logger = logging.getLogger("nebula.autocomplete")
settings = get_settings()

# Constants
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 50
MAX_SUGGESTIONS = 10
AUTOCOMPLETE_CACHE_TTL = 600  # 10 minutes
RECENT_CACHE_TTL = 1800  # 30 minutes
POPULAR_CACHE_TTL = 3600  # 1 hour


class AutocompleteService:
    """Service for autocomplete operations."""

    def __init__(self, db: DatabaseConnection):
        self._db = db
        self._repo = AutocompleteRepository(db)

    @staticmethod
    def _normalize_query(query: str) -> str:
        """Normalize query: lowercase, strip punctuation, collapse whitespace."""
        # Remove control characters
        query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)
        # Remove punctuation except spaces
        query = re.sub(r'[^\w\s]', '', query)
        # Collapse whitespace
        query = re.sub(r'\s+', ' ', query).strip().lower()
        return query

    @staticmethod
    def _validate_query(query: str) -> str:
        """Validate and sanitize query input."""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        query = query.strip()
        if len(query) < MIN_QUERY_LENGTH:
            raise ValueError(f"Query must be at least {MIN_QUERY_LENGTH} characters")
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"Query must be at most {MAX_QUERY_LENGTH} characters")
        normalized = AutocompleteService._normalize_query(query)
        if not normalized:
            raise ValueError("Query contains no valid characters")
        return normalized

    def _calculate_prefix_score(self, query: str, suggestion: str) -> float:
        """Calculate prefix match score (0.0 to 1.0)."""
        suggestion_lower = suggestion.lower()
        query_lower = query.lower()
        if suggestion_lower.startswith(query_lower):
            return 1.0
        if query_lower in suggestion_lower:
            return 0.5
        return 0.0

    def _rank_results(self, query: str, candidates: list[str], popular_data: list[dict]) -> list[str]:
        """Rank suggestions by combined score."""
        # Build popularity lookup
        popular_map = {item["query"]: item for item in popular_data}
        now = time.time()

        scored = []
        for suggestion in candidates:
            prefix_score = self._calculate_prefix_score(query, suggestion)
            pop = popular_map.get(suggestion)
            popularity_score = min(pop["count"] / 100.0, 1.0) if pop else 0.0
            recency_score = 0.0
            if pop and pop.get("last_used"):
                try:
                    from datetime import datetime
                    last_used = datetime.fromisoformat(pop["last_used"]).timestamp()
                    hours_ago = (now - last_used) / 3600
                    recency_score = max(0.0, 1.0 - (hours_ago / (24 * 7)))  # Decay over a week
                except Exception as exc:
                    logger.debug("Autocomplete recency score calculation failed: %s", exc)
            score = (0.60 * prefix_score) + (0.25 * popularity_score) + (0.15 * recency_score)
            scored.append((suggestion, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [suggestion for suggestion, _ in scored[:MAX_SUGGESTIONS]]

    async def get_autocomplete(self, query: str, user_id: int | None = None) -> list[str]:
        """Get autocomplete suggestions for a query."""
        normalized = self._validate_query(query)
        cache_key = f"autocomplete:{normalized}"

        # Try cache first
        cached = await cache_service.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for autocomplete query: %s", normalized)
            return cached

        logger.debug("Cache miss for autocomplete query: %s", normalized)

        # Get candidates from repository
        candidates = await self._repo.search_similar_queries(normalized, MAX_SUGGESTIONS * 2)
        popular_data = await self._repo.get_popular_queries(50)

        # Rank results
        results = self._rank_results(normalized, candidates, popular_data)

        # Cache results
        await cache_service.set(cache_key, results, AUTOCOMPLETE_CACHE_TTL)

        return results

    async def save_recent(self, user_id: int, query: str) -> None:
        """Save a recent search for a user."""
        normalized = self._normalize_query(query)
        if not normalized:
            return
        await self._repo.save_recent_search(user_id, normalized)
        # Invalidate recent cache
        cache_key = f"recent:{user_id}"
        await cache_service.delete(cache_key)
        logger.info("Saved recent search for user %s: %s", user_id, normalized)

    async def get_recent(self, user_id: int, limit: int = 20) -> list[str]:
        """Get recent searches for a user."""
        cache_key = f"recent:{user_id}"
        cached = await cache_service.get(cache_key)
        if cached is not None:
            return cached
        results = await self._repo.get_recent_searches(user_id, limit)
        await cache_service.set(cache_key, results, RECENT_CACHE_TTL)
        return results

    async def clear_recent(self, user_id: int) -> None:
        """Clear recent searches for a user."""
        await self._repo.clear_recent_searches(user_id)
        cache_key = f"recent:{user_id}"
        await cache_service.delete(cache_key)
        logger.info("Cleared recent searches for user %s", user_id)

    async def update_popularity(self, query: str) -> None:
        """Update popularity count for a query."""
        normalized = self._normalize_query(query)
        if not normalized:
            return
        await self._repo.increment_popular_query(normalized)
        # Invalidate popular cache
        await cache_service.delete("popular_queries")
        logger.info("Updated popularity for query: %s", normalized)

    async def get_popular(self, limit: int = 20) -> list[str]:
        """Get popular queries."""
        cache_key = "popular_queries"
        cached = await cache_service.get(cache_key)
        if cached is not None:
            return cached
        data = await self._repo.get_popular_queries(limit)
        results = [item["query"] for item in data]
        await cache_service.set(cache_key, results, POPULAR_CACHE_TTL)
        return results