-- Nebula Search — PostgreSQL schema v1.1 (vector indexing)
-- NOTE: Table creation moved to 002_add_vector_tables_postgres.sql
-- This file now only contains additional indexes and schema updates

-- Additional indexes for document_chunks (created in 002_add_vector_tables_postgres.sql)
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index ON document_chunks(chunk_index);

-- Embeddings table (created in 002_add_vector_tables_postgres.sql)
-- Additional indexes for embeddings
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_user_id ON embeddings(user_id);

-- Citations table (created in 002_add_vector_tables_postgres.sql)
-- Additional indexes for citations
CREATE INDEX IF NOT EXISTS idx_citations_user_id ON citations(user_id);
CREATE INDEX IF NOT EXISTS idx_citations_document_id ON citations(document_id);

-- Search sessions table
CREATE TABLE IF NOT EXISTS search_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'hybrid',
    results_count INTEGER DEFAULT 0,
    metadata_json TEXT DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_search_sessions_user_id ON search_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_search_sessions_started_at ON search_sessions(started_at);

ALTER TABLE documents ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message TEXT;
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
