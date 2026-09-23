"""Role-Based Access Control (RBAC) service.

Provides a static, role-hierarchy-aware permission system that
test_rbac.py exercises exhaustively.  All methods are class-level
so no instantiation is required.
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from app.services.auth import get_current_user_token_payload

# ---------------------------------------------------------------------------
# Role hierarchy — higher number = more privileged
# ---------------------------------------------------------------------------

_ROLE_LEVELS: dict[str, int] = {
    "super_admin": 100,
    "admin": 80,
    "moderator": 50,
    "user": 10,
    "guest": 1,
}

# Ordered from most to least privileged
_ROLE_ORDER = ["super_admin", "admin", "moderator", "user", "guest"]

# ---------------------------------------------------------------------------
# Permissions granted to each role (non-inherited — expanded at call time)
# ---------------------------------------------------------------------------

_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": [
        "users.admin",
        "admin.access",
        "analytics.view",
        "analytics.manage",
        "searches.create",
        "searches.read",
        "searches.delete",
        "searches.manage",
        "files.upload",
        "files.read",
        "files.delete",
        "files.manage",
        "users.read",
        "users.write",
        "users.delete",
        "webhooks.read",
        "webhooks.write",
        "crawler.manage",
        "indexing.manage",
    ],
    "admin": [
        "analytics.view",
        "analytics.manage",
        "searches.create",
        "searches.read",
        "searches.delete",
        "searches.manage",
        "files.upload",
        "files.read",
        "files.delete",
        "files.manage",
        "users.read",
        "users.write",
    ],
    "moderator": [
        "searches.read",
        "searches.delete",
        "searches.manage",
        "files.read",
        "files.delete",
        "files.manage",
    ],
    "user": [
        "searches.create",
        "searches.read",
        "searches.delete",
        "files.upload",
        "files.read",
        "files.delete",
    ],
    "guest": [
        "searches.create",
    ],
}

# ---------------------------------------------------------------------------
# Resource → actions matrix
# Used by can_access_resource()
# ---------------------------------------------------------------------------

# Format: { role: { resource: {allowed_actions} } }
# super_admin has wildcard access handled separately.
_RESOURCE_POLICY: dict[str, dict[str, set[str]]] = {
    "admin": {
        "searches": {"create", "read", "delete", "manage"},
        "files":    {"upload", "read", "delete", "manage"},
        "users":    {"read", "write"},
        "analytics": {"view", "manage"},
    },
    "moderator": {
        "searches": {"read", "delete", "manage"},
        "files":    {"read", "delete", "manage"},
    },
    "user": {
        "searches": {"create", "read", "delete"},
        "files":    {"upload", "read", "delete"},
    },
    "guest": {
        "searches": {"create"},
    },
}


class RBACService:
    """Static RBAC utility — all methods are classmethods."""

    # ── Role hierarchy ──────────────────────────────────────────────────────

    @classmethod
    def get_role_level(cls, role: str) -> int:
        """Return the numeric privilege level of *role* (0 for unknown roles)."""
        return _ROLE_LEVELS.get(role, 0)

    @classmethod
    def has_role_hierarchy(cls, role: str, required_role: str) -> bool:
        """Return True if *role* is at least as privileged as *required_role*."""
        return cls.get_role_level(role) >= cls.get_role_level(required_role)

    @classmethod
    def get_inherited_roles(cls, role: str) -> list[str]:
        """Return all roles that *role* inherits (roles with strictly lower privilege)."""
        level = _ROLE_LEVELS.get(role)
        if level is None:
            return []
        return [r for r, lvl in _ROLE_LEVELS.items() if lvl < level]

    # ── Resource access ─────────────────────────────────────────────────────

    @classmethod
    def can_access_resource(cls, role: str, resource: str, action: str) -> bool:
        """Return True if *role* may perform *action* on *resource*."""
        # super_admin has unrestricted access
        if role == "super_admin":
            return True

        policy = _RESOURCE_POLICY.get(role, {})
        allowed_actions = policy.get(resource, set())
        return action in allowed_actions

    # ── Permission strings ──────────────────────────────────────────────────

    @classmethod
    def get_user_permissions(
        cls,
        role: str,
        additional_permissions: list[str] | None = None,
    ) -> list[str]:
        """Return a deduplicated list of permission strings for *role*.

        Optionally augments with *additional_permissions* (e.g. per-user grants).
        """
        perms: list[str] = list(_ROLE_PERMISSIONS.get(role, []))
        if additional_permissions:
            for p in additional_permissions:
                if p not in perms:
                    perms.append(p)
        return perms

    @classmethod
    def check_permission(
        cls,
        role: str,
        permission: str,
        additional_permissions: list[str] | None = None,
    ) -> bool:
        """Return True if *role* (plus any explicit grants) has *permission*."""
        # super_admin always passes
        if role == "super_admin":
            return True
        user_perms = cls.get_user_permissions(role, additional_permissions)
        return permission in user_perms

    # ── FastAPI dependency factories ────────────────────────────────────────

    @staticmethod
    def require_any_permission(permissions: list[str]):
        """Dependency factory: passes if user has at least one of *permissions*."""
        async def _checker(request: Request):
            payload = await get_current_user_token_payload(request)
            role = payload.get("role", "guest")
            if any(RBACService.check_permission(role, p) for p in permissions):
                return payload
            raise HTTPException(
                status_code=403,
                detail=f"One of these permissions required: {permissions}",
            )
        return _checker

    @staticmethod
    def require_permission(permission: str):
        """Dependency factory: passes if user has *permission* (alias for require_any_permission)."""
        return RBACService.require_any_permission([permission])

    @staticmethod
    def require_all_permissions(permissions: list[str]):
        """Dependency factory: passes only if user has all of *permissions*."""
        async def _checker(request: Request):
            payload = await get_current_user_token_payload(request)
            role = payload.get("role", "guest")
            missing = [p for p in permissions if not RBACService.check_permission(role, p)]
            if missing:
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permissions: {missing}",
                )
            return payload
        return _checker

    @staticmethod
    def require_role(required_role: str):
        """Dependency factory: passes if user's role is at least *required_role*."""
        async def _checker(request: Request):
            payload = await get_current_user_token_payload(request)
            role = payload.get("role", "guest")
            if not RBACService.has_role_hierarchy(role, required_role):
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{required_role}' or higher required",
                )
            return payload
        return _checker


# ---------------------------------------------------------------------------
# Convenience dependency instances used directly in route decorators
# ---------------------------------------------------------------------------

require_admin = RBACService.require_role("admin")
require_user_management = RBACService.require_any_permission(["users.read", "users.write"])
require_file_management = RBACService.require_any_permission(["files.manage"])
require_analytics_access = RBACService.require_any_permission(["analytics.view"])
