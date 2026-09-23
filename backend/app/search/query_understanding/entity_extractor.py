"""
Entity Extraction Module

Extracts named entities from search queries:
- Person names
- Organizations
- Locations
- Dates
- Technical terms
- Product names
- Domain-specific entities
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extracts named entities from search queries.
    
    Uses pattern matching and dictionaries for entity recognition.
    """
    
    # Entity patterns (regex-based)
    ENTITY_PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'url': re.compile(r'https?://[^\s]+'),
        'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
        'date': re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2},? \d{4})\b', re.IGNORECASE),
        'time': re.compile(r'\b(?:\d{1,2}:\d{2}(?::\d{2})?(?:\s?[ap]m)?)\b', re.IGNORECASE),
        'version': re.compile(r'\bv?\d+\.\d+(?:\.\d+)?\b'),
        'file_path': re.compile(r'\b(?:[A-Za-z]:\\|/)?(?:[\w.-]+/)*[\w.-]+\.[a-zA-Z]{1,4}\b'),
        'hashtag': re.compile(r'#\w+'),
        'mention': re.compile(r'@\w+'),
    }
    
    # Common entity dictionaries
    ENTITY_DICTIONARIES = {
        'en': {
            # Programming languages
            'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'go', 'rust',
            'typescript', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab',
            
            # Frameworks
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express',
            'laravel', 'rails', 'asp.net', 'jquery', 'bootstrap', 'tailwind',
            
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
            'oracle', 'sql server', 'cassandra', 'couchbase', 'dynamodb',
            
            # Cloud platforms
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',
            'kubernetes', 'docker', 'terraform', 'ansible',
            
            # Companies
            'google', 'microsoft', 'apple', 'amazon', 'facebook', 'meta',
            'twitter', 'linkedin', 'github', 'gitlab', 'bitbucket',
            
            # Technologies
            'api', 'rest', 'graphql', 'json', 'xml', 'yaml', 'html', 'css',
            'oauth', 'jwt', 'sso', 'vpn', 'cdn', 'dns', 'ssl', 'tls',
        },
        'es': {
            'python', 'javascript', 'java', 'google', 'microsoft', 'amazon',
        },
        'fr': {
            'python', 'javascript', 'java', 'google', 'microsoft', 'amazon',
        },
    }
    
    def __init__(self, language: str = 'en'):
        """
        Initialize entity extractor.
        
        Args:
            language: Language code (default: 'en')
        """
        self.language = language
        self._cache: dict = {}
    
    async def extract(self, query: str) -> dict:
        """
        Extract entities from a search query.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with extracted entities by type
        """
        if not query:
            return {
                'entities': [],
                'entities_by_type': {},
            }
        
        # Check cache
        if query in self._cache:
            return self._cache[query]
        
        entities = []
        entities_by_type = {}
        
        # Extract pattern-based entities
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = pattern.findall(query)
            if matches:
                entities_by_type[entity_type] = matches
                for match in matches:
                    entities.append({
                        'text': match,
                        'type': entity_type,
                        'confidence': 1.0,
                    })
        
        # Extract dictionary-based entities
        dict_entities = self._extract_dictionary_entities(query)
        if dict_entities:
            for entity in dict_entities:
                entity_type = 'keyword'
                entities_by_type.setdefault(entity_type, []).append(entity['text'])
                entities.append(entity)
        
        result = {
            'entities': entities,
            'entities_by_type': entities_by_type,
        }
        
        # Cache result
        self._cache[query] = result
        
        return result
    
    def _extract_dictionary_entities(self, query: str) -> list[dict]:
        """
        Extract entities using dictionary matching.
        
        Args:
            query: Search query
            
        Returns:
            List of extracted entities
        """
        entities = []
        query_lower = query.lower()
        
        # Get dictionary for language
        dictionary = self.ENTITY_DICTIONARIES.get(self.language, set())
        
        # Match entities from dictionary
        for entity in dictionary:
            if entity in query_lower:
                entities.append({
                    'text': entity,
                    'type': 'keyword',
                    'confidence': 0.9,
                })
        
        return entities
    
    async def extract_for_search(self, query: str) -> dict:
        """
        Extract entities and prepare for search.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with entities and search hints
        """
        result = await self.extract(query)
        
        # Add search hints based on entities
        search_hints = []
        
        # If email found, suggest user search
        if 'email' in result['entities_by_type']:
            search_hints.append('user_search')
        
        # If URL found, suggest web search
        if 'url' in result['entities_by_type']:
            search_hints.append('web_search')
        
        # If file path found, suggest file search
        if 'file_path' in result['entities_by_type']:
            search_hints.append('file_search')
        
        # If date found, suggest date filter
        if 'date' in result['entities_by_type']:
            search_hints.append('date_filter')
        
        result['search_hints'] = search_hints
        
        return result
    
    def add_entity(self, entity: str, entity_type: str, language: Optional[str] = None):
        """
        Add custom entity to dictionary.
        
        Args:
            entity: Entity text
            entity_type: Entity type (keyword, person, org, etc.)
            language: Language code (uses instance language if not provided)
        """
        lang = language or self.language
        
        if lang not in self.ENTITY_DICTIONARIES:
            self.ENTITY_DICTIONARIES[lang] = set()
        
        self.ENTITY_DICTIONARIES[lang].add(entity.lower())
        self._cache.clear()
    
    def add_pattern(self, entity_type: str, pattern: str):
        """
        Add custom entity pattern.
        
        Args:
            entity_type: Entity type name
            pattern: Regex pattern string
        """
        self.ENTITY_PATTERNS[entity_type] = re.compile(pattern)
        self._cache.clear()
    
    def clear_cache(self):
        """Clear entity extraction cache."""
        self._cache.clear()


# Singleton instance
entity_extractor = EntityExtractor()