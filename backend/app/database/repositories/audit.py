"""Audit log repository."""

import json
from typing import Any

from app.database.engine import DatabaseConnection


class AuditRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def create(
        self,
        user_id: int | None,
        action: str,
        resource: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        """Create audit log entry."""
        await self._db.execute(
            """INSERT INTO audit_logs 
               (user_id, action, resource, metadata_json, ip, user_agent, status, error_message) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                action,
                resource,
                json.dumps(metadata or {}),
                ip,
                user_agent,
                status,
                error_message,
            ),
        )
        await self._db.commit()

    async def create_audit_event(
        self,
        user_id: int | None,
        session_id: str | None,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        changes: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        location: str | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        """Create comprehensive audit event (for audit.audit_events table)."""
        await self._db.execute(
            """INSERT INTO audit.audit_events 
               (user_id, session_id, action, resource_type, resource_id, 
                old_values, new_values, changes, ip_address, user_agent, 
                location, status, error_message) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                session_id,
                action,
                resource_type,
                resource_id,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                json.dumps(changes) if changes else None,
                ip_address,
                user_agent,
                location,
                status,
                error_message,
            ),
        )
        await self._db.commit()

    async def get_recent(self, limit: int = 100):
        """Get recent audit logs."""
        return await self._db.fetchall(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )

    async def get_for_user(self, user_id: int, limit: int = 100):
        """Get audit logs for a specific user."""
        return await self._db.fetchall(
            "SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )

    async def get_by_action(self, action: str, limit: int = 100):
        """Get audit logs by action type."""
        return await self._db.fetchall(
            "SELECT * FROM audit_logs WHERE action = ? ORDER BY created_at DESC LIMIT ?",
            (action, limit),
        )

    async def get_by_ip(self, ip_address: str, limit: int = 100):
        """Get audit logs by IP address."""
        return await self._db.fetchall(
            "SELECT * FROM audit_logs WHERE ip = ? ORDER BY created_at DESC LIMIT ?",
            (ip_address, limit),
        )

    async def get_security_events(self, limit: int = 100):
        """Get security-related audit events."""
        security_actions = [
            "login",
            "logout",
            "failed_login",
            "password_reset",
            "email_verification",
            "mfa_enabled",
            "mfa_disabled",
            "mfa_backup_code_used",
            "security_alert",
            "account_lockout",
            "session_termination",
        ]
        placeholders = ",".join(["?" for _ in security_actions])
        return await self._db.fetchall(
            f"SELECT * FROM audit_logs WHERE action IN ({placeholders}) ORDER BY created_at DESC LIMIT ?",  # nosec B608: placeholders is ?,?… from static list, values bound separately
            (*security_actions, limit),
        )

    async def delete_old_logs(self, days: int = 90) -> None:
        """Delete audit logs older than N days."""
        # SQLite uses datetime('now', '-N days')
        # Postgres uses CURRENT_TIMESTAMP - INTERVAL 'N days'
        from app.config import get_settings
        settings = get_settings()
        if settings.uses_postgres:
            sql = f"DELETE FROM audit_logs WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '{int(days)} days'"  # nosec B608: days is coerced to int, no user-controlled string interpolation
        else:
            sql = f"DELETE FROM audit_logs WHERE created_at < datetime('now', '-{int(days)} days')"  # nosec B608: days is coerced to int, no user-controlled string interpolation
        await self._db.execute(sql)
        await self._db.commit()

    async def get_audit_statistics(self, days: int = 30) -> dict:
        """Get audit statistics for the last N days."""
        from app.config import get_settings
        settings = get_settings()
        
        if settings.uses_postgres:
            date_filter = f"CURRENT_TIMESTAMP - INTERVAL '{int(days)} days'"
        else:
            date_filter = f"datetime('now', '-{int(days)} days')"
        
        # Total events
        total = await self._db.fetchone(
            f"SELECT COUNT(*) as count FROM audit_logs WHERE created_at > {date_filter}",  # nosec B608: date_filter is built from int(days), not user input
        )
        
        # Events by action
        by_action = await self._db.fetchall(
            f"""SELECT action, COUNT(*) as count 
                FROM audit_logs 
                WHERE created_at > {date_filter}
                GROUP BY action 
                ORDER BY count DESC""",  # nosec B608: date_filter is built from int(days), not user input
        )
        
        # Events by user
        by_user = await self._db.fetchall(
            f"""SELECT user_id, COUNT(*) as count 
                FROM audit_logs 
                WHERE created_at > {date_filter} AND user_id IS NOT NULL
                GROUP BY user_id 
                ORDER BY count DESC 
                LIMIT 10""",  # nosec B608: date_filter is built from int(days), not user input
        )
        
        # Failed events
        failed = await self._db.fetchone(
            f"""SELECT COUNT(*) as count 
                FROM audit_logs 
                WHERE created_at > {date_filter} AND status = 'failure'""",  # nosec B608: date_filter is built from int(days), not user input
        )
        
        return {
            "total_events": total["count"] if total else 0,
            "by_action": {row["action"]: row["count"] for row in by_action},
            "by_user": {row["user_id"]: row["count"] for row in by_user},
            "failed_events": failed["count"] if failed else 0,
        }