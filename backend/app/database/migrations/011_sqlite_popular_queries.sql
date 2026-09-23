-- ============================================
-- Migration 011: Create popular_queries Table for Autocomplete
-- Created: 2026-07-21
-- Description: Creates table for autocomplete functionality
-- ===========================================

-- Create popular_queries table for autocomplete suggestions
CREATE TABLE IF NOT EXISTS popular_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    count INTEGER DEFAULT 1 NOT NULL,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_query_length CHECK (LENGTH(query) <= 1000)
);

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_popular_queries_user_id ON popular_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_popular_queries_query ON popular_queries(query);
CREATE INDEX IF NOT EXISTS idx_popular_queries_count ON popular_queries(count DESC);
CREATE INDEX IF NOT EXISTS idx_popular_queries_last_used ON popular_queries(last_used DESC);

-- Insert initial popular queries for testing
INSERT OR IGNORE INTO popular_queries (query, count, last_used) VALUES
    ('python', 100, CURRENT_TIMESTAMP),
    ('javascript', 85, CURRENT_TIMESTAMP),
    ('react', 75, CURRENT_TIMESTAMP),
    ('api', 70, CURRENT_TIMESTAMP),
    ('database', 65, CURRENT_TIMESTAMP),
    ('search', 60, CURRENT_TIMESTAMP),
    ('help', 55, CURRENT_TIMESTAMP),
    ('login', 50, CURRENT_TIMESTAMP),
    ('register', 48, CURRENT_TIMESTAMP),
    ('welcome', 45, CURRENT_TIMESTAMP);
