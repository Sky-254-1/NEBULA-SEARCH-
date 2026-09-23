"""
Semantic Vector Ranking Engine

Implements semantic search using dense vector embeddings:
- Cosine similarity
- Dot product similarity
- Configurable distance metrics
- Embedding caching
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("nebula.hybrid.semantic")


class SemanticEngine:
    """
    Semantic search engine using vector embeddings.
    
    Features:
    - Cosine similarity scoring
    - Dot product scoring
    - Configurable similarity metrics
    - Vector normalization
    - Top-k retrieval
    """

    def __init__(
        self,
        similarity_metric: str = "cosine",
        vector_dim: int = 384,
        normalize_vectors: bool = True,
    ):
        """
        Initialize semantic engine.
        
        Args:
            similarity_metric: Similarity metric (cosine, dot, euclidean)
            vector_dim: Expected vector dimension
            normalize_vectors: Whether to normalize vectors to unit length
        """
        self.similarity_metric = similarity_metric
        self.vector_dim = vector_dim
        self.normalize_vectors = normalize_vectors
        
        # Document vectors storage
        self.document_vectors: Dict[str, np.ndarray] = {}
        self.document_ids: List[str] = []

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Index documents with their vector embeddings.
        
        Args:
            documents: List of documents with embedding vectors
        """
        self.document_vectors = {}
        self.document_ids = []
        
        for doc in documents:
            doc_id = doc.get("id", "")
            embedding = doc.get("embedding")
            
            if embedding is not None:
                # Convert to numpy array
                if isinstance(embedding, list):
                    embedding = np.array(embedding, dtype=np.float32)
                
                # Validate dimension
                if len(embedding.shape) == 1 and embedding.shape[0] > 0:
                    # Normalize if configured
                    if self.normalize_vectors:
                        norm = np.linalg.norm(embedding)
                        if norm > 0:
                            embedding = embedding / norm
                    
                    self.document_vectors[doc_id] = embedding
                    self.document_ids.append(doc_id)
        
        logger.debug(
            f"Indexed {len(self.document_vectors)} document vectors, "
            f"dimension: {self.vector_dim}"
        )

    def score(
        self,
        query_vector: np.ndarray,
        document_vector: np.ndarray,
    ) -> float:
        """
        Calculate similarity score between query and document vectors.
        
        Args:
            query_vector: Query embedding vector
            document_vector: Document embedding vector
            
        Returns:
            Similarity score (0-1 for cosine, varies for others)
        """
        if self.similarity_metric == "cosine":
            return self._cosine_similarity(query_vector, document_vector)
        elif self.similarity_metric == "dot":
            return self._dot_product(query_vector, document_vector)
        elif self.similarity_metric == "euclidean":
            return self._euclidean_similarity(query_vector, document_vector)
        else:
            logger.warning(f"Unknown similarity metric: {self.similarity_metric}, using cosine")
            return self._cosine_similarity(query_vector, document_vector)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot / (norm1 * norm2))

    def _dot_product(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate dot product similarity"""
        if len(vec1) != len(vec2):
            return 0.0
        
        return float(np.dot(vec1, vec2))

    def _euclidean_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate euclidean distance-based similarity"""
        if len(vec1) != len(vec2):
            return 0.0
        
        distance = np.linalg.norm(vec1 - vec2)
        # Convert distance to similarity (inverse, normalized 0-1)
        # Assuming max distance of sqrt(2) for normalized vectors
        return 1 / (1 + distance)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 20,
        min_score: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """
        Search for top-k similar documents.
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            min_score: Minimum similarity threshold
            
        Returns:
            List of (document_id, score) tuples sorted by score
        """
        if not self.document_vectors:
            return []
        
        # Normalize query vector if configured
        if self.normalize_vectors:
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
        
        # Calculate scores for all documents
        scores = []
        for doc_id, doc_vector in self.document_vectors.items():
            score = self.score(query_vector, doc_vector)
            if score >= min_score:
                scores.append((doc_id, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        return scores[:top_k]

    def get_similarity_matrix(
        self,
        query_vectors: np.ndarray,
        document_vectors: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Calculate similarity matrix between queries and documents.
        
        Args:
            query_vectors: Query embeddings (n_queries x dim)
            document_vectors: Document embeddings (n_docs x dim), uses indexed if None
            
        Returns:
            Similarity matrix (n_queries x n_docs)
        """
        if document_vectors is None:
            # Use indexed vectors
            if not self.document_vectors:
                return np.array([[]])
            
            document_vectors = np.array(list(self.document_vectors.values()))
        
        # Normalize vectors if configured
        if self.normalize_vectors:
            query_norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
            query_norms[query_norms == 0] = 1
            query_vectors = query_vectors / query_norms
            
            doc_norms = np.linalg.norm(document_vectors, axis=1, keepdims=True)
            doc_norms[doc_norms == 0] = 1
            document_vectors = document_vectors / doc_norms
        
        # Calculate similarity matrix
        if self.similarity_metric == "cosine":
            similarity = np.dot(query_vectors, document_vectors.T)
        elif self.similarity_metric == "dot":
            similarity = np.dot(query_vectors, document_vectors.T)
        elif self.similarity_metric == "euclidean":
            # Calculate euclidean distances and convert to similarity
            distances = np.linalg.norm(
                query_vectors[:, np.newaxis] - document_vectors[np.newaxis, :],
                axis=2
            )
            similarity = 1 / (1 + distances)
        else:
            similarity = np.dot(query_vectors, document_vectors.T)
        
        return similarity

    def batch_score(
        self,
        query_vector: np.ndarray,
        document_ids: List[str],
    ) -> Dict[str, float]:
        """
        Score multiple documents against a query.
        
        Args:
            query_vector: Query embedding
            document_ids: List of document IDs to score
            
        Returns:
            Dictionary mapping document_id to score
        """
        scores = {}
        
        for doc_id in document_ids:
            if doc_id in self.document_vectors:
                score = self.score(query_vector, self.document_vectors[doc_id])
                scores[doc_id] = score
        
        return scores

    def get_statistics(self) -> Dict[str, Any]:
        """Get semantic engine statistics"""
        return {
            "indexed_documents": len(self.document_vectors),
            "vector_dimension": self.vector_dim,
            "similarity_metric": self.similarity_metric,
            "normalize_vectors": self.normalize_vectors,
        }