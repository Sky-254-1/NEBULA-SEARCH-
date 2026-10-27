"""Search intelligence services.

Long-lived service singletons used by the search and analytics routes:

- ``search_analytics``       DB-backed search analytics (events, trending,
                             popular queries, history, CTR)
- ``query_suggestion_engine`` query suggestions combining stored
                             suggestions, the user's history and trending
                             queries
- ``autocomplete_engine``    fast prefix autocomplete
- ``spell_corrector``        async spelling correction
- ``personalization_engine`` user profiles and result personalisation

The implementation intentionally degrades gracefully: analytics endpoints
must keep returning valid (possibly empty) payloads on a fresh installation
where the analytics tables have not been created yet, rather than failing
the whole request.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.search.personalization import (
    PersonalizationEngine as _PersonalizationEngineBase,
    UserProfile,
)

logger = logging.getLogger("nebula.search.intelligence")


@dataclass
class Suggestion:
    """A single query suggestion."""

    suggestion: str
    score: float = 0.0
    source: str = "trending"
    metadata: dict[str, Any] = field(default_factory=dict)


def _dedupe_limit(items: Iterable[Suggestion], limit: int) -> list[Suggestion]:
    """De-duplicate suggestions case-insensitively and keep the best ``limit``."""
    seen: set[str] = set()
    unique: list[Suggestion] = []
    for item in items:
        key = (item.suggestion or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    unique.sort(key=lambda item: item.score, reverse=True)
    return unique[: max(limit, 0)]


class _DBSingleton:
    """Mixin for singletons that lazily receive a database connection."""

    _db: Any = None

    def _set_db(self, db: Any) -> None:
        self._db = db


class SearchAnalyticsService(_DBSingleton):
    """DB-backed search analytics facade used by the API layer."""

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _suggestion_repository(self):
        if self._db is None:
            return None
        from app.database.repositories.suggestion_repository import (
            SuggestionRepository,
        )

        return SuggestionRepository(self._db)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    async def log_search_event(
        self,
        user_id: int | None = None,
        query: str = "",
        results_count: int = 0,
        clicked_position: int | None = None,
        clicked_url: str | None = None,
        session_id: str | None = None,
        **_: Any,
    ) -> None:
        """Persist a search event and bump the query's trending counters."""
        if not query:
            return
        repo = self._suggestion_repository()
        if repo is None:
            return
        try:
            await repo.record_search(
                query=query,
                user_id=user_id,
                session_id=session_id or "api",
                clicked_result_id=clicked_position,
                result_count=results_count,
            )
            await repo.increment_trending_query(query)
        except Exception:  # pragma: no cover - analytics must never fail requests
            logger.debug("Failed to record search event for %r", query, exc_info=True)

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #

    async def get_trending_queries(
        self, limit: int = 10, hours: int = 24
    ) -> list[dict[str, Any]]:
        """Return trending queries ordered by popularity."""
        repo = self._suggestion_repository()
        if repo is None:
            return []
        try:
            rows = await repo.get_trending_queries(limit)
        except Exception:  # pragma: no cover - table may not exist yet
            logger.debug("Trending queries unavailable", exc_info=True)
            return []

        trending: list[dict[str, Any]] = []
        for row in rows:
            query = str(row.get("query") or "")
            if not query:
                continue
            frequency = int(row.get("frequency") or 0)
            trending.append(
                {
                    "query": query,
                    "count": frequency,
                    "frequency": frequency,
                    "score": float(row.get("popularity_score") or 0.0),
                    "last_used": row.get("last_used"),
                }
            )
        return trending

    async def get_popular_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the most popular queries of all time."""
        repo = self._suggestion_repository()
        if repo is None:
            return []
        try:
            rows = await repo.get_top_queries(limit)
        except Exception:  # pragma: no cover - table may not exist yet
            logger.debug("Popular queries unavailable", exc_info=True)
            return []

        popular: list[dict[str, Any]] = []
        for row in rows:
            query = str(row.get("query") or "")
            if not query:
                continue
            popular.append(
                {
                    "query": query,
                    "count": int(row.get("frequency") or 0),
                    "frequency": int(row.get("frequency") or 0),
                    "last_used": row.get("last_used"),
                }
            )
        return popular

    async def get_user_search_history(
        self, user_id: int | None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Return the query history for a user."""
        repo = self._suggestion_repository()
        if repo is None or not user_id:
            return []
        try:
            return await repo.get_user_search_history(user_id, limit=limit)
        except Exception:  # pragma: no cover - table may not exist yet
            logger.debug("Search history unavailable", exc_info=True)
            return []

    async def calculate_ctr(self, query: str) -> float:
        """Return the click-through rate for ``query`` (0.0 when unknown)."""
        if self._db is None or not query:
            return 0.0
        try:
            row = await self._db.fetchone(
                """
                SELECT COUNT(*) AS impressions,
                       SUM(CASE WHEN clicked_result_id IS NOT NULL THEN 1 ELSE 0 END) AS clicks
                FROM search_analytics
                WHERE query = ?
                """,
                (query,),
            )
        except Exception:  # pragma: no cover - table may not exist yet
            logger.debug("CTR unavailable for %r", query, exc_info=True)
            return 0.0

        if not row:
            return 0.0
        impressions = int(row["impressions"] or 0) if row["impressions"] is not None else 0
        clicks = int(row["clicks"] or 0) if row["clicks"] is not None else 0
        if impressions <= 0:
            return 0.0
        return round(clicks / impressions, 4)


class QuerySuggestionEngine(_DBSingleton):
    """Generate query suggestions from stored, historical and trending data."""

    @property
    def analytics(self) -> SearchAnalyticsService:
        return search_analytics

    async def get_suggestions(
        self,
        query: str,
        user_id: int | None = None,
        limit: int = 5,
        db: Any = None,
    ) -> list[Suggestion]:
        """Return ranked suggestions for ``query`` (may be empty)."""
        if db is not None:
            self._set_db(db)
        if self._db is None or not query or not query.strip():
            return []

        from app.database.repositories.suggestion_repository import (
            SuggestionRepository,
        )

        repo = SuggestionRepository(self._db)
        prefix = query.strip().lower()
        suggestions: list[Suggestion] = []

        # 1. Suggestions explicitly stored for this query.
        try:
            rows = await repo.get_suggestions(query.strip(), limit)
        except Exception:  # pragma: no cover - table may not exist yet
            rows = []
        for row in rows:
            text = str(row.get("suggestion") or "")
            if text:
                suggestions.append(
                    Suggestion(
                        suggestion=text,
                        score=float(row.get("score") or 0.0),
                        source=str(row.get("type") or "suggestion"),
                    )
                )

        # 2. The user's own recent searches.
        if user_id:
            try:
                history = await repo.get_user_search_history(user_id, limit=limit * 2)
            except Exception:  # pragma: no cover
                history = []
            for entry in history:
                text = str(entry.get("query") or "")
                if text and text.lower().startswith(prefix) and text.lower() != prefix:
                    suggestions.append(
                        Suggestion(suggestion=text, score=0.9, source="history")
                    )

        # 3. Trending queries with the same prefix.
        try:
            trending = await repo.get_trending_queries(limit * 2)
        except Exception:  # pragma: no cover
            trending = []
        for index, row in enumerate(trending):
            text = str(row.get("query") or "")
            if text and text.lower().startswith(prefix) and text.lower() != prefix:
                score = max(0.5, 0.8 - index * 0.01)
                suggestions.append(
                    Suggestion(suggestion=text, score=score, source="trending")
                )

        return _dedupe_limit(suggestions, limit)


class AutocompleteEngine(_DBSingleton):
    """Fast prefix autocomplete backed by recent and popular queries."""

    async def suggest(self, prefix: str, limit: int = 10) -> list[Suggestion]:
        """Return autocomplete completions for ``prefix``."""
        if self._db is None or not prefix or not prefix.strip():
            return []

        from app.database.repositories.autocomplete import AutocompleteRepository

        try:
            queries = await AutocompleteRepository(self._db).search_similar_queries(
                prefix.strip(), limit
            )
        except Exception:  # pragma: no cover - tables may not exist yet
            logger.debug("Autocomplete lookup failed", exc_info=True)
            queries = []

        suggestions = [
            Suggestion(
                suggestion=text,
                score=max(0.0, 1.0 - index * 0.02),
                source="autocomplete",
            )
            for index, text in enumerate(queries)
            if text
        ]
        return _dedupe_limit(suggestions, limit)


class SpellCorrector:
    """Async spell-correction facade around :class:`SpellService`."""

    def __init__(self) -> None:
        self._service = None
        self._loaded = False

    def _get_service(self):
        if self._service is None:
            from app.services.cache import cache_service
            from app.services.spell_service import SpellService

            self._service = SpellService(cache_client=cache_service)
        return self._service

    async def correct_query(self, query: str) -> tuple[str, bool]:
        """Return ``(corrected_query, was_corrected)``."""
        if not query or not query.strip():
            return query, False

        service = self._get_service()
        if not self._loaded:
            self._loaded = True
            try:
                await service.load_dictionary()
            except Exception:  # pragma: no cover - dictionary is optional
                logger.debug("Spell dictionary unavailable", exc_info=True)

        try:
            result = await service.correct_query(query)
        except Exception:  # pragma: no cover - never block a search on spell check
            logger.debug("Spell correction failed for %r", query, exc_info=True)
            return query, False

        corrected = result.corrected or query
        return corrected, bool(result.changed) and corrected != query


class PersonalizationEngine(_PersonalizationEngineBase):
    """Personalisation engine with route-friendly helpers."""

    def _set_db(self, db: Any) -> None:
        from app.database.repositories.suggestion_repository import (
            SuggestionRepository,
        )

        self._db = db
        self._repo = SuggestionRepository(db)
        self._profile_cache.clear()

    async def personalize_results(
        self, user_id: int | None, query: str, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Apply the user's profile to result scores (best effort)."""
        if not results or not user_id:
            return results

        try:
            profile = await self.get_user_profile(user_id)
        except Exception:  # pragma: no cover - personalisation is optional
            logger.debug("Personalisation profile unavailable", exc_info=True)
            return results

        for result in results:
            try:
                boost = self.calculate_result_score_adjustment(profile, result)
            except Exception:  # pragma: no cover
                boost = 0.0
            if not boost:
                continue
            base = result.get("combined_score", result.get("final_score", 0.0)) or 0.0
            result["personalization_boost"] = round(boost, 4)
            result["combined_score"] = round(base * (1.0 + boost), 4)

        results.sort(
            key=lambda item: item.get("combined_score", item.get("final_score", 0.0)),
            reverse=True,
        )
        return results

    async def update_profile_from_click(
        self,
        user_id: int | None,
        query: str,
        clicked_position: int | None = None,
        clicked_url: str | None = None,
        **_: Any,
    ) -> None:
        """Learn from a click on a search result (best effort)."""
        if not user_id:
            return
        try:
            await self.learn_from_search(user_id, query)
        except Exception:  # pragma: no cover - learning is optional
            logger.debug("Personalisation update failed", exc_info=True)


# --------------------------------------------------------------------------- #
# Module-level singletons (imported by the search routes)
# --------------------------------------------------------------------------- #

search_analytics = SearchAnalyticsService()
query_suggestion_engine = QuerySuggestionEngine()
autocomplete_engine = AutocompleteEngine()
spell_corrector = SpellCorrector()
personalization_engine = PersonalizationEngine()


__all__ = [
    "AutocompleteEngine",
    "PersonalizationEngine",
    "QuerySuggestionEngine",
    "SearchAnalyticsService",
    "SpellCorrector",
    "Suggestion",
    "UserProfile",
    "autocomplete_engine",
    "personalization_engine",
    "query_suggestion_engine",
    "search_analytics",
    "spell_corrector",
]
