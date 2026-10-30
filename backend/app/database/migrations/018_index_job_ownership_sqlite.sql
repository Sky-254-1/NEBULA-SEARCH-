-- Migration 004's filename is shadowed by the other 004 SQLite migration in
-- the current migration loader, so create the table here for both fresh and
-- existing databases. IF NOT EXISTS preserves existing job records.
CREATE TABLE IF NOT EXISTS index_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    document_id INTEGER NOT NULL,
    user_id INTEGER,
    filename TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'NORMAL',
    status TEXT NOT NULL DEFAULT 'QUEUED',
    progress INTEGER NOT NULL DEFAULT 0,
    current_step TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    worker_id TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    duration REAL,
    embedding_count INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    file_size INTEGER,
    file_checksum TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
ALTER TABLE index_jobs ADD COLUMN updated_at TEXT;
CREATE INDEX IF NOT EXISTS idx_index_jobs_user_id ON index_jobs(user_id);
