"""PostgreSQL pgvector storage for large-scale vector search."""

import json
import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger("nebula.vector.pgvector")

# Optional pgvector support
try:
    import asyncpg

    _HAS_PGVECTOR = True
except ImportError:
    _HAS_PGVECTOR = False
    logger.info("asyncpg/pgvector not installed — using file-based vector storage")


class PgVectorStore:
    """PostgreSQL pgvector-based vector storage for production deployments."""

    def __init__(self):
        self._pool = None
        self._enabled = False

    async def initialize(self) -> None:
        """Initialize pgvector extension and connection pool."""
        if not _HAS_PGVECTOR or not get_settings().uses_postgres:
            logger.info("pgvector storage disabled (not PostgreSQL or asyncpg not installed)")
            return

        try:
            import asyncpg

            url = get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://")
            self._pool = await asyncpg.create_pool(
                url,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )

            # Enable pgvector extension
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("pgvector extension enabled")

            self._enabled = True
            logger.info("PgVectorStore initialized successfully")
        except Exception as exc:
            logger.warning("Failed to initialize pgvector: %s", exc)
            self._enabled = False

    async def store_embedding(
        self,
        chunk_id: int,
        document_id: int,
        user_id: int,
        vector: list[float],
        model_name: str = "text-embedding-3-small",
    ) -> bool:
        """Store an embedding vector in PostgreSQL."""
        if not self._enabled or not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                # Convert list to pgvector format
                vector_str = "[" + ",".join(str(v) for v in vector) + "]"
                
                await conn.execute(
                    """
                    INSERT INTO embeddings (chunk_id, document_id, user_id, vector, model_name)
                    VALUES ($1, $2, $3, $4::vector, $5)
                    ON CONFLICT (chunk_id) DO UPDATE
                    SET vector = EXCLUDED.vector, model_name = EXCLUDED.model_name
                    """,
                    chunk_id, document_id, user_id, vector_str, model_name
                )
                return True
        except Exception as exc:
            logger.error("Failed to store embedding: %s", exc)
            return False

    async def search_similar(
        self,
        user_id: int,
        query_vector: list[float],
        top_k: int = 10,
        document_id: Optional[int] = None,
    ) -> list[tuple[int, float]]:
        """Search for similar vectors using cosine similarity."""
        if not self._enabled or not self._pool:
            return []

        try:
            vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"
            
            async with self._pool.acquire() as conn:
                if document_id:
                    rows = await conn.fetch(
                        """
                        SELECT chunk_id, 1 - (vector <=> $1::vector) AS similarity
                        FROM embeddings
                        WHERE user_id = $2 AND document_id = $3
                        ORDER BY vector <=> $1::vector
                        LIMIT $4
                        """,
                        vector_str, user_id, document_id, top_k
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT chunk_id, 1 - (vector <=> $1::vector) AS similarity
                        FROM embeddings
                        WHERE user_id = $2
                        ORDER BY vector <=> $1::vector
                        LIMIT $3
                        """,
                        vector_str, user_id, top_k
                    )

                return [(row["chunk_id"], float(row["similarity"])) for row in rows]
        except Exception as exc:
            logger.error("Failed to search similar vectors: %s", exc)
            return []

    async def delete_embeddings(self, document_id: int, user_id: int) -> bool:
        """Delete all embeddings for a document."""
        if not self._enabled or not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM embeddings WHERE document_id = $1 AND user_id = $2",
                    document_id, user_id
                )
                return True
        except Exception as exc:
            logger.error("Failed to delete embeddings: %s", exc)
            return False

    async def get_stats(self, user_id: int) -> dict:
        """Get vector storage statistics."""
        if not self._enabled or not self._pool:
            return {"enabled": False}

        try:
            async with self._pool.acquire() as conn:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM embeddings WHERE user_id = $1",
                    user_id
                )
                return {
                    "enabled": True,
                    "total_embeddings": count or 0,
                    "storage": "pgvector"
                }
        except Exception as exc:
            logger.error("Failed to get stats: %s", exc)
            return {"enabled": False}

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._enabled = False


# Global pgvector store instance
_pgvector_store: Optional[PgVectorStore] = None


def get_pgvector_store() -> PgVectorStore:
    """Get or create the global pgvector store instance."""
    global _pgvector_store
    if _pgvector_store is None:
        _pgvector_store = PgVectorStore()
    return _pgvector_store