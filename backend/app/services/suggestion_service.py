"""Search suggestions service layer."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.database.engine import DatabaseConnection
from app.database.repositories.suggestion_repository import SuggestionRepository
from app.services.cache import cache_service

logger = logging.getLogger("nebula.suggestions")


class SuggestionService:
    """Service for generating and managing search suggestions."""

    def __init__(self, db: DatabaseConnection):
        self._db = db
        self._repo = SuggestionRepository(db)
        self._cache_ttl = 1800  # 30 minutes

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def get_suggestions(
        self,
        query: str,
        limit: int = 5,
        user_id: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Get suggestions for a query combining multiple sources."""
        start = time.monotonic()
        cache_key = f"suggestions:{query.lower().strip()}"

        # Try cache first
        cached = await cache_service.get(cache_key)
        if cached:
            logger.debug("Cache hit for query '%s'", query)
            cached["cache_hit"] = True
            return cached

        logger.debug("Cache miss for query '%s'", query)
        suggestions: list[dict[str, Any]] = []

        # Gather from multiple sources in parallel
        trending, semantic, related = await asyncio.gather(
            self._get_trending_suggestions(query),
            self._get_semantic_suggestions(query),
            self._get_related_suggestions(query),
        )

        suggestions.extend(trending)
        suggestions.extend(semantic)
        suggestions.extend(related)

        # Add personalized suggestions if authenticated
        if user_id:
            personalized = await self._get_personalized_suggestions(query, user_id)
            suggestions.extend(personalized)

        # Rank, deduplicate, and limit
        ranked = await self._rank_and_deduplicate(suggestions, limit)

        response = {
            "query": query,
            "suggestions": ranked,
            "cache_hit": False,
            "latency_ms": int((time.monotonic() - start) * 1000),
        }

        # Cache result
        await cache_service.set(cache_key, response, ttl=self._cache_ttl)

        # Record search for analytics
        if session_id:
            await self._repo.record_search(
                query=query,
                user_id=user_id,
                session_id=session_id,
            )

        return response

    async def get_trending_suggestions(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get trending suggestions for a query."""
        cache_key = f"trending:{query.lower().strip()}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        trending = await self._get_trending_suggestions(query)
        await cache_service.set(cache_key, trending, ttl=self._cache_ttl)
        return trending

    async def get_related_suggestions(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get related suggestions for a query."""
        cache_key = f"related:{query.lower().strip()}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        related = await self._get_related_suggestions(query)
        await cache_service.set(cache_key, related, ttl=self._cache_ttl)
        return related

    async def record_search(
        self,
        query: str,
        user_id: int | None,
        session_id: str,
        clicked_result_id: int | None = None,
        response_time_ms: int | None = None,
        result_count: int = 0,
    ) -> None:
        """Record a search for analytics and trending."""
        if not query or not query.strip():
            return

        query = query.strip()
        await self._repo.record_search(
            query=query,
            user_id=user_id,
            session_id=session_id,
            clicked_result_id=clicked_result_id,
            response_time_ms=response_time_ms,
            result_count=result_count,
        )
        await self._repo.increment_trending_query(query)

        if clicked_result_id:
            # Update related search scores
            await self._handle_click_through(query, session_id, clicked_result_id)

    async def refresh_trending(self) -> dict[str, Any]:
        """Refresh trending metrics."""
        start = time.monotonic()
        count = await self._repo.update_trending_metrics()
        duration = int((time.monotonic() - start) * 1000)
        logger.info("Refreshed trending metrics: %d rows in %dms", count, duration)
        return {"rows_updated": count, "duration_ms": duration}

    async def refresh_related_searches(self) -> dict[str, Any]:
        """Rebuild related searches from analytics."""
        start = time.monotonic()
        count = await self._repo.rebuild_related_searches()
        duration = int((time.monotonic() - start) * 1000)
        logger.info("Rebuilt related searches: %d relationships in %dms", count, duration)
        return {"relationships": count, "duration_ms": duration}

    async def refresh_semantic_suggestions(self) -> dict[str, Any]:
        """Refresh semantic suggestions from embeddings."""
        start = time.monotonic()
        # This would integrate with the vector store to find similar queries
        # For now, we'll use a placeholder implementation
        count = await self._generate_semantic_suggestions()
        duration = int((time.monotonic() - start) * 1000)
        logger.info("Refreshed semantic suggestions: %d in %dms", count, duration)
        return {"suggestions": count, "duration_ms": duration}

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    async def _get_trending_suggestions(self, query: str) -> list[dict[str, Any]]:
        """Get trending suggestions matching the query prefix."""
        rows = await self._db.fetchall(
            """
            SELECT query as suggestion, popularity_score as score, frequency, last_used
            FROM trending_queries
            WHERE LOWER(query) LIKE LOWER(? || '%')
            AND query != ?
            ORDER BY popularity_score DESC
            LIMIT 10
            """,
            (query, query),
        )
        return [
            {
                "text": row["suggestion"],
                "type": "trending",
                "score": min(row["score"] / 100.0, 1.0) if row["score"] > 100 else row["score"],
                "metadata": {"frequency": row["frequency"]},
            }
            for row in rows
        ]

    async def _get_semantic_suggestions(self, query: str) -> list[dict[str, Any]]:
        """Get semantic suggestions using embeddings."""
        # Try to use existing vector search infrastructure
        try:
            from app.hybrid.semantic import semantic_index
            if semantic_index and hasattr(semantic_index, "search"):
                results = await semantic_index.search(query, top_k=5)
                return [
                    {
                        "text": r.get("text", r.get("query", "")),
                        "type": "semantic",
                        "score": r.get("score", 0.0),
                        "metadata": {"source": "embedding"},
                    }
                    for r in results
                    if r.get("text", r.get("query", "")).lower() != query.lower()
                ]
        except Exception:
            logger.debug("Semantic index not available", exc_info=True)

        # Fallback: generate from existing suggestions
        rows = await self._db.fetchall(
            """
            SELECT suggestion, score
            FROM search_suggestions
            WHERE query = ? AND type = 'semantic'
            ORDER BY score DESC
            LIMIT 10
            """,
            (query,),
        )
        return [
            {
                "text": row["suggestion"],
                "type": "semantic",
                "score": row["score"],
                "metadata": {"source": "database"},
            }
            for row in rows
        ]

    async def _get_related_suggestions(self, query: str) -> list[dict[str, Any]]:
        """Get related searches."""
        rows = await self._repo.get_related_searches(query, limit=10)
        return [
            {
                "text": row["related_query"],
                "type": "related",
                "score": min(row["score"] / 10.0, 1.0) if row["score"] > 10 else row["score"],
                "metadata": {
                    "co_occurrence": row["co_occurrence_count"],
                    "clicks": row["click_count"],
                },
            }
            for row in rows
        ]

    async def _get_personalized_suggestions(
        self, query: str, user_id: int
    ) -> list[dict[str, Any]]:
        """Get personalized suggestions based on user history."""
        user_history = await self._repo.get_user_search_history(user_id, limit=20)
        history_queries = [h["query"] for h in user_history]

        suggestions = []
        for hist_query in history_queries:
            if hist_query.lower().startswith(query.lower()) and hist_query != query:
                suggestions.append(
                    {
                        "text": hist_query,
                        "type": "personalized",
                        "score": 0.85,
                        "metadata": {"source": "user_history"},
                    }
                )
            if len(suggestions) >= 3:
                break

        return suggestions

    async def _rank_and_deduplicate(
        self, suggestions: list[dict[str, Any]], limit: int
    ) -> list[dict[str, Any]]:
        """Rank suggestions by weighted score and remove duplicates."""
        if not suggestions:
            return []

        # Deduplicate by text (case-insensitive)
        seen = {}
        for s in suggestions:
            text_lower = s["text"].lower().strip()
            if text_lower not in seen:
                seen[text_lower] = s
            else:
                # Keep the one with higher score
                if s["score"] > seen[text_lower]["score"]:
                    seen[text_lower] = s

        unique = list(seen.values())

        # Sort by score descending
        unique.sort(key=lambda x: x["score"], reverse=True)

        # Normalize scores to [0, 1]
        if unique:
            max_score = max(s["score"] for s in unique)
            if max_score > 0:
                for s in unique:
                    s["score"] = round(s["score"] / max_score, 4)

        return unique[:limit]

    async def _handle_click_through(
        self, query: str, session_id: str, clicked_result_id: int
    ) -> None:
        """Update related search scores based on click-through."""
        # Get queries from the same session
        session_queries = await self._repo.get_session_searches(session_id)
        for other_query in session_queries:
            if other_query != query:
                await self._repo.increment_related_search_clicks(query, other_query)

    async def _generate_semantic_suggestions(self) -> int:
        """Generate semantic suggestions from embeddings. Returns count created."""
        # This is a placeholder that would integrate with the vector store
        # to generate semantic suggestions for all queries
        return 0


