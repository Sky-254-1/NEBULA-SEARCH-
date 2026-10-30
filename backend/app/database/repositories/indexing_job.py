"""Owner-scoped persistence for indexing job records."""

from app.database.engine import DatabaseConnection


class IndexingJobRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        job_id: str,
        user_id: int,
        document_id: int,
        filename: str = "",
        priority: str = "NORMAL",
    ) -> None:
        await self._db.execute(
            "INSERT INTO index_jobs "
            "(job_id, user_id, document_id, filename, priority, status, progress) "
            "VALUES (?, ?, ?, ?, ?, 'QUEUED', 0)",
            (job_id, user_id, document_id, filename, priority),
        )
        await self._db.commit()

    async def get_for_user(self, job_id: str, user_id: int) -> dict | None:
        row = await self._db.fetchone(
            "SELECT job_id, user_id, document_id, filename, priority, status, "
            "progress, current_step, created_at, started_at, completed_at, "
            "worker_id, retry_count, error_message "
            "FROM index_jobs WHERE job_id = ? AND user_id = ?",
            (job_id, user_id),
        )
        return dict(row) if row else None

    async def list_for_user(self, user_id: int, limit: int = 100) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT job_id, user_id, document_id, filename, priority, status, "
            "progress, current_step, created_at, started_at, completed_at, "
            "worker_id, retry_count, error_message "
            "FROM index_jobs WHERE user_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in rows]

    async def set_status(self, job_id: str, status: str) -> None:
        await self._db.execute(
            "UPDATE index_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE job_id = ?",
            (status, job_id),
        )
        await self._db.commit()

    async def delete_for_user(self, job_id: str, user_id: int) -> None:
        await self._db.execute(
            "DELETE FROM index_jobs WHERE job_id = ? AND user_id = ?",
            (job_id, user_id),
        )
        await self._db.commit()
