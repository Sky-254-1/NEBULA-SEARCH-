-- Add is_deleted column to documents table for SQLite
-- This handles the case where the documents table was created without soft delete support

-- Add deleted_at column if not exists
ALTER TABLE documents ADD COLUMN deleted_at TEXT;

-- Add is_deleted column (SQLite requires default value to handle existing rows)
ALTER TABLE documents ADD COLUMN is_deleted INTEGER DEFAULT 0 NOT NULL;

-- Create index if not exists (SQLite allows this with IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id) WHERE is_deleted = 0;
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status) WHERE is_deleted = 0;
CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at DESC) WHERE is_deleted = 0;
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash) WHERE is_deleted = 0 AND content_hash IS NOT NULL;
