-- ============================================
-- Seed Data: Roles
-- ============================================
-- This file seeds the RBAC roles

INSERT INTO public.roles (name, display_name, description, level, is_system) VALUES
    ('super_admin', 'Super Administrator', 'Full system access with all permissions', 100, TRUE),
    ('admin', 'Administrator', 'Administrative access with most permissions', 80, TRUE),
    ('moderator', 'Moderator', 'Content moderation and user management', 50, TRUE),
    ('user', 'User', 'Standard user with basic permissions', 10, TRUE),
    ('guest', 'Guest', 'Limited access for anonymous users', 1, TRUE)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- Seed Complete
-- ============================================

SELECT 'Roles seeded successfully' AS status;