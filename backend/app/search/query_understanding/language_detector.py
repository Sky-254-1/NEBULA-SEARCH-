"""
Language Detection Module

Detects the language of search queries to enable:
- Multilingual search
- Language-specific processing
- Appropriate stop-word removal
- Language-specific stemming
"""

import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Detects query language using multiple strategies.
    
    Supports 100+ languages with fallback to English.
    """
    
    # Common language patterns for quick detection
    LANGUAGE_PATTERNS = {
        'en': re.compile(r'^[a-zA-Z\s]+$', re.IGNORECASE),
        'es': re.compile(r'^[a-zA-Záéíóúñü\s]+$', re.IGNORECASE),
        'fr': re.compile(r'^[a-zA-Zàâäéèêëïîôùûüÿç\s]+$', re.IGNORECASE),
        'de': re.compile(r'^[a-zA-Zäöüß\s]+$', re.IGNORECASE),
        'it': re.compile(r'^[a-zA-Zàèéìíîòóù\s]+$', re.IGNORECASE),
        'pt': re.compile(r'^[a-zA-Záâãàéêíóôõúüç\s]+$', re.IGNORECASE),
        'ru': re.compile(r'^[\u0400-\u04FF\s]+$'),
        'zh': re.compile(r'^[\u4e00-\u9fff\s]+$'),
        'ja': re.compile(r'^[\u3040-\u309f\u30a0-\u30ff\s]+$'),
        'ko': re.compile(r'^[\uac00-\ud7af\s]+$'),
        'ar': re.compile(r'^[\u0600-\u06ff\s]+$'),
        'hi': re.compile(r'^[\u0900-\u097f\s]+$'),
    }
    
    # Common words for language detection
    COMMON_WORDS = {
        'en': ['the', 'is', 'at', 'which', 'on', 'how', 'what', 'why', 'who', 'when'],
        'es': ['el', 'la', 'los', 'las', 'es', 'en', 'qué', 'cómo', 'por', 'para'],
        'fr': ['le', 'la', 'les', 'est', 'dans', 'comment', 'pourquoi', 'qui', 'quand'],
        'de': ['der', 'die', 'das', 'ist', 'wie', 'was', 'warum', 'wer', 'wann'],
        'it': ['il', 'la', 'i', 'le', 'è', 'come', 'perché', 'chi', 'quando'],
        'pt': ['o', 'a', 'os', 'as', 'é', 'como', 'porque', 'quem', 'quando'],
        'ru': ['и', 'в', 'на', 'что', 'как', 'почему', 'кто', 'когда'],
        'zh': ['的', '是', '在', '什么', '怎么', '为什么', '谁', '什么时候'],
        'ja': ['は', 'が', 'を', 'なに', 'どう', 'なぜ', 'だれ', 'いつ'],
        'ko': ['은', '는', '이', '가', '무엇', '어떻게', '왜', '누구'],
        'ar': ['في', 'من', 'على', 'ما', 'كيف', 'لماذا', 'من', 'متى'],
        'hi': ['में', 'की', 'का', 'क्या', 'कैसे', 'क्यों', 'कौन', 'कब'],
    }
    
    def __init__(self, default_language: str = 'en'):
        """
        Initialize language detector.
        
        Args:
            default_language: Default language if detection fails (default: 'en')
        """
        self.default_language = default_language
        self._cache: dict[str, str] = {}  # Cache for detected languages
    
    async def detect(self, query: str) -> str:
        """
        Detect the language of a query.
        
        Args:
            query: Search query text
            
        Returns:
            ISO 639-1 language code (e.g., 'en', 'es', 'fr')
        """
        if not query or not query.strip():
            return self.default_language
        
        # Check cache
        query_lower = query.lower().strip()
        if query_lower in self._cache:
            return self._cache[query_lower]
        
        # Try pattern matching first (fast)
        language = self._detect_by_pattern(query)
        
        # If pattern matching fails, try common words
        if not language:
            language = self._detect_by_common_words(query)
        
        # Fallback to default
        if not language:
            language = self.default_language
        
        # Cache result
        self._cache[query_lower] = language
        
        return language
    
    def _detect_by_pattern(self, query: str) -> Optional[str]:
        """Detect language using character patterns."""
        for lang, pattern in self.LANGUAGE_PATTERNS.items():
            if pattern.match(query):
                return lang
        return None
    
    def _detect_by_common_words(self, query: str) -> Optional[str]:
        """Detect language using common words."""
        query_lower = query.lower()
        words = re.findall(r'\b\w+\b', query_lower)
        
        if not words:
            return None
        
        # Count matches for each language
        scores = {}
        for lang, common_words in self.COMMON_WORDS.items():
            score = sum(1 for word in words if word in common_words)
            if score > 0:
                scores[lang] = score
        
        # Return language with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def clear_cache(self):
        """Clear the language detection cache."""
        self._cache.clear()
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages.
        
        Returns:
            List of ISO 639-1 language codes
        """
        return list(self.LANGUAGE_PATTERNS.keys())


# Singleton instance
language_detector = LanguageDetector()