"""Spell correction repository for dictionary and frequency management."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("nebula.spell")


class SpellRepository:
    """Repository for spell dictionary operations."""

    def __init__(self, db: Any):
        self._db = db

    async def get_all_words(self) -> list[str]:
        """Retrieve all words from the spell dictionary."""
        try:
            rows = await self._db.fetchall(
                "SELECT word FROM spell_dictionary WHERE frequency > 0"
            )
            return [row["word"] for row in rows]
        except Exception:
            return []

    async def get_all_frequencies(self) -> dict[str, int]:
        """Retrieve word frequencies from the spell dictionary."""
        try:
            rows = await self._db.fetchall(
                "SELECT word, frequency FROM spell_dictionary"
            )
            return {row["word"]: row["frequency"] for row in rows}
        except Exception:
            return {}

    async def upsert_word(self, word: str, frequency: int = 1) -> None:
        """Insert or update a word in the dictionary."""
        try:
            if self._db.__class__.__name__ == "PostgresConnection":
                await self._db.execute(
                    """
                    INSERT INTO spell_dictionary (word, frequency)
                    VALUES ($1, $2)
                    ON CONFLICT (word) DO UPDATE SET frequency = spell_dictionary.frequency + $2
                    """,
                    (word, frequency),
                )
            elif self._db.__class__.__name__ == "PostgresPooledConnection":
                await self._db.execute(
                    """
                    INSERT INTO spell_dictionary (word, frequency)
                    VALUES ($1, $2)
                    ON CONFLICT (word) DO UPDATE SET frequency = spell_dictionary.frequency + $2
                    """,
                    (word, frequency),
                )
            else:
                await self._db.execute(
                    """
                    INSERT INTO spell_dictionary (word, frequency)
                    VALUES (?, ?)
                    ON CONFLICT(word) DO UPDATE SET frequency = frequency + ?
                    """,
                    (word, frequency, frequency),
                )
        except Exception as exc:
            logger.warning("upsert_word failed for %s: %s", word, exc)

    async def bulk_upsert(self, items: list[tuple[str, int]]) -> None:
        """Bulk insert or update words."""
        if not items:
            return
        try:
            for word, freq in items:
                await self.upsert_word(word, freq)
        except Exception as exc:
            logger.warning("bulk_upsert failed: %s", exc)

    async def get_frequency(self, word: str) -> int:
        """Get frequency of a specific word."""
        try:
            row = await self._db.fetchone(
                "SELECT frequency FROM spell_dictionary WHERE word = ?",
                (word,),
            )
            return row["frequency"] if row else 0
        except Exception:
            return 0

    async def delete_word(self, word: str) -> None:
        """Delete a word from the dictionary."""
        try:
            await self._db.execute(
                "DELETE FROM spell_dictionary WHERE word = ?", (word,)
            )
        except Exception as exc:
            logger.warning("delete_word failed for %s: %s", word, exc)

    async def clear_dictionary(self) -> None:
        """Clear all entries from the dictionary."""
        try:
            await self._db.execute("DELETE FROM spell_dictionary")
        except Exception as exc:
            logger.warning("clear_dictionary failed: %s", exc)

    async def dictionary_size(self) -> int:
        """Return number of words in dictionary."""
        try:
            row = await self._db.fetchone("SELECT COUNT(*) as cnt FROM spell_dictionary")
            return row["cnt"] if row else 0
        except Exception:
            return 0