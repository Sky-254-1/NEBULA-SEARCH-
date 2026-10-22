"""Tests for backend/app/database/repositories/search_history.py."""

import pytest

from app.database.repositories.search_history import SearchHistoryRepository


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
    return SearchHistoryRepository(db)


async def test_record_search_happy(repo):
    eid = await repo.record_search(user_id=1, query="nebula", result_count=3)
    assert isinstance(eid, int)
    assert repo._db.committed is True


async def test_get_user_history_happy(repo):
    repo._db._rows_by_query["""SELECT * FROM search_history 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC 
            LIMIT ?"""] = [
        {"id": 1, "user_id": 1, "query": "nebula", "result_count": 3}
    ]
    rows = await repo.get_user_history(user_id=1, limit=5, days=30)
    assert len(rows) == 1


async def test_get_user_history_no_results(repo):
    repo._db._rows_by_query["""SELECT * FROM search_history 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC 
            LIMIT ?"""] = []
    rows = await repo.get_user_history(user_id=99, limit=5, days=30)
    assert rows == []


async def test_get_popular_searches_happy(repo):
    repo._db._rows_by_query["""SELECT query, COUNT(*) as search_count, 
            AVG(result_count) as avg_results,
            MAX(created_at) as last_searched
            FROM search_history 
            WHERE created_at >= datetime('now', ?)
            GROUP BY query 
            ORDER BY search_count DESC 
            LIMIT ?"""] = [
        {"query": "nebula", "search_count": 5, "avg_results": 3.0, "last_searched": "2024-01-01"}
    ]
    rows = await repo.get_popular_searches(limit=5, days=7)
    assert len(rows) == 1


async def test_get_user_queries_happy(repo):
    repo._db._rows_by_query["""SELECT DISTINCT query FROM search_history 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC"""] = [
        {"query": "nebula"}
    ]
    queries = await repo.get_user_queries(user_id=1, days=30)
    assert len(queries) == 1


async def test_delete_history_item_happy(repo):
    repo._db._rows_by_query["SELECT * FROM search_history WHERE id = ? AND user_id = ?"] = [
        {"id": 1, "user_id": 1, "query": "nebula", "result_count": 3}
    ]
    deleted = await repo.delete_history_item(user_id=1, search_id=1)
    assert deleted is True
    assert repo._db.committed is True


async def test_clear_user_history_happy(repo):
    repo._db._rows_by_query["SELECT * FROM search_history WHERE user_id = ?"] = [
        {"id": 1, "user_id": 1},
        {"id": 2, "user_id": 1},
    ]
    await repo.clear_user_history(user_id=1)
    assert repo._db.committed is True