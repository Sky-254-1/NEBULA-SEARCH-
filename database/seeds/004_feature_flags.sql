-- ============================================
-- Seed Data: Feature Flags
-- ============================================
-- This file seeds feature flags for gradual feature rollout

-- Core Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('vector_search', 'Vector Search', 'Enable vector-based semantic search using embeddings', TRUE, 100),
    ('ai_synthesis', 'AI Synthesis', 'Enable AI-powered answer synthesis from search results', TRUE, 100),
    ('advanced_analytics', 'Advanced Analytics', 'Enable advanced analytics dashboard with custom reports', FALSE, 0),
    ('file_versioning', 'File Versioning', 'Enable file versioning and history tracking', TRUE, 100),
    ('multi_tenant', 'Multi-Tenant', 'Enable multi-tenant support for organizations', FALSE, 0),
    ('api_access', 'API Access', 'Enable REST API access for users', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- Search Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('search_suggestions', 'Search Suggestions', 'Enable autocomplete and search suggestions', TRUE, 100),
    ('search_history', 'Search History', 'Enable search history tracking and personalization', TRUE, 100),
    ('search_filters', 'Advanced Filters', 'Enable advanced search filters and faceted search', TRUE, 50),
    ('search_analytics', 'Search Analytics', 'Enable search analytics and insights', TRUE, 100),
    ('hybrid_search', 'Hybrid Search', 'Enable hybrid search combining keyword and vector search', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- File Management Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('file_sharing', 'File Sharing', 'Enable file sharing between users', TRUE, 100),
    ('file_permissions', 'File Permissions', 'Enable granular file permissions', TRUE, 100),
    ('file_preview', 'File Preview', 'Enable in-browser file preview', TRUE, 100),
    ('bulk_upload', 'Bulk Upload', 'Enable bulk file upload', TRUE, 50),
    ('file_tags', 'File Tags', 'Enable file tagging and categorization', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- User Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('user_profiles', 'User Profiles', 'Enable extended user profiles', TRUE, 100),
    ('user_avatars', 'User Avatars', 'Enable user avatar upload', TRUE, 100),
    ('user_preferences', 'User Preferences', 'Enable user preference customization', TRUE, 100),
    ('two_factor_auth', 'Two-Factor Authentication', 'Enable 2FA for enhanced security', FALSE, 0),
    ('social_login', 'Social Login', 'Enable social OAuth login (Google, GitHub)', FALSE, 0),
    ('email_verification', 'Email Verification', 'Require email verification for new accounts', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- Notification Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('email_notifications', 'Email Notifications', 'Enable email notifications', TRUE, 100),
    ('push_notifications', 'Push Notifications', 'Enable browser push notifications', TRUE, 50),
    ('notification_preferences', 'Notification Preferences', 'Enable user notification preferences', TRUE, 100),
    ('notification_templates', 'Notification Templates', 'Enable customizable notification templates', TRUE, 100),
    ('notification_batching', 'Notification Batching', 'Enable notification batching to reduce noise', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- Admin Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('admin_dashboard', 'Admin Dashboard', 'Enable admin dashboard', TRUE, 100),
    ('user_management', 'User Management', 'Enable user management in admin panel', TRUE, 100),
    ('system_monitoring', 'System Monitoring', 'Enable system monitoring and health checks', TRUE, 100),
    ('audit_logs', 'Audit Logs', 'Enable comprehensive audit logging', TRUE, 100),
    ('maintenance_mode', 'Maintenance Mode', 'Enable maintenance mode for system updates', TRUE, 100),
    ('feature_flags_ui', 'Feature Flags UI', 'Enable feature flag management UI', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- Experimental Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('ai_chat', 'AI Chat', 'Enable AI-powered chat interface', FALSE, 0),
    ('voice_search', 'Voice Search', 'Enable voice-based search', FALSE, 0),
    ('image_search', 'Image Search', 'Enable image-based search', FALSE, 0),
    ('collaborative_search', 'Collaborative Search', 'Enable collaborative search sessions', FALSE, 0),
    ('search_workflows', 'Search Workflows', 'Enable automated search workflows', FALSE, 0),
    ('data_export', 'Data Export', 'Enable user data export (GDPR compliance)', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- Performance Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('redis_cache', 'Redis Cache', 'Enable Redis caching layer', TRUE, 100),
    ('query_optimization', 'Query Optimization', 'Enable automatic query optimization', TRUE, 100),
    ('lazy_loading', 'Lazy Loading', 'Enable lazy loading for search results', TRUE, 100),
    ('cdn_integration', 'CDN Integration', 'Enable CDN for static assets', TRUE, 100),
    ('compression', 'Response Compression', 'Enable gzip/brotli compression', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- Integration Features
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('webhook_support', 'Webhook Support', 'Enable webhook integrations', FALSE, 0),
    ('slack_integration', 'Slack Integration', 'Enable Slack notifications', FALSE, 0),
    ('teams_integration', 'Teams Integration', 'Enable Microsoft Teams notifications', FALSE, 0),
    ('zapier_integration', 'Zapier Integration', 'Enable Zapier automation', FALSE, 0),
    ('api_rate_limiting', 'API Rate Limiting', 'Enable API rate limiting', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- Seed Complete
-- ============================================

SELECT 'Feature flags seeded successfully' AS status;