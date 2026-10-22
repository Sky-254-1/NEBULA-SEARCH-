-- ============================================
-- Migration: Create Notifications and Analytics Tables
-- Created: 2025-01-04
-- Description: Creates notifications, analytics, and audit tables
-- ============================================

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications.notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_notification_type CHECK (type IN ('info', 'success', 'warning', 'error', 'system'))
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications.notifications(user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications.notifications(user_id, is_read) WHERE is_deleted = FALSE AND is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications.notifications(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications.notifications(expires_at) WHERE is_deleted = FALSE AND expires_at IS NOT NULL;

CREATE TRIGGER IF NOT EXISTS update_notifications_updated_at 
    BEFORE UPDATE ON notifications.notifications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Notification preferences table
CREATE TABLE IF NOT EXISTS notifications.preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    push_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    in_app_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    UNIQUE(user_id, category, is_deleted)
);

CREATE INDEX IF NOT EXISTS idx_notification_prefs_user ON notifications.preferences(user_id) WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_notification_prefs_updated_at 
    BEFORE UPDATE ON notifications.preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Search analytics table
CREATE TABLE IF NOT EXISTS analytics.search_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    query TEXT NOT NULL,
    query_normalized TEXT,
    results_count INTEGER DEFAULT 0,
    clicked_position INTEGER,
    clicked_url TEXT,
    backends TEXT[],
    intent VARCHAR(50),
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_search_events_user ON analytics.search_events(user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_search_events_created ON analytics.search_events(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_search_events_query ON analytics.search_events USING GIN(to_tsvector('english', query)) WHERE is_deleted = FALSE;

-- Usage analytics table
CREATE TABLE IF NOT EXISTS analytics.usage_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id BIGINT,
    metadata JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_event_type CHECK (event_type IN ('view', 'create', 'update', 'delete', 'download', 'share', 'login', 'logout'))
);

CREATE INDEX IF NOT EXISTS idx_usage_stats_user ON analytics.usage_stats(user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_usage_stats_created ON analytics.usage_stats(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_usage_stats_event ON analytics.usage_stats(event_type) WHERE is_deleted = FALSE;

-- Performance metrics table
CREATE TABLE IF NOT EXISTS analytics.performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_perf_metrics_endpoint ON analytics.performance_metrics(endpoint, created_at) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_perf_metrics_created ON analytics.performance_metrics(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_perf_metrics_status ON analytics.performance_metrics(status_code) WHERE is_deleted = FALSE;

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit.audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id BIGINT,
    old_values JSONB,
    new_values JSONB,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'success' NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_audit_status CHECK (status IN ('success', 'failure', 'warning'))
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit.audit_logs(user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit.audit_logs(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit.audit_logs(action) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit.audit_logs(resource_type, resource_id) WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_audit_logs_updated_at 
    BEFORE UPDATE ON audit.audit_logs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Cleanup expired tokens function
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM auth.refresh_tokens
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    DELETE FROM auth.email_verification
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    DELETE FROM auth.password_reset
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    DELETE FROM auth.sessions
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    DELETE FROM notifications.notifications
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    DELETE FROM storage.file_permissions
    WHERE expires_at < NOW() AND is_deleted = FALSE;
END;
$$ LANGUAGE plpgsql;