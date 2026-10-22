"""
Query Tokenization Module

Tokenizes search queries with support for:
- Word tokenization
- Phrase detection
- N-gram generation
- Multi-word token handling
- Language-aware tokenization
"""

import logging
import re

logger = logging.getLogger(__name__)


class QueryTokenizer:
    """
    Tokenizes search queries into meaningful tokens.
    
    Supports multiple tokenization strategies and languages.
    """
    
    def __init__(self, language: str = 'en'):
        """
        Initialize tokenizer.
        
        Args:
            language: Language code for language-specific tokenization
        """
        self.language = language
        self._cache: dict[tuple, dict] = {}
    
    async def tokenize(
        self,
        query: str,
        preserve_phrases: bool = True,
        generate_ngrams: bool = False,
        ngram_size: int = 3,
    ) -> dict:
        """
        Tokenize a search query.
        
        Args:
            query: Search query text
            preserve_phrases: Detect and preserve quoted phrases
            generate_ngrams: Generate n-grams for partial matching
            ngram_size: Size of n-grams (default: 3)
            
        Returns:
            Dictionary with tokens, phrases, and optionally n-grams
        """
        if not query:
            return {
                'tokens': [],
                'phrases': [],
                'ngrams': [],
            }
        
        # Check cache
        cache_key = (query, preserve_phrases, generate_ngrams, ngram_size)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Extract phrases first (quoted text)
        phrases = []
        if preserve_phrases:
            phrases = self._extract_phrases(query)
            # Remove phrases from query for tokenization
            query_for_tokens = self._remove_phrases(query, phrases)
        else:
            query_for_tokens = query
        
        # Tokenize remaining text
        tokens = self._tokenize_text(query_for_tokens)
        
        # Generate n-grams if requested
        ngrams = []
        if generate_ngrams and tokens:
            ngrams = self._generate_ngrams(tokens, ngram_size)
        
        result = {
            'tokens': tokens,
            'phrases': phrases,
            'ngrams': ngrams,
        }
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
    
    def _extract_phrases(self, query: str) -> list[str]:
        """
        Extract quoted phrases from query.
        
        Args:
            query: Search query
            
        Returns:
            List of quoted phrases
        """
        # Match double-quoted phrases
        double_quoted = re.findall(r'"([^"]+)"', query)
        # Match single-quoted phrases
        single_quoted = re.findall(r"'([^']+)'", query)
        
        phrases = double_quoted + single_quoted
        
        # Clean up phrases
        cleaned_phrases = []
        for phrase in phrases:
            phrase = phrase.strip()
            if phrase:
                cleaned_phrases.append(phrase)
        
        return cleaned_phrases
    
    def _remove_phrases(self, query: str, phrases: list[str]) -> str:
        """
        Remove quoted phrases from query.
        
        Args:
            query: Search query
            phrases: List of phrases to remove
            
        Returns:
            Query with phrases removed
        """
        result = query
        for phrase in phrases:
            # Remove both double and single quoted versions
            result = result.replace(f'"{phrase}"', ' ')
            result = result.replace(f"'{phrase}'", ' ')
        return result
    
    def _tokenize_text(self, text: str) -> list[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Language-specific tokenization
        if self.language in ['zh', 'ja', 'ko']:
            # For CJK languages, keep characters as tokens
            tokens = list(text)
        else:
            # For Latin-based languages, split on whitespace and punctuation
            # Keep hyphens within words
            tokens = re.findall(r'\b\w+\b', text)
        
        # Clean tokens
        cleaned_tokens = []
        for token in tokens:
            token = token.strip()
            if token and len(token) > 0:
                cleaned_tokens.append(token)
        
        return cleaned_tokens
    
    def _generate_ngrams(self, tokens: list[str], n: int) -> list[str]:
        """
        Generate n-grams from tokens.
        
        Args:
            tokens: List of tokens
            n: N-gram size
            
        Returns:
            List of n-grams
        """
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i + n])
            ngrams.append(ngram)
        
        return ngrams
    
    async def tokenize_for_search(self, query: str) -> dict:
        """
        Tokenize query for search (optimized).
        
        Args:
            query: Search query
            
        Returns:
            Tokenization result
        """
        return await self.tokenize(
            query,
            preserve_phrases=True,
            generate_ngrams=False,
        )
    
    async def tokenize_for_indexing(self, query: str) -> dict:
        """
        Tokenize query for indexing (with n-grams).
        
        Args:
            query: Search query
            
        Returns:
            Tokenization result with n-grams
        """
        return await self.tokenize(
            query,
            preserve_phrases=True,
            generate_ngrams=True,
            ngram_size=3,
        )
    
    def clear_cache(self):
        """Clear tokenization cache."""
        self._cache.clear()


# Singleton instance
query_tokenizer = QueryTokenizer()

# Alias for backward compatibility
Tokenizer = QueryTokenizer
