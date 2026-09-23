-- Analytics tables for Nebula Search Dashboard

-- Search events log
CREATE TABLE IF NOT EXISTS search_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    user_id INTEGER,
    session_id TEXT NOT NULL,
    search_backend TEXT NOT NULL,
    search_type TEXT NOT NULL,  -- keyword, semantic, hybrid
    results_count INTEGER NOT NULL DEFAULT 0,
    response_time_ms REAL NOT NULL,
    clicked_result INTEGER,
    device TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_search_events_created_at ON search_events(created_at);
CREATE INDEX IF NOT EXISTS idx_search_events_query ON search_events(query);
CREATE INDEX IF NOT EXISTS idx_search_events_user_id ON search_events(user_id);
CREATE INDEX IF NOT EXISTS idx_search_events_session_id ON search_events(session_id);

-- Click events
CREATE TABLE IF NOT EXISTS click_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_event_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    document_id INTEGER NOT NULL,
    rank_position INTEGER NOT NULL,
    time_to_click REAL,  -- seconds from search to click
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (search_event_id) REFERENCES search_events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_click_events_search_event_id ON click_events(search_event_id);
CREATE INDEX IF NOT EXISTS idx_click_events_query ON click_events(query);
CREATE INDEX IF NOT EXISTS idx_click_events_user_id ON click_events(user_id);
CREATE INDEX IF NOT EXISTS idx_click_events_created_at ON click_events(created_at);

-- Response time metrics
CREATE TABLE IF NOT EXISTS response_time_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_latency REAL NOT NULL,
    db_latency REAL NOT NULL DEFAULT 0,
    redis_latency REAL NOT NULL DEFAULT 0,
    semantic_latency REAL NOT NULL DEFAULT 0,
    bm25_latency REAL NOT NULL DEFAULT 0,
    ranking_latency REAL NOT NULL DEFAULT 0,
    snippet_latency REAL NOT NULL DEFAULT 0,
    api_latency REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_response_time_created_at ON response_time_metrics(created_at);

-- Aggregated daily statistics
CREATE TABLE IF NOT EXISTS analytics_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    total_queries INTEGER NOT NULL DEFAULT 0,
    unique_users INTEGER NOT NULL DEFAULT 0,
    zero_result_queries INTEGER NOT NULL DEFAULT 0,
    total_clicks INTEGER NOT NULL DEFAULT 0,
    avg_response_time REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analytics_daily_date ON analytics_daily(date);

-- Aggregated hourly statistics
CREATE TABLE IF NOT EXISTS analytics_hourly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hour_timestamp TIMESTAMP NOT NULL UNIQUE,
    total_queries INTEGER NOT NULL DEFAULT 0,
    unique_users INTEGER NOT NULL DEFAULT 0,
    zero_result_queries INTEGER NOT NULL DEFAULT 0,
    total_clicks INTEGER NOT NULL DEFAULT 0,
    avg_response_time REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analytics_hourly_timestamp ON analytics_hourly(hour_timestamp);

-- Query trends
CREATE TABLE IF NOT EXISTS query_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    category TEXT NOT NULL,  -- trending, growing, declining, seasonal
    score REAL NOT NULL,
    period TEXT NOT NULL,  -- daily, weekly, monthly
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(query, category, period, date)
);

CREATE INDEX IF NOT EXISTS idx_query_trends_date ON query_trends(date);
CREATE INDEX IF NOT EXISTS idx_query_trends_category ON query_trends(category);

-- Popular queries cache
CREATE TABLE IF NOT EXISTS popular_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL UNIQUE,
    count INTEGER NOT NULL DEFAULT 0,
    last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_popular_queries_count ON popular_queries(count DESC);
-- CREATE INDEX IF NOT EXISTS idx_popular_queries_last_searched ON popular_queries(last_searched);
