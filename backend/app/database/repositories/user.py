"""User repository."""

from datetime import datetime, timezone
import json

from app.database.engine import DatabaseConnection


class UserRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def get_by_email(self, email: str):
        return await self._db.fetchone(
            """SELECT id, email, hashed_password, role, email_verified, 
                      is_active, is_locked, failed_login_attempts, last_login, 
                      created_at, updated_at, password_changed_at,
                      mfa_enabled, mfa_secret, mfa_backup_codes
               FROM users WHERE email = ? AND is_deleted = FALSE""",
            (email,),
        )

    async def create(self, email: str, hashed_password: str, role: str = "user") -> None:
        await self._db.execute(
            "INSERT INTO users (email, hashed_password, role) VALUES (?, ?, ?)",
            (email, hashed_password, role),
        )
        await self._db.commit()

    async def get_id_by_email(self, email: str) -> int | None:
        row = await self._db.fetchone(
            "SELECT id FROM users WHERE email = ? AND is_deleted = FALSE", 
            (email,)
        )
        return row["id"] if row else None

    async def get_by_id(self, user_id: int):
        return await self._db.fetchone(
            """SELECT id, email, hashed_password, role, email_verified, 
                      is_active, is_locked, failed_login_attempts, last_login, 
                      created_at, updated_at, password_changed_at,
                      mfa_enabled, mfa_secret, mfa_backup_codes
               FROM users WHERE id = ? AND is_deleted = FALSE""",
            (user_id,),
        )

    async def update_role(self, user_id: int, role: str) -> None:
        await self._db.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, user_id),
        )
        await self._db.commit()

    async def update_status(self, user_id: int, is_active: bool) -> None:
        """Activate or deactivate a user account."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?",
            (is_active, now, user_id),
        )
        await self._db.commit()

    async def update_email_verified(self, user_id: int, verified: bool) -> None:
        """Update email verification status."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE users SET email_verified = ?, updated_at = ? WHERE id = ?",
            (verified, now, user_id),
        )
        await self._db.commit()

    async def update_email(self, user_id: int, new_email: str) -> None:
        """Update user email address."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE users SET email = ?, email_verified = TRUE, updated_at = ? WHERE id = ?",
            (new_email, now, user_id),
        )
        await self._db.commit()

    async def update_password(self, user_id: int, hashed_password: str) -> None:
        """Update user password."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE users SET hashed_password = ?, password_changed_at = ? WHERE id = ?",
            (hashed_password, now, user_id),
        )
        await self._db.commit()

    async def update_last_login(self, user_id: int) -> None:
        """Update last login timestamp."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (now, user_id),
        )
        await self._db.commit()

    async def increment_failed_login(self, user_id: int) -> int:
        """Increment failed login attempts counter."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """UPDATE users 
               SET failed_login_attempts = failed_login_attempts + 1, 
                   last_failed_login = ? 
               WHERE id = ?""",
            (now, user_id),
        )
        await self._db.commit()
        
        # Get updated count
        user = await self.get_by_id(user_id)
        return user.get("failed_login_attempts", 0) if user else 0

    async def clear_failed_login(self, user_id: int) -> None:
        """Clear failed login attempts."""
        await self._db.execute(
            "UPDATE users SET failed_login_attempts = 0, last_failed_login = NULL WHERE id = ?",
            (user_id,),
        )
        await self._db.commit()

    async def lock_account(self, user_id: int, locked_until: datetime) -> None:
        """Lock user account."""
        await self._db.execute(
            "UPDATE users SET is_locked = TRUE, locked_until = ? WHERE id = ?",
            (locked_until.isoformat(), user_id),
        )
        await self._db.commit()

    async def unlock_account(self, user_id: int) -> None:
        """Unlock user account."""
        await self._db.execute(
            "UPDATE users SET is_locked = FALSE, locked_until = NULL, failed_login_attempts = 0 WHERE id = ?",
            (user_id,),
        )
        await self._db.commit()

    async def delete(self, user_id: int) -> None:
        """Soft delete user account."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE users SET is_deleted = TRUE, deleted_at = ? WHERE id = ?",
            (now, user_id),
        )
        await self._db.commit()

    async def hard_delete(self, user_id: int) -> None:
        """Permanently delete user (GDPR compliance)."""
        await self._db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await self._db.commit()

    async def update_mfa(
        self, 
        user_id: int, 
        mfa_enabled: bool, 
        mfa_secret: str = None, 
        mfa_backup_codes: list = None
    ) -> None:
        """Update MFA settings."""
        now = datetime.now(timezone.utc).isoformat()
        backup_codes_json = json.dumps(mfa_backup_codes) if mfa_backup_codes else None
        
        await self._db.execute(
            """UPDATE users 
               SET mfa_enabled = ?, mfa_secret = ?, mfa_backup_codes = ?, updated_at = ? 
               WHERE id = ?""",
            (mfa_enabled, mfa_secret, backup_codes_json, now, user_id),
        )
        await self._db.commit()

    async def disable_mfa(self, user_id: int) -> None:
        """Disable MFA for user."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """UPDATE users 
               SET mfa_enabled = FALSE, mfa_secret = NULL, mfa_backup_codes = NULL, 
                   updated_at = ? 
               WHERE id = ?""",
            (now, user_id),
        )
        await self._db.commit()

    async def update_mfa_backup_codes(self, user_id: int, backup_codes: list) -> None:
        """Update MFA backup codes."""
        now = datetime.now(timezone.utc).isoformat()
        backup_codes_json = json.dumps(backup_codes)
        
        await self._db.execute(
            """UPDATE users 
               SET mfa_backup_codes = ?, updated_at = ? 
               WHERE id = ?""",
            (backup_codes_json, now, user_id),
        )
        await self._db.commit()

    async def link_oauth(self, user_id: int, provider: str, provider_user_id: str) -> int:
        """Link OAuth account to user."""
        sql = """INSERT INTO auth.oauth_accounts 
                 (user_id, provider, provider_user_id) 
                 VALUES (?, ?, ?)"""
        cursor = await self._db.execute(sql, (user_id, provider, provider_user_id))
        await self._db.commit()
        
        if hasattr(cursor, "lastrowid"):
            return cursor.lastrowid
        return 0

    async def unlink_oauth(self, user_id: int, provider: str) -> None:
        """Unlink OAuth account from user."""
        await self._db.execute(
            "DELETE FROM auth.oauth_accounts WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        )
        await self._db.commit()

    async def get_oauth_accounts(self, user_id: int):
        """Get all OAuth accounts linked to user."""
        return await self._db.fetchall(
            """SELECT id, provider, provider_user_id, created_at 
               FROM auth.oauth_accounts 
               WHERE user_id = ? AND is_deleted = FALSE""",
            (user_id,),
        )

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all users (for admin)."""
        rows = await self._db.fetchall(
            """SELECT id, email, role, email_verified, is_active, is_locked,
                      failed_login_attempts, last_login, created_at, updated_at
               FROM users 
               WHERE is_deleted = FALSE
               ORDER BY created_at DESC 
               LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        return [dict(row) for row in rows]

    async def count_all(self) -> int:
        """Count total active (non-deleted) users."""
        row = await self._db.fetchone(
            "SELECT COUNT(*) AS cnt FROM users WHERE is_deleted = FALSE"
        )
        return row["cnt"] if row else 0
