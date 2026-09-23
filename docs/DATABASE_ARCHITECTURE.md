# IOIS (Nebula) — Production Database Architecture

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Schema Design](#schema-design)
4. [Entity Relationship Diagram](#entity-relationship-diagram)
5. [Authentication System](#authentication-system)
6. [Search Architecture](#search-architecture)
7. [Analytics System](#analytics-system)
8. [Storage System](#storage-system)
9. [Performance Optimization](#performance-optimization)
10. [Reliability & Backup](#reliability--backup)
11. [Security](#security)
12. [Implementation Roadmap](#implementation-roadmap)

---

## Overview

### Project: IOIS (Nebula Architecture)
- **Application Type**: Full-stack web application
- **Frontend**: TypeScript (Vanilla JS/HTML)
- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL 15+
- **API**: REST with JWT authentication
- **Deployment**: Docker-ready, containerized
- **Architecture**: Modular, scalable, production-ready

### Design Principles
- **Modularity**: Separate schemas for distinct domains
- **Scalability**: Partitioning, indexing, connection pooling
- **Security**: RBAC, encryption, audit trails, RLS
- **Performance**: Query optimization, caching, materialized views
- **Reliability**: Backups, replication, disaster recovery
- **Maintainability**: Clear naming conventions, migrations, documentation

---

## Architecture Layers

### Layer 1: Core Application Data
- **Schema**: `public`
- **Purpose**: User profiles, roles, permissions, projects
- **Tables**: users, profiles, roles, permissions, user_roles, projects

### Layer 2: Authentication
- **Schema**: `auth`
- **Purpose**: JWT tokens, sessions, email verification, password reset
- **Tables**: refresh_tokens, sessions, email_verification, password_reset, login_history

### Layer 3: Search
- **Schema**: `search`
- **Purpose**: Search queries, history, indexed documents, ranking
- **Tables**: searches, search_history, indexed_documents, ranking_data, search_suggestions

### Layer 4: Analytics
- **Schema**: `analytics`
- **Purpose**: Event tracking, metrics, dashboards
- **Tables**: events, metrics, dashboards, metric_aggregations

### Layer 5: Notifications
- **Schema**: `notifications`
- **Purpose**: User notifications, preferences, delivery tracking
- **Tables**: notifications, notification_preferences, notification_templates

### Layer 6: File Storage
- **Schema**: `storage`
- **Purpose**: File metadata, versions, permissions, quotas
- **Tables**: uploads, file_versions, file_permissions, storage_quotas

### Layer 7: Audit Logs
- **Schema**: `audit`
- **Purpose**: Comprehensive audit trail for all actions
- **Tables**: logs, audit_events, data_access_logs

### Layer 8: Admin System
- **Schema**: `admin`
- **Purpose**: Admin settings, feature flags, system configuration
- **Tables**: settings, feature_flags, system_config, maintenance_windows

---

## Schema Design

### Database Configuration

```sql
-- Database: nebula_db
-- Owner: nebula_admin
-- Encoding: UTF8
-- Collation: en_US.UTF-8
-- Timezone: UTC
-- Connection Limit: 100
-- Shared Buffers: 256MB
-- Work Memory: 64MB
```

### Schema Organization

```sql
-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS search;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS admin;

-- Set search path
ALTER DATABASE nebula_db SET search_path TO public, auth, search, analytics, 
                                    notifications, storage, audit, admin;
```

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         PUBLIC SCHEMA                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │    roles     │─────────│  user_roles  │                     │
│  └──────────────┘         └──────────────┘                     │
│         │                         │                              │
│         │                         │                              │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ permissions  │─────────│ role_perms   │                     │
│  └──────────────┘         └──────────────┘                     │
│         │                                                 │      │
│         │                                                 │      │
│  ┌──────────────┐         ┌──────────────┐         ┌────────┐ │
│  │    users     │─────────│   profiles   │         │projects│ │
│  └──────────────┘         └──────────────┘         └────────┘ │
│         │                                                 │      │
│         │                                                 │      │
│         └─────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          AUTH SCHEMA                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │     users      │─────────│  refresh_tokens  │               │
│  └────────────────┘         └──────────────────┘               │
│         │                                                       │
│         │                                                       │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │   sessions     │         │ login_history    │               │
│  └────────────────┘         └──────────────────┘               │
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │email_verify    │         │  password_reset  │               │
│  └────────────────┘         └──────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         SEARCH SCHEMA                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │    users       │─────────│     searches     │               │
│  └────────────────┘         └──────────────────┘               │
│         │                         │                              │
│         │                         │                              │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │ indexed_docs   │         │  search_history  │               │
│  └────────────────┘         └──────────────────┘               │
│         │                                                       │
│         │                                                       │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │ ranking_data   │         │search_suggestions│               │
│  └────────────────┘         └──────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       ANALYTICS SCHEMA                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │    users       │─────────│      events      │               │
│  └────────────────┘         └──────────────────┘               │
│         │                         │                              │
│         │                         │                              │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │   metrics      │         │ metric_aggs      │               │
│  └────────────────┘         └──────────────────┘               │
│         │                                                       │
│         │                                                       │
│  ┌────────────────┐                                            │
│  │   dashboards   │                                            │
│  └────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE SCHEMA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │    users       │─────────│      uploads      │               │
│  └────────────────┘         └──────────────────┘               │
│         │                         │                              │
│         │                         │                              │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │ file_versions  │         │ file_permissions  │               │
│  └────────────────┘         └──────────────────┘               │
│         │                                                       │
│         │                                                       │
│  ┌────────────────┐                                            │
│  │storage_quotas  │                                            │
│  └────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       NOTIFICATIONS SCHEMA                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │    users       │─────────│  notifications   │               │
│  └────────────────┘         └──────────────────┘               │
│         │                         │                              │
│         │                         │                              │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │notif_prefs     │         │notif_templates   │               │
│  └────────────────┘         └──────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        AUDIT SCHEMA                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │    users       │─────────│   audit_events    │               │
│  └────────────────┘         └──────────────────┘               │
│         │                         │                              │
│         │                         │                              │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │ data_access    │         │       logs        │               │
│  └────────────────┘         └──────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN SCHEMA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │    settings    │         │  feature_flags    │               │
│  └────────────────┘         └──────────────────┘               │
│         │                                                       │
│         │                                                       │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │ system_config  │         │maintenance_window │               │
│  └────────────────┘         └──────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Tables (Public Schema)

### 1. users

**Purpose**: Central user authentication and identification

```sql
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

-- Indexes
CREATE INDEX idx_users_email ON public.users(email) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_active ON public.users(is_active, is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_created ON public.users(created_at DESC);
CREATE UNIQUE INDEX idx_users_email_unique ON public.users(email) WHERE is_deleted = FALSE;

-- Trigger for updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

**Columns**:
- `id`: Unique identifier (BIGSERIAL for scalability)
- `email`: User email (unique, validated)
- `email_verified`: Email verification status
- `password_hash`: PBKDF2-SHA256 hashed password
- `is_active`: Account active status
- `is_locked`: Account lock status
- `locked_until`: Account lock expiration
- `failed_login_attempts`: Brute force protection counter
- `last_failed_login`: Last failed login timestamp
- `created_at`, `updated_at`, `last_login`: Timestamps
- `password_changed_at`: Password rotation tracking
- `deleted_at`, `is_deleted`: Soft delete support

**Constraints**:
- Email format validation
- Lock time must be in future
- Cannot have permanent lock without expiration

**Indexes**:
- Email (unique, partial for non-deleted)
- Active status (composite)
- Created date (for sorting)

---

### 2. profiles

**Purpose**: Extended user profile information

```sql
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

-- Indexes
CREATE INDEX idx_profiles_user_id ON public.profiles(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_profiles_metadata ON public.profiles USING GIN(metadata);

-- Trigger
CREATE TRIGGER update_profiles_updated_at 
    BEFORE UPDATE ON public.profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

**Columns**:
- `user_id`: Foreign key to users
- Personal info: name, avatar, bio, location
- Preferences: theme, notifications, timezone, language
- `metadata`: Flexible JSONB for extensibility

---

### 3. roles

**Purpose**: Role-based access control (RBAC)

```sql
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
    is_system BOOLEAN DEFAULT FALSE NOT NULL,  -- Cannot be deleted
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

-- Indexes
CREATE INDEX idx_roles_name ON public.roles(name) WHERE is_deleted = FALSE AND is_active = TRUE;
CREATE INDEX idx_roles_level ON public.roles(level);

-- Trigger
CREATE TRIGGER update_roles_updated_at 
    BEFORE UPDATE ON public.roles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Seed Data
INSERT INTO public.roles (name, display_name, description, level, is_system) VALUES
    ('super_admin', 'Super Administrator', 'Full system access', 100, TRUE),
    ('admin', 'Administrator', 'Administrative access', 80, TRUE),
    ('moderator', 'Moderator', 'Content moderation', 50, TRUE),
    ('user', 'User', 'Standard user', 10, TRUE),
    ('guest', 'Guest', 'Limited access', 1, TRUE);
```

---

### 4. permissions

**Purpose**: Granular permission definitions

```sql
CREATE TABLE public.permissions (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Permission Information
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    resource VARCHAR(100) NOT NULL,  -- e.g., 'users', 'searches', 'files'
    action VARCHAR(50) NOT NULL,     -- e.g., 'create', 'read', 'update', 'delete'
    
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

-- Indexes
CREATE INDEX idx_permissions_resource ON public.permissions(resource) WHERE is_deleted = FALSE;
CREATE INDEX idx_permissions_name ON public.permissions(name) WHERE is_deleted = FALSE;

-- Trigger
CREATE TRIGGER update_permissions_updated_at 
    BEFORE UPDATE ON public.permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Seed Data
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
```

---

### 5. user_roles

**Purpose**: Many-to-many relationship between users and roles

```sql
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

-- Indexes
CREATE INDEX idx_user_roles_user ON public.user_roles(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_user_roles_role ON public.user_roles(role_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_user_roles_expires ON public.user_roles(expires_at) 
    WHERE is_deleted = FALSE AND expires_at IS NOT NULL;

-- Trigger
CREATE TRIGGER update_user_roles_updated_at 
    BEFORE UPDATE ON public.user_roles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 6. role_permissions

**Purpose**: Many-to-many relationship between roles and permissions

```sql
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

-- Indexes
CREATE INDEX idx_role_perms_role ON public.role_permissions(role_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_role_perms_perm ON public.role_permissions(permission_id) WHERE is_deleted = FALSE;

-- Trigger
CREATE TRIGGER update_role_permissions_updated_at 
    BEFORE UPDATE ON public.role_permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 7. projects

**Purpose**: User projects/workspaces

```sql
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

-- Indexes
CREATE INDEX idx_projects_owner ON public.projects(owner_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_projects_public ON public.projects(is_public, is_archived) 
    WHERE is_deleted = FALSE AND is_public = TRUE;
CREATE INDEX idx_projects_settings ON public.projects USING GIN(settings);

-- Trigger
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON public.projects 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Authentication System (Auth Schema)

### 1. refresh_tokens

**Purpose**: JWT refresh token storage with rotation support

```sql
CREATE TABLE auth.refresh_tokens (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Token Information
    token_hash VARCHAR(255) UNIQUE NOT NULL,  -- Hashed token for security
    jti UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),  -- JWT ID for revocation
    
    -- Device Information
    device_name VARCHAR(200),
    device_type VARCHAR(50),  -- 'mobile', 'desktop', 'tablet'
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

-- Indexes
CREATE INDEX idx_refresh_tokens_user ON auth.refresh_tokens(user_id) 
    WHERE is_deleted = FALSE AND is_revoked = FALSE;
CREATE INDEX idx_refresh_tokens_jti ON auth.refresh_tokens(jti) WHERE is_deleted = FALSE;
CREATE INDEX idx_refresh_tokens_expires ON auth.refresh_tokens(expires_at) 
    WHERE is_deleted = FALSE AND is_revoked = FALSE;

-- Auto-cleanup expired tokens (run periodically)
CREATE INDEX idx_refresh_tokens_cleanup ON auth.refresh_tokens(expires_at) 
    WHERE is_deleted = FALSE AND expires_at < NOW();

-- Trigger
CREATE TRIGGER update_refresh_tokens_updated_at 
    BEFORE UPDATE ON auth.refresh_tokens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 2. sessions

**Purpose**: Active user session management

```sql
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
    location VARCHAR(200),  -- Geo-location
    
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

-- Indexes
CREATE INDEX idx_sessions_user ON auth.sessions(user_id) 
    WHERE is_deleted = FALSE AND is_active = TRUE;
CREATE INDEX idx_sessions_session_id ON auth.sessions(session_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_sessions_expires ON auth.sessions(expires_at) 
    WHERE is_deleted = FALSE AND is_active = TRUE;
CREATE INDEX idx_sessions_last_activity ON auth.sessions(last_activity_at DESC) 
    WHERE is_deleted = FALSE AND is_active = TRUE;

-- Trigger
CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON auth.sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 3. login_history

**Purpose**: Comprehensive login attempt tracking

```sql
CREATE TABLE auth.login_history (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    
    -- Login Attempt
    email VARCHAR(255) NOT NULL,
    attempt_type VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'blocked'
    
    -- Request Information
    ip_address INET NOT NULL,
    user_agent TEXT,
    location VARCHAR(200),
    
    -- Failure Details
    failure_reason VARCHAR(100),  -- 'invalid_password', 'account_locked', 'invalid_token'
    
    -- Timestamps
    attempted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_attempt_type CHECK (attempt_type IN ('success', 'failed', 'blocked'))
);

-- Indexes
CREATE INDEX idx_login_history_user ON auth.login_history(user_id, attempted_at DESC);
CREATE INDEX idx_login_history_email ON auth.login_history(email, attempted_at DESC);
CREATE INDEX idx_login_history_ip ON auth.login_history(ip_address, attempted_at DESC);
CREATE INDEX idx_login_history_attempt ON auth.login_history(attempt_type, attempted_at DESC);

-- Partitioning by month for large-scale deployments
-- CREATE TABLE auth.login_history_y2024m01 PARTITION OF auth.login_history
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

---

### 4. email_verification

**Purpose**: Email verification token management

```sql
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

-- Indexes
CREATE INDEX idx_email_verify_user ON auth.email_verification(user_id) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_email_verify_token ON auth.email_verification(token_hash) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_email_verify_expires ON auth.email_verification(expires_at) 
    WHERE is_deleted = FALSE AND is_used = FALSE;

-- Auto-cleanup
CREATE INDEX idx_email_verify_cleanup ON auth.email_verification(expires_at) 
    WHERE is_deleted = FALSE AND expires_at < NOW();
```

---

### 5. password_reset

**Purpose**: Password reset token management

```sql
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

-- Indexes
CREATE INDEX idx_password_reset_user ON auth.password_reset(user_id) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_password_reset_token ON auth.password_reset(token_hash) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
CREATE INDEX idx_password_reset_expires ON auth.password_reset(expires_at) 
    WHERE is_deleted = FALSE AND is_used = FALSE;
```

---

## Search Architecture (Search Schema)

### 1. searches

**Purpose**: Main search query logging

```sql
CREATE TABLE search.searches (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    project_id BIGINT REFERENCES public.projects(id) ON DELETE SET NULL,
    
    -- Search Query
    query TEXT NOT NULL,
    query_normalized TEXT,  -- Lowercase, trimmed version
    
    -- Search Parameters
    search_type VARCHAR(50) DEFAULT 'web' NOT NULL,  -- 'web', 'vector', 'hybrid'
    filters JSONB DEFAULT '{}'::jsonb,
    
    -- Results
    results_count INTEGER DEFAULT 0 NOT NULL,
    results_data JSONB,  -- Full results for caching
    
    -- Performance
    execution_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Source
    source VARCHAR(50) DEFAULT 'web' NOT NULL,  -- 'web', 'api', 'mobile'
    
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

-- Indexes
CREATE INDEX idx_searches_user ON search.searches(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_query ON search.searches USING GIN(to_tsvector('english', query)) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_created ON search.searches(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_type ON search.searches(search_type) WHERE is_deleted = FALSE;
CREATE INDEX idx_searches_project ON search.searches(project_id) WHERE is_deleted = FALSE;

-- Full-text search index
CREATE INDEX idx_searches_fts ON search.searches USING GIN(
    to_tsvector('english', COALESCE(query, ''))
);

-- Partitioning by month (optional for high volume)
-- CREATE TABLE search.searches_y2024m01 PARTITION OF search.searches
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

---

### 2. search_history

**Purpose**: User search history with personalization data

```sql
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
    dwell_time_seconds INTEGER,  -- Time spent on result
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

-- Indexes
CREATE INDEX idx_search_history_user ON search.search_history(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_history_query ON search.search_history USING GIN(to_tsvector('english', query)) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_history_session ON search.search_history(session_id) 
    WHERE is_deleted = FALSE;

-- Retention: Keep 90 days, archive older
CREATE INDEX idx_search_history_retention ON search.search_history(created_at) 
    WHERE is_deleted = FALSE;
```

---

### 3. indexed_documents

**Purpose**: Vector search document storage

```sql
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
    content_hash VARCHAR(64),  -- SHA-256 for deduplication
    
    -- Vector Embedding (stored separately in vector DB, reference here)
    embedding_id VARCHAR(255),  -- Reference to vector store
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT '{}',
    
    -- Indexing Status
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,  -- 'pending', 'processing', 'indexed', 'failed'
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

-- Indexes
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

-- Trigger
CREATE TRIGGER update_indexed_docs_updated_at 
    BEFORE UPDATE ON search.indexed_documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 4. ranking_data

**Purpose**: Search result ranking and relevance scoring

```sql
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

-- Indexes
CREATE INDEX idx_ranking_search ON search.ranking_data(search_id, position);
CREATE INDEX idx_ranking_document ON search.ranking_data(document_id);
CREATE INDEX idx_ranking_score ON search.ranking_data(score DESC);
```

---

### 5. search_suggestions

**Purpose**: Autocomplete and search suggestions

```sql
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

-- Indexes
CREATE INDEX idx_search_suggestions_query ON search.search_suggestions(query_normalized) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_suggestions_count ON search.search_suggestions(search_count DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_search_suggestions_user ON search.search_suggestions(user_id) 
    WHERE is_deleted = FALSE AND user_id IS NOT NULL;

-- Trigger
CREATE TRIGGER update_search_suggestions_updated_at 
    BEFORE UPDATE ON search.search_suggestions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Analytics System (Analytics Schema)

### 1. events

**Purpose**: Event tracking for user actions

```sql
CREATE TABLE analytics.events (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    project_id BIGINT REFERENCES public.projects(id) ON DELETE SET NULL,
    
    -- Event Information
    event_name VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,  -- 'user', 'search', 'file', 'system'
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

-- Indexes
CREATE INDEX idx_events_user ON analytics.events(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_events_name ON analytics.events(event_name, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_events_category ON analytics.events(event_category, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_events_created ON analytics.events(created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_events_properties ON analytics.events USING GIN(properties);

-- Partitioning by month for high-volume tables
-- CREATE TABLE analytics.events_y2024m01 PARTITION OF analytics.events
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Retention policy: 90 days on main table, archive older
CREATE INDEX idx_events_retention ON analytics.events(created_at) 
    WHERE is_deleted = FALSE;
```

---

### 2. metrics

**Purpose**: Aggregated metrics and KPIs

```sql
CREATE TABLE analytics.metrics (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Metric Information
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,  -- 'counter', 'gauge', 'histogram'
    
    -- Dimensions
    dimensions JSONB DEFAULT '{}'::jsonb,  -- e.g., {"user_type": "premium", "region": "us"}
    
    -- Values
    value FLOAT NOT NULL,
    value_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Time Window
    metric_date DATE NOT NULL,
    metric_hour INTEGER,  -- 0-23 for hourly metrics
    
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

-- Indexes
CREATE INDEX idx_metrics_name_date ON analytics.metrics(metric_name, metric_date DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_metrics_date ON analytics.metrics(metric_date DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_metrics_dimensions ON analytics.metrics USING GIN(dimensions) 
    WHERE is_deleted = FALSE;

-- Trigger
CREATE TRIGGER update_metrics_updated_at 
    BEFORE UPDATE ON analytics.metrics 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 3. dashboards

**Purpose**: User-defined analytics dashboards

```sql
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

-- Indexes
CREATE INDEX idx_dashboards_user ON analytics.dashboards(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_dashboards_public ON analytics.dashboards(is_public, created_at DESC) 
    WHERE is_deleted = FALSE AND is_public = TRUE;

-- Trigger
CREATE TRIGGER update_dashboards_updated_at 
    BEFORE UPDATE ON analytics.dashboards 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Storage System (Storage Schema)

### 1. uploads

**Purpose**: File upload metadata

```sql
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
    storage_provider VARCHAR(50) DEFAULT 'local' NOT NULL,  -- 'local', 's3', 'gcs', 'azure'
    storage_bucket VARCHAR(100),
    storage_key TEXT,
    
    -- Hashing
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    
    -- Status
    status VARCHAR(50) DEFAULT 'uploaded' NOT NULL,  -- 'uploaded', 'processing', 'ready', 'failed'
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

-- Indexes
CREATE INDEX idx_uploads_user ON storage.uploads(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_project ON storage.uploads(project_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_status ON storage.uploads(status) WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_content_type ON storage.uploads(content_type) WHERE is_deleted = FALSE;
CREATE INDEX idx_uploads_sha256 ON storage.uploads(sha256_hash) 
    WHERE is_deleted = FALSE AND sha256_hash IS NOT NULL;
CREATE INDEX idx_uploads_metadata ON storage.uploads USING GIN(metadata);
CREATE INDEX idx_uploads_tags ON storage.uploads USING GIN(tags);

-- Trigger
CREATE TRIGGER update_uploads_updated_at 
    BEFORE UPDATE ON storage.uploads 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 2. file_versions

**Purpose**: File versioning and history

```sql
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

-- Indexes
CREATE INDEX idx_file_versions_upload ON storage.file_versions(upload_id, version_number DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_file_versions_user ON storage.file_versions(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
```

---

### 3. file_permissions

**Purpose**: File access control

```sql
CREATE TABLE storage.file_permissions (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    upload_id BIGINT NOT NULL REFERENCES storage.uploads(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES public.users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES public.roles(id) ON DELETE CASCADE,
    
    -- Permission
    permission VARCHAR(50) NOT NULL,  -- 'read', 'write', 'delete', 'admin'
    
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

-- Indexes
CREATE INDEX idx_file_perms_upload ON storage.file_permissions(upload_id) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_file_perms_user ON storage.file_permissions(user_id) 
    WHERE is_deleted = FALSE AND user_id IS NOT NULL;
CREATE INDEX idx_file_perms_role ON storage.file_permissions(role_id) 
    WHERE is_deleted = FALSE AND role_id IS NOT NULL;
CREATE INDEX idx_file_perms_expires ON storage.file_permissions(expires_at) 
    WHERE is_deleted = FALSE AND expires_at IS NOT NULL;
```

---

### 4. storage_quotas

**Purpose**: User storage quota management

```sql
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

-- Indexes
CREATE UNIQUE INDEX idx_storage_quotas_user ON storage.storage_quotas(user_id) 
    WHERE is_deleted = FALSE;

-- Trigger
CREATE TRIGGER update_storage_quotas_updated_at 
    BEFORE UPDATE ON storage.storage_quotas 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Seed Data: Default quotas
INSERT INTO storage.storage_quotas (user_id, quota_bytes, max_file_size_bytes, max_files_count)
SELECT id, 
    CASE 
        WHEN EXISTS (SELECT 1 FROM public.user_roles ur 
                     JOIN public.roles r ON ur.role_id = r.id 
                     WHERE ur.user_id = users.id AND r.name = 'premium') 
        THEN 10737418240  -- 10GB for premium
        WHEN EXISTS (SELECT 1 FROM public.user_roles ur 
                     JOIN public.roles r ON ur.role_id = r.id 
                     WHERE ur.user_id = users.id AND r.name = 'admin') 
        THEN 107374182400  -- 100GB for admin
        ELSE 1073741824  -- 1GB for regular users
    END,
    104857600,  -- 100MB max file size
    1000  -- Max 1000 files
FROM public.users
WHERE NOT EXISTS (SELECT 1 FROM storage.storage_quotas WHERE user_id = users.id);
```

---

## Notifications System (Notifications Schema)

### 1. notifications

**Purpose**: User notifications

```sql
CREATE TABLE notifications.notifications (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Notification Information
    type VARCHAR(50) NOT NULL,  -- 'info', 'warning', 'error', 'success'
    category VARCHAR(50) NOT NULL,  -- 'system', 'search', 'file', 'account'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Data
    data JSONB DEFAULT '{}'::jsonb,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMPTZ,
    
    -- Delivery
    delivery_status VARCHAR(50) DEFAULT 'pending' NOT NULL,  -- 'pending', 'sent', 'delivered', 'failed'
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

-- Indexes
CREATE INDEX idx_notifications_user ON notifications.notifications(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_notifications_unread ON notifications.notifications(user_id, is_read, created_at DESC) 
    WHERE is_deleted = FALSE AND is_read = FALSE;
CREATE INDEX idx_notifications_type ON notifications.notifications(type) 
    WHERE is_deleted = FALSE;
CREATE INDEX idx_notifications_expires ON notifications.notifications(expires_at) 
    WHERE is_deleted = FALSE AND expires_at IS NOT NULL;

-- Trigger
CREATE TRIGGER update_notifications_updated_at 
    BEFORE UPDATE ON notifications.notifications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 2. notification_preferences

**Purpose**: User notification preferences

```sql
CREATE TABLE notifications.notification_preferences (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Preferences
    category VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,  -- 'email', 'push', 'in_app', 'sms'
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

-- Indexes
CREATE INDEX idx_notif_prefs_user ON notifications.notification_preferences(user_id) 
    WHERE is_deleted = FALSE;

-- Trigger
CREATE TRIGGER update_notification_prefs_updated_at 
    BEFORE UPDATE ON notifications.notification_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 3. notification_templates

**Purpose**: Reusable notification templates

```sql
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
    channels TEXT[] NOT NULL,  -- ['email', 'push']
    
    -- Variables
    variables JSONB DEFAULT '[]'::jsonb,  -- List of template variables
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Indexes
CREATE INDEX idx_notif_templates_name ON notifications.notification_templates(name) 
    WHERE is_deleted = FALSE AND is_active = TRUE;
```

---

## Audit System (Audit Schema)

### 1. audit_events

**Purpose**: Comprehensive audit trail for all actions

```sql
CREATE TABLE audit.audit_events (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Actor
    user_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES auth.sessions(session_id),
    
    -- Action
    action VARCHAR(100) NOT NULL,  -- 'create', 'read', 'update', 'delete', 'login', 'logout'
    resource_type VARCHAR(100) NOT NULL,  -- 'user', 'file', 'search', 'project'
    resource_id BIGINT,
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    changes JSONB,  -- Computed diff
    
    -- Context
    ip_address INET NOT NULL,
    user_agent TEXT,
    location VARCHAR(200),
    
    -- Status
    status VARCHAR(50) DEFAULT 'success' NOT NULL,  -- 'success', 'failure', 'blocked'
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'import')),
    CONSTRAINT valid_status CHECK (status IN ('success', 'failure', 'blocked'))
);

-- Indexes
CREATE INDEX idx_audit_user ON audit.audit_events(user_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit.audit_events(resource_type, resource_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit.audit_events(action, created_at DESC);
CREATE INDEX idx_audit_created ON audit.audit_events(created_at DESC);
CREATE INDEX idx_audit_ip ON audit.audit_events(ip_address, created_at DESC);
CREATE INDEX idx_audit_session ON audit.audit_events(session_id);

-- Partitioning by month
-- CREATE TABLE audit.audit_events_y2024m01 PARTITION OF audit.audit_events
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Retention: 7 years for compliance
CREATE INDEX idx_audit_retention ON audit.audit_events(created_at);
```

---

### 2. data_access_logs

**Purpose**: Track sensitive data access

```sql
CREATE TABLE audit.data_access_logs (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Actor
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES auth.sessions(session_id),
    
    -- Data Access
    data_type VARCHAR(100) NOT NULL,  -- 'user_data', 'search_history', 'files'
    data_id BIGINT NOT NULL,
    access_type VARCHAR(50) NOT NULL,  -- 'read', 'export', 'download'
    
    -- Context
    ip_address INET NOT NULL,
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_access_type CHECK (access_type IN ('read', 'export', 'download', 'update'))
);

-- Indexes
CREATE INDEX idx_data_access_user ON audit.data_access_logs(user_id, created_at DESC);
CREATE INDEX idx_data_access_type ON audit.data_access_logs(data_type, data_id, created_at DESC);
CREATE INDEX idx_data_access_created ON audit.data_access_logs(created_at DESC);
```

---

## Admin System (Admin Schema)

### 1. settings

**Purpose**: Application settings

```sql
CREATE TABLE admin.settings (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Setting Information
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(50) DEFAULT 'string' NOT NULL,  -- 'string', 'integer', 'boolean', 'json'
    
    -- Metadata
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,  -- Can be exposed via API
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_value_type CHECK (value_type IN ('string', 'integer', 'boolean', 'json', 'float'))
);

-- Indexes
CREATE UNIQUE INDEX idx_settings_key ON admin.settings(key);

-- Trigger
CREATE TRIGGER update_settings_updated_at 
    BEFORE UPDATE ON admin.settings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Seed Data
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
```

---

### 2. feature_flags

**Purpose**: Feature flag management

```sql
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
    rollout_percentage INTEGER DEFAULT 100 NOT NULL,  -- 0-100
    target_roles TEXT[],  -- ['admin', 'premium']
    target_users BIGINT[],  -- Specific user IDs
    
    -- Timestamps
    enabled_at TIMESTAMPTZ,
    disabled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_rollout CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100)
);

-- Indexes
CREATE UNIQUE INDEX idx_feature_flags_name ON admin.feature_flags(name);

-- Trigger
CREATE TRIGGER update_feature_flags_updated_at 
    BEFORE UPDATE ON admin.feature_flags 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Seed Data
INSERT INTO admin.feature_flags (name, display_name, description, is_enabled, rollout_percentage) VALUES
    ('vector_search', 'Vector Search', 'Enable vector-based semantic search', TRUE, 100),
    ('ai_synthesis', 'AI Synthesis', 'Enable AI-powered answer synthesis', TRUE, 100),
    ('advanced_analytics', 'Advanced Analytics', 'Enable advanced analytics dashboard', FALSE, 0),
    ('file_versioning', 'File Versioning', 'Enable file versioning', TRUE, 100),
    ('multi_tenant', 'Multi-Tenant', 'Enable multi-tenant support', FALSE, 0),
    ('api_access', 'API Access', 'Enable API access for users', TRUE, 100);
```

---

### 3. system_config

**Purpose**: System configuration

```sql
CREATE TABLE admin.system_config (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Configuration
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    
    -- Metadata
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE NOT NULL,  -- Encrypt in transit
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Indexes
CREATE UNIQUE INDEX idx_system_config_key ON admin.system_config(config_key) 
    WHERE is_deleted = FALSE;

-- Trigger
CREATE TRIGGER update_system_config_updated_at 
    BEFORE UPDATE ON admin.system_config 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 4. maintenance_windows

**Purpose**: Scheduled maintenance windows

```sql
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
    status VARCHAR(50) DEFAULT 'scheduled' NOT NULL,  -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    
    -- Impact
    affects_reads BOOLEAN DEFAULT TRUE NOT NULL,
    affects_writes BOOLEAN DEFAULT TRUE NOT NULL,
    affected_services TEXT[],  -- ['api', 'search', 'storage']
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    CONSTRAINT valid_dates CHECK (ends_at > starts_at)
);

-- Indexes
CREATE INDEX idx_maintenance_windows_dates ON admin.maintenance_windows(starts_at, ends_at) 
    WHERE status IN ('scheduled', 'in_progress');
```

---

## Utility Functions

### Updated At Trigger Function

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Soft Delete Function

```sql
CREATE OR REPLACE FUNCTION soft_delete()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_deleted = TRUE;
    NEW.deleted_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Cleanup Expired Tokens Function

```sql
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

-- Schedule cleanup (run daily via cron or pg_cron)
-- SELECT cron.schedule('cleanup-expired-tokens', '0 0 * * *', 'SELECT cleanup_expired_tokens();');
```

---

## Performance Optimization

### Indexes Summary

```sql
-- Composite indexes for common queries
CREATE INDEX idx_users_email_active ON public.users(email, is_active) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_searches_user_created ON search.searches(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_events_user_created ON analytics.events(user_id, created_at DESC) 
    WHERE is_deleted = FALSE;

-- Covering indexes for frequent queries
CREATE INDEX idx_users_email_covering ON public.users(email) 
    INCLUDE (id, is_active, email_verified) 
    WHERE is_deleted = FALSE;

-- Partial indexes for filtered queries
CREATE INDEX idx_active_sessions ON auth.sessions(session_id) 
    WHERE is_deleted = FALSE AND is_active = TRUE AND expires_at > NOW();

-- Expression indexes
CREATE INDEX idx_users_email_lower ON public.users(LOWER(email)) 
    WHERE is_deleted = FALSE;
```

### Query Optimization

```sql
-- Materialized view for search analytics
CREATE MATERIALIZED VIEW search.search_analytics_daily AS
SELECT 
    DATE_TRUNC('day', created_at) AS date,
    COUNT(*) AS total_searches,
    COUNT(DISTINCT user_id) AS unique_users,
    AVG(execution_time_ms) AS avg_execution_time,
    COUNT(CASE WHEN cache_hit THEN 1 END) AS cache_hits,
    COUNT(CASE WHEN cache_hit THEN 1 END)::FLOAT / COUNT(*) * 100 AS cache_hit_rate
FROM search.searches
WHERE is_deleted = FALSE
GROUP BY DATE_TRUNC('day', created_at);

-- Index on materialized view
CREATE UNIQUE INDEX idx_search_analytics_daily_date ON search.search_analytics_daily(date);

-- Refresh strategy (run daily)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY search.search_analytics_daily;

-- Materialized view for user activity
CREATE MATERIALIZED VIEW analytics.user_activity_summary AS
SELECT 
    u.id AS user_id,
    u.email,
    COUNT(DISTINCT s.id) AS total_searches,
    COUNT(DISTINCT e.id) AS total_events,
    MAX(s.created_at) AS last_search,
    MAX(e.created_at) AS last_activity
FROM public.users u
LEFT JOIN search.searches s ON s.user_id = u.id AND s.is_deleted = FALSE
LEFT JOIN analytics.events e ON e.user_id = u.id AND e.is_deleted = FALSE
WHERE u.is_deleted = FALSE
GROUP BY u.id, u.email;

CREATE UNIQUE INDEX idx_user_activity_summary_user ON analytics.user_activity_summary(user_id);
```

### Partitioning Strategy

```sql
-- Partition large tables by month
-- Example for analytics.events
CREATE TABLE analytics.events_y2024m01 PARTITION OF analytics.events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE analytics.events_y2024m02 PARTITION OF analytics.events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Add indexes to partitions
CREATE INDEX idx_events_y2024m01_user ON analytics.events_y2024m01(user_id, created_at DESC);
CREATE INDEX idx_events_y2024m01_created ON analytics.events_y2024m01(created_at DESC);

-- Auto-partition creation function
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    start_date := DATE_TRUNC('month', NOW())::DATE;
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'events_y' || EXTRACT(year FROM start_date) || 'm' || LPAD(EXTRACT(month FROM start_date)::TEXT, 2, '0');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS analytics.%I PARTITION OF analytics.events FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_user ON analytics.%I(user_id, created_at DESC)',
                   partition_name, partition_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_created ON analytics.%I(created_at DESC)',
                   partition_name, partition_name);
END;
$$ LANGUAGE plpgsql;
```

### Connection Pooling

```sql
-- PgBouncer configuration (in pgbouncer.ini)
-- [databases]
-- nebula_db = host=localhost port=5432 dbname=nebula_db
--
-- [pgbouncer]
-- pool_mode = transaction
-- max_client_conn = 1000
-- default_pool_size = 25
-- min_pool_size = 10
-- reserve_pool_size = 5
-- max_db_connections = 50
-- max_user_connections = 25
-- server_lifetime = 3600
-- server_idle_timeout = 600
```

### Caching Strategy

```sql
-- Redis cache keys structure:
-- user:{user_id}:profile
-- search:{query_hash}:results
-- metrics:daily:{date}
-- session:{session_id}

-- Cache invalidation triggers
CREATE OR REPLACE FUNCTION invalidate_user_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Invalidate user cache
    PERFORM pg_notify('cache_invalidation', json_build_object(
        'key', 'user:' || NEW.id || ':profile',
        'action', 'delete'
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER invalidate_user_cache_trigger
    AFTER UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION invalidate_user_cache();
```

---

## Reliability & Backup

### Backup Strategy

```sql
-- Full backup (daily)
-- pg_dump -Fc -U nebula_admin -d nebula_db -f /backups/nebula_db_daily.dump

-- Incremental backup (hourly)
-- pg_basebackup -D /backups/incremental -Ft -z -P -U nebula_replicator

-- WAL archiving (continuous)
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'cp %p /archive/%f'
-- archive_timeout = 300

-- Point-in-time recovery (PITR)
-- recovery_target_time = '2024-01-15 14:30:00'
-- recovery_target_action = 'promote'
```

### Replication Setup

```sql
-- Primary server (postgresql.conf)
-- wal_level = replica
-- max_wal_senders = 10
-- wal_keep_size = 1GB
-- hot_standby = on

-- Create replication user
CREATE ROLE nebula_replicator WITH REPLICATION LOGIN PASSWORD 'secure_password';

-- Standby server (postgresql.conf)
-- primary_conninfo = 'host=primary_host port=5432 user=nebula_replicator password=secure_password'
-- hot_standby = on

-- Monitor replication lag
SELECT 
    client_addr,
    state,
    sent_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
FROM pg_stat_replication;
```

### Disaster Recovery

```sql
-- 1. Automated daily backups
-- 2. WAL archiving for point-in-time recovery
-- 3. Streaming replication to standby server
-- 4. Cross-region backup storage (S3, GCS)
-- 5. Regular restore testing (monthly)
-- 6. RPO: 5 minutes (WAL archiving)
-- 7. RTO: 1 hour (standby promotion)

-- Recovery procedures documented in:
-- docs/DISASTER_RECOVERY.md
```

---

## Security

### Row-Level Security (RLS)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE search.searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage.uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.events ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY user_data_policy ON public.users
    FOR ALL
    TO application_role
    USING (id = current_setting('app.current_user_id')::BIGINT);

-- Users can only see their own searches
CREATE POLICY user_searches_policy ON search.searches
    FOR ALL
    TO application_role
    USING (user_id = current_setting('app.current_user_id')::BIGINT);

-- Users can only see their own uploads
CREATE POLICY user_uploads_policy ON storage.uploads
    FOR ALL
    TO application_role
    USING (user_id = current_setting('app.current_user_id')::BIGINT);

-- Admin can see all data
CREATE POLICY admin_all_policy ON public.users
    FOR ALL
    TO admin_role
    USING (true);
```

### Encrypted Fields

```sql
-- Use pgcrypto for sensitive data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example: Encrypted email (if required by compliance)
-- ALTER TABLE public.users ADD COLUMN email_encrypted BYTEA;
-- UPDATE public.users SET email_encrypted = pgp_sym_encrypt(email, 'encryption_key');

-- Decrypt: pgp_sym_decrypt(email_encrypted, 'encryption_key')
```

### Audit Trail

```sql
-- Audit trigger for critical tables
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.audit_events (
        user_id,
        session_id,
        action,
        resource_type,
        resource_id,
        old_values,
        new_values,
        ip_address,
        user_agent,
        status
    ) VALUES (
        current_setting('app.current_user_id')::BIGINT,
        current_setting('app.current_session_id')::UUID,
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN row_to_json(NEW) ELSE NULL END,
        current_setting('app.current_ip_address')::INET,
        current_setting('app.current_user_agent'),
        'success'
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

### SQL Injection Protection

```sql
-- Use parameterized queries in application code
-- Example (Python with asyncpg):
-- await conn.execute(
--     "SELECT * FROM users WHERE email = $1",
--     user_email
-- )

-- Never use string concatenation:
-- BAD: f"SELECT * FROM users WHERE email = '{user_email}'"
-- GOOD: "SELECT * FROM users WHERE email = $1", user_email

-- Input validation at application layer
-- Use Pydantic schemas for request validation
```

---

## Migrations

### Migration Order

```sql
-- 001_initial_schema.sql
--   - Create schemas
--   - Create utility functions
--   - Create all tables
--   - Create indexes
--   - Create triggers
--   - Insert seed data

-- 002_add_user_preferences.sql
--   - Add user preference columns

-- 003_add_file_versioning.sql
--   - Add file_versions table
--   - Add file_permissions table

-- 004_add_analytics.sql
--   - Add analytics schema
--   - Add events table
--   - Add metrics table

-- 005_add_notifications.sql
--   - Add notifications schema
--   - Add notification tables

-- 006_add_audit.sql
--   - Add audit schema
--   - Add audit triggers

-- 007_add_admin.sql
--   - Add admin schema
--   - Add settings table

-- 008_enable_rls.sql
--   - Enable RLS on sensitive tables
--   - Create RLS policies

-- 009_add_partitioning.sql
--   - Add partitioning for large tables

-- 010_add_materialized_views.sql
--   - Add materialized views for analytics
```

### Migration Tool Configuration

```yaml
# alembic.ini or custom migration tool
[alembic]
script_location = database/migrations
sqlalchemy.url = postgresql://nebula_admin:password@localhost:5432/nebula_db

[post_write_hooks]
hooks = black, isort
```

---

## Naming Conventions

### Tables
- **Format**: `snake_case`
- **Pattern**: `{schema}.{table_name}`
- **Examples**: `auth.refresh_tokens`, `search.searches`, `storage.uploads`

### Columns
- **Format**: `snake_case`
- **Pattern**: `{descriptive_name}`
- **Examples**: `user_id`, `created_at`, `is_deleted`, `file_size_bytes`

### Indexes
- **Format**: `idx_{table}_{columns}`
- **Pattern**: `idx_{table_name}_{column_names}`
- **Examples**: `idx_users_email`, `idx_searches_user_created`

### Constraints
- **Format**: `{type}_{table}_{columns}`
- **Examples**: `valid_email`, `unique_user_email`, `fk_users_projects`

### Functions
- **Format**: `snake_case`
- **Pattern**: `{action}_{object}`
- **Examples**: `update_updated_at_column()`, `cleanup_expired_tokens()`

---

## Folder Structure

```
database/
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_user_preferences.sql
│   ├── 003_add_file_versioning.sql
│   ├── 004_add_analytics.sql
│   ├── 005_add_notifications.sql
│   ├── 006_add_audit.sql
│   ├── 007_add_admin.sql
│   ├── 008_enable_rls.sql
│   ├── 009_add_partitioning.sql
│   └── 010_add_materialized_views.sql
├── seeds/
│   ├── 001_roles.sql
│   ├── 002_permissions.sql
│   ├── 003_settings.sql
│   └── 004_feature_flags.sql
├── backups/
│   ├── daily/
│   ├── weekly/
│   └── monthly/
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   ├── migrate.sh
│   └── cleanup.sh
├── schema/
│   ├── public.sql
│   ├── auth.sql
│   ├── search.sql
│   ├── analytics.sql
│   ├── notifications.sql
│   ├── storage.sql
│   ├── audit.sql
│   └── admin.sql
└── README.md
```

---

## Implementation Roadmap

### Phase 1: Core Schema (Week 1)
- [x] Design database architecture
- [ ] Create initial schema (public, auth)
- [ ] Implement users, profiles, roles, permissions
- [ ] Set up authentication tables
- [ ] Create indexes and constraints
- [ ] Write seed data

### Phase 2: Search & Analytics (Week 2)
- [ ] Implement search schema
- [ ] Create search tables and indexes
- [ ] Implement analytics schema
- [ ] Set up event tracking
- [ ] Create materialized views

### Phase 3: Storage & Notifications (Week 3)
- [ ] Implement storage schema
- [ ] Create file management tables
- [ ] Implement notifications schema
- [ ] Set up notification preferences

### Phase 4: Audit & Admin (Week 4)
- [ ] Implement audit schema
- [ ] Create audit triggers
- [ ] Implement admin schema
- [ ] Set up feature flags
- [ ] Configure settings

### Phase 5: Performance & Security (Week 5)
- [ ] Add partitioning
- [ ] Optimize indexes
- [ ] Implement RLS
- [ ] Set up connection pooling
- [ ] Configure caching

### Phase 6: Reliability (Week 6)
- [ ] Set up backups
- [ ] Configure replication
- [ ] Test disaster recovery
- [ ] Document procedures
- [ ] Train team

### Phase 7: Testing & Deployment (Week 7)
- [ ] Load testing
- [ ] Security audit
- [ ] Performance testing
- [ ] Deploy to staging
- [ ] Deploy to production

---

## Scaling Plan

### Horizontal Scaling
- **Read Replicas**: 2-3 read replicas for read-heavy workloads
- **Connection Pooling**: PgBouncer for connection management
- **Caching**: Redis for frequent queries
- **CDN**: For static assets and file downloads

### Vertical Scaling
- **CPU**: 8+ cores for complex queries
- **RAM**: 32GB+ for caching and sorting
- **Storage**: SSD/NVMe for I/O performance
- **Network**: 10Gbps for replication

### Data Partitioning
- **Time-based**: Partition events, logs by month
- **Hash-based**: Distribute users across shards (future)
- **Range-based**: Partition by user ID ranges (future)

### Monitoring
- **Metrics**: Query performance, connection count, cache hit rate
- **Alerts**: Slow queries, high CPU, disk usage
- **Logging**: Query logs, error logs, audit logs

---

## Conclusion

This database architecture provides:

1. **Modularity**: Separate schemas for distinct domains
2. **Scalability**: Partitioning, indexing, connection pooling
3. **Security**: RBAC, RLS, encryption, audit trails
4. **Performance**: Query optimization, caching, materialized views
5. **Reliability**: Backups, replication, disaster recovery
6. **Maintainability**: Clear naming, migrations, documentation

The architecture is production-ready and can scale to millions of users with proper infrastructure.

---

## Next Steps

1. Review this architecture with the team
2. Create migration files
3. Set up development database
4. Implement ORM models (SQLAlchemy)
5. Write database tests
6. Deploy to staging environment
7. Load test and optimize
8. Deploy to production

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: Database Architecture Team  
**Status**: Production-Ready