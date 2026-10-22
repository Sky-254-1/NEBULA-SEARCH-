-- Migration 013: Create saved_searches table for SQLite
-- Idempotent: uses CREATE TABLE IF NOT EXISTS

CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'hybrid',
    filters TEXT DEFAULT '{}',
    is_alert INTEGER NOT NULL DEFAULT 0,
    label TEXT,
    last_run_at TEXT,
    run_count INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_saved_searches_user_id
    ON saved_searches (user_id);

CREATE INDEX IF NOT EXISTS idx_saved_searches_user_active
    ON saved_searches (user_id, is_deleted, created_at);
