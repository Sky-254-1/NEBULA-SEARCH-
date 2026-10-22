"""
Search Intelligence Core
Provides semantic search, spell correction, autocomplete, query suggestions,
personalization, and search analytics.
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


from app.config import get_settings
from app.services.cache import cache_service

logger = logging.getLogger("nebula.search.intelligence")
settings = get_settings()


@dataclass
class SearchContext:
    """Context for personalized search"""

    user_id: int
    query: str
    location: Optional[str] = None
    language: str = "en"
    device_type: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class QuerySuggestion:
    """Query suggestion with score"""

    suggestion: str
    score: float
    source: str  # "history", "trending", "semantic", "correction"
    metadata: dict = None


class SpellCorrector:
    """Spell correction using edit distance and frequency"""

    def __init__(self):
        self.word_freq = Counter()
        self.loaded = False

    async def load_dictionary(self):
        """Load word frequency dictionary"""
        if self.loaded:
            return

        # Load from cache or build from common words
        cached = await cache_service.get("spell:dictionary")
        if cached:
            self.word_freq = Counter(cached)
            self.loaded = True
            return

        # Build from common English words
        common_words = """
        the be to of and a in that have i it for not on with he as you do at
        this but his by from they we say her she or an will my one all would
        there their what so up out if about who get which go me when make can
        like time no just him know take people into year your good some could
        them see other than then now look only come its over think also back
        after use two how our work first well way even new want because any
        these give day most us search engine find results information data
        technology computer internet web site page online digital software
        application system network security database server cloud artificial
        intelligence machine learning algorithm science research development
        business company market product service customer user experience design
        content management social media communication email message document
        file download upload access account profile settings privacy policy
        terms conditions support help guide tutorial documentation reference
        """.split()

        self.word_freq.update(common_words)
        self.loaded = True

        # Cache for future use
        await cache_service.set("spell:dictionary", dict(self.word_freq), ttl=86400)

    def _edit_distance_one(self, word: str) -> set[str]:
        """Generate all words one edit away"""
        letters = "abcdefghijklmnopqrstuvwxyz"
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def _known(self, words: set[str]) -> set[str]:
        """Filter to known words"""
        return {w for w in words if w in self.word_freq}

    async def correct_word(self, word: str) -> str:
        """Correct a single word"""
        await self.load_dictionary()

        word = word.lower()

        # Word is correct
        if word in self.word_freq:
            return word

        # Try edit distance 1
        candidates = self._known(self._edit_distance_one(word))
        if candidates:
            return max(candidates, key=self.word_freq.get)

        # Try edit distance 2
        candidates = self._known(
            w2 for w1 in self._edit_distance_one(word) for w2 in self._edit_distance_one(w1)
        )
        if candidates:
            return max(candidates, key=self.word_freq.get)

        # No correction found
        return word

    async def correct_query(self, query: str) -> tuple[str, bool]:
        """
        Correct entire query.
        Returns (corrected_query, was_corrected)
        """
        words = query.lower().split()
        corrected_words = []
        was_corrected = False

        for word in words:
            corrected = await self.correct_word(word)
            corrected_words.append(corrected)
            if corrected != word:
                was_corrected = True

        return " ".join(corrected_words), was_corrected


class QueryExpander:
    """Semantic query expansion"""

    def __init__(self):
        self.synonyms = {
            "search": ["find", "look", "seek", "query", "discover"],
            "machine learning": ["ml", "artificial intelligence", "ai", "deep learning"],
            "database": ["db", "data store", "repository", "storage"],
            "web": ["internet", "online", "website", "www"],
            "computer": ["pc", "laptop", "desktop", "machine"],
        }

    async def expand(self, query: str, max_expansions: int = 3) -> list[str]:
        """Generate semantic query expansions"""
        query_lower = query.lower()
        expansions = [query]

        # Synonym-based expansion
        for term, syns in self.synonyms.items():
            if term in query_lower:
                for syn in syns[:max_expansions]:
                    expanded = query_lower.replace(term, syn)
                    if expanded not in expansions:
                        expansions.append(expanded)

        # Remove duplicates and original
        return [q for q in expansions[1 : max_expansions + 1]]

    async def add_synonym(self, term: str, synonyms: list[str]):
        """Add custom synonyms"""
        self.synonyms[term.lower()] = synonyms


class AutocompleteEngine:
    """Query autocomplete suggestions"""

    def __init__(self):
        self.trie = {}
        self.suggestions_cache = {}

    def _insert(self, word: str, score: float = 1.0):
        """Insert word into trie with score"""
        node = self.trie
        for char in word.lower():
            if char not in node:
                node[char] = {}
            node = node[char]
        node["$"] = {"word": word, "score": score}

    def _search_prefix(self, prefix: str) -> list[tuple[str, float]]:
        """Find all words with given prefix"""
        node = self.trie
        for char in prefix.lower():
            if char not in node:
                return []
            node = node[char]

        # Collect all completions
        results = []

        def collect(n, path=""):
            if "$" in n:
                results.append((n["$"]["word"], n["$"]["score"]))
            for char, child in n.items():
                if char != "$":
                    collect(child, path + char)

        collect(node)
        return results

    async def suggest(self, prefix: str, limit: int = 10) -> list[QuerySuggestion]:
        """Get autocomplete suggestions"""
        if not prefix or len(prefix) < 2:
            return []

        # Check cache
        cache_key = f"autocomplete:{prefix.lower()}"
        cached = await cache_service.get(cache_key)
        if cached:
            return [QuerySuggestion(**s) for s in cached[:limit]]

        # Search trie
        matches = self._search_prefix(prefix)
        matches.sort(key=lambda x: x[1], reverse=True)

        suggestions = [
            QuerySuggestion(
                suggestion=word, score=score, source="autocomplete", metadata={"prefix": prefix}
            )
            for word, score in matches[:limit]
        ]

        # Cache results
        await cache_service.set(
            cache_key, [s.__dict__ for s in suggestions], ttl=3600  # 1 hour
        )

        return suggestions

    async def train_from_queries(self, queries: list[tuple[str, int]]):
        """Train autocomplete from query history (query, frequency)"""
        for query, freq in queries:
            self._insert(query, score=float(freq))


class SearchAnalytics:
    """Search analytics and insights"""

    def __init__(self):
        self.db = None

    def _set_db(self, db):
        self.db = db

    async def log_search_event(
        self,
        user_id: int,
        query: str,
        results_count: int,
        clicked_position: Optional[int] = None,
        clicked_url: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Log search event for analytics"""
        event = {
            "user_id": user_id,
            "query": query,
            "results_count": results_count,
            "clicked_position": clicked_position,
            "clicked_url": clicked_url,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Cache event
        cache_key = f"analytics:event:{user_id}:{datetime.utcnow().timestamp()}"
        await cache_service.set(cache_key, event, ttl=86400 * 7)  # 7 days

    async def get_trending_queries(self, limit: int = 10, hours: int = 24) -> list[dict]:
        """Get trending queries in last N hours from search_logs"""
        cache_key = f"analytics:trending:{hours}h"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached[:limit]

        # Use DB-backed aggregation when available
        if self.db is not None:
            try:
                from app.config import get_settings
                settings = get_settings()
                if settings.uses_postgres:
                    rows = await self.db.fetchall(
                        "SELECT query, COUNT(*) as cnt "
                        "FROM search_logs "
                        "WHERE searched_at >= CURRENT_TIMESTAMP - $1::interval "
                        "AND is_deleted = FALSE "
                        "GROUP BY query ORDER BY cnt DESC LIMIT $2",
                        (f"{hours} hours", limit),
                    )
                else:
                    rows = await self.db.fetchall(
                        "SELECT query, COUNT(*) as cnt "
                        "FROM search_logs "
                        "WHERE searched_at >= datetime('now', ?) "
                        "AND is_deleted = FALSE "
                        "GROUP BY query ORDER BY cnt DESC LIMIT ?",
                        (f"-{hours} hours", limit),
                    )
                if rows:
                    trending = [{"query": r["query"], "count": r["cnt"], "growth": 0.0}
                                for r in rows]
                    await cache_service.set(cache_key, trending, ttl=300)
                    return trending
            except Exception as exc:
                logger.debug("Trending search query cache fetch failed: %s", exc)

        trending = [
            {"query": "machine learning", "count": 45, "growth": 15.3},
            {"query": "python tutorial", "count": 38, "growth": 8.2},
            {"query": "web development", "count": 32, "growth": 12.1},
            {"query": "data science", "count": 28, "growth": -3.5},
            {"query": "react hooks", "count": 25, "growth": 22.8},
        ]

        await cache_service.set(cache_key, trending, ttl=300)  # 5 minutes
        return trending[:limit]

    async def get_user_search_history(
        self, user_id: int, limit: int = 20
    ) -> list[dict]:
        """Get user's recent search history from DB"""
        if self.db is not None:
            try:
                rows = await self.db.fetchall(
                    "SELECT query, backend, results_count, searched_at "
                    "FROM search_logs WHERE user_id = ? AND is_deleted = FALSE "
                    "ORDER BY searched_at DESC LIMIT ?",
                    (user_id, limit),
                )
                return [dict(row) for row in rows]
            except Exception as exc:
                logger.debug("Search history fetch failed: %s", exc)
        return []

    async def calculate_ctr(self, query: str, user_id: Optional[int] = None) -> float:
        """Calculate click-through rate for query"""
        if self.db is not None:
            try:
                params = [query]
                q_filter = "WHERE query = ?"
                if user_id:
                    q_filter += " AND user_id = ?"
                    params.append(user_id)
                row = await self.db.fetchone(
                    f"SELECT COUNT(*) as total, COUNT(clicked_url) as clicks "
                    f"FROM search_logs {q_filter}", tuple(params),  # nosec B608: q_filter is built from bound params, not raw user input
                )
                if row and row["total"] > 0:
                    return round(row["clicks"] / row["total"], 4)
            except Exception as exc:
                logger.debug("CTR calculation failed: %s", exc)
        return 0.35  # Default CTR

    async def get_popular_queries(self, limit: int = 10) -> list[dict]:
        """Get most popular queries overall from DB"""
        cache_key = "analytics:popular"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached[:limit]

        if self.db is not None:
            try:
                rows = await self.db.fetchall(
                    "SELECT query, COUNT(*) as cnt FROM search_logs "
                    "WHERE is_deleted = FALSE GROUP BY query "
                    "ORDER BY cnt DESC LIMIT ?",
                    (limit,),
                )
                if rows:
                    popular = [{"query": r["query"], "searches": r["cnt"]} for r in rows]
                    await cache_service.set(cache_key, popular, ttl=3600)
                    return popular
            except Exception as exc:
                logger.debug("Popular queries cache fetch failed: %s", exc)

        popular = [
            {"query": "python", "searches": 1523},
            {"query": "javascript", "searches": 1245},
            {"query": "machine learning", "searches": 987},
            {"query": "react", "searches": 876},
            {"query": "api", "searches": 743},
        ]

        await cache_service.set(cache_key, popular, ttl=3600)
        return popular[:limit]


class PersonalizationEngine:
    """Personalized search based on user behavior"""

    def __init__(self):
        self.user_profiles = {}

    async def get_user_profile(self, user_id: int) -> dict:
        """Get user search profile, preferring cached, then DB, then empty"""
        cache_key = f"profile:{user_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        profile = {
            "user_id": user_id,
            "interests": [],
            "preferred_sources": [],
            "click_patterns": {},
            "query_style": "general",
            "last_updated": datetime.utcnow().isoformat(),
        }

        await cache_service.set(cache_key, profile, ttl=3600)
        return profile

    async def update_profile_from_click(
        self, user_id: int, query: str, clicked_position: int, clicked_url: str
    ):
        """Update user profile based on click behavior"""
        profile = await self.get_user_profile(user_id)

        # Update interests based on query keywords
        query_words = query.lower().split()
        for word in query_words:
            if len(word) > 3:  # Ignore short words
                profile["interests"].append(word)

        # Keep only recent interests (last 50)
        profile["interests"] = profile["interests"][-50:]

        # Extract domain from URL
        domain_match = re.search(r"https?://([^/]+)", clicked_url)
        if domain_match:
            domain = domain_match.group(1)
            profile["preferred_sources"].append(domain)
            profile["preferred_sources"] = profile["preferred_sources"][-20:]

        profile["last_updated"] = datetime.utcnow().isoformat()

        # Update cache
        cache_key = f"profile:{user_id}"
        await cache_service.set(cache_key, profile, ttl=3600)

    async def personalize_results(
        self, user_id: int, query: str, results: list[dict]
    ) -> list[dict]:
        """Re-rank results based on user profile"""
        profile = await self.get_user_profile(user_id)
        interests = set(profile.get("interests", []))
        preferred_sources = set(profile.get("preferred_sources", []))

        if not interests and not preferred_sources:
            return results  # No personalization data

        scored_results = []
        for result in results:
            score = 0.0

            # Boost based on interests
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            for interest in interests:
                if interest in text:
                    score += 0.5

            # Boost based on preferred sources
            url = result.get("url", "")
            for source in preferred_sources:
                if source in url:
                    score += 1.0

            scored_results.append((score, result))

        # Sort by personalization score (stable sort keeps original order for ties)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        return [result for _, result in scored_results]


class QuerySuggestionEngine:
    """Generate intelligent query suggestions"""

    def __init__(self):
        self.spell_corrector = SpellCorrector()
        self.query_expander = QueryExpander()
        self.autocomplete = AutocompleteEngine()
        self.analytics = SearchAnalytics()

    async def _train_autocomplete(self, db) -> None:
        """Train autocomplete trie from search history"""
        try:
            rows = await db.fetchall(
                "SELECT query, COUNT(*) as cnt FROM search_logs "
                "WHERE is_deleted = FALSE GROUP BY query ORDER BY cnt DESC LIMIT 500",
            )
            queries = [(r["query"], r["cnt"]) for r in rows]
            await self.autocomplete.train_from_queries(queries)
        except Exception as exc:
            logger.debug("Autocomplete training failed: %s", exc)

    async def get_suggestions(
        self, partial_query: str, user_id: Optional[int] = None, limit: int = 10,
        db=None,
    ) -> list[QuerySuggestion]:
        """Get comprehensive query suggestions"""
        if not partial_query or len(partial_query) < 2:
            return []

        # Train autocomplete from DB on first call
        if db is not None:
            await self._train_autocomplete(db)

        suggestions = []

        # 1. Autocomplete suggestions
        autocomplete_results = await self.autocomplete.suggest(partial_query, limit=5)
        suggestions.extend(autocomplete_results)

        # 2. Spell-corrected version
        corrected, was_corrected = await self.spell_corrector.correct_query(partial_query)
        if was_corrected:
            suggestions.append(
                QuerySuggestion(
                    suggestion=corrected,
                    score=0.9,
                    source="correction",
                    metadata={"original": partial_query},
                )
            )

        # 3. User's recent queries (if authenticated)
        if user_id:
            history = await self.analytics.get_user_search_history(user_id, limit=5)
            for item in history:
                query = item.get("query", "")
                if partial_query.lower() in query.lower():
                    suggestions.append(
                        QuerySuggestion(
                            suggestion=query,
                            score=0.8,
                            source="history",
                            metadata={"timestamp": item.get("searched_at")},
                        )
                    )

        # 4. Trending queries
        trending = await self.analytics.get_trending_queries(limit=5)
        for item in trending:
            query = item.get("query", "")
            if partial_query.lower() in query.lower():
                suggestions.append(
                    QuerySuggestion(
                        suggestion=query,
                        score=0.7,
                        source="trending",
                        metadata={"count": item.get("count"), "growth": item.get("growth")},
                    )
                )

        # Remove duplicates and sort by score
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s.suggestion.lower() not in seen:
                seen.add(s.suggestion.lower())
                unique_suggestions.append(s)

        unique_suggestions.sort(key=lambda x: x.score, reverse=True)

        return unique_suggestions[:limit]


# Global instances
spell_corrector = SpellCorrector()
query_expander = QueryExpander()
autocomplete_engine = AutocompleteEngine()
search_analytics = SearchAnalytics()
personalization_engine = PersonalizationEngine()
query_suggestion_engine = QuerySuggestionEngine()
