"""
Query Intent Detection

Classifies queries by intent to dynamically adjust search parameters.
"""

import logging
import re
from typing import Any, Dict

logger = logging.getLogger("nebula.hybrid.intent")


class IntentDetector:
    """
    Detect query intent to optimize search strategy.
    
    Intent types:
    - keyword: Short, specific terms (product names, codes)
    - question: Questions starting with who, what, where, when, why, how
    - natural_language: Conversational queries
    - phrase: Exact phrases in quotes
    - code: Programming-related queries
    - document: Document/file search
    - mixed: Combination of above
    """

    def __init__(self):
        """Initialize intent detector"""
        # Patterns for different intents
        self.question_patterns = [
            r"^(who|what|where|when|why|how)\s",
            r"\?$",
            r"(can you|could you|please|explain|describe|tell me)",
        ]
        
        self.code_patterns = [
            r"(function|class|def|import|from|const|var|let|if|else|for|while)",
            r"(python|javascript|java|cpp|c\+\+|typescript|react|vue|angular)",
            r"(api|endpoint|method|variable|array|object|string|integer)",
            r"(```|`[a-z]+`|\.py|\.js|\.ts|\.java)",
        ]
        
        self.document_patterns = [
            r"(file|document|pdf|doc|txt|presentation|spreadsheet)",
            r"(upload|download|attachment|import|export)",
            r"(find|search).*(file|document|pdf)",
        ]
        
        self.phrase_pattern = r'"[^"]+"'
        
        # Stop words for keyword detection
        self.stop_words = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        }

    def detect(self, query: str) -> Dict[str, Any]:
        """
        Detect query intent.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with intent classification and confidence
        """
        query = query.strip()
        query_lower = query.lower()
        
        if not query:
            return {
                "intent": "natural_language",
                "confidence": 0.5,
                "scores": {},
            }
        
        # Calculate scores for each intent
        scores = {
            "keyword": self._score_keyword(query_lower),
            "question": self._score_question(query_lower),
            "natural_language": self._score_natural_language(query_lower),
            "phrase": self._score_phrase(query_lower),
            "code": self._score_code(query_lower),
            "document": self._score_document(query_lower),
        }
        
        # Get the intent with highest score
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # Calculate confidence (how much this intent dominates)
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.5
        
        # Normalize scores to probabilities
        score_sum = sum(scores.values())
        if score_sum > 0:
            scores = {k: v / score_sum for k, v in scores.items()}
        
        return {
            "intent": max_intent,
            "confidence": min(1.0, confidence),
            "scores": scores,
            "query_length": len(query.split()),
            "is_phrase": bool(re.search(self.phrase_pattern, query)),
        }

    def _score_keyword(self, query: str) -> float:
        """Score for keyword lookup intent"""
        words = query.split()
        
        # Short queries (1-3 words) are more likely to be keyword searches
        if len(words) <= 3:
            # Check if it's mostly stop words
            stop_word_count = sum(1 for w in words if w in self.stop_words)
            if stop_word_count == 0:
                return 1.0
            elif stop_word_count == 1:
                return 0.7
            else:
                return 0.4
        
        # Longer queries are less likely to be pure keyword
        return 0.2

    def _score_question(self, query: str) -> float:
        """Score for question intent"""
        score = 0.0
        
        # Check for question patterns
        for pattern in self.question_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.5
        
        # Ends with question mark
        if query.strip().endswith("?"):
            score += 0.5
        
        return min(1.0, score)

    def _score_natural_language(self, query: str) -> float:
        """Score for natural language intent"""
        words = query.split()
        
        # Longer queries are more likely natural language
        if len(words) > 5:
            return 0.8
        elif len(words) > 3:
            return 0.6
        else:
            return 0.3

    def _score_phrase(self, query: str) -> float:
        """Score for exact phrase search intent"""
        # Check for quoted phrases
        matches = re.findall(self.phrase_pattern, query)
        
        if matches:
            # Score based on whether the query is entirely quoted
            if len(matches) == 1 and matches[0] == query:
                return 1.0
            else:
                return 0.7
        
        return 0.0

    def _score_code(self, query: str) -> float:
        """Score for code search intent"""
        score = 0.0
        
        # Check for code patterns
        for pattern in self.code_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.3
        
        # Check for code blocks (backticks)
        if "`" in query:
            score += 0.4
        
        # Check for file extensions
        if re.search(r"\.\w{1,4}$", query):
            score += 0.3
        
        return min(1.0, score)

    def _score_document(self, query: str) -> float:
        """Score for document search intent"""
        score = 0.0
        
        # Check for document patterns
        for pattern in self.document_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.5
        
        return min(1.0, score)

    def get_search_strategy(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recommended search strategy based on intent.
        
        Args:
            intent_result: Result from detect()
            
        Returns:
            Recommended search parameters
        """
        intent = intent_result.get("intent", "natural_language")
        intent_result.get("confidence", 0.5)
        
        # Default strategy
        strategy = {
            "keyword_weight": 0.5,
            "semantic_weight": 0.5,
            "use_phrase_matching": True,
            "use_synonyms": True,
            "top_k_keyword": 50,
            "top_k_vector": 50,
            "expand_query": True,
        }
        
        # Adjust based on intent
        if intent == "keyword":
            strategy.update({
                "keyword_weight": 0.8,
                "semantic_weight": 0.2,
                "use_phrase_matching": True,
                "expand_query": False,
            })
        elif intent == "question":
            strategy.update({
                "keyword_weight": 0.3,
                "semantic_weight": 0.7,
                "use_phrase_matching": False,
                "expand_query": True,
            })
        elif intent == "natural_language":
            strategy.update({
                "keyword_weight": 0.4,
                "semantic_weight": 0.6,
                "use_phrase_matching": False,
                "expand_query": True,
            })
        elif intent == "phrase":
            strategy.update({
                "keyword_weight": 0.7,
                "semantic_weight": 0.3,
                "use_phrase_matching": True,
                "expand_query": False,
            })
        elif intent == "code":
            strategy.update({
                "keyword_weight": 0.6,
                "semantic_weight": 0.4,
                "use_phrase_matching": True,
                "expand_query": False,
            })
        elif intent == "document":
            strategy.update({
                "keyword_weight": 0.5,
                "semantic_weight": 0.5,
                "use_phrase_matching": True,
                "expand_query": True,
            })
        
        return strategy

    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            "keyword": "Keyword/Exact term search",
            "question": "Question/Informational query",
            "natural_language": "Natural language search",
            "phrase": "Exact phrase search",
            "code": "Code/programming query",
            "document": "Document/file search",
            "mixed": "Mixed intent search",
        }
        return descriptions.get(intent, "Unknown intent")