"""
Qdrant Vector Store Implementation

Vector store using Qdrant - production-ready vector database.
"""

import logging
from typing import Optional

from .abstract import VectorStore

logger = logging.getLogger(__name__)


class QdrantStore(VectorStore):
    """
    Qdrant implementation of VectorStore.
    
    Requires:
    - Qdrant server running (local or cloud)
    - qdrant-client package
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize Qdrant store.
        
        Args:
            connection_string: Qdrant connection string (e.g., "http://localhost:6333")
            **kwargs: Additional options (api_key, collection_prefix, etc.)
        """
        super().__init__(connection_string, **kwargs)
        self.collection_prefix = kwargs.get('collection_prefix', 'nebula_')
        self._client = None
        
        # Lazy import to avoid dependency if not used
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            self.qdrant_client = QdrantClient
            self.qdrant_models = models
            self._qdrant_available = True
        except ImportError:
            logger.warning("qdrant-client not installed. Install with: pip install qdrant-client")
            self._qdrant_available = False
    
    async def connect(self) -> None:
        """Establish connection to Qdrant."""
        if not self._qdrant_available:
            raise ImportError("qdrant-client is not installed")
        
        try:
            self._client = self.qdrant_client(
                url=self.connection_string,
                api_key=self.config.get('api_key'),
            )
            self._connected = True
            logger.info(f"Connected to Qdrant at {self.connection_string}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Qdrant."""
        if self._client:
            self._client = None
            self._connected = False
            logger.info("Disconnected from Qdrant")
    
    async def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            if not self._client:
                return False
            
            # Try to get cluster info
            self._client.get_cluster_info()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def _get_collection_name(self, collection_name: str) -> str:
        """Get full collection name with prefix."""
        return f"{self.collection_prefix}{collection_name}"
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        metric: str = "cosine",
        **kwargs
    ) -> None:
        """
        Create a new collection in Qdrant.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            metric: Distance metric ("cosine", "euclidean", "dot")
            **kwargs: Additional options
        """
        full_name = self._get_collection_name(collection_name)
        
        # Map metric to Qdrant distance
        metric_map = {
            'cosine': self.qdrant_models.Distance.COSINE,
            'euclidean': self.qdrant_models.Distance.EUCLID,
            'dot': self.qdrant_models.Distance.DOT,
        }
        distance = metric_map.get(metric, self.qdrant_models.Distance.COSINE)
        
        # Create collection
        self._client.create_collection(
            collection_name=full_name,
            vectors_config=self.qdrant_models.VectorParams(
                size=dimension,
                distance=distance,
            ),
            **kwargs
        )
        
        logger.info(f"Created collection: {full_name} (dim={dimension}, metric={metric})")
    
    async def drop_collection(self, collection_name: str) -> None:
        """Delete collection from Qdrant."""
        full_name = self._get_collection_name(collection_name)
        
        self._client.delete_collection(collection_name=full_name)
        logger.info(f"Dropped collection: {full_name}")
    
    async def list_collections(self) -> list[str]:
        """List all collections."""
        collections = self._client.get_collections().collections
        
        # Remove prefix from names
        result = [
            col.name.replace(self.collection_prefix, '')
            for col in collections
        ]
        
        return result
    
    async def upsert(
        self,
        collection_name: str,
        vectors: list[dict],
    ) -> list[str]:
        """
        Insert or update vectors in Qdrant.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector dictionaries
            
        Returns:
            List of vector IDs
        """
        if not vectors:
            return []
        
        full_name = self._get_collection_name(collection_name)
        vector_ids = []
        
        # Prepare points for Qdrant
        points = []
        for vec in vectors:
            point = self.qdrant_models.PointStruct(
                id=vec['id'],
                vector=vec['vector'],
                payload={
                    'metadata': vec.get('metadata', {}),
                    'document_id': vec.get('document_id'),
                },
            )
            points.append(point)
        
        # Upsert points
        self._client.upsert(
            collection_name=full_name,
            points=points,
        )
        
        vector_ids = [vec['id'] for vec in vectors]
        return vector_ids
    
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 10,
        filter: Optional[dict] = None,
        threshold: float = 0.0,
    ) -> list[dict]:
        """
        Search for similar vectors in Qdrant.
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            top_k: Number of results
            filter: Optional metadata filter
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results
        """
        full_name = self._get_collection_name(collection_name)
        
        # Build filter if provided
        qdrant_filter = None
        if filter:
            must_conditions = []
            for key, value in filter.items():
                must_conditions.append(
                    self.qdrant_models.FieldCondition(
                        key=f"metadata.{key}",
                        match=self.qdrant_models.MatchValue(value=value),
                    )
                )
            qdrant_filter = self.qdrant_models.Filter(must=must_conditions)
        
        # Search
        results = self._client.search(
            collection_name=full_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            score_threshold=threshold if threshold > 0.0 else None,
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': str(result.id),
                'score': result.score,
                'metadata': result.payload.get('metadata', {}),
                'document_id': result.payload.get('document_id'),
            })
        
        return formatted_results
    
    async def delete(
        self,
        collection_name: str,
        vector_ids: list[str],
    ) -> int:
        """Delete vectors by ID."""
        if not vector_ids:
            return 0
        
        full_name = self._get_collection_name(collection_name)
        
        self._client.delete(
            collection_name=full_name,
            points_selector=self.qdrant_models.PointIdsList(
                points=vector_ids
            ),
        )
        
        logger.info(f"Deleted {len(vector_ids)} vectors from {full_name}")
        return len(vector_ids)
    
    async def delete_by_filter(
        self,
        collection_name: str,
        filter: dict,
    ) -> int:
        """Delete vectors matching filter."""
        full_name = self._get_collection_name(collection_name)
        
        # Build filter
        must_conditions = []
        for key, value in filter.items():
            must_conditions.append(
                self.qdrant_models.FieldCondition(
                    key=f"metadata.{key}",
                    match=self.qdrant_models.MatchValue(value=value),
                )
            )
        
        qdrant_filter = self.qdrant_models.Filter(must=must_conditions)
        
        # Delete matching points
        result = self._client.delete(
            collection_name=full_name,
            points_selector=self.qdrant_models.FilterSelector(
                filter=qdrant_filter
            ),
        )
        
        logger.info(f"Deleted vectors from {full_name} by filter")
        return result.status.operation_count if hasattr(result, 'status') else 0
    
    async def get_vector(
        self,
        collection_name: str,
        vector_id: str,
    ) -> Optional[dict]:
        """Get vector by ID."""
        full_name = self._get_collection_name(collection_name)
        
        try:
            result = self._client.retrieve(
                collection_name=full_name,
                ids=[vector_id],
                with_vectors=True,
            )
            
            if not result:
                return None
            
            point = result[0]
            return {
                'id': str(point.id),
                'vector': point.vector,
                'metadata': point.payload.get('metadata', {}),
                'document_id': point.payload.get('document_id'),
            }
        except Exception as e:
            logger.error(f"Failed to get vector {vector_id}: {e}")
            return None
    
    async def count(
        self,
        collection_name: str,
        filter: Optional[dict] = None,
    ) -> int:
        """Count vectors in collection."""
        full_name = self._get_collection_name(collection_name)
        
        # Build filter if provided
        qdrant_filter = None
        if filter:
            must_conditions = []
            for key, value in filter.items():
                must_conditions.append(
                    self.qdrant_models.FieldCondition(
                        key=f"metadata.{key}",
                        match=self.qdrant_models.MatchValue(value=value),
                    )
                )
            qdrant_filter = self.qdrant_models.Filter(must=must_conditions)
        
        # Count
        result = self._client.count(
            collection_name=full_name,
            count_filter=qdrant_filter,
        )
        
        return result.count
    
    async def update_metadata(
        self,
        collection_name: str,
        vector_id: str,
        metadata: dict,
    ) -> None:
        """Update vector metadata."""
        full_name = self._get_collection_name(collection_name)
        
        self._client.set_payload(
            collection_name=full_name,
            payload={'metadata': metadata},
            points=[vector_id],
        )
        
        logger.debug(f"Updated metadata for vector {vector_id}")
    
    async def batch_upsert(
        self,
        collection_name: str,
        vectors: list[dict],
        batch_size: int = 100,
    ) -> list[str]:
        """
        Batch upsert vectors.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector dictionaries
            batch_size: Batch size
            
        Returns:
            List of all vector IDs
        """
        all_ids = []
        
        # Process in batches
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            ids = await self.upsert(collection_name, batch)
            all_ids.extend(ids)
        
        return all_ids
    
    async def get_collection_info(self, collection_name: str) -> dict:
        """Get collection information."""
        full_name = self._get_collection_name(collection_name)
        
        info = self._client.get_collection(collection_name=full_name)
        
        return {
            'name': collection_name,
            'vector_count': info.points_count,
            'dimension': info.config.params.vectors.size,
            'backend': 'qdrant',
        }