"""
Semantic Search Engine

Orchestrates semantic search using embeddings and vector stores:
- Embedding generation
- Vector storage and retrieval
- Semantic reranking
- Hybrid search combination
"""

import logging
from typing import Optional
import numpy as np

from .embeddings import (
    OpenAIEmbeddingProvider,
    CohereEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
    OllamaEmbeddingProvider,
)
from .vector_store import (
    VectorStore,
    PGVectorStore,
    QdrantStore,
    MilvusStore,
    ElasticsearchVectorStore,
)

logger = logging.getLogger(__name__)


class SemanticEngine:
    """
    Semantic search engine using vector embeddings.
    
    Provides:
    - Document indexing with embeddings
    - Semantic search
    - Semantic reranking of results
    - Multiple embedding and vector store providers
    """
    
    def __init__(
        self,
        embedding_provider: Optional[str] = None,
        vector_store: Optional[VectorStore] = None,
        **kwargs
    ):
        """
        Initialize semantic engine.
        
        Args:
            embedding_provider: Embedding provider name ('openai', 'cohere', 'huggingface', 'ollama')
            vector_store: Vector store instance (if None, uses PGVector by default)
            **kwargs: Additional configuration
        """
        self.config = kwargs
        self._embedding_provider = None
        self._vector_store = vector_store
        self._cache = {}
        self._vector_store_backend = kwargs.get("vector_store_backend") or "local"

        # Initialize embedding provider
        if embedding_provider:
            self._initialize_embedding_provider(embedding_provider, **kwargs)
    
    def _initialize_embedding_provider(self, provider_name: str, **kwargs):
        """
        Initialize embedding provider.
        
        Args:
            provider_name: Provider name
            **kwargs: Provider configuration
        """
        api_key = kwargs.get('api_key')
        model_name = kwargs.get('model_name')
        
        provider_config = {
            'api_key': api_key,
            'model_name': model_name,
        }
        
        if provider_name == 'openai':
            self._embedding_provider = OpenAIEmbeddingProvider(**provider_config)
        elif provider_name == 'cohere':
            self._embedding_provider = CohereEmbeddingProvider(**provider_config)
        elif provider_name == 'huggingface':
            self._embedding_provider = HuggingFaceEmbeddingProvider(**provider_config)
        elif provider_name == 'ollama':
            self._embedding_provider = OllamaEmbeddingProvider(**provider_config)
        else:
            raise ValueError(f"Unknown embedding provider: {provider_name}")
        
        logger.info(f"Initialized embedding provider: {provider_name}")
    
    async def ensure_vector_store(self) -> VectorStore:
        """
        Ensure vector store is initialized.
        
        Returns:
            Vector store instance
        """
        if self._vector_store:
            return self._vector_store

        backend = self._vector_store_backend
        connection_string = self.config.get("database_url", "")
        
        if backend == "pgvector":
            self._vector_store = PGVectorStore(connection_string)
        elif backend == "qdrant":
            self._vector_store = QdrantStore(connection_string)
        elif backend == "milvus":
            self._vector_store = MilvusStore(connection_string)
        elif backend == "elasticsearch":
            self._vector_store = ElasticsearchVectorStore(connection_string)
        else:
            raise ValueError(
                f"Unsupported vector store backend: {backend}. "
                "Use 'local' for file-based vectors (handled by vector/pipeline) "
                "or configure 'pgvector'/'qdrant'/'milvus'."
            )
        
        await self._vector_store.connect()
        logger.info("SemanticEngine vector store initialized: %s", backend)
        return self._vector_store
    
    async def index_documents(self, documents: list[dict]) -> list[str]:
        """
        Index documents with embeddings.
        
        Args:
            documents: List of document dictionaries with keys:
                - id: Document ID
                - content: Document content
                - metadata: Optional metadata
                
        Returns:
            List of indexed document IDs
        """
        if not documents:
            return []
        
        # Ensure vector store
        vector_store = await self.ensure_vector_store()
        
        # Ensure embedding provider
        if not self._embedding_provider:
            raise ValueError("Embedding provider not initialized")
        
        # Extract texts
        texts = [doc.get('content', '') for doc in documents]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents")
        embeddings = await self._embedding_provider.generate_embeddings(texts)
        
        # Prepare vectors for storage
        vectors = []
        for doc, embedding in zip(documents, embeddings):
            if not embedding:
                logger.warning(f"Empty embedding for document {doc.get('id')}")
                continue
            
            vector_id = f"doc_{doc['id']}"
            vectors.append({
                'id': vector_id,
                'vector': embedding,
                'metadata': doc.get('metadata', {}),
                'document_id': doc.get('id'),
            })
        
        # Store vectors
        if vectors:
            collection_name = self.config.get('collection_name', 'documents')
            await vector_store.upsert(collection_name, vectors)
            logger.info(f"Indexed {len(vectors)} documents")
        
        return [doc.get('id') for doc in documents]
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results
            threshold: Minimum similarity threshold
            filter: Optional metadata filter
            
        Returns:
            List of search results
        """
        if not query:
            return []
        
        # Check cache
        cache_key = (query, top_k, threshold, str(filter))
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Ensure vector store
        vector_store = await self.ensure_vector_store()
        
        # Ensure embedding provider
        if not self._embedding_provider:
            raise ValueError("Embedding provider not initialized")
        
        # Generate query embedding
        query_embedding = await self._embedding_provider.generate_embedding(query)
        
        if not query_embedding:
            logger.warning("Empty query embedding")
            return []
        
        # Search vector store
        collection_name = self.config.get('collection_name', 'documents')
        results = await vector_store.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            top_k=top_k,
            filter=filter,
            threshold=threshold,
        )
        
        # Cache results
        self._cache[cache_key] = results
        
        return results
    
    async def rerank(
        self,
        query: str,
        documents: list[dict],
        alpha: float = 0.3,
    ) -> list[dict]:
        """
        Rerank documents using semantic similarity.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            alpha: Weight for semantic score (0.0 to 1.0)
                  1.0 = pure semantic, 0.0 = pure keyword
                  
        Returns:
            Reranked list of documents
        """
        if not documents or not query:
            return documents
        
        # Ensure embedding provider
        if not self._embedding_provider:
            logger.warning("No embedding provider, returning original order")
            return documents
        
        try:
            # Generate query embedding
            query_embedding = await self._embedding_provider.generate_embedding(query)
            
            if not query_embedding:
                return documents
            
            # Generate embeddings for documents
            doc_texts = [doc.get('title', '') + ' ' + doc.get('snippet', '') for doc in documents]
            doc_embeddings = await self._embedding_provider.generate_embeddings(doc_texts)
            
            # Calculate similarity scores
            scored_docs = []
            for doc, doc_embedding in zip(documents, doc_embeddings):
                if not doc_embedding:
                    semantic_score = 0.0
                else:
                    # Calculate cosine similarity
                    semantic_score = self._cosine_similarity(query_embedding, doc_embedding)
                
                # Get existing score (keyword score)
                keyword_score = doc.get('score', 0.5)
                
                # Combine scores
                combined_score = (alpha * semantic_score) + ((1 - alpha) * keyword_score)
                
                # Add scores to document
                doc_copy = doc.copy()
                doc_copy['semantic_score'] = semantic_score
                doc_copy['keyword_score'] = keyword_score
                doc_copy['combined_score'] = combined_score
                
                scored_docs.append(doc_copy)
            
            # Sort by combined score
            scored_docs.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return scored_docs
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return documents
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        
        # Normalize to 0-1 range
        return (similarity + 1.0) / 2.0
    
    async def get_embedding(self, text: str) -> list[float]:
        """
        Get embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if not self._embedding_provider:
            raise ValueError("Embedding provider not initialized")
        
        return await self._embedding_provider.generate_embedding(text)
    
    async def health_check(self) -> dict:
        """
        Check health of semantic engine.
        
        Returns:
            Health status dictionary
        """
        status = {
            'embedding_provider': False,
            'vector_store': False,
        }
        
        # Check embedding provider
        if self._embedding_provider:
            status['embedding_provider'] = await self._embedding_provider.health_check()
        
        # Check vector store
        if self._vector_store:
            status['vector_store'] = await self._vector_store.health_check()
        
        return status
    
    def clear_cache(self):
        """Clear search cache."""
        self._cache.clear()


# Singleton instance
semantic_engine = SemanticEngine()