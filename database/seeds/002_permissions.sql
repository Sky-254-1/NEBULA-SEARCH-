-- ============================================
-- Seed Data: Permissions
-- ============================================
-- This file seeds granular permissions for all resources

-- User Management Permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('users.create', 'Create Users', 'Create new user accounts', 'users', 'create', TRUE),
    ('users.read', 'Read Users', 'View user profiles and information', 'users', 'read', TRUE),
    ('users.update', 'Update Users', 'Edit user profiles and settings', 'users', 'update', TRUE),
    ('users.delete', 'Delete Users', 'Delete user accounts', 'users', 'delete', TRUE),
    ('users.admin', 'Admin Users', 'Full user management including role assignment', 'users', 'admin', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Search Permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('searches.create', 'Create Searches', 'Perform web and vector searches', 'searches', 'create', TRUE),
    ('searches.read', 'Read Searches', 'View search history and results', 'searches', 'read', TRUE),
    ('searches.update', 'Update Searches', 'Modify search history', 'searches', 'update', TRUE),
    ('searches.delete', 'Delete Searches', 'Delete search history', 'searches', 'delete', TRUE),
    ('searches.manage', 'Manage Searches', 'Full search management', 'searches', 'manage', TRUE)
ON CONFLICT (name) DO NOTHING;

-- File Management Permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('files.upload', 'Upload Files', 'Upload files to storage', 'files', 'create', TRUE),
    ('files.read', 'Read Files', 'View and download files', 'files', 'read', TRUE),
    ('files.update', 'Update Files', 'Modify file metadata', 'files', 'update', TRUE),
    ('files.delete', 'Delete Files', 'Delete files from storage', 'files', 'delete', TRUE),
    ('files.manage', 'Manage Files', 'Full file management including permissions', 'files', 'manage', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Analytics Permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('analytics.view', 'View Analytics', 'View analytics dashboards and reports', 'analytics', 'read', TRUE),
    ('analytics.export', 'Export Analytics', 'Export analytics data', 'analytics', 'export', TRUE),
    ('analytics.manage', 'Manage Analytics', 'Configure analytics settings', 'analytics', 'manage', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Project Permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('projects.create', 'Create Projects', 'Create new projects', 'projects', 'create', TRUE),
    ('projects.read', 'Read Projects', 'View project details', 'projects', 'read', TRUE),
    ('projects.update', 'Update Projects', 'Edit project settings', 'projects', 'update', TRUE),
    ('projects.delete', 'Delete Projects', 'Delete projects', 'projects', 'delete', TRUE),
    ('projects.manage', 'Manage Projects', 'Full project management', 'projects', 'manage', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Notification Permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('notifications.view', 'View Notifications', 'View notifications', 'notifications', 'read', TRUE),
    ('notifications.manage', 'Manage Notifications', 'Manage notification settings', 'notifications', 'manage', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Admin Permissions
INSERT INTO public.permissions (name, display_name, description, resource, action, is_system) VALUES
    ('admin.access', 'Admin Access', 'Access admin panel', 'admin', 'admin', TRUE),
    ('admin.settings', 'Manage Settings', 'Modify application settings', 'admin', 'update', TRUE),
    ('admin.feature_flags', 'Manage Feature Flags', 'Toggle feature flags', 'admin', 'update', TRUE),
    ('admin.system', 'System Administration', 'Full system administration', 'admin', 'admin', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- Seed Role-Permission Mappings
-- ============================================

-- Super Admin gets all permissions
INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT 
    r.id AS role_id,
    p.id AS permission_id,
    NULL AS granted_by,
    NOW() AS granted_at
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'super_admin'
ON CONFLICT (role_id, permission_id, is_deleted) DO NOTHING;

-- Admin gets most permissions (except users.admin and admin.system)
INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT 
    r.id AS role_id,
    p.id AS permission_id,
    NULL AS granted_by,
    NOW() AS granted_at
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'admin'
    AND p.name NOT IN ('users.admin', 'admin.system')
ON CONFLICT (role_id, permission_id, is_deleted) DO NOTHING;

-- Moderator gets search and file permissions
INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT 
    r.id AS role_id,
    p.id AS permission_id,
    NULL AS granted_by,
    NOW() AS granted_at
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'moderator'
    AND p.resource IN ('searches', 'files', 'users.read')
ON CONFLICT (role_id, permission_id, is_deleted) DO NOTHING;

-- Regular User gets basic permissions
INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT 
    r.id AS role_id,
    p.id AS permission_id,
    NULL AS granted_by,
    NOW() AS granted_at
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'user'
    AND p.name IN (
        'searches.create',
        'searches.read',
        'searches.delete',
        'files.upload',
        'files.read',
        'files.delete',
        'projects.create',
        'projects.read',
        'projects.update',
        'projects.delete',
        'notifications.view'
    )
ON CONFLICT (role_id, permission_id, is_deleted) DO NOTHING;

-- Guest gets minimal permissions
INSERT INTO public.role_permissions (role_id, permission_id, granted_by, granted_at)
SELECT 
    r.id AS role_id,
    p.id AS permission_id,
    NULL AS granted_by,
    NOW() AS granted_at
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'guest'
    AND p.name IN (
        'searches.create',
        'searches.read'
    )
ON CONFLICT (role_id, permission_id, is_deleted) DO NOTHING;

-- ============================================
-- Seed Complete
-- ============================================

SELECT 'Permissions and role mappings seeded successfully' AS status;