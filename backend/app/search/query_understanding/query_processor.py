"""
Query Processor

Orchestrates the query understanding pipeline:
1. Language detection
2. Query normalization
3. Tokenization
4. Stop-word removal
5. Stemming/Lemmatization
6. Synonym expansion
7. Entity extraction
8. Intent classification
"""

import logging
from typing import Any, Optional

from .language_detector import language_detector
from .normalizer import query_normalizer
from .tokenizer import query_tokenizer
from .stopwords import stop_word_remover
from .stemmer import query_stemmer
from .synonym_expander import synonym_expander
from .entity_extractor import entity_extractor
from .intent_classifier import intent_classifier

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Orchestrates query understanding pipeline.
    
    Processes search queries through multiple stages to extract
    meaning, intent, and improve search quality.
    """
    
    def __init__(self, language: str = 'en'):
        """
        Initialize query processor.
        
        Args:
            language: Default language code
        """
        self.language = language
        self._cache: dict[str, Any] = {}
    
    async def process(
        self,
        query: str,
        language: Optional[str] = None,
        enable_synonyms: bool = True,
        enable_stemming: bool = True,
        enable_stopwords: bool = False,  # Usually false for search
    ) -> dict:
        """
        Process a search query through the understanding pipeline.
        
        Args:
            query: Raw search query
            language: Language code (auto-detect if not provided)
            enable_synonyms: Enable synonym expansion
            enable_stemming: Enable stemming/lemmatization
            enable_stopwords: Enable stop-word removal
            
        Returns:
            Dictionary with processed query information
        """
        if not query or not query.strip():
            return {
                'original': query,
                'processed': query,
                'language': self.language,
                'tokens': [],
                'entities': [],
                'intent': {},
            }
        
        # Check cache
        cache_key = (query, language, enable_synonyms, enable_stemming, enable_stopwords)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Step 1: Detect language
        lang = language or await language_detector.detect(query)
        logger.debug(f"Detected language: {lang}")
        
        # Step 2: Normalize query
        normalized = await query_normalizer.normalize(query)
        logger.debug(f"Normalized query: {normalized}")
        
        # Step 3: Tokenize
        tokenization = await query_tokenizer.tokenize(normalized)
        tokens = tokenization['tokens']
        phrases = tokenization['phrases']
        logger.debug(f"Tokens: {tokens}, Phrases: {phrases}")
        
        # Step 4: Remove stop words (optional)
        if enable_stopwords and tokens:
            stop_word_result = await stop_word_remover.process(normalized)
            tokens = stop_word_result['filtered']
            logger.debug(f"Tokens after stop-word removal: {tokens}")
        
        # Step 5: Stem/Lemmatize tokens (optional)
        if enable_stemming and tokens:
            stemmed_tokens = await query_stemmer.stem_tokens(tokens)
            logger.debug(f"Stemmed tokens: {stemmed_tokens}")
        else:
            stemmed_tokens = tokens
        
        # Step 6: Expand synonyms (optional)
        expanded_query = normalized
        synonyms_added = []
        if enable_synonyms:
            synonym_result = await synonym_expander.expand(normalized)
            expanded_query = synonym_result['expanded']
            synonyms_added = synonym_result['synonyms_added']
            logger.debug(f"Expanded query: {expanded_query}")
        
        # Step 7: Extract entities
        entities_result = await entity_extractor.extract(query)
        entities = entities_result['entities']
        logger.debug(f"Extracted entities: {entities}")
        
        # Step 8: Classify intent
        intent_result = await intent_classifier.classify(query)
        intent = intent_result['intent']
        logger.debug(f"Classified intent: {intent}")
        
        # Build result
        result = {
            'original': query,
            'normalized': normalized,
            'processed': expanded_query,
            'language': lang,
            'tokens': tokens,
            'stemmed_tokens': stemmed_tokens,
            'phrases': phrases,
            'entities': entities,
            'intent': intent,
            'intent_confidence': intent_result['confidence'],
            'all_intent_scores': intent_result['all_scores'],
            'synonyms_added': synonyms_added,
            'entity_types': list(entities_result['entities_by_type'].keys()),
        }
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
    
    async def process_for_search(self, query: str, language: Optional[str] = None) -> dict:
        """
        Process query for search (optimized settings).
        
        Args:
            query: Search query
            language: Language code
            
        Returns:
            Processed query information
        """
        return await self.process(
            query,
            language=language,
            enable_synonyms=True,
            enable_stemming=True,
            enable_stopwords=False,  # Don't remove stop words for search
        )
    
    async def process_for_indexing(self, query: str, language: Optional[str] = None) -> dict:
        """
        Process query for indexing (more aggressive processing).
        
        Args:
            query: Search query
            language: Language code
            
        Returns:
            Processed query information
        """
        return await self.process(
            query,
            language=language,
            enable_synonyms=True,
            enable_stemming=True,
            enable_stopwords=True,  # Remove stop words for indexing
        )
    
    def clear_cache(self):
        """Clear processing cache."""
        self._cache.clear()
        
        # Clear all component caches
        language_detector.clear_cache()
        query_tokenizer.clear_cache()
        query_stemmer.clear_cache()
        synonym_expander.clear_cache()
        entity_extractor.clear_cache()
        intent_classifier.clear_cache()


# Singleton instance
query_processor = QueryProcessor()