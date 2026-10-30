-- Durable indexing job records with owner attribution for API authorization.
CREATE TABLE IF NOT EXISTS index_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT UNIQUE NOT NULL,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'NORMAL',
    status TEXT NOT NULL DEFAULT 'QUEUED',
    progress INTEGER NOT NULL DEFAULT 0,
    current_step TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    worker_id TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    duration DOUBLE PRECISION,
    embedding_count INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    file_size BIGINT,
    file_checksum TEXT
);
CREATE INDEX IF NOT EXISTS idx_index_jobs_user_id ON index_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_index_jobs_status ON index_jobs(status);
CREATE INDEX IF NOT EXISTS idx_index_jobs_document_id ON index_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_index_jobs_created_at ON index_jobs(created_at);
