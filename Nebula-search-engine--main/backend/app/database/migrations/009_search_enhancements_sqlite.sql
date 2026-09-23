-- Migration 009: Search enhancements (saved searches, search suggestions) - SQLite-safe

CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    mode TEXT DEFAULT 'hybrid' NOT NULL,
    filters TEXT DEFAULT '{}',
    is_alert INTEGER DEFAULT 0 NOT NULL,
    last_alerted_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0 NOT NULL,
    deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_saved_searches_user ON saved_searches(user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_searches_user_query ON saved_searches(user_id, query) WHERE is_deleted = 0;
