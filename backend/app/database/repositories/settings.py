"""User settings repository."""

import json
from datetime import datetime, timezone

from app.database.engine import DatabaseConnection


class SettingsRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def get_for_user(self, user_id: int) -> dict:
        row = await self._db.fetchone("SELECT data_json FROM settings WHERE user_id = ?", (user_id,))
        if not row:
            return {}
        try:
            return json.loads(row["data_json"])
        except json.JSONDecodeError:
            return {}

    async def upsert(self, user_id: int, data: dict) -> dict:
        existing = await self.get_for_user(user_id)
        merged = {**existing, **data}
        payload = json.dumps(merged)
        now = datetime.now(timezone.utc).isoformat()
        row = await self._db.fetchone("SELECT id FROM settings WHERE user_id = ?", (user_id,))
        if row:
            await self._db.execute(
                "UPDATE settings SET data_json = ?, updated_at = ? WHERE user_id = ?",
                (payload, now, user_id),
            )
        else:
            await self._db.execute(
                "INSERT INTO settings (user_id, data_json, updated_at) VALUES (?, ?, ?)",
                (user_id, payload, now),
            )
        await self._db.commit()
        return merged
