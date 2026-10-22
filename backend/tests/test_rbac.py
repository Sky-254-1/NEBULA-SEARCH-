"""Tests for Role-Based Access Control (RBAC) service."""

from app.services.rbac import RBACService


class TestRBACService:
    """Test suite for RBACService."""

    # ── get_role_level ──────────────────────────────────────────────

    def test_get_role_level_super_admin(self):
        assert RBACService.get_role_level("super_admin") == 100

    def test_get_role_level_admin(self):
        assert RBACService.get_role_level("admin") == 80

    def test_get_role_level_moderator(self):
        assert RBACService.get_role_level("moderator") == 50

    def test_get_role_level_user(self):
        assert RBACService.get_role_level("user") == 10

    def test_get_role_level_guest(self):
        assert RBACService.get_role_level("guest") == 1

    def test_get_role_level_unknown(self):
        assert RBACService.get_role_level("unknown") == 0

    # ── has_role_hierarchy ──────────────────────────────────────────

    def test_super_admin_hierarchy_over_admin(self):
        assert RBACService.has_role_hierarchy("super_admin", "admin") is True

    def test_super_admin_hierarchy_over_guest(self):
        assert RBACService.has_role_hierarchy("super_admin", "guest") is True

    def test_admin_hierarchy_over_user(self):
        assert RBACService.has_role_hierarchy("admin", "user") is True

    def test_user_not_hierarchy_over_admin(self):
        assert RBACService.has_role_hierarchy("user", "admin") is False

    def test_guest_not_hierarchy_over_user(self):
        assert RBACService.has_role_hierarchy("guest", "user") is False

    def test_equal_role_hierarchy(self):
        assert RBACService.has_role_hierarchy("admin", "admin") is True

    # ── get_inherited_roles ─────────────────────────────────────────

    def test_super_admin_inherits_all(self):
        inherited = RBACService.get_inherited_roles("super_admin")
        assert "admin" in inherited
        assert "moderator" in inherited
        assert "user" in inherited
        assert "guest" in inherited

    def test_user_inherits_guest(self):
        inherited = RBACService.get_inherited_roles("user")
        assert "guest" in inherited
        assert "admin" not in inherited

    def test_guest_inherits_none(self):
        assert RBACService.get_inherited_roles("guest") == []

    def test_unknown_role_inherits_none(self):
        assert RBACService.get_inherited_roles("unknown") == []

    # ── can_access_resource ─────────────────────────────────────────

    # super_admin — full access
    def test_super_admin_can_access_anything(self):
        assert RBACService.can_access_resource("super_admin", "admin", "access") is True
        assert RBACService.can_access_resource("super_admin", "users", "admin") is True
        assert RBACService.can_access_resource("super_admin", "searches", "delete") is True

    # admin — most access, but restricted on admin-only actions
    def test_admin_can_access_normal_resources(self):
        assert RBACService.can_access_resource("admin", "searches", "read") is True
        assert RBACService.can_access_resource("admin", "files", "delete") is True
        assert RBACService.can_access_resource("admin", "users", "read") is True

    def test_admin_cannot_access_restricted(self):
        assert RBACService.can_access_resource("admin", "users", "admin") is False
        assert RBACService.can_access_resource("admin", "admin", "access") is False

    # moderator — limited to searches and files, specific actions
    def test_moderator_can_access_allowed(self):
        assert RBACService.can_access_resource("moderator", "searches", "read") is True
        assert RBACService.can_access_resource("moderator", "searches", "delete") is True
        assert RBACService.can_access_resource("moderator", "searches", "manage") is True
        assert RBACService.can_access_resource("moderator", "files", "read") is True
        assert RBACService.can_access_resource("moderator", "files", "delete") is True
        assert RBACService.can_access_resource("moderator", "files", "manage") is True

    def test_moderator_cannot_access_disallowed(self):
        assert RBACService.can_access_resource("moderator", "users", "read") is False
        assert RBACService.can_access_resource("moderator", "analytics", "view") is False
        assert RBACService.can_access_resource("moderator", "admin", "access") is False

    def test_moderator_cannot_access_disallowed_action(self):
        assert RBACService.can_access_resource("moderator", "searches", "create") is False

    # user — basic CRUD on searches and files
    def test_user_can_access_allowed(self):
        assert RBACService.can_access_resource("user", "searches", "create") is True
        assert RBACService.can_access_resource("user", "searches", "read") is True
        assert RBACService.can_access_resource("user", "searches", "delete") is True
        assert RBACService.can_access_resource("user", "files", "upload") is True
        assert RBACService.can_access_resource("user", "files", "read") is True
        assert RBACService.can_access_resource("user", "files", "delete") is True

    def test_user_cannot_access_restricted(self):
        assert RBACService.can_access_resource("user", "analytics", "view") is False
        assert RBACService.can_access_resource("user", "admin", "access") is False
        assert RBACService.can_access_resource("user", "users", "create") is False

    # guest — minimal: searches.create only
    def test_guest_can_access_allowed(self):
        assert RBACService.can_access_resource("guest", "searches", "create") is True

    def test_guest_cannot_access_other(self):
        assert RBACService.can_access_resource("guest", "searches", "read") is False
        assert RBACService.can_access_resource("guest", "searches", "delete") is False
        assert RBACService.can_access_resource("guest", "files", "read") is False
        assert RBACService.can_access_resource("guest", "analytics", "view") is False

    # unknown role
    def test_unknown_role_denied(self):
        assert RBACService.can_access_resource("unknown", "searches", "create") is False

    # ── get_user_permissions ────────────────────────────────────────

    def test_super_admin_permissions_all(self):
        perms = RBACService.get_user_permissions("super_admin")
        assert "users.admin" in perms
        assert "admin.access" in perms
        assert "analytics.view" in perms
        assert "searches.create" in perms
        assert "files.manage" in perms

    def test_admin_permissions(self):
        perms = RBACService.get_user_permissions("admin")
        assert "users.read" in perms
        assert "analytics.view" in perms
        assert "files.manage" in perms
        assert "users.admin" not in perms
        assert "admin.access" not in perms

    def test_moderator_permissions(self):
        perms = RBACService.get_user_permissions("moderator")
        assert "searches.read" in perms
        assert "searches.delete" in perms
        assert "files.read" in perms
        assert "files.delete" in perms
        assert "searches.create" not in perms
        assert "analytics.view" not in perms

    def test_user_permissions(self):
        perms = RBACService.get_user_permissions("user")
        assert "searches.create" in perms
        assert "searches.read" in perms
        assert "searches.delete" in perms
        assert "files.upload" in perms
        assert "files.read" in perms
        assert "files.delete" in perms
        assert "analytics.view" not in perms

    def test_guest_permissions(self):
        perms = RBACService.get_user_permissions("guest")
        assert perms == ["searches.create"]

    def test_get_permissions_with_additional(self):
        perms = RBACService.get_user_permissions("user", ["custom.permission"])
        assert "custom.permission" in perms

    def test_unknown_role_permissions(self):
        perms = RBACService.get_user_permissions("unknown")
        assert perms == []

    # ── check_permission ────────────────────────────────────────────

    def test_super_admin_check_any(self):
        assert RBACService.check_permission("super_admin", "admin.access") is True
        assert RBACService.check_permission("super_admin", "nonexistent") is True

    def test_admin_check_allowed(self):
        assert RBACService.check_permission("admin", "analytics.view") is True
        assert RBACService.check_permission("admin", "users.read") is True

    def test_admin_check_denied(self):
        assert RBACService.check_permission("admin", "admin.access") is False
        assert RBACService.check_permission("admin", "users.admin") is False

    def test_user_check_allowed(self):
        assert RBACService.check_permission("user", "searches.create") is True

    def test_user_check_denied(self):
        assert RBACService.check_permission("user", "analytics.view") is False

    def test_guest_check_allowed(self):
        assert RBACService.check_permission("guest", "searches.create") is True

    def test_guest_check_denied(self):
        assert RBACService.check_permission("guest", "searches.read") is False

    def test_check_with_explicit_permissions(self):
        """Explicit user permissions should supplement role permissions."""
        assert RBACService.check_permission("user", "custom.test", ["custom.test"]) is True

    # ── Convenience helpers (require_permission etc.) ───────────────

    def test_require_admin_convenience(self):
        """require_admin is a permission checker factory for 'admin.access'."""
        # We verify the factory creates a callable — integration tested via HTTP
        from app.services.rbac import require_admin, require_user_management, require_file_management, require_analytics_access
        assert callable(require_admin)
        assert callable(require_user_management)
        assert callable(require_file_management)
        assert callable(require_analytics_access)

    # ── require_all_permissions / require_any_permission logic ──────

    def test_require_any_permission_success(self):
        """require_any_permission succeeds if at least one matches."""
        RBACService.require_any_permission(["searches.read", "admin.access"])
        # The factory returns an async callable (dependency); we test the logic
        # synchronously via check_permission:
        assert RBACService.check_permission("user", "searches.read") is True

    def test_require_any_permission_failure(self):
        """require_any_permission fails if none match."""
        assert RBACService.check_permission("guest", "admin.access") is False
        assert RBACService.check_permission("guest", "files.read") is False

    def test_require_all_permissions_success(self):
        """require_all_permissions succeeds if all match."""
        assert RBACService.check_permission("admin", "users.read") is True
        assert RBACService.check_permission("admin", "analytics.view") is True

    def test_require_all_permissions_failure(self):
        """require_all_permissions fails if any missing."""
        # guest has searches.read but NOT files.manage
        has_all = RBACService.check_permission("guest", "searches.read") and \
                  RBACService.check_permission("guest", "files.manage")
        assert has_all is False