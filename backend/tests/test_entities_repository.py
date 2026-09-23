"""Tests for backend/app/database/repositories/entities.py."""

import pytest

from app.database.repositories.entities import EntitiesRepository


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
    return EntitiesRepository(db)


async def test_add_entity_happy(repo):
    eid = await repo.add_entity("python", "language", frequency=5, confidence=0.9)
    assert isinstance(eid, int)
    assert repo._db.committed is True


async def test_get_entities_by_type_happy(repo):
    repo._db._rows_by_query["SELECT * FROM entities WHERE entity_type = ? ORDER BY frequency DESC"] = [
        {"id": 1, "entity_text": "python", "entity_type": "language", "frequency": 5, "confidence": 0.9}
    ]
    rows = await repo.get_entities_by_type("language")
    assert len(rows) == 1
    assert rows[0]["entity_text"] == "python"


async def test_get_entities_by_type_no_results(repo):
    repo._db._rows_by_query["SELECT * FROM entities WHERE entity_type = ? ORDER BY frequency DESC"] = []
    rows = await repo.get_entities_by_type("missing")
    assert rows == []


async def test_get_entity_happy(repo):
    repo._db._rows_by_query["SELECT * FROM entities WHERE entity_text = ? AND entity_type = ?"] = [
        {"id": 2, "entity_text": "fastapi", "entity_type": "framework", "frequency": 1, "confidence": 1.0}
    ]
    result = await repo.get_entity("fastapi", "framework")
    assert result is not None
    assert result["entity_text"] == "fastapi"


async def test_search_entities_happy(repo):
    repo._db._rows_by_query["""SELECT * FROM entities 
            WHERE entity_text LIKE ? 
            ORDER BY frequency DESC 
            LIMIT ?"""] = [
        {"id": 3, "entity_text": "nebula search", "entity_type": "product", "frequency": 1, "confidence": 1.0}
    ]
    results = await repo.search_entities("nebula", limit=10)
    assert len(results) >= 1


async def test_get_popular_entities_happy(repo):
    repo._db._rows_by_query["""SELECT entity_text, entity_type, SUM(frequency) as total_frequency,
            AVG(confidence) as avg_confidence
            FROM entities
            GROUP BY entity_text, entity_type
            ORDER BY total_frequency DESC
            LIMIT ?"""] = [
        {"entity_text": "python", "entity_type": "language", "total_frequency": 15, "avg_confidence": 0.95}
    ]
    popular = await repo.get_popular_entities(limit=5)
    assert len(popular) >= 1


async def test_delete_entity_happy(repo):
    repo._db._rows_by_query["SELECT id FROM entities WHERE entity_text = ? AND entity_type = ?"] = [
        {"id": 4, "entity_text": "tmp", "entity_type": "test"}
    ]
    deleted = await repo.delete_entity("tmp", "test")
    assert deleted is True
    assert repo._db.committed is True


async def test_bulk_add_entities_happy(repo):
    entities = [
        {"entity_text": "a", "entity_type": "t"},
        {"entity_text": "b", "entity_type": "t", "frequency": 2},
    ]
    await repo.bulk_add_entities(entities)
    assert len(repo._db.executed) >= 2


async def test_add_entity_failure_missing_db_methods(repo):
    """Failure path: DB missing fetchone should surface cleanly."""

    class BrokenDB:
        async def execute(self, *args, **kwargs):
            return self
        async def commit(self):
            return None

    bad = EntitiesRepository(BrokenDB())  # type: ignore[arg-type]
    with pytest.raises(Exception):
        await bad.add_entity("x", "y")