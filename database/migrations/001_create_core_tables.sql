-- ============================================
-- Migration: Create Core Tables
-- Created: 2025-01-04
-- Description: Creates users, profiles, roles, permissions tables
-- ============================================

-- Utility functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION soft_delete()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_deleted = TRUE;
    NEW.deleted_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS search;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS admin;

-- Users table
CREATE TABLE IF NOT EXISTS public.users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    locked_until TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    last_failed_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_login TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_lock_time CHECK (locked_until IS NULL OR locked_until > NOW()),
    CONSTRAINT no_self_lock CHECK (NOT (is_locked = TRUE AND locked_until IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_users_active ON public.users(is_active, is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_users_created ON public.users(created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON public.users(email) WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Profiles table
CREATE TABLE IF NOT EXISTS public.profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,
    bio TEXT,
    location VARCHAR(200),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_theme CHECK (theme IN ('light', 'dark', 'system')),
    CONSTRAINT valid_language CHECK (language ~* '^[a-z]{2}(-[A-Z]{2})?$'),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles(user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_profiles_metadata ON public.profiles USING GIN(metadata);

CREATE TRIGGER IF NOT EXISTS update_profiles_updated_at 
    BEFORE UPDATE ON public.profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Roles table
CREATE TABLE IF NOT EXISTS public.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_role_id INTEGER REFERENCES public.roles(id),
    level INTEGER DEFAULT 0 NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_role_name CHECK (name ~* '^[a-z_]+$'),
    CONSTRAINT valid_level CHECK (level >= 0 AND level <= 100)
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON public.roles(name) WHERE is_deleted = FALSE AND is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_roles_level ON public.roles(level);

CREATE TRIGGER IF NOT EXISTS update_roles_updated_at 
    BEFORE UPDATE ON public.roles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Permissions table
CREATE TABLE IF NOT EXISTS public.permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'manage', 'admin')),
    UNIQUE(resource, action, name)
);

CREATE INDEX IF NOT EXISTS idx_permissions_resource ON public.permissions(resource) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_permissions_name ON public.permissions(name) WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_permissions_updated_at 
    BEFORE UPDATE ON public.permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- User roles junction table
CREATE TABLE IF NOT EXISTS public.user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
    assigned_by BIGINT REFERENCES public.users(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > assigned_at),
    UNIQUE(user_id, role_id, is_deleted)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON public.user_roles(user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON public.user_roles(role_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_roles_expires ON public.user_roles(expires_at) 
    WHERE is_deleted = FALSE AND expires_at IS NOT NULL;

CREATE TRIGGER IF NOT EXISTS update_user_roles_updated_at 
    BEFORE UPDATE ON public.user_roles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Role permissions junction table
CREATE TABLE IF NOT EXISTS public.role_permissions (
    id BIGSERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES public.permissions(id) ON DELETE CASCADE,
    granted_by BIGINT REFERENCES public.users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT valid_permission_expiry CHECK (expires_at IS NULL OR expires_at > granted_at),
    UNIQUE(role_id, permission_id, is_deleted)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON public.role_permissions(role_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON public.role_permissions(permission_id) WHERE is_deleted = FALSE;

CREATE TRIGGER IF NOT EXISTS update_role_permissions_updated_at 
    BEFORE UPDATE ON public.role_permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default roles
INSERT INTO public.roles (name, display_name, description, level, is_system) 
VALUES ('admin', 'Administrator', 'Full system access', 100, TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO public.roles (name, display_name, description, level, is_system) 
VALUES ('user', 'User', 'Standard user access', 10, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO public.permissions (name, display_name, resource, action, is_system)
VALUES ('users.read', 'Read Users', 'users', 'read', TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO public.permissions (name, display_name, resource, action, is_system)
VALUES ('users.write', 'Write Users', 'users', 'write', TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO public.permissions (name, display_name, resource, action, is_system)
VALUES ('admin.access', 'Admin Access', 'admin', 'admin', TRUE)
ON CONFLICT (name) DO NOTHING;