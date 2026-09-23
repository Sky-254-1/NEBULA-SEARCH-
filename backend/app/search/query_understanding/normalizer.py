"""
Query Normalization Module

Normalizes search queries by:
- Converting to lowercase
- Removing punctuation
- Removing extra whitespace
- Normalizing unicode
- Removing special characters
- Standardizing numbers and dates
"""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


class QueryNormalizer:
    """
    Normalizes search queries for consistent processing.
    
    Applies multiple normalization steps in configurable order.
    """
    
    def __init__(
        self,
        lowercase: bool = True,
        remove_punctuation: bool = True,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_special_chars: bool = False,
        normalize_numbers: bool = False,
    ):
        """
        Initialize query normalizer.
        
        Args:
            lowercase: Convert to lowercase
            remove_punctuation: Remove punctuation marks
            remove_extra_whitespace: Remove extra spaces
            normalize_unicode: Normalize unicode characters
            remove_special_chars: Remove special characters
            normalize_numbers: Normalize number formats
        """
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_special_chars = remove_special_chars
        self.normalize_numbers = normalize_numbers
    
    async def normalize(self, query: str) -> str:
        """
        Normalize a search query.
        
        Args:
            query: Raw search query
            
        Returns:
            Normalized query string
        """
        if not query:
            return query
        
        normalized = query
        
        # Step 1: Unicode normalization
        if self.normalize_unicode:
            normalized = self._normalize_unicode(normalized)
        
        # Step 2: Lowercase
        if self.lowercase:
            normalized = normalized.lower()
        
        # Step 3: Remove special characters
        if self.remove_special_chars:
            normalized = self._remove_special_chars(normalized)
        
        # Step 4: Remove punctuation
        if self.remove_punctuation:
            normalized = self._remove_punctuation(normalized)
        
        # Step 5: Normalize numbers
        if self.normalize_numbers:
            normalized = self._normalize_numbers(normalized)
        
        # Step 6: Remove extra whitespace
        if self.remove_extra_whitespace:
            normalized = self._remove_extra_whitespace(normalized)
        
        return normalized.strip()
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters (NFKD form)."""
        normalized = unicodedata.normalize('NFKD', text)
        # Remove combining characters
        normalized = ''.join(
            c for c in normalized 
            if not unicodedata.combining(c)
        )
        return normalized
    
    def _remove_punctuation(self, text: str) -> str:
        """Remove punctuation marks."""
        # Keep some punctuation that might be meaningful
        # Remove: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
        return re.sub(r'[^\w\s\-]', ' ', text)
    
    def _remove_special_chars(self, text: str) -> str:
        """Remove special characters (keep only alphanumeric and spaces)."""
        return re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    def _remove_extra_whitespace(self, text: str) -> str:
        """Remove extra whitespace (multiple spaces, tabs, newlines)."""
        return re.sub(r'\s+', ' ', text)
    
    def _normalize_numbers(self, text: str) -> str:
        """Normalize number formats (e.g., 1,000 -> 1000)."""
        # Remove commas from numbers
        text = re.sub(r'(\d),(\d)', r'\1\2', text)
        # Normalize decimal points
        text = re.sub(r'(\d)\.(\d)', r'\1.\2', text)
        return text
    
    async def normalize_for_storage(self, query: str) -> str:
        """
        Normalize query for storage/indexing (more aggressive).
        
        Args:
            query: Search query
            
        Returns:
            Normalized query for storage
        """
        # More aggressive normalization for storage
        normalized = await self.normalize(query)
        # Remove stop words, etc. (can be added later)
        return normalized
    
    async def normalize_for_search(self, query: str) -> str:
        """
        Normalize query for search (less aggressive).
        
        Args:
            query: Search query
            
        Returns:
            Normalized query for search
        """
        # Less aggressive normalization for search
        normalized = await self.normalize(query)
        return normalized


# Singleton instance
query_normalizer = QueryNormalizer()

# Alias for backward compatibility
Normalizer = QueryNormalizer
