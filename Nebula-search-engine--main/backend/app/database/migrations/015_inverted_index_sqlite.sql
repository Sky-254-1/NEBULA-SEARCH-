-- Inverted index for full-text search (SQLite version)
-- Supports BM25 ranking and fast keyword lookup

-- Documents table for crawled/indexed content
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    language TEXT DEFAULT 'en',
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'indexed' NOT NULL,
    last_indexed TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Inverted index: word -> document occurrences
CREATE TABLE IF NOT EXISTS inverted_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    term_frequency INTEGER NOT NULL DEFAULT 1,
    positions TEXT NOT NULL DEFAULT '[]',
    field TEXT NOT NULL DEFAULT 'content',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast word lookup
CREATE INDEX IF NOT EXISTS idx_inverted_index_word ON inverted_index(word);

-- Composite index for document+word queries
CREATE INDEX IF NOT EXISTS idx_inverted_index_document_word ON inverted_index(document_id, word);

-- Document stats for BM25 scoring
CREATE TABLE IF NOT EXISTS document_stats (
    document_id INTEGER PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    avg_term_frequency REAL NOT NULL DEFAULT 0.0,
    unique_words INTEGER NOT NULL DEFAULT 0,
    total_terms INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Global corpus stats for BM25
CREATE TABLE IF NOT EXISTS corpus_stats (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total_documents INTEGER NOT NULL DEFAULT 0,
    avg_document_length REAL NOT NULL DEFAULT 0.0,
    total_terms INTEGER NOT NULL DEFAULT 0,
    vocabulary_size INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default corpus stats if not exists
INSERT OR IGNORE INTO corpus_stats (id, total_documents, avg_document_length, total_terms, vocabulary_size)
VALUES (1, 0, 0.0, 0, 0);

-- Search query log for analytics and personalization
CREATE TABLE IF NOT EXISTS search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    query_text TEXT NOT NULL,
    query_normalized TEXT NOT NULL,
    results_count INTEGER NOT NULL DEFAULT 0,
    clicked_result_id INTEGER,
    search_mode TEXT DEFAULT 'hybrid',
    response_time_ms REAL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Autocomplete suggestions
CREATE TABLE IF NOT EXISTS autocomplete_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion TEXT NOT NULL,
    frequency INTEGER NOT NULL DEFAULT 1,
    last_used TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for autocomplete queries
CREATE INDEX IF NOT EXISTS idx_autocomplete_suggestion ON autocomplete_suggestions(suggestion);

-- Synonyms for query expansion
CREATE TABLE IF NOT EXISTS synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    synonym TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word, synonym)
);

-- Search filters saved by users
CREATE TABLE IF NOT EXISTS saved_filters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    filters TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
