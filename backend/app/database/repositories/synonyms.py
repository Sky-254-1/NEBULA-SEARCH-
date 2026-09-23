"""Synonyms repository for query expansion."""


from app.database.engine import DatabaseConnection


class SynonymsRepository:
    """Repository for synonym management."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    async def add_synonym(
        self,
        term: str,
        synonym: str,
        language: str = "en",
        bidirectional: bool = True,
    ) -> int:
        """Add a synonym. Returns the synonym ID."""
        await self._db.execute(
            """INSERT INTO synonyms (term, synonym, language, bidirectional)
            VALUES (?, ?, ?, ?)""",
            (term.lower(), synonym.lower(), language, 1 if bidirectional else 0),
        )
        await self._db.commit()
        cursor = await self._db.execute("SELECT last_insert_rowid()")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_synonyms(self, term: str, language: str = None) -> list[dict]:
        """Get synonyms for a term."""
        query = "SELECT * FROM synonyms WHERE term = ?"
        params: list = [term.lower()]
        if language:
            query += " AND language = ?"
            params.append(language)
        rows = await self._db.fetchall(query, tuple(params))
        return [dict(row) for row in rows]

    async def expand_query(self, query: str, language: str = None) -> list[str]:
        """Expand query with synonyms. Returns original terms + synonyms."""
        terms = query.lower().split()
        expanded = set(terms)

        for term in terms:
            synonyms = await self.get_synonyms(term, language)
            for syn in synonyms:
                expanded.add(syn["synonym"])

        return list(expanded)

    async def delete_synonym(self, term: str, synonym: str) -> bool:
        """Delete a synonym."""
        await self._db.execute(
            "DELETE FROM synonyms WHERE term = ? AND synonym = ?",
            (term.lower(), synonym.lower()),
        )
        await self._db.commit()
        return True

    async def bulk_add_synonyms(self, pairs: list[tuple[str, str]], language: str = "en") -> None:
        """Bulk add synonym pairs."""
        for term, synonym in pairs:
            await self.add_synonym(term, synonym, language)

    async def get_all_synonyms(self) -> list[dict]:
        """Get all synonyms."""
        rows = await self._db.fetchall("SELECT * FROM synonyms ORDER BY term")
        return [dict(row) for row in rows]