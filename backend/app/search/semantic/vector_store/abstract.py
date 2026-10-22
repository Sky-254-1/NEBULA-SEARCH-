"""
Abstract Vector Store Base Class

Defines the interface that all vector store implementations must follow.
This enables pluggable vector database backends.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """
    Abstract base class for vector stores.
    
    All vector database implementations must inherit from this class
    and implement all abstract methods.
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize vector store.
        
        Args:
            connection_string: Database connection string
            **kwargs: Additional configuration options
        """
        self.connection_string = connection_string
        self.config = kwargs
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to vector database.
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to vector database."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if vector database is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        metric: str = "cosine",
        **kwargs
    ) -> None:
        """
        Create a new collection/index for vectors.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension (e.g., 1536 for OpenAI embeddings)
            metric: Distance metric ("cosine", "euclidean", "dot_product")
            **kwargs: Additional collection configuration
            
        Raises:
            CollectionExistsError: If collection already exists
        """
        pass
    
    @abstractmethod
    async def drop_collection(self, collection_name: str) -> None:
        """
        Delete a collection and all its vectors.
        
        Args:
            collection_name: Name of the collection to delete
        """
        pass
    
    @abstractmethod
    async def list_collections(self) -> list[str]:
        """
        List all collections.
        
        Returns:
            List of collection names
        """
        pass
    
    @abstractmethod
    async def upsert(
        self,
        collection_name: str,
        vectors: list[dict],
    ) -> list[str]:
        """
        Insert or update vectors in the collection.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector dictionaries with keys:
                - id: Unique vector ID
                - vector: List of floats
                - metadata: Optional metadata dictionary
                - document_id: Optional document ID reference
            
        Returns:
            List of inserted/updated vector IDs
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 10,
        filter: Optional[dict] = None,
        threshold: float = 0.0,
    ) -> list[dict]:
        """
        Search for similar vectors.
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector (list of floats)
            top_k: Number of results to return
            filter: Optional metadata filter
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of search results with keys:
                - id: Vector ID
                - score: Similarity score
                - metadata: Vector metadata
                - document_id: Associated document ID
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        collection_name: str,
        vector_ids: list[str],
    ) -> int:
        """
        Delete vectors by ID.
        
        Args:
            collection_name: Name of the collection
            vector_ids: List of vector IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        pass
    
    @abstractmethod
    async def delete_by_filter(
        self,
        collection_name: str,
        filter: dict,
    ) -> int:
        """
        Delete vectors matching a filter.
        
        Args:
            collection_name: Name of the collection
            filter: Metadata filter
            
        Returns:
            Number of vectors deleted
        """
        pass
    
    @abstractmethod
    async def get_vector(
        self,
        collection_name: str,
        vector_id: str,
    ) -> Optional[dict]:
        """
        Get a specific vector by ID.
        
        Args:
            collection_name: Name of the collection
            vector_id: Vector ID
            
        Returns:
            Vector dictionary or None if not found
        """
        pass
    
    @abstractmethod
    async def count(self, collection_name: str, filter: Optional[dict] = None) -> int:
        """
        Count vectors in collection.
        
        Args:
            collection_name: Name of the collection
            filter: Optional metadata filter
            
        Returns:
            Number of vectors
        """
        pass
    
    @abstractmethod
    async def update_metadata(
        self,
        collection_name: str,
        vector_id: str,
        metadata: dict,
    ) -> None:
        """
        Update vector metadata.
        
        Args:
            collection_name: Name of the collection
            vector_id: Vector ID
            metadata: New metadata dictionary
        """
        pass
    
    @abstractmethod
    async def batch_upsert(
        self,
        collection_name: str,
        vectors: list[dict],
        batch_size: int = 100,
    ) -> list[str]:
        """
        Insert or update vectors in batches.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector dictionaries
            batch_size: Number of vectors per batch
            
        Returns:
            List of all inserted/updated vector IDs
        """
        pass
    
    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> dict:
        """
        Get collection information.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection info (size, dimension, etc.)
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        return False