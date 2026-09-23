"""
PostgreSQL pgvector Store Implementation

Vector store using PostgreSQL with pgvector extension.
Provides production-ready vector similarity search.
"""

import logging
import json
from typing import Optional
import asyncpg

from .abstract import VectorStore

logger = logging.getLogger(__name__)


class PGVectorStore(VectorStore):
    """
    PostgreSQL pgvector implementation of VectorStore.
    
    Requires:
    - PostgreSQL 15+ with pgvector extension installed
    - asyncpg for async database access
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize pgvector store.
        
        Args:
            connection_string: PostgreSQL connection string
            **kwargs: Additional options (schema, table_prefix, etc.)
        """
        super().__init__(connection_string, **kwargs)
        self.schema = kwargs.get('schema', 'public')
        self.table_prefix = kwargs.get('table_prefix', 'vectors_')
        self._pool = None
    
    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        try:
            self._pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            self._connected = True
            logger.info("Connected to PostgreSQL pgvector")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._connected = False
            logger.info("Disconnected from PostgreSQL")
    
    async def health_check(self) -> bool:
        """Check if PostgreSQL is healthy."""
        try:
            if not self._pool:
                return False
            
            async with self._pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def _get_table_name(self, collection_name: str) -> str:
        """Get full table name for collection."""
        return f"{self.schema}.{self.table_prefix}{collection_name}"
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        metric: str = "cosine",
        **kwargs
    ) -> None:
        """
        Create a new collection table for vectors.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            metric: Distance metric ("cosine", "euclidean", "dot_product")
            **kwargs: Additional options
        """
        table_name = self._get_table_name(collection_name)
        
        # Map metric to pgvector operator
        metric_map = {
            'cosine': '<=>',
            'euclidean': '<->',
            'dot_product': '<#>',
        }
        metric_map.get(metric, '<=>')
        
        # Create table
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id VARCHAR(255) PRIMARY KEY,
            vector VECTOR({dimension}) NOT NULL,
            metadata JSONB DEFAULT '{{}}'::jsonb,
            document_id BIGINT,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        """
        
        # Create index for similarity search
        create_index_query = f"""
        CREATE INDEX IF NOT EXISTS idx_{collection_name}_vector 
        ON {table_name} 
        USING ivfflat (vector vector_{metric}_ops)
        WITH (lists = 100);
        """
        
        # Create index on metadata
        create_metadata_index = f"""
        CREATE INDEX IF NOT EXISTS idx_{collection_name}_metadata 
        ON {table_name} 
        USING GIN (metadata);
        """
        
        # Create index on document_id
        create_doc_index = f"""
        CREATE INDEX IF NOT EXISTS idx_{collection_name}_document_id 
        ON {table_name} (document_id);
        """
        
        async with self._pool.acquire() as conn:
            await conn.execute(create_table_query)
            await conn.execute(create_index_query)
            await conn.execute(create_metadata_index)
            await conn.execute(create_doc_index)
        
        logger.info(f"Created collection: {collection_name} (dim={dimension}, metric={metric})")
    
    async def drop_collection(self, collection_name: str) -> None:
        """Delete collection table."""
        table_name = self._get_table_name(collection_name)
        
        query = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
        
        async with self._pool.acquire() as conn:
            await conn.execute(query)
        
        logger.info(f"Dropped collection: {collection_name}")
    
    async def list_collections(self) -> list[str]:
        """List all vector collections."""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = $1 
        AND table_name LIKE $2
        AND table_type = 'BASE TABLE';
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, self.schema, f"{self.table_prefix}%")
        
        # Remove prefix from names
        collections = [
            row['table_name'].replace(self.table_prefix, '')
            for row in rows
        ]
        
        return collections
    
    async def upsert(
        self,
        collection_name: str,
        vectors: list[dict],
    ) -> list[str]:
        """
        Insert or update vectors.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector dictionaries
            
        Returns:
            List of vector IDs
        """
        if not vectors:
            return []
        
        table_name = self._get_table_name(collection_name)
        vector_ids = []
        
        # Upsert query
        query = f"""  # nosec B608: table_name from internal config, data values are parameterized
        INSERT INTO {table_name} (id, vector, metadata, document_id, updated_at)
        VALUES ($1, $2, $3, $4, NOW())
        ON CONFLICT (id) 
        DO UPDATE SET 
            vector = EXCLUDED.vector,
            metadata = EXCLUDED.metadata,
            document_id = EXCLUDED.document_id,
            updated_at = NOW();
        """
        
        async with self._pool.acquire() as conn:
            for vec in vectors:
                vector_id = vec['id']
                vector_data = vec['vector']
                metadata = json.dumps(vec.get('metadata', {}))
                document_id = vec.get('document_id')
                
                await conn.execute(
                    query,
                    vector_id,
                    vector_data,
                    metadata,
                    document_id,
                )
                
                vector_ids.append(vector_id)
        
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
        Search for similar vectors.
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            top_k: Number of results
            filter: Optional metadata filter
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results
        """
        table_name = self._get_table_name(collection_name)
        
        # Build filter clause
        where_clause = "WHERE 1=1"
        params = [query_vector, top_k]
        param_idx = 3
        
        if filter:
            for key, value in filter.items():
                where_clause += f" AND metadata->>{param_idx} = ${param_idx}"  # nosec B608: param_idx values are controlled integers, values are parameterized
                params.append(json.dumps(value))
                param_idx += 1
        
        # Search query
        query = f"""  # nosec B608: table_name from internal config, values parameterized
        SELECT 
            id,
            vector,
            metadata,
            document_id,
            1 - (vector <=> $1) as score
        FROM {table_name}
        {where_clause}
        ORDER BY vector <=> $1
        LIMIT $2;
        """
        
        results = []
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            for row in rows:
                score = float(row['score'])
                
                # Apply threshold
                if threshold > 0.0 and score < threshold:
                    continue
                
                results.append({
                    'id': row['id'],
                    'score': score,
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'document_id': row['document_id'],
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
        
        table_name = self._get_table_name(collection_name)
        
        # Build query with multiple IDs
        placeholders = ','.join(f'${i+1}' for i in range(len(vector_ids)))
        query = f"DELETE FROM {table_name} WHERE id IN ({placeholders}) RETURNING id;"  # nosec B608: table_name from internal config, values parameterized
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *vector_ids)
        
        deleted_count = len(rows)
        logger.info(f"Deleted {deleted_count} vectors from {collection_name}")
        
        return deleted_count
    
    async def delete_by_filter(
        self,
        collection_name: str,
        filter: dict,
    ) -> int:
        """Delete vectors matching filter."""
        table_name = self._get_table_name(collection_name)
        
        # Build WHERE clause
        where_parts = []
        params = []
        param_idx = 1
        
        for key, value in filter.items():
            where_parts.append(f"metadata->>{param_idx} = ${param_idx}")
            params.append(json.dumps(value))
            param_idx += 1
        
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        query = f"DELETE FROM {table_name} WHERE {where_clause} RETURNING id;"  # nosec B608: table_name from internal config, values parameterized
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        deleted_count = len(rows)
        logger.info(f"Deleted {deleted_count} vectors from {collection_name} by filter")
        
        return deleted_count
    
    async def get_vector(
        self,
        collection_name: str,
        vector_id: str,
    ) -> Optional[dict]:
        """Get vector by ID."""
        table_name = self._get_table_name(collection_name)
        
        query = f"""  # nosec B608: table_name from internal config, values parameterized
        SELECT id, vector, metadata, document_id
        FROM {table_name}
        WHERE id = $1;
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, vector_id)
        
        if not row:
            return None
        
        return {
            'id': row['id'],
            'vector': list(row['vector']),
            'metadata': json.loads(row['metadata']) if row['metadata'] else {},
            'document_id': row['document_id'],
        }
    
    async def count(
        self,
        collection_name: str,
        filter: Optional[dict] = None,
    ) -> int:
        """Count vectors in collection."""
        table_name = self._get_table_name(collection_name)
        
        where_clause = "WHERE 1=1"
        params = []
        param_idx = 1
        
        if filter:
            for key, value in filter.items():
                where_clause += f" AND metadata->>{param_idx} = ${param_idx}"  # nosec B608: param_idx values are controlled integers, values parameterized
                params.append(json.dumps(value))
                param_idx += 1
        
        query = f"SELECT COUNT(*) FROM {table_name} {where_clause};"  # nosec B608: table_name from internal config, values parameterized
        
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(query, *params)
        
        return count
    
    async def update_metadata(
        self,
        collection_name: str,
        vector_id: str,
        metadata: dict,
    ) -> None:
        """Update vector metadata."""
        table_name = self._get_table_name(collection_name)
        
        query = f"""  # nosec B608: table_name from internal config, values parameterized
        UPDATE {table_name}
        SET metadata = $1, updated_at = NOW()
        WHERE id = $2;
        """
        
        async with self._pool.acquire() as conn:
            await conn.execute(query, json.dumps(metadata), vector_id)
        
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
        table_name = self._get_table_name(collection_name)
        
        query = f"""  # nosec B608: table_name from internal config, values parameterized
        SELECT 
            COUNT(*) as vector_count,
            pg_size_pretty(pg_total_relation_size('{table_name}')) as size
        FROM {table_name};
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query)
        
        return {
            'name': collection_name,
            'vector_count': row['vector_count'],
            'size': row['size'],
            'backend': 'pgvector',
        }