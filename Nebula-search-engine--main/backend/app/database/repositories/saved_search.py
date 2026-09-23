"""Saved search repository."""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.database.engine import DatabaseConnection

settings = get_settings()
# Use plain table name for both SQLite and PostgreSQL (schema prefix only for Postgres)
_TABLE = "saved_searches"
_PG_TABLE = "search.saved_searches"

# Strict identifier validator for SQL identifiers used in dynamic table names.
# Table/column names CANNOT be bound as parameters, so we enforce a known-safe shape.
_SAFE_SQL_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def _validate_table_name(value: str) -> str:
    if not _SAFE_SQL_IDENT_RE.match(value):
        raise ValueError(f"Refusing unsafe SQL table identifier: {value!r}")
    return value


class SavedSearchRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db
        self._table = _validate_table_name(_PG_TABLE if settings.uses_postgres else _TABLE)

    def _ph(self, n: int = 1) -> str:
        """Return the correct placeholder for the current DB engine."""
        if settings.uses_postgres:
            return ", ".join(f"${i}" for i in range(1, n + 1))
        return ", ".join("?" * n)

    def _p(self, name: str, idx: int) -> str:
        """Single named placeholder."""
        return f"${idx}" if settings.uses_postgres else "?"

    async def create(
        self,
        user_id: int,
        query: str,
        mode: str = "hybrid",
        filters: Optional[dict] = None,
        is_alert: bool = False,
    ) -> int:
        filters_json = json.dumps(filters or {})
        ph = self._ph(5)
        await self._db.execute(
            f"INSERT INTO {self._table} "  # nosec B608
            f"(user_id, query, mode, filters, is_alert) VALUES ({ph})",
            (user_id, query, mode, filters_json, is_alert),
        )
        await self._db.commit()
        if settings.uses_postgres:
            row = await self._db.fetchone(
                f"SELECT id FROM {self._table} WHERE user_id = $1 AND query = $2 "  # nosec B608
                "AND is_deleted = FALSE ORDER BY id DESC LIMIT 1",
                (user_id, query),
            )
        else:
            row = await self._db.fetchone(
                f"SELECT id FROM {self._table} WHERE user_id = ? AND query = ? "  # nosec B608
                "AND is_deleted = FALSE ORDER BY id DESC LIMIT 1",
                (user_id, query),
            )
        return row["id"] if row else 0

    async def list_for_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        if settings.uses_postgres:
            rows = await self._db.fetchall(
                f"SELECT id, query, mode, filters, is_alert, created_at, updated_at "  # nosec B608
                f"FROM {self._table} WHERE user_id = $1 AND is_deleted = FALSE "
                "ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                (user_id, limit, offset),
            )
        else:
            rows = await self._db.fetchall(
                f"SELECT id, query, mode, filters, is_alert, created_at, updated_at "  # nosec B608
                f"FROM {self._table} WHERE user_id = ? AND is_deleted = FALSE "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset),
            )
        return [dict(row) for row in rows]

    async def get_by_id(self, saved_id: int, user_id: int) -> Optional[dict]:
        if settings.uses_postgres:
            row = await self._db.fetchone(
                f"SELECT id, user_id, query, mode, filters, is_alert, created_at, updated_at "  # nosec B608
                f"FROM {self._table} WHERE id = $1 AND user_id = $2 AND is_deleted = FALSE",
                (saved_id, user_id),
            )
        else:
            row = await self._db.fetchone(
                f"SELECT id, user_id, query, mode, filters, is_alert, created_at, updated_at "  # nosec B608
                f"FROM {self._table} WHERE id = ? AND user_id = ? AND is_deleted = FALSE",
                (saved_id, user_id),
            )
        return dict(row) if row else None

    async def delete(self, saved_id: int, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if settings.uses_postgres:
            await self._db.execute(
                f"UPDATE {self._table} SET is_deleted = TRUE, deleted_at = $1 "  # nosec B608
                "WHERE id = $2 AND user_id = $3 AND is_deleted = FALSE",
                (now, saved_id, user_id),
            )
        else:
            await self._db.execute(
                f"UPDATE {self._table} SET is_deleted = TRUE, deleted_at = ? "  # nosec B608
                "WHERE id = ? AND user_id = ? AND is_deleted = FALSE",
                (now, saved_id, user_id),
            )
        await self._db.commit()

    async def count_for_user(self, user_id: int) -> int:
        """Return total non-deleted saved searches for a user."""
        if settings.uses_postgres:
            row = await self._db.fetchone(
                f"SELECT COUNT(*) AS cnt FROM {self._table} WHERE user_id = $1 AND is_deleted = FALSE",  # nosec B608
                (user_id,),
            )
        else:
            row = await self._db.fetchone(
                f"SELECT COUNT(*) AS cnt FROM {self._table} WHERE user_id = ? AND is_deleted = FALSE",  # nosec B608
                (user_id,),
            )
        return int(row["cnt"]) if row else 0
