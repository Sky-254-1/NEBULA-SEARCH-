"""Personalization engine for search results.

Implements:
- User interest extraction from search history
- Personalized ranking weights
- Search history analysis
- Preference learning
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger("nebula.search.personalization")


class UserProfile:
    """User profile with interests and preferences."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.interests: list[str] = []
        self.frequent_queries: list[str] = []
        self.preferred_categories: list[str] = []
        self.personalization_enabled: bool = True
        self.last_updated: datetime = datetime.now()

        # Computed fields
        self.interest_weights: dict[str, float] = {}
        self.category_weights: dict[str, float] = {}

    @classmethod
    def from_dict(cls, user_id: int, data: dict[str, Any]) -> "UserProfile":
        """Create profile from dictionary."""
        profile = cls(user_id)
        profile.interests = data.get("interests", [])
        profile.frequent_queries = json.loads(data.get("frequent_queries", "[]"))
        profile.preferred_categories = json.loads(data.get("preferred_categories", "[]"))
        profile.personalization_enabled = data.get("personalization_enabled", True)
        return profile

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "user_id": self.user_id,
            "interests": self.interests,
            "frequent_queries": self.frequent_queries,
            "preferred_categories": self.preferred_categories,
            "personalization_enabled": self.personalization_enabled,
            "interest_weights": self.interest_weights,
            "category_weights": self.category_weights,
        }


class PersonalizationEngine:
    """Engine for personalizing search results."""

    def __init__(self, db: Any = None):
        """
        Initialize personalization engine.

        Args:
            db: Database connection (optional, for fetching user data)
        """
        self._db = db
        from app.database.repositories.suggestion_repository import SuggestionRepository
        self._repo = SuggestionRepository(db) if db else None
        self._profile_cache: dict[int, UserProfile] = {}
        self.cache_ttl = timedelta(hours=1)

    async def get_user_profile(self, user_id: int) -> UserProfile:
        """
        Get user profile with interests and preferences.

        Args:
            user_id: User ID

        Returns:
            User profile
        """
        # Check cache first
        if user_id in self._profile_cache:
            cached = self._profile_cache[user_id]
            if datetime.now() - cached.last_updated < self.cache_ttl:
                return cached

        # Create default profile if no db
        if not self._repo:
            profile = UserProfile(user_id)
            self._profile_cache[user_id] = profile
            return profile

        # Fetch from database
        prefs = await self._repo.get_user_preferences(user_id)
        if not prefs:
            profile = UserProfile(user_id)
            self._profile_cache[user_id] = profile
            return profile

        # Extract interests from search history
        search_history = await self._repo.get_user_search_history(user_id, limit=100)
        interests = self._extract_interests(search_history)

        # Build profile
        profile = UserProfile.from_dict(user_id, prefs)
        profile.interests = interests
        profile.interest_weights = self._calculate_interest_weights(search_history)
        profile.category_weights = self._calculate_category_weights(profile.preferred_categories)

        # Cache profile
        self._profile_cache[user_id] = profile

        return profile

    def _extract_interests(self, search_history: list[dict], top_k: int = 20) -> list[str]:
        """
        Extract user interests from search history.

        Args:
            search_history: List of search history items
            top_k: Number of top interests to return

        Returns:
            List of interest keywords
        """
        # Extract all query terms
        all_terms = []
        for item in search_history:
            query = item.get("query", "")
            terms = query.lower().split()
            all_terms.extend(terms)

        # Count term frequencies
        term_counts = Counter(all_terms)

        # Filter out common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
            "they", "me", "him", "her", "us", "them", "my", "your", "his", "its",
            "our", "their", "this", "that", "these", "those", "what", "which",
            "who", "whom", "whose", "when", "where", "why", "how", "all", "each",
            "every", "both", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too", "very",
            "can", "just", "now", "also", "in", "on", "at", "to", "for", "with",
            "from", "by", "about", "as", "into", "through", "during", "before",
            "after", "above", "below", "between", "under", "again", "further",
            "then", "once", "here", "there", "and", "but", "if", "or", "because",
            "until", "while", "of", "off", "up", "down", "out", "over", "under",
        }

        # Filter and get top terms
        interests = [
            term for term, count in term_counts.most_common(top_k * 2)
            if term not in stop_words and len(term) > 2
        ][:top_k]

        return interests

    def _calculate_interest_weights(self, search_history: list[dict]) -> dict[str, float]:
        """
        Calculate weights for user interests based on frequency and recency.

        Args:
            search_history: List of search history items

        Returns:
            Dictionary mapping interest terms to weights
        """
        weights = defaultdict(float)
        now = datetime.now()

        for item in search_history:
            query = item.get("query", "")
            frequency = item.get("frequency", 1)
            last_used_str = item.get("last_used")

            # Calculate recency factor (0.0 to 1.0)
            if last_used_str:
                try:
                    last_used = datetime.fromisoformat(last_used_str.replace('Z', '+00:00'))
                    days_old = (now - last_used).days
                    recency = max(0.0, 1.0 * (0.95 ** days_old))
                except Exception:
                    recency = 0.5
            else:
                recency = 0.5

            # Weight = frequency * recency
            weight = frequency * recency

            # Add to interests
            for term in query.lower().split():
                weights[term] += weight

        # Normalize weights to 0-1 range
        if weights:
            max_weight = max(weights.values())
            if max_weight > 0:
                weights = {k: v / max_weight for k, v in weights.items()}

        return dict(weights)

    def _calculate_category_weights(self, preferred_categories: list[str]) -> dict[str, float]:
        """
        Calculate weights for preferred categories.

        Args:
            preferred_categories: List of preferred categories

        Returns:
            Dictionary mapping categories to weights
        """
        if not preferred_categories:
            return {}

        # Equal weights for all categories initially
        weight = 1.0 / len(preferred_categories)
        return {cat: weight for cat in preferred_categories}

    async def learn_from_search(
        self,
        user_id: int,
        query: str,
        clicked_doc_ids: Optional[list[int]] = None,
        dwell_time: Optional[float] = None,
    ) -> None:
        """
        Learn from user search behavior.

        Args:
            user_id: User ID
            query: Search query
            clicked_doc_ids: List of clicked document IDs
            dwell_time: Time spent on clicked results (seconds)
        """
        if not self._repo:
            return

        # Update frequent queries in preferences
        prefs = await self._repo.get_user_preferences(user_id)
        if prefs:
            frequent_queries = json.loads(prefs.get("frequent_queries", "[]"))

            # Add query if not already in list
            if query not in frequent_queries:
                frequent_queries.append(query)
                # Keep only last 50 queries
                frequent_queries = frequent_queries[-50:]

                await self._repo.upsert_user_preferences(
                    user_id=user_id,
                    frequent_queries=json.dumps(frequent_queries),
                    personalization_enabled=prefs.get("personalization_enabled", True),
                )

        # Invalidate cache
        if user_id in self._profile_cache:
            del self._profile_cache[user_id]

    async def get_personalized_weights(
        self, user_id: int, base_weights: dict[str, float]
    ) -> dict[str, float]:
        """
        Get personalized ranking weights for a user.

        Args:
            user_id: User ID
            base_weights: Base ranking weights

        Returns:
            Personalized weights
        """
        profile = await self.get_user_profile(user_id)

        if not profile.personalization_enabled:
            return base_weights

        # Adjust weights based on user interests
        personalized = base_weights.copy()

        # Boost personalization weight if user has strong interests
        if profile.interest_weights:
            avg_interest = sum(profile.interest_weights.values()) / len(profile.interest_weights)
            if avg_interest > 0.5:
                personalized["personalization"] = min(0.3, personalized.get("personalization", 0.1) + 0.1)

        return personalized

    def calculate_result_score_adjustment(
        self, profile: UserProfile, document: dict
    ) -> float:
        """
        Calculate score adjustment for a document based on user profile.

        Args:
            profile: User profile
            document: Document to score

        Returns:
            Score adjustment (0.0 to 0.2)
        """
        if not profile.personalization_enabled:
            return 0.0

        doc_text = f"{document.get('title', '')} {document.get('snippet', '')}".lower()

        # Check for interest matches
        interest_matches = sum(
            1 for interest in profile.interests if interest in doc_text
        )

        # Check for category matches
        category_matches = sum(
            1 for cat in profile.preferred_categories if cat.lower() in doc_text
        )

        # Calculate adjustment
        adjustment = 0.0
        if interest_matches > 0:
            adjustment += 0.05 * min(interest_matches, 3)  # Max +0.15
        if category_matches > 0:
            adjustment += 0.1 * min(category_matches, 2)  # Max +0.2

        return min(adjustment, 0.2)  # Cap at +0.2