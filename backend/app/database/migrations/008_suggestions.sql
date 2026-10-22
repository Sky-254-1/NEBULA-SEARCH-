-- Search Suggestions System
-- Supports trending queries, semantic suggestions, and related searches

-- SQLite version
-- Table: search_suggestions
CREATE TABLE IF NOT EXISTS search_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL COLLATE NOCASE,
    suggestion TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('trending', 'semantic', 'related', 'personalized')),
    score REAL NOT NULL DEFAULT 0.0,
    frequency INTEGER NOT NULL DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: search_suggestions is created with type column above, so no ALTER TABLE needed.
-- SQLite does not support CHECK constraints in ALTER TABLE ADD COLUMN, so the column
-- is defined in the CREATE TABLE IF NOT EXISTS above. The backfill below handles
-- pre-existing rows from a prior schema version that lacked the type column.
UPDATE search_suggestions SET type = 'personalized' WHERE type IS NULL;

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_search_suggestions_query ON search_suggestions(query);
CREATE INDEX IF NOT EXISTS idx_search_suggestions_type ON search_suggestions(type);
CREATE INDEX IF NOT EXISTS idx_search_suggestions_score ON search_suggestions(score DESC);
CREATE INDEX IF NOT EXISTS idx_search_suggestions_frequency ON search_suggestions(frequency DESC);

-- Table: trending_queries
CREATE TABLE IF NOT EXISTS trending_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL UNIQUE COLLATE NOCASE,
    frequency INTEGER NOT NULL DEFAULT 1,
    searches_today INTEGER NOT NULL DEFAULT 0,
    searches_week INTEGER NOT NULL DEFAULT 0,
    searches_month INTEGER NOT NULL DEFAULT 0,
    growth_rate REAL NOT NULL DEFAULT 0.0,
    popularity_score REAL NOT NULL DEFAULT 0.0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trending_queries_popularity ON trending_queries(popularity_score DESC);
CREATE INDEX IF NOT EXISTS idx_trending_queries_frequency ON trending_queries(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_trending_queries_last_used ON trending_queries(last_used DESC);

-- Table: related_searches
CREATE TABLE IF NOT EXISTS related_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL COLLATE NOCASE,
    related_query TEXT NOT NULL COLLATE NOCASE,
    co_occurrence_count INTEGER NOT NULL DEFAULT 1,
    click_count INTEGER NOT NULL DEFAULT 0,
    score REAL NOT NULL DEFAULT 0.0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(query, related_query)
);

CREATE INDEX IF NOT EXISTS idx_related_searches_query ON related_searches(query);
CREATE INDEX IF NOT EXISTS idx_related_searches_score ON related_searches(score DESC);

-- Table: search_analytics
CREATE TABLE IF NOT EXISTS search_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL COLLATE NOCASE,
    user_id INTEGER,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    clicked_result_id INTEGER,
    response_time_ms INTEGER,
    result_count INTEGER DEFAULT 0,
    autocomplete_used BOOLEAN DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_search_analytics_query ON search_analytics(query);
CREATE INDEX IF NOT EXISTS idx_search_analytics_timestamp ON search_analytics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_search_analytics_user_id ON search_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_search_analytics_session_id ON search_analytics(session_id);

-- Table: user_search_preferences
CREATE TABLE IF NOT EXISTS user_search_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    preferred_categories TEXT DEFAULT '[]',
    frequent_queries TEXT DEFAULT '[]',
    personalization_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Triggers for updating timestamps
CREATE TRIGGER IF NOT EXISTS update_search_suggestions_timestamp
    AFTER UPDATE ON search_suggestions
    FOR EACH ROW
    BEGIN
        UPDATE search_suggestions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_trending_queries_timestamp
    AFTER UPDATE ON trending_queries
    FOR EACH ROW
    BEGIN
        UPDATE trending_queries SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_related_searches_timestamp
    AFTER UPDATE ON related_searches
    FOR EACH ROW
    BEGIN
        UPDATE related_searches SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;