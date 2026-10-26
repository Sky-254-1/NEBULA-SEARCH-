"""Analytics repository for tracking search and indexing metrics."""

from app.database.engine import DatabaseConnection


class AnalyticsRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db
