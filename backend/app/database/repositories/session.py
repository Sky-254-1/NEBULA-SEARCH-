"""Session (refresh token) repository."""

import uuid
from datetime import datetime, timezone

from app.database.engine import DatabaseConnection


class SessionRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        user_id: int,
        refresh_token_hash: str,
        expires_at: datetime,
        session_id: str | None = None,
        device_name: str | None = None,
        device_type: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        parent_refresh_id: int | None = None,
    ) -> int:
        from app.config import get_settings
        get_settings()

        # Generate session_id if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())

        sql = """INSERT INTO auth_sessions
                 (user_id, token_hash, expires_at, session_id, device_name, 
                  device_type, ip_address, user_agent, parent_refresh_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        cursor = await self._db.execute(
            sql,
            (
                user_id,
                refresh_token_hash,
                expires_at.isoformat(),
                session_id,
                device_name,
                device_type,
                ip_address,
                user_agent,
                parent_refresh_id,
            ),
        )
        await self._db.commit()

        if hasattr(cursor, "lastrowid"):
            return cursor.lastrowid
        return 0

    async def get_by_hash(self, refresh_token_hash: str):
        return await self._db.fetchone(
            """SELECT id, user_id, expires_at, session_id, device_name, device_type,
                      ip_address, user_agent, parent_refresh_id, rotated_at, 
                      revoked_reason, is_active, created_at, last_activity_at
               FROM auth_sessions 
               WHERE token_hash = ? AND is_deleted = FALSE""",
            (refresh_token_hash,),
        )

    async def get_by_session_id(self, session_id: str):
        return await self._db.fetchone(
            """SELECT id, user_id, session_id, token_hash, device_name, device_type,
                      ip_address, user_agent, is_active, expires_at, created_at, 
                      last_activity_at, terminated_at, termination_reason
               FROM auth_sessions 
               WHERE session_id = ? AND is_deleted = FALSE""",
            (session_id,),
        )

    async def get_active_for_user(self, user_id: int):
        """Get all active sessions for a user."""
        return await self._db.fetchall(
            """SELECT id, session_id, device_name, device_type, ip_address, user_agent,
                      created_at, last_activity_at, expires_at
               FROM auth_sessions 
               WHERE user_id = ? AND is_active = TRUE 
                     AND is_deleted = FALSE 
                     AND expires_at > ?
               ORDER BY last_activity_at DESC""",
            (user_id, datetime.now(timezone.utc).isoformat()),
        )

    async def delete(self, session_id: int) -> None:
        await self._db.execute("DELETE FROM auth_sessions WHERE id = ?", (session_id,))
        await self._db.commit()

    async def delete_by_session_id(self, session_id: str) -> None:
        await self._db.execute(
            "DELETE FROM auth_sessions WHERE session_id = ?", 
            (session_id,)
        )
        await self._db.commit()

    async def delete_all_for_user(self, user_id: int) -> None:
        await self._db.execute(
            "DELETE FROM auth_sessions WHERE user_id = ?", 
            (user_id,)
        )
        await self._db.commit()

    async def revoke_session_family(self, session_id: str, reason: str) -> None:
        await self._db.execute(
            "UPDATE auth_sessions SET revoked_reason = ? WHERE session_id = ?",
            (reason, session_id),
        )
        await self._db.commit()

    async def update_rotation(self, session_id: int, rotated_at: datetime) -> None:
        await self._db.execute(
            "UPDATE auth_sessions SET rotated_at = ? WHERE id = ?",
            (rotated_at.isoformat(), session_id),
        )
        await self._db.commit()

    async def update_last_seen(self, session_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE auth_sessions SET last_activity_at = ? WHERE id = ?",
            (now, session_id),
        )
        await self._db.commit()

    async def terminate_session(self, session_id: str, reason: str) -> None:
        """Terminate a session."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """UPDATE auth_sessions 
               SET is_active = FALSE, terminated_at = ?, termination_reason = ? 
               WHERE session_id = ?""",
            (now, reason, session_id),
        )
        await self._db.commit()

    async def delete_expired(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "DELETE FROM auth_sessions WHERE expires_at < ? AND is_deleted = FALSE",
            (now,),
        )
        await self._db.commit()
