"""
BM25 Ranking Engine

Implements production-grade BM25 keyword ranking with:
- TF-IDF weighting
- Field-length normalization
- Multi-field search (title, content, headings, tags)
- Phrase matching support
"""

import logging
import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nebula.hybrid.bm25")


class BM25Engine:
    """
    BM25 ranking algorithm for keyword-based search.
    
    Features:
    - Standard BM25 implementation with configurable k1 and b parameters
    - Multi-field indexing (title, content, headings, tags)
    - Field-specific weight boosting
    - Phrase matching bonus
    - Stop word handling
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        field_weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize BM25 engine.
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
            field_weights: Custom weights for different fields
        """
        self.k1 = k1
        self.b = b
        self.field_weights = field_weights or {
            "title": 3.0,
            "headings": 2.0,
            "tags": 2.0,
            "content": 1.0,
            "snippet": 0.8,
        }
        
        # Index statistics
        self.doc_count = 0
        self.avg_doc_length = 0.0
        self.doc_freq = Counter()
        self.doc_lengths = {}
        self.field_doc_freq = defaultdict(Counter)
        self.field_doc_lengths = defaultdict(dict)
        
        # Stop words (basic set)
        self.stop_words = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their",
            "what", "so", "up", "out", "if", "about", "who", "get", "which",
            "go", "me", "when", "make", "can", "like", "time", "no", "just",
            "him", "know", "take", "people", "into", "year", "your", "good",
            "some", "could", "them", "see", "other", "than", "then", "now",
            "look", "only", "come", "its", "over", "think", "also", "back",
            "after", "use", "two", "how", "our", "work", "first", "well",
            "way", "even", "new", "want", "because", "any", "these", "give",
            "day", "most", "us", "is", "am", "are", "was", "were", "been",
            "being", "has", "had", "does", "did", "doing", "a", "an", "the",
            "and", "but", "if", "or", "because", "as", "until", "while",
            "of", "at", "by", "for", "with", "about", "against", "between",
            "into", "through", "during", "before", "after", "above", "below",
            "to", "from", "up", "down", "in", "out", "on", "off", "over",
            "under", "again", "further", "then", "once", "here", "there",
        }

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Index documents for BM25 scoring.
        
        Args:
            documents: List of documents to index
        """
        self.doc_count = len(documents)
        total_length = 0
        
        for doc in documents:
            doc_id = doc.get("id", "")
            
            # Index each field separately
            for field, weight in self.field_weights.items():
                text = self._extract_field_text(doc, field)
                terms = self._tokenize(text)
                doc_length = len(terms)
                
                # Track field-specific statistics
                self.field_doc_lengths[field][doc_id] = doc_length
                total_length += doc_length
                
                # Track document frequency for this field
                unique_terms = set(terms)
                for term in unique_terms:
                    self.field_doc_freq[field][term] += 1
                    self.doc_freq[term] += 1
            
            # Track total document length (sum of all fields)
            all_text = " ".join(
                self._extract_field_text(doc, field) for field in self.field_weights
            )
            all_terms = self._tokenize(all_text)
            self.doc_lengths[doc_id] = len(all_terms)
        
        # Calculate average document length
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0
        
        logger.debug(
            f"Indexed {self.doc_count} documents, "
            f"avg length: {self.avg_doc_length:.1f}, "
            f"vocabulary: {len(self.doc_freq)} terms"
        )

    def score(
        self,
        query: str,
        document: Dict[str, Any],
        phrase_match: bool = True,
    ) -> float:
        """
        Calculate BM25 score for a document.
        
        Args:
            query: Search query
            document: Document to score
            phrase_match: Whether to apply phrase matching bonus
            
        Returns:
            BM25 score (higher is better)
        """
        if self.doc_count == 0:
            return 0.0
        
        query_terms = self._tokenize(query.lower())
        if not query_terms:
            return 0.0
        
        # Calculate BM25 score per field
        total_score = 0.0
        
        for field, weight in self.field_weights.items():
            field_score = self._score_field(query_terms, document, field)
            total_score += weight * field_score
        
        # Apply phrase matching bonus
        if phrase_match and len(query_terms) > 1:
            phrase_bonus = self._calculate_phrase_bonus(query, document)
            total_score *= 1 + phrase_bonus
        
        return total_score

    def _score_field(
        self,
        query_terms: List[str],
        document: Dict[str, Any],
        field: str,
    ) -> float:
        """Calculate BM25 score for a specific field"""
        field_text = self._extract_field_text(document, field)
        doc_terms = self._tokenize(field_text.lower())
        doc_length = len(doc_terms)
        
        if doc_length == 0:
            return 0.0
        
        term_freq = Counter(doc_terms)
        field_avg_length = sum(self.field_doc_lengths[field].values()) / len(
            self.field_doc_lengths[field]
        ) if self.field_doc_lengths[field] else 1
        
        score = 0.0
        for term in query_terms:
            tf = term_freq.get(term, 0)
            df = self.field_doc_freq[field].get(term, 0)
            
            if tf == 0 or df == 0:
                continue
            
            # IDF component with smoothing
            idf = math.log(
                (self.doc_count - df + 0.5) / (df + 0.5) + 1.0
            )
            
            # Length normalization
            norm = 1 - self.b + self.b * (doc_length / field_avg_length)
            
            # BM25 formula
            score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * norm)
        
        return score

    def _calculate_phrase_bonus(self, query: str, document: Dict[str, Any]) -> float:
        """Calculate bonus for exact phrase matches"""
        query_lower = query.lower()
        
        # Check for phrase in title (highest bonus)
        title = document.get("title", "").lower()
        if query_lower in title:
            return 0.5
        
        # Check for phrase in content
        content = document.get("content", "").lower()
        if query_lower in content:
            return 0.3
        
        # Check for phrase in snippet
        snippet = document.get("snippet", "").lower()
        if query_lower in snippet:
            return 0.2
        
        return 0.0

    def _extract_field_text(self, document: Dict[str, Any], field: str) -> str:
        """Extract text from a document field"""
        if field == "headings":
            # Combine all headings
            headings = document.get("headings", [])
            if isinstance(headings, list):
                return " ".join(str(h) for h in headings)
            return str(headings)
        elif field == "tags":
            tags = document.get("tags", [])
            if isinstance(tags, list):
                return " ".join(str(t) for t in tags)
            return str(tags)
        elif field == "content":
            return document.get("content", "")
        elif field == "snippet":
            return document.get("snippet", "")
        elif field == "title":
            return document.get("title", "")
        return ""

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into terms.
        
        - Convert to lowercase
        - Remove punctuation
        - Remove stop words
        - Split on whitespace
        """
        if not text:
            return []
        
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        
        # Split into words
        words = text.split()
        
        # Remove stop words and empty strings
        terms = [w for w in words if w and w not in self.stop_words]
        
        return terms

    def get_term_frequencies(self, document: Dict[str, Any]) -> Dict[str, int]:
        """Get term frequencies for a document"""
        all_text = " ".join(
            self._extract_field_text(document, field) for field in self.field_weights
        )
        terms = self._tokenize(all_text.lower())
        return dict(Counter(terms))

    def get_statistics(self) -> Dict[str, Any]:
        """Get BM25 index statistics"""
        return {
            "doc_count": self.doc_count,
            "avg_doc_length": self.avg_doc_length,
            "vocabulary_size": len(self.doc_freq),
            "field_weights": self.field_weights,
            "k1": self.k1,
            "b": self.b,
        }