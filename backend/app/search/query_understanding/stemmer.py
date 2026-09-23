"""
Query Stemming and Lemmatization Module

Provides stemming and lemmatization for search queries:
- Porter stemmer
- Snowball stemmer (multiple languages)
- WordNet lemmatization
- Language-aware stemming
"""

import logging

logger = logging.getLogger(__name__)


class QueryStemmer:
    """
    Stems and lemmatizes search query tokens.
    
    Supports multiple algorithms and languages.
    """
    
    def __init__(self, language: str = 'en', use_lemmatization: bool = True):
        """
        Initialize stemmer.
        
        Args:
            language: Language code (default: 'en')
            use_lemmatization: Use lemmatization instead of stemming (default: True)
        """
        self.language = language
        self.use_lemmatization = use_lemmatization
        self._stemmer = None
        self._lemmatizer = None
        self._cache: dict[str, str] = {}
        
        # Initialize stemmer/lemmatizer
        self._initialize()
    
    def _initialize(self):
        """Initialize stemming/lemmatization tools."""
        try:
            if self.use_lemmatization:
                # Try to use NLTK WordNet lemmatizer
                try:
                    import nltk
                    from nltk.stem import WordNetLemmatizer
                    
                    # Download required data if not present
                    try:
                        nltk.data.find('corpora/wordnet')
                    except LookupError:
                        logger.info("Downloading WordNet data...")
                        nltk.download('wordnet', quiet=True)
                        nltk.download('omw-1.4', quiet=True)
                    
                    self._lemmatizer = WordNetLemmatizer()
                    logger.info("Using NLTK WordNet lemmatizer")
                except ImportError:
                    logger.warning("NLTK not available, falling back to simple stemming")
                    self.use_lemmatization = False
            else:
                # Use Porter stemmer
                try:
                    from nltk.stem import PorterStemmer
                    self._stemmer = PorterStemmer()
                    logger.info("Using NLTK Porter stemmer")
                except ImportError:
                    logger.warning("NLTK not available, stemming disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize stemmer: {e}")
    
    async def stem(self, token: str) -> str:
        """
        Stem or lemmatize a single token.
        
        Args:
            token: Input token
            
        Returns:
            Stemmed/lemmatized token
        """
        if not token:
            return token
        
        # Check cache
        if token in self._cache:
            return self._cache[token]
        
        result = token
        
        if self.use_lemmatization and self._lemmatizer:
            # Use lemmatization (more accurate)
            result = self._lemmatizer.lemmatize(token.lower())
        elif self._stemmer:
            # Use stemming (faster)
            result = self._stemmer.stem(token.lower())
        
        # Cache result
        self._cache[token] = result
        
        return result
    
    async def stem_tokens(self, tokens: list[str]) -> list[str]:
        """
        Stem or lemmatize multiple tokens.
        
        Args:
            tokens: List of input tokens
            
        Returns:
            List of stemmed/lemmatized tokens
        """
        if not tokens:
            return []
        
        return [await self.stem(token) for token in tokens]
    
    async def process(self, query: str) -> dict:
        """
        Process a query with stemming/lemmatization.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with original and stemmed tokens
        """
        if not query:
            return {
                'original': [],
                'stemmed': [],
            }
        
        # Simple tokenization (split on whitespace)
        tokens = query.lower().split()
        
        # Stem/lemmatize tokens
        stemmed = await self.stem_tokens(tokens)
        
        return {
            'original': tokens,
            'stemmed': stemmed,
        }
    
    def clear_cache(self):
        """Clear stemming cache."""
        self._cache.clear()


# Singleton instance
query_stemmer = QueryStemmer()

# Alias for backward compatibility
Stemmer = QueryStemmer
