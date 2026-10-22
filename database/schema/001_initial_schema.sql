-- ============================================
-- IOIS (Nebula) - Initial Database Schema
-- ============================================
-- This migration creates the complete database schema
-- including all tables, indexes, triggers, and seed data

-- ============================================
-- UTILITY FUNCTIONS
-- ============================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function for soft delete
CREATE OR REPLACE FUNCTION soft_delete()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_deleted = TRUE;
    NEW.deleted_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- Cleanup expired refresh tokens
    DELETE FROM auth.refresh_tokens
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    -- Cleanup expired email verification tokens
    DELETE FROM auth.email_verification
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    -- Cleanup expired password reset tokens
    DELETE FROM auth.password_reset
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    -- Cleanup expired sessions
    DELETE FROM auth.sessions
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    -- Cleanup expired notifications
    DELETE FROM notifications.notifications
    WHERE expires_at < NOW() AND is_deleted = FALSE;
    
    -- Cleanup expired file permissions
    DELETE FROM storage.file_permissions
    WHERE expires_at < NOW() AND is_deleted = FALSE;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- CREATE SCHEMAS
-- ============================================

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS search;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS admin;

-- ============================================
-- PUBLIC SCHEMA - CORE TABLES
-- ============================================

-- Users table
CREATE TABLE public.users (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Account Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    locked_until TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    last_failed_login TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_login TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_lock_time CHECK (locked_until IS NULL OR locked_until > NOW()),
    CONSTRAINT no_self_lock CHECK (NOT (is_locked = TRUE AND locked_until IS NULL))
);

-- Indexes for users
CREATE INDEX idx_users_email ON public.users(email) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_active ON public.users(is_active, is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_created ON public.users(created_at DESC);
CREATE UNIQUE INDEX idx_users_email_unique ON public.users(email) WHERE is_deleted = FALSE;

-- Trigger for users
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Profiles table
CREATE TABLE public.profiles (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Personal Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,
    bio TEXT,
    location VARCHAR(200),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- Preferences
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_theme CHECK (theme IN ('light', 'dark', 'system')),
    CONSTRAINT valid_language CHECK (language ~* '^[a-z]{2}(-[A-Z]{2})?$'),
    UNIQUE(user_id)
);

-- Indexes for profiles
CREATE INDEX idx_profiles_user_id ON public.profiles(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_profiles_metadata ON public.profiles USING GIN(metadata);

-- Trigger for profiles
CREATE TRIGGER update_profiles_updated_at 
    BEFORE UPDATE ON public.profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Roles table
CREATE TABLE public.roles (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Role Information
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Hierarchy
    parent_role_id INTEGER REFERENCES public.roles(id),
    level INTEGER DEFAULT 0 NOT NULL,
    
    -- Status
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_role_name CHECK (name ~* '^[a-z_]+$'),
    CONSTRAINT valid_level CHECK (level >= 0 AND level <= 100)
);

-- Indexes for roles
CREATE INDEX idx_roles_name ON public.roles(name) WHERE is_deleted = FALSE AND is_active = TRUE;
CREATE INDEX idx_roles_level ON public.roles(level);

-- Trigger for roles
CREATE TRIGGER update_roles_updated_at 
    BEFORE UPDATE ON public.roles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Permissions table
CREATE TABLE public.permissions (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Permission Information
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    
    -- Status
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'manage', 'admin')),
    UNIQUE(resource, action, name)
);

-- Indexes for permissions
CREATE INDEX idx_permissions_resource ON public.permissions(resource) WHERE is_deleted = FALSE;
CREATE INDEX idx_permissions_name ON public.permissions(name) WHERE is_deleted = FALSE;

-- Trigger for permissions
CREATE TRIGGER update_permissions_updated_at 
    BEFORE UPDATE ON public.permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- User roles junction table
CREATE TABLE public.user_roles (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
    
    -- Assignment Details
    assigned_by BIGINT REFERENCES public.users(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > assigned_at),
    UNIQUE(user_id, role_id, is_deleted)
);

-- Indexes for user_roles
CREATE INDEX idx_user_roles_user ON public.user_roles(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_user_roles_role ON public.user_roles(role_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_user_roles_expires ON public.user_roles(expires_at) 
    WHERE is_deleted = FALSE AND expires_at IS NOT NULL;

-- Trigger for user_roles
CREATE TRIGGER update_user_roles_updated_at 
    BEFORE UPDATE ON public.user_roles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Role permissions junction table
CREATE TABLE public.role_permissions (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    role_id INTEGER NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES public.permissions(id) ON DELETE CASCADE,
    
    -- Assignment Details
    granted_by BIGINT REFERENCES public.users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > granted_at),
    UNIQUE(role_id, permission_id, is_deleted)
);

-- Indexes for role_permissions
CREATE INDEX idx_role_perms_role ON public.role_permissions(role_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_role_perms_perm ON public.role_permissions(permission_id) WHERE is_deleted = FALSE;

-- Trigger for role_permissions
CREATE TRIGGER update_role_permissions_updated_at 
    BEFORE UPDATE ON public.role_permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Projects table
CREATE TABLE public.projects (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Project Information
    name VARCHAR(200) NOT NULL,
    description TEXT,
    owner_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Settings
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    is_archived BOOLEAN DEFAULT FALSE NOT NULL,
    settings JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    archived_at TIMESTAMPTZ,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_project_name CHECK (LENGTH(TRIM(name)) > 0)
);

-- Indexes for projects
CREATE INDEX idx_projects_owner ON public.projects(owner_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_projects_public ON public.projects(is_public, is_archived) 
    WHERE is_deleted = FALSE AND is_public = TRUE;
CREATE INDEX idx_projects_settings ON public.projects USING GIN(settings);

-- Trigger for projects
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON public.projects 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- AUTH SCHEMA
-- ============================================

-- Refresh tokens table
CREATE TABLE auth.refresh_tokens (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Token Information
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    jti UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Device Information
    device_name VARCHAR(200),
    device_type VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    
    -- Status
    is_revoked BOOLEAN DEFAULT FALSE NOT NULL,
    revoked_at TIMESTAMPTZ,
    revoked_reason VARCHAR(100),
    
    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Indexes for refresh_tokens
CREATE INDEX idx_refresh_tokens_user ON auth.refresh_tokens(user_id) 
    WHERE is_deleted = FALSE AND is_revoked = FALSE;
CREATE INDEX idx_refresh_tokens_jti ON auth.refresh_tokens(jti) WHERE is_deleted = FALSE;
CREATE INDEX idx_refresh_tokens_expires ON auth.refresh_tokens(expires_at) 
    WHERE is_deleted = FALSE AND is_revoked = FALSE;
CREATE INDEX idx_refresh_tokens_cleanup ON auth.refresh_tokens(expires_at) 
    WHERE is_deleted = FALSE AND expires_at < NOW();

-- Trigger for refresh_tokens
CREATE TRIGGER update_refresh_tokens_updated_at 
    BEFORE UPDATE ON auth.refresh_tokens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Sessions table
CREATE TABLE auth.sessions (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Session Information
    session_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    token_hash VARCHAR(255) NOT NULL,
    
    -- Device Information
    device_name VARCHAR(200),
    device_type VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    location VARCHAR(200),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    terminated_at TIMESTAMPTZ,
    termination_reason VARCHAR(100),
    
    -- Activity
    last_activity_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    activity_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_session_expiry CHECK (expires_at > created_at),
    CONSTRAINT valid_termination CHECK (
        (is_active = FALSE AND terminated_at IS NOT NULL) OR
        (is_active = TRUE AND terminated_at IS NULL)
    )
);

-- Indexes for sessions
CREATE INDEX idx_sessions_user ON auth.sessions(user_id) 
    WHERE is_deleted = FALSE AND is_active = TRUE;
CREATE INDEX idx_sessions_session_id ON auth.sessions(session_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_sessions_expires ON auth.sessions(expires_at) 
    WHERE is_deleted = FALSE AND is_active = TRUE;
CREATE INDEX idx_sessions_last_activity ON auth.sessions(last_activity_at DESC) 
    WHERE is_deleted = FALSE AND is_active = TRUE;

-- Trigger for sessions
CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON auth.sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Login history table
CREATE TABLE auth.login_history (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    
    -- Login Attempt
    email VARCHAR(255) NOT NULL,
    attempt_type VARCHAR(20) NOT NULL,
    
    -- Request Information
    ip_address INET NOT NULL,
    user_agent TEXT,
    location VARCHAR(200),
    
    -- Failure Details
    failure_reason VARCHAR(100),
    
    -- Timestamps
    attempted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_attempt_type CHECK (attempt_type IN ('success', 'failed', 'blocked'))
);

-- Indexes for login_history
CREATE INDEX idx_login_history_user ON auth.login_history(user_id, attempted_at DESC);
CREATE INDEX idx_login_history_email ON auth.login_history(email, attempted_at DESC);
CREATE INDEX idx_login_history_ip ON auth.login_history(ip_address, attempted_at DESC);
CREATE INDEX idx_login_history_attempt ON auth.login_history(attempt_type, attempted_at DESC);

-- Email verification table
CREATE TABLE auth.email_verification (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Token Information
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(50) DEFAULT 'email_verify' NOT NULL,
    
    -- Status
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMPTZ,
    
    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_expiry CHECK (expires_at > created_at),
    CONSTRAINT valid_usage CHECK (
        (is_used = TRUE AND used_at IS NOT NULL) OR
        (is_used = FALSE AND used_at IS NULL)
    )
);

-- Indexes for email_verification
CREATE INDEX idx_email_verify_user ON auth.email_verification(user_id) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_email_verify_token ON auth.email_verification(token_hash) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_email_verify_expires ON auth.email_verification(expires_at) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_email_verify_cleanup ON auth.email_verification(expires_at) 
    WHERE is_deleted = FALSE AND expires_at < NOW();

-- Password reset table
CREATE TABLE auth.password_reset (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Token Information
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    
    -- Status
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMPTZ,
    
    -- Request Information
    ip_address INET,
    user_agent TEXT,
    
    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Indexes for password_reset
CREATE INDEX idx_password_reset_user ON auth.password_reset(user_id) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_password_reset_token ON auth.password_reset(token_hash) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_password_reset_expires ON auth.password_reset(expires_at) 
    WHERE is_deleted = FALSE AND is_used = FALSE;

-- ============================================
-- SEARCH SCHEMA
-- ============================================

-- Searches table
CREATE TABLE search.searches (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    project_id BIGINT REFERENCES public.projects(id) ON DELETE SET NULL,
    
    -- Search Query
    query TEXT NOT NULL,
    query_normalized TEXT,
    
    -- Search Parameters
    search_type VARCHAR(50) DEFAULT 'web' NOT NULL,
    filters JSONB DEFAULT '{}'::jsonb,
    
    -- Results
    results_count INTEGER DEFAULT 0 NOT NULL,
    results_data JSONB,
    
    -- Performance
    execution_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Source
    source VARCHAR(50) DEFAULT 'web' NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_search_type CHECK (search_type IN ('web', 'vector', 'hybrid', 'ai')),
    CONSTRAINT valid_source CHECK (source IN ('web', 'api', 'mobile', 'desktop')),
    CONSTRAINT valid_results_count CHECK (results_count >= 0)
);

-- Indexes for searches
CREATE INDEX idx_searches_user ON search.searches(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_query ON search.searches USING GIN(to_tsvector('english', query)) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_created ON search.searches(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_type ON search.searches(search_type) WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_project ON search.searches(project_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_fts ON search.searches USING GIN(
    to_tsvector('english', COALESCE(query, ''))
);

-- Search history table
CREATE TABLE search.search_history (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    search_id BIGINT REFERENCES search.searches(id) ON DELETE SET NULL,
    
    -- Search Data
    query TEXT NOT NULL,
    query_normalized TEXT,
    
    -- Interaction
    clicked_result_url TEXT,
    dwell_time_seconds INTEGER,
    was_helpful BOOLEAN,
    
    -- Context
    session_id UUID REFERENCES auth.sessions(session_id),
    device_type VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_dwell_time CHECK (dwell_time_seconds IS NULL OR dwell_time_seconds >= 0)
);

-- Indexes for search_history
CREATE INDEX idx_search_history_user ON search.search_history(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_history_query ON search.search_history USING GIN(to_tsvector('english', query)) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_history_session ON search.search_history(session_id) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_history_retention ON search.search_history(created_at) 
    WHERE is_deleted = FALSE;

-- Indexed documents table
CREATE TABLE search.indexed_documents (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT REFERENCES public.users(id) ON DELETE CASCADE,
    project_id BIGINT REFERENCES public.projects(id) ON DELETE CASCADE,
    
    -- Document Information
    filename VARCHAR(500) NOT NULL,
    file_path TEXT,
    content_type VARCHAR(100),
    file_size_bytes BIGINT,
    
    -- Content
    content TEXT,
    content_hash VARCHAR(64),
    
    -- Vector Embedding
    embedding_id VARCHAR(255),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT '{}',
    
    -- Indexing Status
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    indexed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'indexed', 'failed')),
    CONSTRAINT valid_file_size CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0)
);

-- Indexes for indexed_documents
CREATE INDEX idx_indexed_docs_user ON search.indexed_documents(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_indexed_docs_project ON search.indexed_documents(project_id) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_indexed_docs_status ON search.indexed_documents(status) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_indexed_docs_content ON search.indexed_documents USING GIN(to_tsvector('english', content)) 
    WHERE is_deleted = FALSE AND status = 'indexed';
CREATE INDEX idx_indexed_docs_metadata ON search.indexed_documents USING GIN(metadata);
CREATE INDEX idx_indexed_docs_tags ON search.indexed_documents USING GIN(tags);
CREATE INDEX idx_indexed_docs_hash ON search.indexed_documents(content_hash) 
    WHERE is_deleted = FALSE AND content_hash IS NOT NULL;

-- Trigger for indexed_documents
CREATE TRIGGER update_indexed_docs_updated_at 
    BEFORE UPDATE ON search.indexed_documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Ranking data table
CREATE TABLE search.ranking_data (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    search_id BIGINT NOT NULL REFERENCES search.searches(id) ON DELETE CASCADE,
    document_id BIGINT REFERENCES search.indexed_documents(id) ON DELETE SET NULL,
    
    -- Ranking Information
    position INTEGER NOT NULL,
    score FLOAT NOT NULL,
    
    -- Score Components
    relevance_score FLOAT,
    popularity_score FLOAT,
    recency_score FLOAT,
    personalization_score FLOAT,
    
    -- Result Data
    title TEXT,
    snippet TEXT,
    url TEXT,
    source VARCHAR(255),
    
    -- User Interaction
    was_clicked BOOLEAN DEFAULT FALSE NOT NULL,
    click_position INTEGER,
    dwell_time_seconds INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_position CHECK (position > 0),
    CONSTRAINT valid_score CHECK (score >= 0 AND score <= 1),
    CONSTRAINT valid_component_score CHECK (
        relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 1)
    ),
    UNIQUE(search_id, position)
);

-- Indexes for ranking_data
CREATE INDEX idx_ranking_search ON search.ranking_data(search_id, position);
CREATE INDEX idx_ranking_document ON search.ranking_data(document_id);
CREATE INDEX idx_ranking_score ON search.ranking_data(score DESC);

-- Search suggestions table
CREATE TABLE search.search_suggestions (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Suggestion Data
    query TEXT NOT NULL,
    query_normalized TEXT NOT NULL,
    
    -- Metrics
    search_count INTEGER DEFAULT 1 NOT NULL,
    last_searched_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Context
    user_id BIGINT REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_search_count CHECK (search_count > 0),
    UNIQUE(query_normalized, user_id, is_deleted)
);

-- Indexes for search_suggestions
CREATE INDEX idx_search_suggestions_query ON search.search_suggestions(query_normalized) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_suggestions_count ON search.search_suggestions(search_count DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_suggestions_user ON search.search_suggestions(user_id) 
    WHERE is_deleted = FALSE AND user_id IS NOT NULL;

-- Trigger for search_suggestions
CREATE TRIGGER update_search_suggestions_updated_at 
    BEFORE UPDATE ON search.search_suggestions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ANALYTICS SCHEMA
-- ============================================

-- Events table
CREATE TABLE analytics.events (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    project_id BIGINT REFERENCES public.projects(id) ON DELETE SET NULL,
    
    -- Event Information
    event_name VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    event_action VARCHAR(50) NOT NULL,
    
    -- Event Data
    properties JSONB DEFAULT '{}'::jsonb,
    
    -- Context
    session_id UUID REFERENCES auth.sessions(session_id),
    ip_address INET,
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_event_category CHECK (event_category IN ('user', 'search', 'file', 'system', 'api'))
);

-- Indexes for events
CREATE INDEX idx_events_user ON analytics.events(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_events_name ON analytics.events(event_name, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_events_category ON analytics.events(event_category, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_events_created ON analytics.events(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_events_properties ON analytics.events USING GIN(properties);
CREATE INDEX idx_events_retention ON analytics.events(created_at) 
    WHERE is_deleted = FALSE;

-- Metrics table
CREATE TABLE analytics.metrics (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Metric Information
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    
    -- Dimensions
    dimensions JSONB DEFAULT '{}'::jsonb,
    
    -- Values
    value FLOAT NOT NULL,
    value_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Time Window
    metric_date DATE NOT NULL,
    metric_hour INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_metric_type CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'sum')),
    CONSTRAINT valid_metric_hour CHECK (metric_hour IS NULL OR (metric_hour >= 0 AND metric_hour <= 23)),
    UNIQUE(metric_name, metric_date, metric_hour, dimensions, is_deleted)
);

-- Indexes for metrics
CREATE INDEX idx_metrics_name_date ON analytics.metrics(metric_name, metric_date DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_metrics_date ON analytics.metrics(metric_date DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_metrics_dimensions ON analytics.metrics USING GIN(dimensions) 
    WHERE is_deleted = FALSE;

-- Trigger for metrics
CREATE TRIGGER update_metrics_updated_at 
    BEFORE UPDATE ON analytics.metrics 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Dashboards table
CREATE TABLE analytics.dashboards (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Dashboard Information
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Configuration
    layout JSONB DEFAULT '{}'::jsonb,
    widgets JSONB DEFAULT '[]'::jsonb,
    filters JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Indexes for dashboards
CREATE INDEX idx_dashboards_user ON analytics.dashboards(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_dashboards_public ON analytics.dashboards(is_public, created_at DESC) 
    WHERE is_deleted = FALSE AND is_public = TRUE;

-- Trigger for dashboards
CREATE TRIGGER update_dashboards_updated_at 
    BEFORE UPDATE ON analytics.dashboards 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- NOTIFICATIONS SCHEMA
-- ============================================

-- Notifications table
CREATE TABLE notifications.notifications (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Notification Information
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Data
    data JSONB DEFAULT '{}'::jsonb,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMPTZ,
    
    -- Delivery
    delivery_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    delivered_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_type CHECK (type IN ('info', 'warning', 'error', 'success')),
    CONSTRAINT valid_category CHECK (category IN ('system', 'search', 'file', 'account', 'security'))
);

-- Indexes for notifications
CREATE INDEX idx_notifications_user ON notifications.notifications(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_notifications_unread ON notifications.notifications(user_id, is_read, created_at DESC) 
    WHERE is_deleted = FALSE AND is_read = FALSE;
CREATE INDEX idx_notifications_type ON notifications.notifications(type) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_notifications_expires ON notifications.notifications(expires_at) 
    WHERE is_deleted = FALSE AND expires_at IS NOT NULL;

-- Trigger for notifications
CREATE TRIGGER update_notifications_updated_at 
    BEFORE UPDATE ON notifications.notifications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Notification preferences table
CREATE TABLE notifications.notification_preferences (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Preferences
    category VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_channel CHECK (channel IN ('email', 'push', 'in_app', 'sms')),
    UNIQUE(user_id, category, channel, is_deleted)
);

-- Indexes for notification_preferences
CREATE INDEX idx_notif_prefs_user ON notifications.notification_preferences(user_id) 
    WHERE is_deleted = FALSE;

-- Trigger for notification_preferences
CREATE TRIGGER update_notification_prefs_updated_at 
    BEFORE UPDATE ON notifications.notification_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Notification templates table
CREATE TABLE notifications.notification_templates (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Template Information
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    
    -- Template Content
    title_template TEXT NOT NULL,
    message_template TEXT NOT NULL,
    
    -- Configuration
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    channels TEXT[] NOT NULL,
    
    -- Variables
    variables JSONB DEFAULT '[]'::jsonb,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Indexes for notification_templates
CREATE INDEX idx_notif_templates_name ON notifications.notification_templates(name) 
    WHERE is_deleted = FALSE AND is_active = TRUE;

-- ============================================
-- STORAGE SCHEMA
-- ============================================

-- Uploads table
CREATE TABLE storage.uploads (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    project_id BIGINT REFERENCES public.projects(id) ON DELETE SET NULL,
    
    -- File Information
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_url TEXT,
    content_type VARCHAR(100),
    file_size_bytes BIGINT NOT NULL,
    
    -- Storage
    storage_provider VARCHAR(50) DEFAULT 'local' NOT NULL,
    storage_bucket VARCHAR(100),
    storage_key TEXT,
    
    -- Hashing
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    
    -- Status
    status VARCHAR(50) DEFAULT 'uploaded' NOT NULL,
    error_message TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMPTZ,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('uploaded', 'processing', 'ready', 'failed', 'deleted')),
    CONSTRAINT valid_file_size CHECK (file_size_bytes > 0),
    CONSTRAINT valid_storage_provider CHECK (storage_provider IN ('local', 's3', 'gcs', 'azure'))
);

-- Indexes for uploads
CREATE INDEX idx_uploads_user ON storage.uploads(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_project ON storage.uploads(project_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_status ON storage.uploads(status) WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_content_type ON storage.uploads(content_type) WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_sha256 ON storage.uploads(sha256_hash) 
    WHERE is_deleted = FALSE AND sha256_hash IS NOT NULL;
CREATE INDEX idx_uploads_metadata ON storage.uploads USING GIN(metadata);
CREATE INDEX idx_uploads_tags ON storage.uploads USING GIN(tags);

-- Trigger for uploads
CREATE TRIGGER update_uploads_updated_at 
    BEFORE UPDATE ON storage.uploads 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- File versions table
CREATE TABLE storage.file_versions (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    upload_id BIGINT NOT NULL REFERENCES storage.uploads(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Version Information
    version_number INTEGER NOT NULL,
    change_description TEXT,
    
    -- File Information
    filename VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    content_type VARCHAR(100),
    sha256_hash VARCHAR(64),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_version CHECK (version_number > 0),
    CONSTRAINT valid_file_size CHECK (file_size_bytes > 0),
    UNIQUE(upload_id, version_number, is_deleted)
);

-- Indexes for file_versions
CREATE INDEX idx_file_versions_upload ON storage.file_versions(upload_id, version_number DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_file_versions_user ON storage.file_versions(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;

-- File permissions table
CREATE TABLE storage.file_permissions (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    upload_id BIGINT NOT NULL REFERENCES storage.uploads(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES public.users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES public.roles(id) ON DELETE CASCADE,
    
    -- Permission
    permission VARCHAR(50) NOT NULL,
    
    -- Grant Details
    granted_by BIGINT NOT NULL REFERENCES public.users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_permission CHECK (permission IN ('read', 'write', 'delete', 'admin')),
    CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > granted_at),
    CONSTRAINT valid_grantee CHECK (
        (user_id IS NOT NULL AND role_id IS NULL) OR
        (user_id IS NULL AND role_id IS NOT NULL)
    ),
    UNIQUE(upload_id, user_id, role_id, permission, is_deleted)
);

-- Indexes for file_permissions
CREATE INDEX idx_file_perms_upload ON storage.file_permissions(upload_id) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_file_perms_user ON storage.file_permissions(user_id) 
    WHERE is_deleted = FALSE AND user_id IS NOT NULL;
CREATE INDEX idx_file_perms_role ON storage.file_permissions(role_id) 
    WHERE is_deleted = FALSE AND role_id IS NOT NULL;
CREATE INDEX idx_file_perms_expires ON storage.file_permissions(expires_at) 
    WHERE is_deleted = FALSE AND expires_at IS NOT NULL;

-- Storage quotas table
CREATE TABLE storage.storage_quotas (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE UNIQUE,
    
    -- Quota Information
    quota_bytes BIGINT NOT NULL,
    used_bytes BIGINT DEFAULT 0 NOT NULL,
    
    -- Limits
    max_file_size_bytes BIGINT,
    max_files_count INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_quota CHECK (quota_bytes > 0),
    CONSTRAINT valid_used CHECK (used_bytes >= 0 AND used_bytes <= quota_bytes),
    CONSTRAINT valid_max_file_size CHECK (max_file_size_bytes IS NULL OR max_file_size_bytes > 0),
    CONSTRAINT valid_max_files CHECK (max_files_count IS NULL OR max_files_count > 0)
);

-- Indexes for storage_quotas
CREATE UNIQUE INDEX idx_storage_quotas_user ON storage.storage_quotas(user_id) 
    WHERE is_deleted = FALSE;

-- Trigger for storage_quotas
CREATE TRIGGER update_storage_quotas_updated_at 
    BEFORE UPDATE ON storage.storage_quotas 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- AUDIT SCHEMA
-- ============================================

-- Audit events table
CREATE TABLE audit.audit_events (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Actor
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES auth.sessions(session_id),
    
    -- Action
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id BIGINT,
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    changes JSONB,
    
    -- Context
    ip_address INET NOT NULL,
    user_agent TEXT,
    location VARCHAR(200),
    
    -- Status
    status VARCHAR(50) DEFAULT 'success' NOT NULL,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'import')),
    CONSTRAINT valid_status CHECK (status IN ('success', 'failure', 'blocked'))
);

-- Indexes for audit_events
CREATE INDEX idx_audit_user ON audit.audit_events(user_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit.audit_events(resource_type, resource_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit.audit_events(action, created_at DESC);
CREATE INDEX idx_audit_created ON audit.audit_events(created_at DESC);
CREATE INDEX idx_audit_ip ON audit.audit_events(ip_address, created_at DESC);
CREATE INDEX idx_audit_session ON audit.audit_events(session_id);
CREATE INDEX idx_audit_retention ON audit.audit_events(created_at);

-- Data access logs table
CREATE TABLE audit.data_access_logs (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Actor
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES auth.sessions(session_id),
    
    -- Data Access
    data_type VARCHAR(100) NOT NULL,
    data_id BIGINT NOT NULL,
    access_type VARCHAR(50) NOT NULL,
    
    -- Context
    ip_address INET NOT NULL,
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_access_type CHECK (access_type IN ('read', 'export', 'download', 'update'))
);

-- Indexes for data_access_logs
CREATE INDEX idx_data_access_user ON audit.data_access_logs(user_id, created_at DESC);
CREATE INDEX idx_data_access_type ON audit.data_access_logs(data_type, data_id, created_at DESC);
CREATE INDEX idx_data_access_created ON audit.data_access_logs(created_at DESC);

-- ============================================
-- ADMIN SCHEMA
-- ============================================

-- Settings table
CREATE TABLE admin.settings (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Setting Information
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(50) DEFAULT 'string' NOT NULL,
    
    -- Metadata
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_value_type CHECK (value_type IN ('string', 'integer', 'boolean', 'json', 'float'))
);

-- Indexes for settings
CREATE UNIQUE INDEX idx_settings_key ON admin.settings(key);

-- Trigger for settings
CREATE TRIGGER update_settings_updated_at 
    BEFORE UPDATE ON admin.settings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Feature flags table
CREATE TABLE admin.feature_flags (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Flag Information
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    
    -- Status
    is_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Rollout
    rollout_percentage INTEGER DEFAULT 100 NOT NULL,
    target_roles TEXT[],
    target_users BIGINT[],
    
    -- Timestamps
    enabled_at TIMESTAMPTZ,
    disabled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_rollout CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100)
);

-- Indexes for feature_flags
CREATE UNIQUE INDEX idx_feature_flags_name ON admin.feature_flags(name);

-- Trigger for feature_flags
CREATE TRIGGER update_feature_flags_updated_at 
    BEFORE UPDATE ON admin.feature_flags 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- System config table
CREATE TABLE admin.system_config (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Configuration
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    
    -- Metadata
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Indexes for system_config
CREATE UNIQUE INDEX idx_system_config_key ON admin.system_config(config_key) 
    WHERE is_deleted = FALSE;

-- Trigger for system_config
CREATE TRIGGER update_system_config_updated_at 
    BEFORE UPDATE ON admin.system_config 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Maintenance windows table
CREATE TABLE admin.maintenance_windows (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Window Information
    title VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Schedule
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'scheduled' NOT NULL,
    
    -- Impact
    affects_reads BOOLEAN DEFAULT TRUE NOT NULL,
    affects_writes BOOLEAN DEFAULT TRUE NOT NULL,
    affected_services TEXT[],
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    CONSTRAINT valid_dates CHECK (ends_at > starts_at)
);

-- Indexes for maintenance_windows
CREATE INDEX idx_maintenance_windows_dates ON admin.maintenance_windows(starts_at, ends_at) 
    WHERE status IN ('scheduled', 'in_progress');

-- ============================================
-- SEED DATA
-- ============================================

-- Seed roles
INSERT INTO public.roles (name, display_name, description, level, is_system) VALUES
    ('super_admin', 'Super Administrator', 'Full system access', 100, TRUE),
    ('admin', 'Administrator', 'Administrative access', 80, TRUE),
    ('moderator', 'Moderator', 'Content moderation', 50, TRUE),
    ('user', 'User', 'Standard user', 10, TRUE),
    ('guest', 'Guest', 'Limited access', 1, TRUE);

-- Seed permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('users.create', 'Create Users', 'Create new users', 'users', 'create', TRUE),
    ('users.read', 'Read Users', 'View user profiles', 'users', 'read', TRUE),
    ('users.update', 'Update Users', 'Edit user profiles', 'users', 'update', TRUE),
    ('users.delete', 'Delete Users', 'Delete users', 'users', 'delete', TRUE),
    ('users.admin', 'Admin Users', 'Full user management', 'users', 'admin', TRUE),
    ('searches.create', 'Create Searches', 'Perform searches', 'searches', 'create', TRUE),
    ('searches.read', 'Read Searches', 'View search history', 'searches', 'read', TRUE),
    ('searches.delete', 'Delete Searches', 'Delete search history', 'searches', 'delete', TRUE),
    ('files.upload', 'Upload Files', 'Upload files', 'files', 'create', TRUE),
    ('files.read', 'Read Files', 'View files', 'files', 'read', TRUE),
    ('files.delete', 'Delete Files', 'Delete files', 'files', 'delete', TRUE),
    ('files.manage', 'Manage Files', 'Full file management', 'files', 'manage', TRUE),
    ('analytics.view', 'View Analytics', 'View analytics dashboards', 'analytics', 'read', TRUE),
    ('admin.access', 'Admin Access', 'Access admin panel', 'admin', 'admin', TRUE);

-- Seed role-permission mappings
INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT r.id, p.id, NULL, NOW()
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'super_admin';

INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT r.id, p.id, NULL, NOW()
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'admin' AND p.name NOT IN ('users.admin', 'admin.access');

INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT r.id, p.id, NULL, NOW()
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'moderator' AND p.resource IN ('searches', 'files');

INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT r.id, p.id, NULL, NOW()
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'user' AND p.name IN ('searches.create', 'searches.read', 'files.upload', 'files.read');

INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT r.id, p.id, NULL, NOW()
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'guest' AND p.name IN ('searches.create');

-- Seed settings
INSERT INTO admin.settings (key, value, value_type, description, is_public) VALUES
    ('app.name', 'Nebula Search', 'string', 'Application name', TRUE),
    ('app.version', '1.0.0', 'string', 'Application version', TRUE),
    ('app.environment', 'production', 'string', 'Environment (development, staging, production)', FALSE),
    ('auth.jwt_expiry_minutes', '15', 'integer', 'JWT access token expiry in minutes', FALSE),
    ('auth.refresh_token_expiry_days', '7', 'integer', 'Refresh token expiry in days', FALSE),
    ('auth.max_login_attempts', '5', 'integer', 'Maximum failed login attempts before lockout', FALSE),
    ('auth.lockout_duration_minutes', '30', 'integer', 'Account lockout duration in minutes', FALSE),
    ('search.max_results', '100', 'integer', 'Maximum search results per query', TRUE),
    ('search.cache_ttl_seconds', '300', 'integer', 'Search cache TTL in seconds', FALSE),
    ('storage.max_upload_size_mb', '100', 'integer', 'Maximum file upload size in MB', TRUE),
    ('analytics.retention_days', '90', 'integer', 'Analytics data retention in days', FALSE),
    ('notifications.max_per_user', '100', 'integer', 'Maximum notifications per user', FALSE);

-- Seed feature flags
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('vector_search', 'Vector Search', 'Enable vector-based semantic search', TRUE, 100),
    ('ai_synthesis', 'AI Synthesis', 'Enable AI-powered answer synthesis', TRUE, 100),
    ('advanced_analytics', 'Advanced Analytics', 'Enable advanced analytics dashboard', FALSE, 0),
    ('file_versioning', 'File Versioning', 'Enable file versioning', TRUE, 100),
    ('multi_tenant', 'Multi-Tenant', 'Enable multi-tenant support', FALSE, 0),
    ('api_access', 'API Access', 'Enable API access for users', TRUE, 100);

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

-- Record migration
CREATE TABLE IF NOT EXISTS public.migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

INSERT INTO public.migrations (version, name) VALUES ('001', 'Initial schema');