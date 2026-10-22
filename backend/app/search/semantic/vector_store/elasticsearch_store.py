"""
Elasticsearch Vector Store Implementation

Vector store using Elasticsearch with vector search capabilities.
"""

import logging
from typing import Optional

from .abstract import VectorStore

logger = logging.getLogger(__name__)


class ElasticsearchVectorStore(VectorStore):
    """
    Elasticsearch implementation of VectorStore.
    
    Requires:
    - Elasticsearch 8.0+ with vector search enabled
    - elasticsearch package
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize Elasticsearch vector store.
        
        Args:
            connection_string: Elasticsearch connection string (e.g., "http://localhost:9200")
            **kwargs: Additional options (index_prefix, etc.)
        """
        super().__init__(connection_string, **kwargs)
        self.index_prefix = kwargs.get('index_prefix', 'nebula_vectors_')
        self._client = None
        
        # Lazy import to avoid dependency if not used
        try:
            from elasticsearch import AsyncElasticsearch
            self.AsyncElasticsearch = AsyncElasticsearch
            self._elasticsearch_available = True
        except ImportError:
            logger.warning("elasticsearch not installed. Install with: pip install elasticsearch")
            self._elasticsearch_available = False
    
    async def connect(self) -> None:
        """Establish connection to Elasticsearch."""
        if not self._elasticsearch_available:
            raise ImportError("elasticsearch is not installed")
        
        try:
            self._client = self.AsyncElasticsearch(
                hosts=[self.connection_string],
            )
            # Test connection
            await self._client.info()
            self._connected = True
            logger.info(f"Connected to Elasticsearch at {self.connection_string}")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Elasticsearch."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False
            logger.info("Disconnected from Elasticsearch")
    
    async def health_check(self) -> bool:
        """Check if Elasticsearch is healthy."""
        try:
            if not self._client:
                return False
            
            health = await self._client.cluster.health()
            return health.get('status') in ['green', 'yellow']
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def _get_index_name(self, collection_name: str) -> str:
        """Get full index name with prefix."""
        return f"{self.index_prefix}{collection_name}"
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        metric: str = "cosine",
        **kwargs
    ) -> None:
        """
        Create a new index in Elasticsearch.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            metric: Distance metric ("cosine", "euclidean", "dot")
            **kwargs: Additional options
        """
        index_name = self._get_index_name(collection_name)
        
        # Map metric to Elasticsearch similarity
        metric_map = {
            'cosine': 'cosine',
            'euclidean': 'l2_norm',
            'dot': 'dot_product',
        }
        similarity = metric_map.get(metric, 'cosine')
        
        # Create index with vector field
        index_body = {
            "mappings": {
                "properties": {
                    "vector": {
                        "type": "dense_vector",
                        "dims": dimension,
                        "index": True,
                        "similarity": similarity,
                    },
                    "metadata": {
                        "type": "object",
                        "enabled": True,
                    },
                    "document_id": {
                        "type": "long",
                    },
                }
            }
        }
        
        await self._client.indices.create(
            index=index_name,
            body=index_body,
        )
        
        logger.info(f"Created index: {index_name} (dim={dimension}, metric={metric})")
    
    async def drop_collection(self, collection_name: str) -> None:
        """Delete index from Elasticsearch."""
        index_name = self._get_index_name(collection_name)
        
        await self._client.indices.delete(index=index_name, ignore=[404])
        logger.info(f"Dropped index: {index_name}")
    
    async def list_collections(self) -> list[str]:
        """List all vector collections."""
        # Get all indices with prefix
        indices = await self._client.indices.get_alias(index=f"{self.index_prefix}*")
        
        # Remove prefix from names
        result = [
            idx.replace(self.index_prefix, '')
            for idx in indices.keys()
        ]
        
        return result
    
    async def upsert(
        self,
        collection_name: str,
        vectors: list[dict],
    ) -> list[str]:
        """
        Insert or update vectors in Elasticsearch.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector dictionaries
            
        Returns:
            List of vector IDs
        """
        if not vectors:
            return []
        
        index_name = self._get_index_name(collection_name)
        vector_ids = []
        
        # Bulk index vectors
        from elasticsearch.helpers import async_bulk
        
        actions = []
        for vec in vectors:
            action = {
                "_index": index_name,
                "_id": vec['id'],
                "_source": {
                    "vector": vec['vector'],
                    "metadata": vec.get('metadata', {}),
                    "document_id": vec.get('document_id'),
                }
            }
            actions.append(action)
            vector_ids.append(vec['id'])
        
        # Bulk insert
        success, failed = await async_bulk(
            self._client,
            actions,
            raise_on_error=False,
        )
        
        if failed:
            logger.warning(f"Failed to index {len(failed)} vectors")
        
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
        Search for similar vectors in Elasticsearch.
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            top_k: Number of results
            filter: Optional metadata filter
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results
        """
        index_name = self._get_index_name(collection_name)
        
        # Build query
        query = {
            "size": top_k,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                        "params": {"query_vector": query_vector}
                    }
                }
            }
        }
        
        # Add filter if provided
        if filter:
            query["query"] = {
                "bool": {
                    "must": [
                        {"script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                                "params": {"query_vector": query_vector}
                            }
                        }}
                    ],
                    "filter": [
                        {"term": {f"metadata.{key}": value}}
                        for key, value in filter.items()
                    ]
                }
            }
        
        # Execute search
        response = await self._client.search(
            index=index_name,
            body=query,
        )
        
        # Format results
        results = []
        for hit in response['hits']['hits']:
            score = hit['_score'] / 2.0  # Normalize from [0, 2] to [0, 1]
            
            # Apply threshold
            if threshold > 0.0 and score < threshold:
                continue
            
            results.append({
                'id': hit['_id'],
                'score': score,
                'metadata': hit['_source'].get('metadata', {}),
                'document_id': hit['_source'].get('document_id'),
            })
        
        return results
    
    async def delete(
        self,
        collection_name: str,
        vector_ids: list[str],
    ) -> int:
        """Delete vectors by ID."""
        if not vector_ids:
            return 0
        
        index_name = self._get_index_name(collection_name)
        
        # Bulk delete
        from elasticsearch.helpers import async_bulk
        
        actions = [
            {
                "_op_type": "delete",
                "_index": index_name,
                "_id": vector_id,
            }
            for vector_id in vector_ids
        ]
        
        success, failed = await async_bulk(
            self._client,
            actions,
            raise_on_error=False,
        )
        
        deleted_count = len(vector_ids) - len(failed)
        logger.info(f"Deleted {deleted_count} vectors from {index_name}")
        
        return deleted_count
    
    async def delete_by_filter(
        self,
        collection_name: str,
        filter: dict,
    ) -> int:
        """Delete vectors matching filter."""
        index_name = self._get_index_name(collection_name)
        
        # Build delete query
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {f"metadata.{key}": value}}
                        for key, value in filter.items()
                    ]
                }
            }
        }
        
        # Delete by query
        response = await self._client.delete_by_query(
            index=index_name,
            body=query,
        )
        
        deleted_count = response.get('deleted', 0)
        logger.info(f"Deleted {deleted_count} vectors from {index_name} by filter")
        
        return deleted_count
    
    async def get_vector(
        self,
        collection_name: str,
        vector_id: str,
    ) -> Optional[dict]:
        """Get vector by ID."""
        index_name = self._get_index_name(collection_name)
        
        try:
            response = await self._client.get(
                index=index_name,
                id=vector_id,
            )
            
            source = response['_source']
            return {
                'id': response['_id'],
                'vector': source.get('vector', []),
                'metadata': source.get('metadata', {}),
                'document_id': source.get('document_id'),
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
        index_name = self._get_index_name(collection_name)
        
        # Build query
        query = {"query": {"match_all": {}}}
        
        if filter:
            query["query"] = {
                "bool": {
                    "filter": [
                        {"term": {f"metadata.{key}": value}}
                        for key, value in filter.items()
                    ]
                }
            }
        
        # Count
        response = await self._client.count(
            index=index_name,
            body=query,
        )
        
        return response.get('count', 0)
    
    async def update_metadata(
        self,
        collection_name: str,
        vector_id: str,
        metadata: dict,
    ) -> None:
        """Update vector metadata."""
        index_name = self._get_index_name(collection_name)
        
        await self._client.update(
            index=index_name,
            id=vector_id,
            body={
                "doc": {
                    "metadata": metadata,
                }
            }
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
        index_name = self._get_index_name(collection_name)
        
        # Get index stats
        stats = await self._client.indices.stats(index=index_name)
        
        doc_count = stats.get('indices', {}).get(index_name, {}).get('primaries', {}).get('docs', {}).get('count', 0)
        
        return {
            'name': collection_name,
            'vector_count': doc_count,
            'backend': 'elasticsearch',
        }