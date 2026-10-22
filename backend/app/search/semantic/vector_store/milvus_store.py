"""
Milvus Vector Store Implementation

Vector store using Milvus - high-performance vector database.
"""

import logging
import json
from typing import Optional

from .abstract import VectorStore

logger = logging.getLogger(__name__)


class MilvusStore(VectorStore):
    """
    Milvus implementation of VectorStore.
    
    Requires:
    - Milvus server running (local or cloud)
    - pymilvus package
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize Milvus store.
        
        Args:
            connection_string: Milvus connection string (e.g., "localhost:19530")
            **kwargs: Additional options (collection_prefix, etc.)
        """
        super().__init__(connection_string, **kwargs)
        self.collection_prefix = kwargs.get('collection_prefix', 'nebula_')
        self._client = None
        self._connections = None
        
        # Lazy import to avoid dependency if not used
        try:
            from pymilvus import MilvusClient
            self.MilvusClient = MilvusClient
            self._milvus_available = True
        except ImportError:
            logger.warning("pymilvus not installed. Install with: pip install pymilvus")
            self._milvus_available = False
    
    async def connect(self) -> None:
        """Establish connection to Milvus."""
        if not self._milvus_available:
            raise ImportError("pymilvus is not installed")
        
        try:
            self._client = self.MilvusClient(
                uri=self.connection_string,
            )
            self._connected = True
            logger.info(f"Connected to Milvus at {self.connection_string}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Milvus."""
        if self._client:
            self._client = None
            self._connected = False
            logger.info("Disconnected from Milvus")
    
    async def health_check(self) -> bool:
        """Check if Milvus is healthy."""
        try:
            if not self._client:
                return False
            
            # Try to list collections
            self._client.list_collections()
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
        Create a new collection in Milvus.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            metric: Distance metric ("cosine", "euclidean", "ip")
            **kwargs: Additional options
        """
        full_name = self._get_collection_name(collection_name)
        
        # Map metric to Milvus metric type
        metric_map = {
            'cosine': 'COSINE',
            'euclidean': 'L2',
            'ip': 'IP',
        }
        milvus_metric = metric_map.get(metric, 'COSINE')
        
        # Create collection
        self._client.create_collection(
            collection_name=full_name,
            dimension=dimension,
            metric_type=milvus_metric,
            **kwargs
        )
        
        logger.info(f"Created collection: {full_name} (dim={dimension}, metric={metric})")
    
    async def drop_collection(self, collection_name: str) -> None:
        """Delete collection from Milvus."""
        full_name = self._get_collection_name(collection_name)
        
        self._client.drop_collection(collection_name=full_name)
        logger.info(f"Dropped collection: {full_name}")
    
    async def list_collections(self) -> list[str]:
        """List all collections."""
        collections = self._client.list_collections()
        
        # Remove prefix from names
        result = [
            col.replace(self.collection_prefix, '')
            for col in collections
        ]
        
        return result
    
    async def upsert(
        self,
        collection_name: str,
        vectors: list[dict],
    ) -> list[str]:
        """
        Insert or update vectors in Milvus.
        
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
        
        # Prepare data for Milvus
        data = []
        for vec in vectors:
            data.append({
                'id': vec['id'],
                'vector': vec['vector'],
                'metadata': json.dumps(vec.get('metadata', {})),
                'document_id': vec.get('document_id'),
            })
        
        # Upsert data
        self._client.upsert(
            collection_name=full_name,
            data=data,
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
        Search for similar vectors in Milvus.
        
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
        milvus_filter = None
        if filter:
            filter_parts = []
            for key, value in filter.items():
                filter_parts.append(f'metadata == "{json.dumps(value)}"')
            milvus_filter = " && ".join(filter_parts) if filter_parts else None
        
        # Search
        results = self._client.search(
            collection_name=full_name,
            data=[query_vector],
            limit=top_k,
            filter=milvus_filter,
        )
        
        # Format results (Milvus returns nested list)
        formatted_results = []
        if results and len(results) > 0:
            for result in results[0]:
                metadata = {}
                try:
                    if result.get('metadata'):
                        metadata = json.loads(result['metadata'])
                except Exception as exc:
                    logger.debug("Milvus result metadata parse failed: %s", exc)
                
                formatted_results.append({
                    'id': str(result['id']),
                    'score': result['distance'],
                    'metadata': metadata,
                    'document_id': result.get('document_id'),
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
            ids=vector_ids,
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
        filter_parts = []
        for key, value in filter.items():
            filter_parts.append(f'metadata == "{json.dumps(value)}"')
        milvus_filter = " && ".join(filter_parts) if filter_parts else None
        
        # Delete
        result = self._client.delete(
            collection_name=full_name,
            filter=milvus_filter,
        )
        
        logger.info(f"Deleted vectors from {full_name} by filter")
        return result.delete_count if hasattr(result, 'delete_count') else 0
    
    async def get_vector(
        self,
        collection_name: str,
        vector_id: str,
    ) -> Optional[dict]:
        """Get vector by ID."""
        full_name = self._get_collection_name(collection_name)
        
        try:
            result = self._client.get(
                collection_name=full_name,
                ids=[vector_id],
            )
            
            if not result:
                return None
            
            data = result[0]
            metadata = {}
            try:
                if data.get('metadata'):
                    metadata = json.loads(data['metadata'])
            except Exception as exc:
                logger.debug("Milvus vector metadata parse failed: %s", exc)
            
            return {
                'id': str(data['id']),
                'vector': data['vector'],
                'metadata': metadata,
                'document_id': data.get('document_id'),
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
        milvus_filter = None
        if filter:
            filter_parts = []
            for key, value in filter.items():
                filter_parts.append(f'metadata == "{json.dumps(value)}"')
            milvus_filter = " && ".join(filter_parts) if filter_parts else None
        
        # Count
        result = self._client.get_collection_stats(
            collection_name=full_name,
            filter=milvus_filter,
        )
        
        return result.get('row_count', 0)
    
    async def update_metadata(
        self,
        collection_name: str,
        vector_id: str,
        metadata: dict,
    ) -> None:
        """Update vector metadata."""
        full_name = self._get_collection_name(collection_name)
        
        # Milvus doesn't have direct metadata update, need to upsert
        # Get existing vector
        existing = await self.get_vector(full_name, vector_id)
        if existing:
            # Update with new metadata
            existing['metadata'] = metadata
            await self.upsert(full_name, [existing])
        
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
        
        stats = self._client.get_collection_stats(collection_name=full_name)
        
        return {
            'name': collection_name,
            'vector_count': stats.get('row_count', 0),
            'backend': 'milvus',
        }