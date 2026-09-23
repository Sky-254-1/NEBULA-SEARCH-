"""Tests for backend/app/database/repositories/synonyms.py."""

import pytest

from app.database.repositories.synonyms import SynonymsRepository


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    async def fetchone(self):
        return self._rows[0] if self._rows else None

    async def fetchall(self):
        return list(self._rows)


class FakeDB:
    def __init__(self, rows_by_query=None):
        self._rows_by_query = rows_by_query or {}
        self.committed = False
        self.executed = []

    async def execute(self, sql, args=None):
        self.executed.append((sql, args))
        return FakeCursor(self._rows_by_query.get(sql, []))

    async def commit(self):
        self.committed = True

    async def fetchone(self, sql, args=None):
        rows = self._rows_by_query.get(sql, [{}])
        return rows[0] if rows else None

    async def fetchall(self, sql, args=None):
        return list(self._rows_by_query.get(sql, []))


@pytest.fixture
def repo():
    db = FakeDB()
    return SynonymsRepository(db)


async def test_add_synonym_happy(repo):
    eid = await repo.add_synonym("car", "automobile")
    assert isinstance(eid, int)
    assert repo._db.committed is True


async def test_get_synonyms_happy(repo):
    repo._db._rows_by_query["SELECT * FROM synonyms WHERE term = ?"] = [
        {"id": 1, "term": "car", "synonym": "automobile", "language": "en", "bidirectional": 1}
    ]
    rows = await repo.get_synonyms("car")
    assert len(rows) == 1


async def test_get_synonyms_language_filter(repo):
    repo._db._rows_by_query["SELECT * FROM synonyms WHERE term = ? AND language = ?"] = [
        {"id": 1, "term": "car", "synonym": "automobile", "language": "en", "bidirectional": 1}
    ]
    rows = await repo.get_synonyms("car", language="en")
    assert len(rows) == 1


async def test_expand_query_happy(repo):
    repo._db._rows_by_query["SELECT * FROM synonyms WHERE term = ?"] = [
        {"id": 1, "term": "car", "synonym": "automobile"}
    ]
    expanded = await repo.expand_query("car rental")
    assert "car" in expanded
    assert "automobile" in expanded


async def test_delete_synonym_happy(repo):
    repo._db._rows_by_query["SELECT * FROM synonyms WHERE term = ? AND synonym = ?"] = [
        {"id": 1, "term": "car", "synonym": "automobile"}
    ]
    deleted = await repo.delete_synonym("car", "automobile")
    assert deleted is True
    assert repo._db.committed is True


async def test_bulk_add_synonyms_happy(repo):
    pairs = [("car", "automobile"), ("phone", "mobile")]
    await repo.bulk_add_synonyms(pairs)
    assert len(repo._db.executed) >= 2


async def test_get_all_synonyms_happy(repo):
    repo._db._rows_by_query["SELECT * FROM synonyms ORDER BY term"] = [
        {"id": 1, "term": "car", "synonym": "automobile"},
        {"id": 2, "term": "phone", "synonym": "mobile"},
    ]
    rows = await repo.get_all_synonyms()
    assert len(rows) == 2