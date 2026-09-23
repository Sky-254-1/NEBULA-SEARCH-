-- Nebula Search — Performance Indexes & Unique Constraints
-- Migration: 004
-- Purpose: Add missing indexes and unique constraints for production readiness

-- ========================================
-- UNIQUE CONSTRAINTS
-- ========================================

-- SQLite: Unique constraint on sessions.refresh_token_hash
-- Note: SQLite doesn't support IF NOT EXISTS for CREATE UNIQUE INDEX in the same way
-- We use a try-catch approach in the migration runner
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_refresh_token_hash 
    ON sessions(refresh_token_hash);

-- PostgreSQL: Unique constraint on sessions.refresh_token_hash
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_refresh_token_hash 
--     ON sessions(refresh_token_hash);

-- SQLite: Unique composite constraint for documents (user_id, storage_path)
-- This prevents duplicate document uploads per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_unique_user_path 
    ON documents(user_id, storage_path);

-- PostgreSQL: Unique composite constraint for documents (user_id, storage_path)
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_unique_user_path 
--     ON documents(user_id, storage_path);

-- ========================================
-- ADDITIONAL PERFORMANCE INDEXES
-- ========================================

-- Documents table indexes (some may already exist from earlier migrations)
-- These ensure optimal query performance for common lookups
CREATE INDEX IF NOT EXISTS idx_documents_status 
    ON documents(status);

CREATE INDEX IF NOT EXISTS idx_documents_content_hash 
    ON documents(content_hash);

-- Embeddings table indexes for vector search performance
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id 
    ON embeddings(chunk_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_user_id 
    ON embeddings(user_id);

-- Exports table index
CREATE INDEX IF NOT EXISTS idx_exports_user_id 
    ON exports(user_id);

-- Search sessions table index
CREATE INDEX IF NOT EXISTS idx_search_sessions_user_id 
    ON search_sessions(user_id);

-- Audit logs table indexes for audit trail queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at 
    ON audit_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action 
    ON audit_logs(action);

-- ========================================
-- COMPOSITE INDEXES FOR COMMON QUERIES
-- ========================================

-- Composite index for user document lookups (very common query pattern)
CREATE INDEX IF NOT EXISTS idx_documents_user_id_status 
    ON documents(user_id, status);

-- Composite index for user search sessions
CREATE INDEX IF NOT EXISTS idx_search_sessions_user_id_started_at 
    ON search_sessions(user_id, started_at DESC);

-- Composite index for user audits (common in admin dashboards)
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id_created_at 
    ON audit_logs(user_id, created_at DESC);

-- ========================================
-- NOTES
-- ========================================
-- The following indexes are already created in earlier migrations:
-- - idx_sessions_user_id (001)
-- - idx_sessions_expires_at (001)
-- - idx_documents_user_id (001)
-- - idx_exports_user_id (001)
-- - idx_search_logs_user_id (001)
-- - idx_chat_history_user_id (001)
-- 
-- This migration adds the MISSING indexes and unique constraints identified in
-- the production readiness audit (PRODUCTION_READINESS_FINAL.md).