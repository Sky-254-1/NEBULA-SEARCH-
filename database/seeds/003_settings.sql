-- ============================================
-- Seed Data: Application Settings
-- ============================================
-- This file seeds application configuration settings

-- Application Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('app.name', 'Nebula Search', 'string', 'Application name displayed in UI and emails', TRUE),
    ('app.version', '1.0.0', 'string', 'Current application version', TRUE),
    ('app.environment', 'production', 'string', 'Environment: development, staging, or production', FALSE),
    ('app.url', 'https://nebula-search.io', 'string', 'Application base URL', TRUE),
    ('app.support_email', 'support@nebula-search.io', 'string', 'Support contact email', TRUE),
    ('app.maintenance_mode', 'false', 'boolean', 'Enable maintenance mode to block user access', FALSE)
ON CONFLICT (key) DO NOTHING;

-- Authentication Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('auth.jwt_expiry_minutes', '15', 'integer', 'JWT access token expiry time in minutes', FALSE),
    ('auth.refresh_token_expiry_days', '7', 'integer', 'Refresh token expiry time in days', FALSE),
    ('auth.max_login_attempts', '5', 'integer', 'Maximum failed login attempts before account lockout', FALSE),
    ('auth.lockout_duration_minutes', '30', 'integer', 'Account lockout duration in minutes after max failed attempts', FALSE),
    ('auth.password_min_length', '8', 'integer', 'Minimum password length for new accounts', FALSE),
    ('auth.password_require_uppercase', 'true', 'boolean', 'Require uppercase letter in password', FALSE),
    ('auth.password_require_lowercase', 'true', 'boolean', 'Require lowercase letter in password', FALSE),
    ('auth.password_require_number', 'true', 'boolean', 'Require number in password', FALSE),
    ('auth.password_require_special', 'false', 'boolean', 'Require special character in password', FALSE),
    ('auth.email_verification_required', 'true', 'boolean', 'Require email verification for new accounts', FALSE),
    ('auth.allow_signup', 'true', 'boolean', 'Allow new user registration', TRUE),
    ('auth.allow_password_reset', 'true', 'boolean', 'Allow password reset via email', TRUE)
ON CONFLICT (key) DO NOTHING;

-- Search Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('search.max_results', '100', 'integer', 'Maximum number of search results per query', TRUE),
    ('search.default_results', '10', 'integer', 'Default number of search results', TRUE),
    ('search.cache_ttl_seconds', '300', 'integer', 'Search result cache TTL in seconds (5 minutes)', FALSE),
    ('search.enable_fulltext', 'true', 'boolean', 'Enable PostgreSQL full-text search', FALSE),
    ('search.enable_vector', 'true', 'boolean', 'Enable vector/semantic search', FALSE),
    ('search.enable_hybrid', 'true', 'boolean', 'Enable hybrid search (keyword + vector)', FALSE),
    ('search.max_query_length', '500', 'integer', 'Maximum search query length', TRUE),
    ('search.min_query_length', '2', 'integer', 'Minimum search query length', TRUE),
    ('search.rate_limit_per_minute', '60', 'integer', 'Search rate limit per user per minute', FALSE),
    ('search.enable_suggestions', 'true', 'boolean', 'Enable search suggestions/autocomplete', TRUE),
    ('search.enable_history', 'true', 'boolean', 'Enable search history tracking', TRUE),
    ('search.history_retention_days', '90', 'integer', 'Search history retention period in days', FALSE)
ON CONFLICT (key) DO NOTHING;

-- Storage Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('storage.max_upload_size_mb', '100', 'integer', 'Maximum file upload size in MB', TRUE),
    ('storage.allowed_file_types', 'pdf,doc,docx,txt,md,png,jpg,jpeg,gif,zip', 'string', 'Comma-separated list of allowed file extensions', TRUE),
    ('storage.default_quota_bytes', '1073741824', 'integer', 'Default storage quota per user (1GB)', FALSE),
    ('storage.premium_quota_bytes', '10737418240', 'integer', 'Premium user storage quota (10GB)', FALSE),
    ('storage.admin_quota_bytes', '107374182400', 'integer', 'Admin user storage quota (100GB)', FALSE),
    ('storage.max_file_versions', '10', 'integer', 'Maximum file versions to keep', FALSE),
    ('storage.enable_versioning', 'true', 'boolean', 'Enable file versioning', TRUE),
    ('storage.virus_scan_enabled', 'true', 'boolean', 'Enable virus scanning for uploads', FALSE),
    ('storage.encryption_enabled', 'true', 'boolean', 'Enable encryption at rest for files', FALSE)
ON CONFLICT (key) DO NOTHING;

-- Analytics Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('analytics.retention_days', '90', 'integer', 'Analytics data retention period in days', FALSE),
    ('analytics.enable_tracking', 'true', 'boolean', 'Enable analytics event tracking', TRUE),
    ('analytics.enable_session_recording', 'false', 'boolean', 'Enable session recording (privacy consideration)', FALSE),
    ('analytics.aggregation_interval_hours', '1', 'integer', 'Metrics aggregation interval in hours', FALSE),
    ('analytics.max_events_per_user', '10000', 'integer', 'Maximum events to store per user', FALSE),
    ('analytics.anonymize_after_days', '365', 'integer', 'Anonymize analytics data after this many days', FALSE)
ON CONFLICT (key) DO NOTHING;

-- Notification Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('notifications.max_per_user', '100', 'integer', 'Maximum notifications stored per user', FALSE),
    ('notifications.default_expiry_days', '30', 'integer', 'Default notification expiry in days', FALSE),
    ('notifications.enable_email', 'true', 'boolean', 'Enable email notifications', TRUE),
    ('notifications.enable_push', 'true', 'boolean', 'Enable push notifications', TRUE),
    ('notifications.enable_in_app', 'true', 'boolean', 'Enable in-app notifications', TRUE),
    ('notifications.batch_enabled', 'true', 'boolean', 'Enable notification batching', FALSE),
    ('notifications.batch_interval_minutes', '15', 'integer', 'Notification batch interval in minutes', FALSE)
ON CONFLICT (key) DO NOTHING;

-- Security Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('security.enable_2fa', 'false', 'boolean', 'Enable two-factor authentication', TRUE),
    ('security.enforce_2fa_for_admins', 'true', 'boolean', 'Require 2FA for admin accounts', FALSE),
    ('security.session_timeout_minutes', '120', 'integer', 'Session timeout in minutes', FALSE),
    ('security.max_sessions_per_user', '5', 'integer', 'Maximum concurrent sessions per user', FALSE),
    ('security.enable_cors', 'true', 'boolean', 'Enable CORS protection', FALSE),
    ('security.enable_rate_limiting', 'true', 'boolean', 'Enable API rate limiting', FALSE),
    ('security.rate_limit_requests', '100', 'integer', 'Rate limit: requests per minute', FALSE),
    ('security.enable_sql_injection_protection', 'true', 'boolean', 'Enable SQL injection protection', FALSE),
    ('security.enable_xss_protection', 'true', 'boolean', 'Enable XSS protection headers', FALSE),
    ('security.enable_csrf_protection', 'true', 'boolean', 'Enable CSRF protection', FALSE),
    ('security.allowed_origins', 'http://localhost:3000,http://localhost:5173', 'string', 'Comma-separated allowed CORS origins', FALSE)
ON CONFLICT (key) DO NOTHING;

-- Email Settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('email.provider', 'smtp', 'string', 'Email provider: smtp, sendgrid, mailgun', FALSE),
    ('email.smtp_host', 'smtp.example.com', 'string', 'SMTP host', FALSE),
    ('email.smtp_port', '587', 'integer', 'SMTP port', FALSE),
    ('email.smtp_username', '', 'string', 'SMTP username', FALSE),
    ('email.smtp_password', '', 'string', 'SMTP password (encrypted)', FALSE),
    ('email.smtp_use_tls', 'true', 'boolean', 'Use TLS for SMTP', FALSE),
    ('email.from_address', 'noreply@nebula-search.io', 'string', 'Default from email address', TRUE),
    ('email.from_name', 'Nebula Search', 'string', 'Default from name', TRUE)
ON CONFLICT (key) DO NOTHING;

-- ============================================
-- Seed Complete
-- ============================================

SELECT 'Settings seeded successfully' AS status;