"""Full document indexing pipeline: ingest → chunk → embed → store."""

import logging
from pathlib import Path

from app.database.engine import DatabaseConnection
from app.database.repositories.document import DocumentRepository
from vector.chunking import chunk_text, estimate_tokens
from vector.embeddings import embed_text, save_vector
from vector.ingestion import content_hash, extract_text
from vector.storage import vector_path

logger = logging.getLogger("nebula.vector.pipeline")


class ChunkRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        document_id: int,
        user_id: int,
        chunk_index: int,
        content: str,
        token_count: int,
        content_hash_val: str,
    ) -> int:
        await self._db.execute(
            "INSERT INTO document_chunks (document_id, user_id, chunk_index, content, token_count, content_hash) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (document_id, user_id, chunk_index, content, token_count, content_hash_val),
        )
        await self._db.commit()
        row = await self._db.fetchone(
            "SELECT id FROM document_chunks WHERE document_id = ? AND chunk_index = ?",
            (document_id, chunk_index),
        )
        return row["id"] if row else 0

    async def delete_for_document(self, document_id: int) -> None:
        await self._db.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        await self._db.commit()

    async def list_for_user(self, user_id: int) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT c.id, c.document_id, c.chunk_index, c.content, d.filename "
            "FROM document_chunks c JOIN documents d ON d.id = c.document_id "
            "WHERE c.user_id = ?",
            (user_id,),
        )
        return [dict(row) for row in rows]


class EmbeddingRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        chunk_id: int,
        document_id: int,
        user_id: int,
        model: str,
        dimensions: int,
        vector_path_str: str,
    ) -> int:
        await self._db.execute(
            "INSERT INTO embeddings (chunk_id, document_id, user_id, model, dimensions, vector_path) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (chunk_id, document_id, user_id, model, dimensions, vector_path_str),
        )
        await self._db.commit()
        row = await self._db.fetchone(
            "SELECT id FROM embeddings WHERE chunk_id = ?",
            (chunk_id,),
        )
        return row["id"] if row else 0

    async def delete_for_document(self, document_id: int) -> None:
        await self._db.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
        await self._db.commit()

    async def candidates_for_user(self, user_id: int) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT e.chunk_id, e.document_id, e.vector_path, c.content, d.filename "
            "FROM embeddings e JOIN document_chunks c ON c.id = e.chunk_id "
            "JOIN documents d ON d.id = e.document_id "
            "WHERE e.user_id = ? AND d.indexed_at IS NOT NULL",
            (user_id,),
        )
        return [dict(row) for row in rows]


class SearchSessionRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(self, user_id: int | None, query: str, mode: str = "hybrid") -> int:
        await self._db.execute(
            "INSERT INTO search_sessions (user_id, query, mode) VALUES (?, ?, ?)",
            (user_id, query, mode),
        )
        await self._db.commit()
        row = await self._db.fetchone(
            "SELECT id FROM search_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        return row["id"] if row else 0

    async def complete(self, session_id: int, results_count: int, metadata: str = "{}") -> None:
        await self._db.execute(
            "UPDATE search_sessions SET results_count = ?, metadata_json = ?, "
            "completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (results_count, metadata, session_id),
        )
        await self._db.commit()


async def index_document(db: DatabaseConnection, document_id: int, user_id: int) -> bool:
    docs = DocumentRepository(db)
    row = await docs.get_by_id(document_id, user_id)
    if not row:
        logger.warning("Document %s not found for user %s", document_id, user_id)
        return False

    path = Path(row["storage_path"])
    if not path.exists():
        await docs.set_status(document_id, "error", error_message="File not found on disk")
        return False

    await docs.set_status(document_id, "indexing")

    try:
        text = extract_text(path)
        file_hash = content_hash(text)

        existing = await docs.find_by_hash(user_id, file_hash)
        if existing and existing["id"] != document_id:
            await docs.set_status(document_id, "duplicate", content_hash=file_hash)
            logger.info("Duplicate content detected for document %s", document_id)
            return False

        chunks_repo = ChunkRepository(db)
        embed_repo = EmbeddingRepository(db)
        await chunks_repo.delete_for_document(document_id)
        await embed_repo.delete_for_document(document_id)

        chunks = chunk_text(text)
        if not chunks:
            await docs.set_status(document_id, "error", error_message="No extractable text")
            return False

        for idx, chunk_content in enumerate(chunks):
            ch_hash = content_hash(chunk_content)
            chunk_id = await chunks_repo.create(
                document_id, user_id, idx, chunk_content, estimate_tokens(chunk_content), ch_hash
            )
            vector, model, dims = await embed_text(chunk_content)
            vpath = vector_path(user_id, document_id, chunk_id)
            save_vector(vpath, vector)
            await embed_repo.create(chunk_id, document_id, user_id, model, dims, str(vpath))

        await docs.mark_indexed(document_id, content_hash=file_hash)
        logger.info("Indexed document %s (%d chunks)", document_id, len(chunks))
        return True
    except Exception as exc:
        logger.exception("Failed to index document %s", document_id)
        await docs.set_status(document_id, "error", error_message=str(exc))
        return False


async def hybrid_search(
    db: DatabaseConnection,
    user_id: int,
    query: str,
    top_k: int = 10,
) -> list[dict]:
    from vector.embeddings import embed_text
    from vector.ranking import rerank
    from vector.retrieval import retrieve_chunks
    from vector.citations import CitationRepository

    sessions = SearchSessionRepository(db)
    session_id = await sessions.create(user_id, query, mode="hybrid")

    embed_repo = EmbeddingRepository(db)
    candidates = await embed_repo.candidates_for_user(user_id)
    if not candidates:
        await sessions.complete(session_id, 0, '{"reason":"no_candidates"}')
        return []

    query_vec, _, _ = await embed_text(query)
    results = retrieve_chunks(query_vec, candidates, query, top_k=top_k)
    results = rerank(results)

    citations = CitationRepository(db)
    for item in results:
        await citations.create(
            user_id,
            query,
            item.get("document_id"),
            item.get("chunk_id"),
            item.get("content", "")[:500],
            item.get("score", 0),
        )

    await sessions.complete(session_id, len(results))
    return results


async def reindex_all_documents(
    db: DatabaseConnection, user_id: int, limit: int = 100
) -> dict[str, int]:
    docs = DocumentRepository(db)
    rows = await docs.list_for_user(user_id, limit=limit)
    stats = {"total": len(rows), "success": 0, "failed": 0}
    for row in rows:
        try:
            if await index_document(db, row["id"], user_id):
                stats["success"] += 1
            else:
                stats["failed"] += 1
        except Exception:
            logger.exception("Reindex failed for doc %s", row["id"])
            stats["failed"] += 1
    return stats
