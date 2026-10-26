"""Search history repository for tracking user search queries."""

from app.database.engine import DatabaseConnection


class SearchHistoryRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db
