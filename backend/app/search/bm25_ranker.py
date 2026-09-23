"""BM25 ranking algorithm for text search."""

import logging
import math
from collections import Counter
from typing import List, Dict, Any

logger = logging.getLogger("nebula.search.bm25")


class BM25Ranker:
    """BM25 probabilistic ranking algorithm."""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        Initialize BM25 ranker.
        
        Args:
            k1: Term frequency saturation parameter (typical: 1.2)
            b: Length normalization parameter (typical: 0.75)
        """
        self.k1 = k1
        self.b = b
        self._corpus_stats = None
        self._document_stats = {}
    
    async def initialize(self, db):
        """Load corpus statistics from database."""
        # This would load from corpus_stats table
        # For now, use defaults
        self._corpus_stats = {
            "total_documents": 1000,
            "avg_document_length": 500,
            "total_terms": 500000,
        }
    
    def rank(
        self,
        query_terms: List[str],
        documents: List[Dict[str, Any]],
        term_frequencies: Dict[int, Dict[str, int]],
        document_lengths: Dict[int, int],
    ) -> List[Dict[str, Any]]:
        """
        Rank documents using BM25 algorithm.
        
        Args:
            query_terms: List of query terms
            documents: List of documents
            term_frequencies: {doc_id: {term: frequency}}
            document_lengths: {doc_id: length}
            
        Returns:
            Ranked list of documents with scores
        """
        if not self._corpus_stats or not documents:
            return documents
        
        total_docs = self._corpus_stats["total_documents"]
        avg_doc_length = self._corpus_stats["avg_document_length"]
        
        scored_docs = []
        
        for doc in documents:
            doc_id = doc.get("id")
            doc_length = document_lengths.get(doc_id, avg_doc_length)
            doc_tf = term_frequencies.get(doc_id, {})
            
            score = 0.0
            for term in query_terms:
                if term in doc_tf:
                    tf = doc_tf[term]
                    # IDF calculation
                    docs_with_term = sum(1 for doc_tf_map in term_frequencies.values() if term in doc_tf_map)
                    idf = math.log((total_docs - docs_with_term + 0.5) / (docs_with_term + 0.5) + 1)
                    
                    # TF component with saturation and length normalization
                    tf_component = (tf * (self.k1 + 1)) / (
                        tf + self.k1 * (1 - self.b + self.b * doc_length / avg_doc_length)
                    )
                    
                    score += idf * tf_component
            
            scored_doc = doc.copy()
            scored_doc["score"] = score
            scored_docs.append(scored_doc)
        
        # Sort by score descending
        scored_docs.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return scored_docs
    
    def rank_with_field_boosts(
        self,
        query_terms: List[str],
        documents: List[Dict[str, Any]],
        field_weights: Dict[str, float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank documents with field-specific boosts.
        
        Args:
            query_terms: List of query terms
            documents: List of documents
            field_weights: Weight for each field (e.g., {"title": 2.0, "content": 1.0})
            
        Returns:
            Ranked list of documents with scores
        """
        if field_weights is None:
            field_weights = {"title": 2.0, "content": 1.0, "headings": 1.5}
        
        # Extract term frequencies per field
        term_frequencies = {}
        document_lengths = {}
        
        for doc in documents:
            doc_id = doc.get("id")
            term_frequencies[doc_id] = {}
            doc_length = 0
            
            for field, weight in field_weights.items():
                field_text = doc.get(field, "")
                if field_text:
                    words = field_text.lower().split()
                    doc_length += len(words)
                    
                    for word in words:
                        if word not in term_frequencies[doc_id]:
                            term_frequencies[doc_id][word] = 0
                        term_frequencies[doc_id][word] += weight
            
            document_lengths[doc_id] = doc_length
        
        return self.rank(query_terms, documents, term_frequencies, document_lengths)


# Global ranker instance
bm25_ranker = BM25Ranker()