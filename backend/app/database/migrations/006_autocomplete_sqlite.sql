-- Nebula Search — Autocomplete system v1 (SQLite)

-- Recent searches per user
CREATE TABLE IF NOT EXISTS recent_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_recent_searches_user_id ON recent_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_recent_searches_searched_at ON recent_searches(searched_at DESC);

-- Popular queries across all users
CREATE TABLE IF NOT EXISTS popular_queries (
    query TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_popular_queries_count ON popular_queries(count DESC);
CREATE INDEX IF NOT EXISTS idx_popular_queries_last_used ON popular_queries(last_used DESC);