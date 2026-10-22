-- Migration 009: Search enhancements (saved searches, search suggestions)

CREATE SCHEMA IF NOT EXISTS search;
CREATE SCHEMA IF NOT EXISTS notifications;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Saved searches table
CREATE TABLE IF NOT EXISTS search.saved_searches (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    mode VARCHAR(20) DEFAULT 'hybrid' NOT NULL,
    filters JSONB DEFAULT '{}'::jsonb,
    is_alert BOOLEAN DEFAULT FALSE NOT NULL,
    last_alerted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT valid_mode CHECK (mode IN ('webrecyc', 'vector', 'hybrid', 'ai'))
);

CREATE INDEX IF NOT EXISTS idx_saved_searches_user
    ON search.saved_searches(user_id, created_at DESC)
    WHERE is_deleted = FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_searches_user_query
    ON search.saved_searches(user_id, query, is_deleted)
    WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_saved_searches_updated_at
    BEFORE UPDATE ON search.saved_searches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Notifications table (if not already in ref schema)
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
    delivery_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT valid_type CHECK (type IN ('info', 'warning', 'error', 'success')),
    CONSTRAINT valid_category CHECK (category IN ('system', 'search', 'file', 'account', 'security'))
);

CREATE INDEX IF NOT EXISTS idx_notifications_user
    ON notifications.notifications(user_id, created_at DESC)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_notifications_unread
    ON notifications.notifications(user_id, is_read, created_at DESC)
    WHERE is_deleted = FALSE AND is_read = FALSE;

CREATE TRIGGER IF NOT EXISTS update_notifications_updated_at
    BEFORE UPDATE ON notifications.notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Notification preferences table
CREATE TABLE IF NOT EXISTS notifications.notification_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT valid_channel CHECK (channel IN ('email', 'push', 'in_app', 'sms')),
    UNIQUE(user_id, category, channel, is_deleted)
);

CREATE INDEX IF NOT EXISTS idx_notif_prefs_user
    ON notification_preferences(user_id)
    WHERE is_deleted = FALSE;
