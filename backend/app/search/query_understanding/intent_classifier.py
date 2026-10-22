"""
Intent Classification Module

Classifies search query intent to improve results:
- Informational queries
- Navigational queries
- Transactional queries
- Local queries
- News queries
- Shopping queries
"""

import logging
import re

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies search query intent.
    
    Uses pattern matching and keyword detection.
    """
    
    # Intent patterns
    INTENT_PATTERNS = {
        'informational': {
            'patterns': [
                r'\b(?:how|what|why|when|where|who|which|explain|define|meaning|tutorial|guide|learn|understand)\b',
                r'\b(?:is|are|was|were|does|do|did|can|could|would|should)\b.*\?',
            ],
            'keywords': {
                'how to', 'what is', 'why does', 'when did', 'where is', 'who is',
                'explain', 'definition', 'meaning', 'tutorial', 'guide', 'learn',
                'understand', 'examples', 'difference between', 'compare',
            },
            'weight': 1.0,
        },
        'navigational': {
            'patterns': [
                r'\b(?:login|sign in|log in|access|open|go to|navigate|website|site|page|portal|dashboard)\b',
            ],
            'keywords': {
                'login', 'sign in', 'log in', 'access', 'open', 'go to',
                'navigate', 'website', 'site', 'page', 'portal', 'dashboard',
                'homepage', 'app', 'application',
            },
            'weight': 1.0,
        },
        'transactional': {
            'patterns': [
                r'\b(?:buy|purchase|order|book|reserve|subscribe|download|install|register|sign up|create account)\b',
                r'\b(?:price|cost|cheap|expensive|discount|deal|offer|sale|free)\b',
            ],
            'keywords': {
                'buy', 'purchase', 'order', 'book', 'reserve', 'subscribe',
                'download', 'install', 'register', 'sign up', 'create account',
                'price', 'cost', 'cheap', 'expensive', 'discount', 'deal',
                'offer', 'sale', 'free', 'payment', 'checkout', 'cart',
            },
            'weight': 1.0,
        },
        'local': {
            'patterns': [
                r'\b(?:near|nearby|close to|around|in my area|local|nearest|closest)\b',
                r'\b(?:restaurant|cafe|store|shop|gas station|bank|atm|hospital|pharmacy|hotel)\b.*\b(?:near|nearby|close)\b',
            ],
            'keywords': {
                'near', 'nearby', 'close to', 'around', 'in my area', 'local',
                'nearest', 'closest', 'restaurant', 'cafe', 'store', 'shop',
                'gas station', 'bank', 'atm', 'hospital', 'pharmacy', 'hotel',
                'directions', 'map', 'location', 'address',
            },
            'weight': 1.0,
        },
        'news': {
            'patterns': [
                r'\b(?:news|latest|breaking|update|current|today|yesterday|this week|this month)\b',
                r'\b(?:headlines|articles|stories|reports|announcement)\b',
            ],
            'keywords': {
                'news', 'latest', 'breaking', 'update', 'current', 'today',
                'yesterday', 'this week', 'this month', 'headlines', 'articles',
                'stories', 'reports', 'announcement', 'press release',
            },
            'weight': 1.0,
        },
        'shopping': {
            'patterns': [
                r'\b(?:best|top|review|compare|vs|versus|alternative|recommendation)\b.*\b(?:product|service|tool|software|app)\b',
                r'\b(?:product|service|tool|software|app)\b.*\b(?:review|comparison|alternative|best|top)\b',
            ],
            'keywords': {
                'best', 'top', 'review', 'compare', 'vs', 'versus', 'alternative',
                'recommendation', 'product', 'service', 'tool', 'software', 'app',
                'laptop', 'phone', 'camera', 'headphones', 'watch', 'gadget',
            },
            'weight': 1.0,
        },
    }
    
    def __init__(self, language: str = 'en'):
        """
        Initialize intent classifier.
        
        Args:
            language: Language code (default: 'en')
        """
        self.language = language
        self._cache: dict = {}
    
    async def classify(self, query: str) -> dict:
        """
        Classify query intent.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with intent classification and confidence
        """
        if not query:
            return {
                'intent': 'informational',
                'confidence': 0.0,
                'all_scores': {},
            }
        
        # Check cache
        query_lower = query.lower().strip()
        if query_lower in self._cache:
            return self._cache[query_lower]
        
        # Calculate scores for each intent
        scores = {}
        for intent_name, intent_config in self.INTENT_PATTERNS.items():
            score = self._calculate_intent_score(query, intent_config)
            scores[intent_name] = score
        
        # Get intent with highest score
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = scores[best_intent]
        else:
            best_intent = 'informational'
            confidence = 0.0
        
        result = {
            'intent': best_intent,
            'confidence': confidence,
            'all_scores': scores,
        }
        
        # Cache result
        self._cache[query_lower] = result
        
        return result
    
    def _calculate_intent_score(self, query: str, intent_config: dict) -> float:
        """
        Calculate intent score for a query.
        
        Args:
            query: Search query
            intent_config: Intent configuration with patterns and keywords
            
        Returns:
            Score between 0.0 and 1.0
        """
        query_lower = query.lower()
        score = 0.0
        
        # Check pattern matches
        for pattern in intent_config.get('patterns', []):
            if re.search(pattern, query_lower):
                score += 0.3
        
        # Check keyword matches
        keywords = intent_config.get('keywords', set())
        query_words = set(query_lower.split())
        keyword_matches = query_words.intersection(keywords)
        
        if keyword_matches:
            # Score based on percentage of query that matches keywords
            match_ratio = len(keyword_matches) / len(query_words) if query_words else 0
            score += match_ratio * 0.7
        
        # Normalize score
        score = min(score, 1.0)
        
        return score
    
    async def get_intent_boost(self, intent: str, result: dict) -> float:
        """
        Get boost factor for search results based on intent.
        
        Args:
            intent: Classified intent
            result: Search result
            
        Returns:
            Boost factor (1.0 = no boost, >1.0 = boost, <1.0 = demote)
        """
        # Default boost
        boost = 1.0
        
        # Intent-specific boosts
        if intent == 'transactional':
            # Boost results with purchase-related content
            result_text = result.get('title', '') + ' ' + result.get('snippet', '')
            if any(word in result_text.lower() for word in ['buy', 'purchase', 'price', 'order']):
                boost = 1.2
        
        elif intent == 'informational':
            # Boost results with informative content
            result_text = result.get('title', '') + ' ' + result.get('snippet', '')
            if any(word in result_text.lower() for word in ['tutorial', 'guide', 'learn', 'explain']):
                boost = 1.2
        
        elif intent == 'local':
            # Boost results with location data
            if result.get('location') or result.get('address'):
                boost = 1.3
        
        elif intent == 'news':
            # Boost recent results
            if result.get('published_at'):
                boost = 1.2
        
        return boost
    
    def clear_cache(self):
        """Clear classification cache."""
        self._cache.clear()


# Singleton instance
intent_classifier = IntentClassifier()