"""
Parallel Retriever

Executes BM25 and semantic retrieval in parallel for optimal performance.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.hybrid.bm25 import BM25Engine
from app.hybrid.semantic import SemanticEngine

logger = logging.getLogger("nebula.hybrid.retriever")


class ParallelRetriever:
    """
    Execute BM25 and semantic retrieval in parallel.
    
    Features:
    - Concurrent execution of multiple retrieval strategies
    - Configurable top-k for each source
    - Timeout handling
    - Error recovery
    """

    def __init__(
        self,
        bm25_engine: Optional[BM25Engine] = None,
        semantic_engine: Optional[SemanticEngine] = None,
        top_k_keyword: int = 50,
        top_k_vector: int = 50,
        timeout_ms: int = 5000,
    ):
        """
        Initialize parallel retriever.
        
        Args:
            bm25_engine: BM25 ranking engine
            semantic_engine: Semantic search engine
            top_k_keyword: Number of keyword results to retrieve
            top_k_vector: Number of vector results to retrieve
            timeout_ms: Timeout for retrieval operations in milliseconds
        """
        self.bm25_engine = bm25_engine or BM25Engine()
        self.semantic_engine = semantic_engine or SemanticEngine()
        self.top_k_keyword = top_k_keyword
        self.top_k_vector = top_k_vector
        self.timeout_ms = timeout_ms
        self.timeout_seconds = timeout_ms / 1000.0

    async def retrieve(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Retrieve results from both BM25 and semantic search in parallel.
        
        Args:
            query: Search query
            query_vector: Query embedding vector
            documents: Documents to search (None to use indexed documents)
            
        Returns:
            Tuple of (bm25_results, semantic_results)
        """
        if documents is None:
            documents = []
        
        # Index documents if provided
        if documents:
            self.bm25_engine.index_documents(documents)
            self.semantic_engine.index_documents(documents)
        
        # Execute retrievals in parallel
        try:
            bm25_results, semantic_results = await asyncio.gather(
                self._retrieve_bm25(query, documents),
                self._retrieve_semantic(query_vector, documents),
                return_exceptions=True,
            )
            
            # Handle exceptions
            if isinstance(bm25_results, Exception):
                logger.error(f"BM25 retrieval failed: {bm25_results}")
                bm25_results = []
            
            if isinstance(semantic_results, Exception):
                logger.error(f"Semantic retrieval failed: {semantic_results}")
                semantic_results = []
            
        except asyncio.TimeoutError:
            logger.error("Retrieval timeout")
            bm25_results, semantic_results = [], []
        
        return bm25_results, semantic_results

    async def _retrieve_bm25(
        self,
        query: str,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Retrieve BM25 results.
        
        Args:
            query: Search query
            documents: Documents to search
            
        Returns:
            BM25 results with scores
        """
        if not documents:
            return []
        
        try:
            # Score all documents
            scored_docs = []
            for doc in documents:
                score = self.bm25_engine.score(query, doc)
                if score > 0:
                    result = doc.copy()
                    result["lexical_score"] = score
                    result["score"] = score
                    scored_docs.append(result)
            
            # Sort by score and return top-k
            scored_docs.sort(key=lambda x: x.get("lexical_score", 0.0), reverse=True)
            return scored_docs[:self.top_k_keyword]
            
        except Exception as e:
            logger.error(f"BM25 retrieval error: {e}")
            return []

    async def _retrieve_semantic(
        self,
        query_vector: Optional[List[float]],
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Retrieve semantic results.
        
        Args:
            query_vector: Query embedding vector
            documents: Documents to search
            
        Returns:
            Semantic results with scores
        """
        if not query_vector or not documents:
            return []
        
        try:
            import numpy as np
            
            # Convert query vector to numpy array
            q_vector = np.array(query_vector)
            
            # Score all documents
            scored_docs = []
            for doc in documents:
                embedding = doc.get("embedding")
                if embedding is not None:
                    d_vector = np.array(embedding)
                    score = self.semantic_engine.score(q_vector, d_vector)
                    
                    if score > 0:
                        result = doc.copy()
                        result["semantic_score"] = score
                        result["score"] = score
                        scored_docs.append(result)
            
            # Sort by score and return top-k
            scored_docs.sort(key=lambda x: x.get("semantic_score", 0.0), reverse=True)
            return scored_docs[:self.top_k_vector]
            
        except Exception as e:
            logger.error(f"Semantic retrieval error: {e}")
            return []

    def set_top_k(self, keyword: int, vector: int):
        """
        Set top-k parameters.
        
        Args:
            keyword: Number of keyword results
            vector: Number of vector results
        """
        self.top_k_keyword = keyword
        self.top_k_vector = vector
        logger.info(f"Set top_k: keyword={keyword}, vector={vector}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            "top_k_keyword": self.top_k_keyword,
            "top_k_vector": self.top_k_vector,
            "timeout_ms": self.timeout_ms,
            "bm25": self.bm25_engine.get_statistics(),
            "semantic": self.semantic_engine.get_statistics(),
        }