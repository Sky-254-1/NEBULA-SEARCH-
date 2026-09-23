from app.database.engine import DatabaseConnection

class CollectionRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, user_id: int, name: str, description: str | None, is_public: bool) -> int:
        row = await self.db.fetchone(
            "INSERT INTO collections (user_id, name, description, is_public) VALUES (?, ?, ?, ?) RETURNING id",
            (user_id, name, description, is_public),
        )
        return row["id"] if row else None

    async def list_for_user(self, user_id: int) -> list[dict]:
        return await self.db.fetchall(
            """SELECT c.*, (SELECT COUNT(*) FROM collection_items ci WHERE ci.collection_id = c.id) as item_count
               FROM collections c WHERE c.user_id = ? ORDER BY c.updated_at DESC""",
            (user_id,),
        )

    async def get_by_id(self, collection_id: int, user_id: int) -> dict | None:
        row = await self.db.fetchone(
            "SELECT * FROM collections WHERE id = ? AND user_id = ?",
            (collection_id, user_id),
        )
        if row:
            count = await self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM collection_items WHERE collection_id = ?",
                (collection_id,),
            )
            row["item_count"] = count["cnt"] if count else 0
        return row

    async def update(self, collection_id: int, user_id: int, **kwargs) -> None:
        sets = []
        params = []
        for key, val in kwargs.items():
            if val is not None:
                sets.append(f"{key} = ?")
                params.append(val)
        if sets:
            params.extend([collection_id, user_id])
            await self.db.execute(
                 f"UPDATE collections SET {', '.join(sets)} WHERE id = ? AND user_id = ?",  # nosec B608: SET columns come from kwargs keys, values are parameterized
                tuple(params),
            )
            await self.db.commit()

    async def delete(self, collection_id: int, user_id: int) -> None:
        await self.db.execute("DELETE FROM collection_items WHERE collection_id = ?", (collection_id,))
        await self.db.execute("DELETE FROM collections WHERE id = ? AND user_id = ?", (collection_id, user_id))
        await self.db.commit()

    async def add_item(self, collection_id: int, document_id: int | None, search_result_id: int | None, note: str | None = None) -> int:
        row = await self.db.fetchone(
            "INSERT INTO collection_items (collection_id, document_id, search_result_id, note) VALUES (?, ?, ?, ?) RETURNING id",
            (collection_id, document_id, search_result_id, note),
        )
        return row["id"] if row else None

    async def list_items(self, collection_id: int) -> list[dict]:
        return await self.db.fetchall(
            "SELECT * FROM collection_items WHERE collection_id = ? ORDER BY created_at DESC",
            (collection_id,),
        )

    async def remove_item(self, item_id: int) -> None:
        await self.db.execute("DELETE FROM collection_items WHERE id = ?", (item_id,))
        await self.db.commit()
