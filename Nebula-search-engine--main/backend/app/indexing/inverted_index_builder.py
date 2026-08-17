"""Build and maintain inverted index from documents."""

import hashlib
import logging
import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

from app.config import get_settings

logger = logging.getLogger("nebula.indexing.inverted_index")

settings = get_settings()

# Stop words to filter out
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it",
    "its", "of", "on", "that", "the", "to", "was", "were", "will", "with", "the", "this", "but",
    "they", "have", "had", "what", "when", "where", "who", "which", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just", "should", "now",
}


class InvertedIndexBuilder:
    """Build inverted index from documents."""

    def __init__(self):
        self._index: Dict[str, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))
        self._documents: Dict[int, Dict] = {}
        self._term_frequencies: Dict[int, Counter] = {}
        self._document_lengths: Dict[int, int] = {}
        self._vocabulary: Set[str] = set()
        self._total_terms = 0

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-z0-9]+\b', text)
        
        # Remove stop words and short words
        tokens = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        
        return tokens

    def add_document(self, doc_id: int, title: str, content: str, metadata: Dict = None) -> None:
        """
        Add a document to the index.
        
        Args:
            doc_id: Document ID
            title: Document title
            content: Document content
            metadata: Optional metadata
        """
        # Combine title and content with title weighted more
        title_tokens = self.tokenize(title) * 3  # Triple weight for title
        content_tokens = self.tokenize(content)
        all_tokens = title_tokens + content_tokens
        
        # Store document
        self._documents[doc_id] = {
            "id": doc_id,
            "title": title,
            "content": content,
            "metadata": metadata or {},
            "word_count": len(all_tokens),
        }
        
        # Store term frequencies
        self._term_frequencies[doc_id] = Counter(all_tokens)
        self._document_lengths[doc_id] = len(all_tokens)
        self._total_terms += len(all_tokens)
        
        # Build inverted index
        for position, token in enumerate(all_tokens):
            self._vocabulary.add(token)
            self._index[token][doc_id].append(position)

    def remove_document(self, doc_id: int) -> None:
        """Remove a document from the index."""
        if doc_id not in self._documents:
            return
        
        # Remove from inverted index
        for token in list(self._index.keys()):
            if doc_id in self._index[token]:
                del self._index[token][doc_id]
        
        # Clean up empty entries
        self._index = {k: v for k, v in self._index.items() if v}
        
        # Update stats
        doc = self._documents[doc_id]
        self._total_terms -= self._document_lengths.get(doc_id, 0)
        
        del self._documents[doc_id]
        del self._term_frequencies[doc_id]
        del self._document_lengths[doc_id]

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search the inverted index.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_id, score) tuples
        """
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []
        
        # Calculate BM25 scores
        scores = defaultdict(float)
        total_docs = len(self._documents)
        avg_doc_length = self._total_terms / total_docs if total_docs > 0 else 0
        
        k1 = 1.2
        b = 0.75
        
        for token in query_tokens:
            if token not in self._index:
                continue
            
            # IDF
            docs_with_token = len(self._index[token])
            idf = math.log((total_docs - docs_with_token + 0.5) / (docs_with_token + 0.5) + 1)
            
            # TF for each document
            for doc_id, positions in self._index[token].items():
                tf = len(positions)
                doc_length = self._document_lengths.get(doc_id, avg_doc_length)
                
                # BM25 formula
                tf_component = (tf * (k1 + 1)) / (
                    tf + k1 * (1 - b + b * doc_length / avg_doc_length)
                )
                
                scores[doc_id] += idf * tf_component
        
        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def get_document(self, doc_id: int) -> Dict:
        """Get document by ID."""
        return self._documents.get(doc_id)

    def get_term_frequency(self, doc_id: int, term: str) -> int:
        """Get term frequency for a document."""
        return self._term_frequencies.get(doc_id, {}).get(term, 0)

    def get_corpus_stats(self) -> Dict:
        """Get corpus statistics."""
        return {
            "total_documents": len(self._documents),
            "total_terms": self._total_terms,
            "vocabulary_size": len(self._vocabulary),
            "avg_document_length": self._total_terms / len(self._documents) if self._documents else 0,
        }

    def get_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """
        Get autocomplete suggestions from vocabulary.
        
        Args:
            prefix: Prefix to search for
            limit: Maximum suggestions
            
        Returns:
            List of suggestions
        """
        prefix = prefix.lower()
        suggestions = [word for word in self._vocabulary if word.startswith(prefix)]
        return sorted(suggestions)[:limit]

    def get_expanded_query(self, query: str) -> List[str]:
        """
        Get expanded query with synonyms.
        
        Args:
            query: Original query
            
        Returns:
            Expanded query terms
        """
        tokens = self.tokenize(query)
        expanded = set(tokens)
        
        # Add related terms from co-occurrence (simplified)
        for token in tokens:
            if token in self._index:
                # Find documents containing this token
                docs = list(self._index[token].keys())
                # Find other tokens that appear in same documents
                for doc_id in docs[:10]:  # Limit to first 10 docs
                    doc_tf = self._term_frequencies.get(doc_id, {})
                    for term, freq in doc_tf.most_common(5):
                        if term != token and term not in STOP_WORDS:
                            expanded.add(term)
        
        return list(expanded)


# Global instance
inverted_index_builder = InvertedIndexBuilder()