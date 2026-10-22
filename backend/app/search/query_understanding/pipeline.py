"""Query preprocessing pipeline for intelligent search."""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.search.query_understanding.language_detector import LanguageDetector
from app.search.query_understanding.normalizer import Normalizer
from app.search.query_understanding.tokenizer import Tokenizer
from app.search.query_understanding.stemmer import Stemmer
from app.search.query_understanding.stopwords import StopwordRemover
from app.search.query_understanding.synonym_expander import SynonymExpander
from app.search.query_understanding.entity_extractor import EntityExtractor
from app.search.query_understanding.intent_classifier import IntentClassifier
from app.search.query_understanding.query_processor import QueryProcessor

logger = logging.getLogger("nebula.search.pipeline")


class SearchIntent(str, Enum):
    """Search intent types."""
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    TRANSACTIONAL = "transactional"
    COMPARISON = "comparison"
    LOCAL = "local"


@dataclass
class ProcessedQuery:
    """Processed query with all NLP enhancements."""
    original: str
    normalized: str
    tokens: List[str]
    stemmed: List[str]
    language: str
    intent: SearchIntent
    entities: List[Dict]
    synonyms: List[str]
    expanded_query: str
    filters: Dict


class QueryPreprocessor:
    """Query preprocessing pipeline for intelligent search."""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.normalizer = Normalizer()
        self.tokenizer = Tokenizer()
        self.stemmer = Stemmer()
        self.stopword_remover = StopwordRemover()
        self.synonym_expander = SynonymExpander()
        self.entity_extractor = EntityExtractor()
        self.intent_classifier = IntentClassifier()
        self.query_processor = QueryProcessor()
        logger.info("QueryPreprocessor initialized")
    
    async def process(self, query: str) -> ProcessedQuery:
        """
        Process query through full NLP pipeline.
        
        Steps:
        1. Language detection
        2. Normalization
        3. Tokenization
        4. Stopword removal
        5. Stemming
        6. Entity extraction
        7. Intent classification
        8. Synonym expansion
        9. Query expansion
        10. Filter extraction
        """
        try:
            # 1. Language detection
            language = await self.language_detector.detect(query)
            logger.debug(f"Detected language: {language}")
            
            # 2. Normalization
            normalized = await self.normalizer.normalize(query)
            logger.debug(f"Normalized query: {normalized}")
            
            # 3. Tokenization
            tokens = await self.tokenizer.tokenize(normalized)
            logger.debug(f"Tokens: {tokens}")
            
            # 4. Stopword removal
            filtered_tokens = self.stopword_remover.remove(tokens, language)
            logger.debug(f"Filtered tokens: {filtered_tokens}")
            
            # 5. Stemming
            stemmed = [self.stemmer.stem(token, language) for token in filtered_tokens]
            logger.debug(f"Stemmed tokens: {stemmed}")
            
            # 6. Entity extraction
            entities = self.entity_extractor.extract(normalized)
            logger.debug(f"Extracted entities: {entities}")
            
            # 7. Intent classification
            intent = self.intent_classifier.classify(normalized, entities)
            logger.debug(f"Classified intent: {intent}")
            
            # 8. Synonym expansion
            synonyms = self.synonym_expander.expand(filtered_tokens, language)
            logger.debug(f"Synonyms: {synonyms}")
            
            # 9. Query expansion
            expanded_query = self.query_processor.expand(
                normalized, synonyms, entities
            )
            logger.debug(f"Expanded query: {expanded_query}")
            
            # 10. Extract filters from entities
            filters = self._extract_filters(entities)
            logger.debug(f"Extracted filters: {filters}")
            
            return ProcessedQuery(
                original=query,
                normalized=normalized,
                tokens=filtered_tokens,
                stemmed=stemmed,
                language=language,
                intent=intent,
                entities=entities,
                synonyms=synonyms,
                expanded_query=expanded_query,
                filters=filters
            )
            
        except Exception as e:
            logger.error(f"Query preprocessing failed: {e}", exc_info=True)
            # Fallback to basic processing
            return ProcessedQuery(
                original=query,
                normalized=query.lower().strip(),
                tokens=query.lower().split(),
                stemmed=[],
                language="en",
                intent=SearchIntent.INFORMATIONAL,
                entities=[],
                synonyms=[],
                expanded_query=query,
                filters={}
            )
    
    def _extract_filters(self, entities: List[Dict]) -> Dict:
        """
        Extract search filters from entities.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Dictionary of filters
        """
        filters = {}
        
        for entity in entities:
            entity_type = entity.get("type")
            entity_value = entity.get("value")
            
            if not entity_type or not entity_value:
                continue
            
            if entity_type == "date":
                filters["date_range"] = entity_value
            elif entity_type == "location":
                filters["location"] = entity_value
            elif entity_type == "category":
                filters["category"] = entity_value
            elif entity_type == "file_type":
                filters["file_type"] = entity_value
            elif entity_type == "author":
                filters["author"] = entity_value
            elif entity_type == "language":
                filters["language"] = entity_value
        
        return filters


# Singleton instance
_query_preprocessor: Optional[QueryPreprocessor] = None


def get_query_preprocessor() -> QueryPreprocessor:
    """Get singleton query preprocessor instance."""
    global _query_preprocessor
    if _query_preprocessor is None:
        _query_preprocessor = QueryPreprocessor()
    return _query_preprocessor