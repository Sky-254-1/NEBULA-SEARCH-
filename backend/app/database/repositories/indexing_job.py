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

    async def list_for_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        rows = await self._db.fetchall(
            "SELECT job_id, user_id, document_id, filename, priority, status, "
            "progress, current_step, created_at, started_at, completed_at, "
            "worker_id, retry_count, error_message "
            "FROM index_jobs WHERE user_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )
        return [dict(row) for row in rows]

    async def count_for_user(self, user_id: int) -> int:
        row = await self._db.fetchone(
            "SELECT COUNT(*) AS count FROM index_jobs WHERE user_id = ?",
            (user_id,),
        )
        return int(row["count"]) if row else 0

    async def set_status(
        self, job_id: str, status: str, retry_count: int | None = None
    ) -> None:
        if retry_count is None:
            await self._db.execute(
                "UPDATE index_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE job_id = ?",
                (status, job_id),
            )
        else:
            await self._db.execute(
                "UPDATE index_jobs SET status = ?, retry_count = ?, "
                "updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
                (status, retry_count, job_id),
            )
        await self._db.commit()

    async def reserve_retry_for_user(
        self, job_id: str, user_id: int, max_retries: int
    ) -> bool:
        """Atomically reserve one manual retry for a failed owned job."""
        result = await self._db.execute(
            "UPDATE index_jobs SET status = 'RETRYING', retry_count = retry_count + 1, "
            "updated_at = CURRENT_TIMESTAMP "
            "WHERE job_id = ? AND user_id = ? AND status = 'FAILED' "
            "AND retry_count < ?",
            (job_id, user_id, max_retries),
        )
        await self._db.commit()
        return result.rowcount == 1

    async def delete_for_user(self, job_id: str, user_id: int) -> None:
        await self._db.execute(
            "DELETE FROM index_jobs WHERE job_id = ? AND user_id = ?",
            (job_id, user_id),
        )
        await self._db.commit()
