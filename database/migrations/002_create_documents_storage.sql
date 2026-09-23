-- ============================================
-- Migration: Create Documents and Storage Tables
-- Created: 2025-01-04
-- Description: Creates document management and file storage tables
-- ============================================

-- Documents table
CREATE TABLE IF NOT EXISTS public.documents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    storage_path TEXT NOT NULL,
    size_bytes BIGINT,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    content_hash VARCHAR(64),
    error_message TEXT,
    indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'indexed', 'failed', 'deleted'))
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents(user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents(status) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_documents_created ON public.documents(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_documents_hash ON public.documents(content_hash) WHERE is_deleted = FALSE AND content_hash IS NOT NULL;

CREATE TRIGGER IF NOT EXISTS update_documents_updated_at 
    BEFORE UPDATE ON public.documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- File permissions table
CREATE TABLE IF NOT EXISTS storage.file_permissions (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    permission_level VARCHAR(50) DEFAULT 'read' NOT NULL,
    granted_by BIGINT REFERENCES public.users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_permission CHECK (permission_level IN ('read', 'write', 'admin')),
    CONSTRAINT valid_permission_expiry CHECK (expires_at IS NULL OR expires_at > granted_at),
    UNIQUE(document_id, user_id, is_deleted)
);

CREATE INDEX IF NOT EXISTS idx_file_permissions_document ON storage.file_permissions(document_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_file_permissions_user ON storage.file_permissions(user_id) WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_file_permissions_updated_at 
    BEFORE UPDATE ON storage.file_permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Storage buckets table
CREATE TABLE IF NOT EXISTS storage.buckets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    max_file_size_mb INTEGER DEFAULT 10,
    allowed_mime_types TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_buckets_name ON storage.buckets(name) WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_buckets_updated_at 
    BEFORE UPDATE ON storage.buckets 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default storage bucket
INSERT INTO storage.buckets (name, description, is_public, max_file_size_mb, allowed_mime_types)
VALUES ('default', 'Default storage bucket', FALSE, 10, ARRAY['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'])
ON CONFLICT (name) DO NOTHING;