"""
Metadata Boosting

Applies configurable boosts to search results based on metadata quality and relevance.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger("nebula.hybrid.boosting")


class MetadataBooster:
    """
    Boost search results based on metadata signals.
    
    Supported boosts:
    - Title matches
    - Heading matches
    - Tag matches
    - Category matches
    - Recency
    - Popularity
    - Custom metadata fields
    """

    def __init__(
        self,
        title_boost: float = 2.0,
        heading_boost: float = 1.5,
        tag_boost: float = 1.3,
        category_boost: float = 1.2,
        recency_boost: float = 1.4,
        popularity_boost: float = 1.3,
    ):
        """
        Initialize metadata booster.
        
        Args:
            title_boost: Boost factor for title matches
            heading_boost: Boost factor for heading matches
            tag_boost: Boost factor for tag matches
            category_boost: Boost factor for category matches
            recency_boost: Boost factor for recent documents
            popularity_boost: Boost factor for popular documents
        """
        self.boosts = {
            "title": title_boost,
            "heading": heading_boost,
            "tag": tag_boost,
            "category": category_boost,
            "recency": recency_boost,
            "popularity": popularity_boost,
        }

    def boost(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Apply metadata boosts to search results.
        
        Args:
            results: List of search results
            query: Original search query
            
        Returns:
            Boosted results with updated scores
        """
        if not results:
            return results
        
        query_terms = query.lower().split()
        
        boosted_results = []
        for result in results:
            boosted = result.copy()
            boost_factors = []
            
            # Apply boosts
            title_boost = self._boost_title(boosted, query_terms)
            if title_boost > 1.0:
                boost_factors.append(("title", title_boost))
            
            heading_boost = self._boost_heading(boosted, query_terms)
            if heading_boost > 1.0:
                boost_factors.append(("heading", heading_boost))
            
            tag_boost = self._boost_tags(boosted, query_terms)
            if tag_boost > 1.0:
                boost_factors.append(("tag", tag_boost))
            
            category_boost = self._boost_categories(boosted, query_terms)
            if category_boost > 1.0:
                boost_factors.append(("category", category_boost))
            
            recency_boost = self._boost_recency(boosted)
            if recency_boost > 1.0:
                boost_factors.append(("recency", recency_boost))
            
            popularity_boost = self._boost_popularity(boosted)
            if popularity_boost > 1.0:
                boost_factors.append(("popularity", popularity_boost))
            
            # Calculate combined boost (multiply all factors)
            combined_boost = 1.0
            for _, factor in boost_factors:
                combined_boost *= factor
            
            # Apply boost to score
            original_score = boosted.get("score", 0.0)
            boosted["score"] = original_score * combined_boost
            boosted["original_score"] = original_score
            boosted["boost_factors"] = boost_factors
            boosted["boost_multiplier"] = combined_boost
            
            boosted_results.append(boosted)
        
        return boosted_results

    def _boost_title(self, result: Dict[str, Any], query_terms: List[str]) -> float:
        """Boost based on title matches"""
        title = result.get("title", "").lower()
        if not title:
            return 1.0
        
        boost = 1.0
        for term in query_terms:
            if term in title:
                boost *= self.boosts["title"]
        
        # Cap the boost
        return min(boost, self.boosts["title"] * 2)

    def _boost_heading(self, result: Dict[str, Any], query_terms: List[str]) -> float:
        """Boost based on heading matches"""
        headings = result.get("headings", [])
        if not headings:
            return 1.0
        
        boost = 1.0
        for heading in headings:
            heading_lower = str(heading).lower()
            for term in query_terms:
                if term in heading_lower:
                    boost *= self.boosts["heading"]
        
        return min(boost, self.boosts["heading"] * 2)

    def _boost_tags(self, result: Dict[str, Any], query_terms: List[str]) -> float:
        """Boost based on tag matches"""
        tags = result.get("tags", [])
        if not tags:
            return 1.0
        
        boost = 1.0
        for tag in tags:
            tag_lower = str(tag).lower()
            for term in query_terms:
                if term in tag_lower:
                    boost *= self.boosts["tag"]
        
        return min(boost, self.boosts["tag"] * 2)

    def _boost_categories(self, result: Dict[str, Any], query_terms: List[str]) -> float:
        """Boost based on category matches"""
        categories = result.get("categories", [])
        if not categories:
            return 1.0
        
        boost = 1.0
        for category in categories:
            category_lower = str(category).lower()
            for term in query_terms:
                if term in category_lower:
                    boost *= self.boosts["category"]
        
        return min(boost, self.boosts["category"] * 2)

    def _boost_recency(self, result: Dict[str, Any]) -> float:
        """Boost based on document recency"""
        from datetime import datetime
        
        updated_at = result.get("updated_at")
        if not updated_at:
            return 1.0
        
        # Parse date
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return 1.0
        
        # Calculate age in days
        now = datetime.utcnow()
        if hasattr(updated_at, 'tzinfo') and updated_at.tzinfo:
            from datetime import timezone
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        age_days = (now - updated_at).total_seconds() / 86400
        
        # Exponential decay boost (newer = higher boost)
        # Boost decays from recency_boost to 1.0 over 30 days
        if age_days < 0:
            return 1.0
        
        decay = self.boosts["recency"]
        half_life = 7.0  # Days
        boost = 1.0 + (decay - 1.0) * (2 ** (-age_days / half_life))
        
        return min(boost, decay)

    def _boost_popularity(self, result: Dict[str, Any]) -> float:
        """Boost based on document popularity"""
        views = result.get("views", 0)
        clicks = result.get("clicks", 0)
        
        if views == 0 and clicks == 0:
            return 1.0
        
        # Calculate popularity score (log scale)
        popularity_score = 0.0
        if views > 0:
            popularity_score += min(1.0, views / 1000.0)
        if clicks > 0:
            popularity_score += min(1.0, clicks / 100.0)
        
        # Map to boost factor
        boost = 1.0 + (popularity_score * (self.boosts["popularity"] - 1.0))
        
        return min(boost, self.boosts["popularity"])

    def boost_custom_field(
        self,
        result: Dict[str, Any],
        field: str,
        query_terms: List[str],
        boost_factor: float = 1.5,
    ) -> float:
        """
        Boost based on custom metadata field.
        
        Args:
            result: Search result
            field: Custom field name
            query_terms: Query terms to match
            boost_factor: Boost multiplier
            
        Returns:
            Boost factor applied
        """
        field_value = result.get(field)
        if not field_value:
            return 1.0
        
        # Check if any query term matches
        field_text = str(field_value).lower()
        for term in query_terms:
            if term in field_text:
                return boost_factor
        
        return 1.0

    def update_boost(self, boost_type: str, boost_factor: float):
        """
        Update a boost factor.
        
        Args:
            boost_type: Type of boost (title, heading, tag, etc.)
            boost_factor: New boost factor
        """
        if boost_type in self.boosts:
            self.boosts[boost_type] = boost_factor
            logger.info(f"Updated {boost_type} boost to {boost_factor}")
        else:
            logger.warning(f"Unknown boost type: {boost_type}")

    def get_boost_factors(self) -> Dict[str, float]:
        """Get current boost factors"""
        return self.boosts.copy()