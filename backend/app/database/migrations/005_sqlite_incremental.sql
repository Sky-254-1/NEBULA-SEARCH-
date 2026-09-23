-- Nebula Search — Incremental Re-indexing System Schema v1

-- Index tracking table for incremental re-indexing
CREATE TABLE IF NOT EXISTS index_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,
    metadata_hash TEXT NOT NULL,
    chunk_hashes TEXT NOT NULL,  -- Comma-separated chunk hashes
    chunk_count INTEGER DEFAULT 0 NOT NULL,
    embedding_count INTEGER DEFAULT 0 NOT NULL,
    last_indexed TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_scanned TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_modified TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1 NOT NULL,
    index_generation INTEGER DEFAULT 1 NOT NULL,
    sync_status TEXT DEFAULT 'synced' NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_index_tracking_document_id ON index_tracking(document_id);
CREATE INDEX IF NOT EXISTS idx_index_tracking_file_hash ON index_tracking(file_hash);
CREATE INDEX IF NOT EXISTS idx_index_tracking_metadata_hash ON index_tracking(metadata_hash);
CREATE INDEX IF NOT EXISTS idx_index_tracking_sync_status ON index_tracking(sync_status);
CREATE INDEX IF NOT EXISTS idx_index_tracking_last_scanned ON index_tracking(last_scanned);

-- Incremental re-indexing jobs table
CREATE TABLE IF NOT EXISTS incremental_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    document_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending' NOT NULL,
    change_type TEXT,
    priority TEXT DEFAULT 'NORMAL' NOT NULL,
    chunks_added INTEGER DEFAULT 0,
    chunks_removed INTEGER DEFAULT 0,
    chunks_modified INTEGER DEFAULT 0,
    chunks_reused INTEGER DEFAULT 0,
    embeddings_generated INTEGER DEFAULT 0,
    embeddings_reused INTEGER DEFAULT 0,
    metadata_updated BOOLEAN DEFAULT 0,
    requires_full_reindex BOOLEAN DEFAULT 0,
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    duration_seconds REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_incremental_jobs_document_id ON incremental_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_incremental_jobs_status ON incremental_jobs(status);
CREATE INDEX IF NOT EXISTS idx_incremental_jobs_created_at ON incremental_jobs(created_at);

-- Re-indexing history table
CREATE TABLE IF NOT EXISTS reindex_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    change_type TEXT,
    chunks_affected INTEGER DEFAULT 0,
    embeddings_regenerated INTEGER DEFAULT 0,
    metadata_fields_updated TEXT,
    duration_seconds REAL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_reindex_history_document_id ON reindex_history(document_id);
CREATE INDEX IF NOT EXISTS idx_reindex_history_event_type ON reindex_history(event_type);
CREATE INDEX IF NOT EXISTS idx_reindex_history_created_at ON reindex_history(created_at);

-- Cleanup operations log
CREATE TABLE IF NOT EXISTS cleanup_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL,
    records_deleted INTEGER DEFAULT 0,
    storage_reclaimed_bytes INTEGER DEFAULT 0,
    dry_run BOOLEAN DEFAULT 0,
    duration_seconds REAL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cleanup_logs_created_at ON cleanup_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_cleanup_logs_operation_type ON cleanup_logs(operation_type);

-- File watcher state table
CREATE TABLE IF NOT EXISTS file_watcher_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    last_check TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    files_tracked INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_file_watcher_state_path ON file_watcher_state(path);
CREATE INDEX IF NOT EXISTS idx_file_watcher_state_is_active ON file_watcher_state(is_active);

-- Scheduler configurations for incremental re-indexing
CREATE TABLE IF NOT EXISTS incremental_scheduler_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    schedule_type TEXT NOT NULL,  -- cron, interval, manual
    cron_expression TEXT,
    interval_seconds INTEGER,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    last_run TEXT,
    next_run TEXT,
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_incremental_scheduler_configs_name ON incremental_scheduler_configs(name);
CREATE INDEX IF NOT EXISTS idx_incremental_scheduler_configs_is_active ON incremental_scheduler_configs(is_active);

-- Triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_index_tracking_timestamp
    AFTER UPDATE ON index_tracking
    FOR EACH ROW
    BEGIN
        UPDATE index_tracking SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_file_watcher_state_timestamp
    AFTER UPDATE ON file_watcher_state
    FOR EACH ROW
    BEGIN
        UPDATE file_watcher_state SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_incremental_scheduler_configs_timestamp
    AFTER UPDATE ON incremental_scheduler_configs
    FOR EACH ROW
    BEGIN
        UPDATE incremental_scheduler_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

-- Views for common queries
CREATE VIEW IF NOT EXISTS v_incremental_stats AS
SELECT
    COUNT(*) as total_documents,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_documents,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_documents,
    COUNT(CASE WHEN sync_status = 'failed' THEN 1 END) as failed_documents,
    AVG(chunk_count) as avg_chunk_count,
    AVG(embedding_count) as avg_embedding_count,
    MAX(last_scanned) as last_scan_time,
    MIN(created_at) as first_tracked
FROM index_tracking;

CREATE VIEW IF NOT EXISTS v_recent_changes AS
SELECT
    rh.document_id,
    d.filename,
    rh.event_type,
    rh.change_type,
    rh.chunks_affected,
    rh.embeddings_regenerated,
    rh.duration_seconds,
    rh.created_at
FROM reindex_history rh
LEFT JOIN documents d ON rh.document_id = d.id
WHERE rh.created_at >= datetime('now', '-7 days')
ORDER BY rh.created_at DESC;

-- Insert default scheduler configs
INSERT OR IGNORE INTO incremental_scheduler_configs (name, schedule_type, cron_expression, interval_seconds, is_active)
VALUES ('hourly_scan', 'cron', '0 * * * *', NULL, 1);

INSERT OR IGNORE INTO incremental_scheduler_configs (name, schedule_type, cron_expression, interval_seconds, is_active)
VALUES ('daily_cleanup', 'cron', '0 2 * * *', NULL, 1);

INSERT OR IGNORE INTO incremental_scheduler_configs (name, schedule_type, cron_expression, interval_seconds, is_active)
VALUES ('weekly_full_scan', 'cron', '0 3 * * 0', NULL, 1);
