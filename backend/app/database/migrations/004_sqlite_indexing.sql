-- Nebula Search — Indexing System Schema v1

-- Index jobs table
CREATE TABLE IF NOT EXISTS index_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    document_id INTEGER NOT NULL,
    user_id INTEGER,
    filename TEXT NOT NULL,
    priority TEXT DEFAULT 'NORMAL' NOT NULL,
    status TEXT DEFAULT 'QUEUED' NOT NULL,
    progress INTEGER DEFAULT 0 NOT NULL,
    current_step TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    worker_id TEXT,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    error_message TEXT,
    duration REAL,
    embedding_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    file_size INTEGER,
    file_checksum TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_index_jobs_status ON index_jobs(status);
CREATE INDEX IF NOT EXISTS idx_index_jobs_priority ON index_jobs(priority);
CREATE INDEX IF NOT EXISTS idx_index_jobs_document_id ON index_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_index_jobs_created_at ON index_jobs(created_at);

-- Dead letter queue for failed jobs
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    document_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    retries INTEGER DEFAULT 0 NOT NULL,
    failed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    worker_id TEXT,
    stack_trace TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_failed_at ON dead_letter_queue(failed_at);

-- Worker health table
CREATE TABLE IF NOT EXISTS worker_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'IDLE' NOT NULL,
    cpu_usage REAL DEFAULT 0.0,
    memory_usage REAL DEFAULT 0.0,
    current_job_id TEXT,
    processed_jobs INTEGER DEFAULT 0 NOT NULL,
    failed_jobs INTEGER DEFAULT 0 NOT NULL,
    average_duration REAL DEFAULT 0.0,
    heartbeat TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_worker_health_status ON worker_health(status);

-- Indexing metrics table
CREATE TABLE IF NOT EXISTS indexing_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_indexing_metrics_name_time ON indexing_metrics(metric_name, recorded_at);

-- Scheduler configurations
CREATE TABLE IF NOT EXISTS scheduler_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    schedule_type TEXT NOT NULL, -- cron, interval, manual
    cron_expression TEXT,
    interval_seconds INTEGER,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    last_run TEXT,
    next_run TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Document chunks for incremental indexing
CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    chunk_hash TEXT NOT NULL,
    embedding_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_id)
);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_hash ON document_chunks(chunk_hash);
