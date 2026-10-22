"""Email verification and password reset token repository."""

from datetime import datetime, timezone

from app.database.engine import DatabaseConnection


class EmailVerificationRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(self, user_id: int, token_hash: str, expires_at: datetime, pending_email: str = None) -> int:
        """Create an email verification token."""
        sql = """INSERT INTO email_verification 
                 (user_id, token_hash, expires_at, pending_email) 
                 VALUES (?, ?, ?, ?)"""
        cursor = await self._db.execute(sql, (user_id, token_hash, expires_at.isoformat(), pending_email))
        await self._db.commit()
        
        if hasattr(cursor, "lastrowid"):
            return cursor.lastrowid
        return 0

    async def get_by_token_hash(self, token_hash: str):
        """Get verification token by hash."""
        return await self._db.fetchone(
            """SELECT id, user_id, token_hash, is_used, expires_at, created_at, pending_email 
               FROM email_verification 
               WHERE token_hash = ? AND is_used = FALSE AND is_deleted = FALSE""",
            (token_hash,),
        )

    async def get_by_user_id(self, user_id: int, active_only: bool = True):
        """Get verification tokens for a user."""
        if active_only:
            return await self._db.fetchall(
                """SELECT id, token_hash, is_used, expires_at, created_at 
                   FROM email_verification 
                   WHERE user_id = ? AND is_used = FALSE AND is_deleted = FALSE 
                   ORDER BY created_at DESC""",
                (user_id,),
            )
        return await self._db.fetchall(
            """SELECT id, token_hash, is_used, expires_at, created_at 
               FROM email_verification 
               WHERE user_id = ? AND is_deleted = FALSE 
               ORDER BY created_at DESC""",
            (user_id,),
        )

    async def mark_as_used(self, token_id: int) -> None:
        """Mark verification token as used."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE email_verification SET is_used = TRUE, used_at = ? WHERE id = ?",
            (now, token_id),
        )
        await self._db.commit()

    async def invalidate_user_tokens(self, user_id: int) -> None:
        """Invalidate all unused verification tokens for a user."""
        await self._db.execute(
            "UPDATE email_verification SET is_deleted = TRUE WHERE user_id = ? AND is_used = FALSE",
            (user_id,),
        )
        await self._db.commit()

    async def delete_expired(self) -> None:
        """Delete expired verification tokens."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "DELETE FROM email_verification WHERE expires_at < ? AND is_deleted = FALSE",
            (now,),
        )
        await self._db.commit()


class PasswordResetRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(self, user_id: int, token_hash: str, expires_at: datetime, 
                     ip_address: str = None, user_agent: str = None) -> int:
        """Create a password reset token."""
        sql = """INSERT INTO password_reset 
                 (user_id, token_hash, expires_at, ip_address, user_agent) 
                 VALUES (?, ?, ?, ?, ?)"""
        cursor = await self._db.execute(
            sql, 
            (user_id, token_hash, expires_at.isoformat(), ip_address, user_agent)
        )
        await self._db.commit()
        
        if hasattr(cursor, "lastrowid"):
            return cursor.lastrowid
        return 0

    async def get_by_token_hash(self, token_hash: str):
        """Get reset token by hash."""
        return await self._db.fetchone(
            """SELECT id, user_id, token_hash, is_used, expires_at, ip_address, user_agent, created_at 
               FROM password_reset 
               WHERE token_hash = ? AND is_used = FALSE AND is_deleted = FALSE""",
            (token_hash,),
        )

    async def get_by_user_id(self, user_id: int, active_only: bool = True):
        """Get reset tokens for a user."""
        if active_only:
            return await self._db.fetchall(
                """SELECT id, token_hash, is_used, expires_at, created_at 
                   FROM password_reset 
                   WHERE user_id = ? AND is_used = FALSE AND is_deleted = FALSE 
                   ORDER BY created_at DESC""",
                (user_id,),
            )
        return await self._db.fetchall(
            """SELECT id, token_hash, is_used, expires_at, created_at 
               FROM password_reset 
               WHERE user_id = ? AND is_deleted = FALSE 
               ORDER BY created_at DESC""",
            (user_id,),
        )

    async def mark_as_used(self, token_id: int) -> None:
        """Mark reset token as used."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE password_reset SET is_used = TRUE, used_at = ? WHERE id = ?",
            (now, token_id),
        )
        await self._db.commit()

    async def invalidate_user_tokens(self, user_id: int) -> None:
        """Invalidate all unused reset tokens for a user."""
        await self._db.execute(
            "UPDATE password_reset SET is_deleted = TRUE WHERE user_id = ? AND is_used = FALSE",
            (user_id,),
        )
        await self._db.commit()

    async def delete_expired(self) -> None:
        """Delete expired reset tokens."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "DELETE FROM password_reset WHERE expires_at < ? AND is_deleted = FALSE",
            (now,),
        )
        await self._db.commit()
