"""Entities repository for entity recognition data."""


from app.database.engine import DatabaseConnection


class EntitiesRepository:
    """Repository for entity management."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def add_entity(
        self,
        entity_text: str,
        entity_type: str,
        frequency: int = 1,
        confidence: float = 1.0,
    ) -> int:
        """Add or update an entity. Returns entity ID."""
        await self._db.execute(
            """INSERT INTO entities (entity_text, entity_type, frequency, confidence)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_text, entity_type) DO UPDATE SET
                frequency = frequency + excluded.frequency,
                confidence = MAX(confidence, excluded.confidence)""",
            (entity_text.lower(), entity_type, frequency, confidence),
        )
        await self._db.commit()
        cursor = await self._db.execute(
            "SELECT id FROM entities WHERE entity_text = ? AND entity_type = ?",
            (entity_text.lower(), entity_type),
        )
        row = await cursor.fetchone()
        return row["id"] if row else 0

    async def get_entities_by_type(self, entity_type: str) -> list[dict]:
        """Get all entities of a specific type."""
        rows = await self._db.fetchall(
            "SELECT * FROM entities WHERE entity_type = ? ORDER BY frequency DESC",
            (entity_type,),
        )
        return [dict(row) for row in rows]

    async def get_entity(self, entity_text: str, entity_type: str) -> dict | None:
        """Get a specific entity."""
        row = await self._db.fetchone(
            "SELECT * FROM entities WHERE entity_text = ? AND entity_type = ?",
            (entity_text.lower(), entity_type),
        )
        return dict(row) if row else None

    async def search_entities(self, query: str, limit: int = 10) -> list[dict]:
        """Search entities by text."""
        rows = await self._db.fetchall(
            """SELECT * FROM entities 
            WHERE entity_text LIKE ? 
            ORDER BY frequency DESC 
            LIMIT ?""",
            (f"%{query.lower()}%", limit),
        )
        return [dict(row) for row in rows]

    async def get_popular_entities(self, limit: int = 20) -> list[dict]:
        """Get most popular entities."""
        rows = await self._db.fetchall(
            """SELECT entity_text, entity_type, SUM(frequency) as total_frequency,
            AVG(confidence) as avg_confidence
            FROM entities
            GROUP BY entity_text, entity_type
            ORDER BY total_frequency DESC
            LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in rows]

    async def delete_entity(self, entity_text: str, entity_type: str) -> bool:
        """Delete an entity."""
        await self._db.execute(
            "DELETE FROM entities WHERE entity_text = ? AND entity_type = ?",
            (entity_text.lower(), entity_type),
        )
        await self._db.commit()
        return True

    async def bulk_add_entities(self, entities: list[dict]) -> None:
        """Bulk add entities.
        
        Args:
            entities: List of dicts with keys: entity_text, entity_type, frequency, confidence
        """
        for ent in entities:
            await self.add_entity(
                ent["entity_text"],
                ent["entity_type"],
                ent.get("frequency", 1),
                ent.get("confidence", 1.0),
            )