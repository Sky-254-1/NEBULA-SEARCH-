"""Behavioral coverage expansion for low-coverage services.

Uses @pytest.mark.asyncio for all async tests (compatible with conftest.py's
pytest-asyncio mode).  Mocks DNS, network, and DB dependencies so tests are
deterministic and Windows-compatible.
"""

import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.rbac import RBACService
from app.services.search import sanitize_query
from app.services.spell_service import SpellService, normalize_text, levenshtein_distance
from app.services.webhook import WebhookService


# =============================================================
# RBAC  (pure sync, no harness conflicts)
# =============================================================
class TestRBACService:
    def test_get_role_level_known(self):
        assert RBACService.get_role_level("admin") == 80

    def test_get_role_level_unknown(self):
        assert RBACService.get_role_level("unknown") == 0

    def test_has_role_hierarchy_true(self):
        assert RBACService.has_role_hierarchy("admin", "user") is True

    def test_has_role_hierarchy_equal(self):
        assert RBACService.has_role_hierarchy("admin", "admin") is True

    def test_has_role_hierarchy_false(self):
        assert RBACService.has_role_hierarchy("user", "admin") is False

    def test_get_inherited_roles_super_admin(self):
        roles = RBACService.get_inherited_roles("super_admin")
        assert "admin" in roles
        assert "guest" in roles

    def test_get_inherited_roles_guest(self):
        assert RBACService.get_inherited_roles("guest") == []

    def test_can_access_resource_super_admin(self):
        assert RBACService.can_access_resource("super_admin", "any", "any") is True

    def test_can_access_resource_admin_restricted(self):
        assert RBACService.can_access_resource("admin", "users", "admin") is False

    def test_can_access_resource_admin_allowed(self):
        assert RBACService.can_access_resource("admin", "searches", "read") is True

    def test_can_access_resource_moderator_allowed(self):
        assert RBACService.can_access_resource("moderator", "files", "delete") is True

    def test_can_access_resource_moderator_denied(self):
        assert RBACService.can_access_resource("moderator", "users", "read") is False

    def test_can_access_resource_user_allowed(self):
        assert RBACService.can_access_resource("user", "files", "upload") is True

    def test_can_access_resource_user_denied(self):
        assert RBACService.can_access_resource("user", "admin", "access") is False

    def test_can_access_resource_guest_allowed(self):
        assert RBACService.can_access_resource("guest", "searches", "create") is True

    def test_can_access_resource_guest_denied(self):
        assert RBACService.can_access_resource("guest", "files", "read") is False

    def test_get_user_permissions_super_admin(self):
        perms = RBACService.get_user_permissions("super_admin")
        assert "users.admin" in perms
        assert "admin.access" in perms

    def test_get_user_permissions_moderator(self):
        perms = RBACService.get_user_permissions("moderator")
        assert "searches.read" in perms
        assert "files.delete" in perms
        assert "files.upload" not in perms

    def test_get_user_permissions_with_existing(self):
        perms = RBACService.get_user_permissions("user", ["custom.perm"])
        assert "custom.perm" in perms
        assert "searches.create" in perms

    def test_check_permission_super_admin(self):
        assert RBACService.check_permission("super_admin", "anything") is True

    def test_check_permission_user_allowed(self):
        assert RBACService.check_permission("user", "searches.read") is True

    def test_check_permission_user_denied(self):
        assert RBACService.check_permission("user", "admin.access") is False

    def test_require_permission_returns_callable(self):
        checker = RBACService.require_permission("admin.access")
        assert callable(checker)

    def test_require_any_permission_returns_callable(self):
        checker = RBACService.require_any_permission(["searches.read", "files.read"])
        assert callable(checker)

    def test_require_all_permissions_returns_callable(self):
        checker = RBACService.require_all_permissions(["searches.read", "files.read"])
        assert callable(checker)


# =============================================================
# Search utils  (pure sync, no network)
# =============================================================
class TestSearchUtils:
    def test_sanitize_query_normal(self):
        assert "hello" in sanitize_query("hello world")

    def test_sanitize_query_strip_control(self):
        result = sanitize_query("hi\x00\x01there")
        assert "\x00" not in result
        assert "\x01" not in result

    def test_sanitize_query_collapse_whitespace(self):
        result = sanitize_query("a   b\n\nc")
        # sanitize_query strips control chars (\n) and collapses remaining whitespace
        assert "a" in result and "b" in result and "c" in result
        assert "\n" not in result

    def test_sanitize_query_empty(self):
        assert sanitize_query("") == ""

    def test_sanitize_query_only_whitespace(self):
        assert sanitize_query("   ") == ""

    def test_validate_url_https(self):
        from app.services.search import _validate_url
        with patch("socket.gethostbyname", return_value="208.80.154.224"):
            _validate_url("https://en.wikipedia.org/wiki/A")

    def test_validate_url_invalid_scheme(self):
        from app.services.search import _validate_url
        with pytest.raises(HTTPException):
            _validate_url("ftp://example.com")

    def test_validate_url_missing_hostname(self):
        from app.services.search import _validate_url
        with pytest.raises(HTTPException):
            _validate_url("https://")

    def test_validate_url_not_allowed_domain(self):
        from app.services.search import _validate_url
        with pytest.raises(HTTPException):
            _validate_url("https://evil.example.com/")

    def test_validate_url_cannot_resolve(self):
        from app.services.search import _validate_url
        with patch("socket.gethostbyname", side_effect=socket.gaierror):
            with pytest.raises(HTTPException):
                _validate_url("https://en.wikipedia.org/wiki/A")


# =============================================================
# SpellService  (pure sync helpers + async with mocked cache)
# =============================================================
class TestSpellService:
    def test_normalize_text_basic(self):
        assert normalize_text("Hello World") == "hello world"

    def test_normalize_text_accent(self):
        result = normalize_text("café")
        assert "é" not in result
        assert "cafe" in result

    def test_normalize_control_characters(self):
        result = normalize_text("a\x00b\x7f")
        # \x00 is codepoint < 32 (control) — stripped
        assert "\x00" not in result
        # \x7f (DEL, 127) is NOT < 32 — kept by normalize_text
        assert "\x7f" in result

    def test_normalize_empty(self):
        assert normalize_text("") == ""

    def test_normalize_only_whitespace(self):
        assert normalize_text("   ") == ""

    def test_levenshtein_equal(self):
        assert levenshtein_distance("abc", "abc") == 0

    def test_levenshtein_insertion(self):
        assert levenshtein_distance("ab", "abc") == 1

    def test_levenshtein_deletion(self):
        assert levenshtein_distance("abc", "ab") == 1

    def test_levenshtein_substitution(self):
        assert levenshtein_distance("axc", "abc") == 1

    def test_levenshtein_max_distance_exceeded(self):
        assert levenshtein_distance("a", "zzzz", max_distance=1) > 1

    def test_levenshtein_empty_strings(self):
        assert levenshtein_distance("", "") == 0

    def test_levenshtein_one_empty(self):
        assert levenshtein_distance("abc", "") == 3

    def test_spell_service_init_no_cache(self):
        svc = SpellService(cache_client=None, dictionary={"hello", "world"})
        assert svc._cache is None
        assert "hello" in svc._dictionary

    def test_spell_service_cache_key_deterministic(self):
        svc = SpellService(cache_client=None, dictionary={"hello"})
        assert svc._cache_key("Hello") == svc._cache_key("hello")

    @pytest.mark.asyncio
    async def test_correct_query_no_changes(self):
        svc = SpellService(cache_client=None, dictionary={"hello", "world"})
        result = await svc.correct_query("hello world")
        assert result.changed is False
        assert result.corrected == "hello world"

    @pytest.mark.asyncio
    async def test_correct_query_empty(self):
        svc = SpellService(cache_client=None, dictionary={"hello"})
        result = await svc.correct_query("")
        assert result.changed is False

    @pytest.mark.asyncio
    async def test_correct_query_too_long(self):
        svc = SpellService(cache_client=None, dictionary={"hello"})
        result = await svc.correct_query("x" * 101)
        assert result.changed is False

    @pytest.mark.asyncio
    async def test_correct_query_correction(self):
        svc = SpellService(
            cache_client=None,
            dictionary={"hello", "world"},
            frequency={"hello": 100, "world": 50},
        )
        result = await svc.correct_query("helloo world")
        assert result.changed is True
        assert result.suggestions is not None

    @pytest.mark.asyncio
    async def test_update_dictionary(self):
        svc = SpellService(cache_client=None, dictionary=set())
        await svc.update_dictionary(["hello", "HELLO"])
        assert svc._dictionary == {"hello"}
        assert svc._frequency.get("hello") == 2

    @pytest.mark.asyncio
    async def test_update_dictionary_skips_digits(self):
        svc = SpellService(cache_client=None, dictionary=set())
        await svc.update_dictionary(["hello", "test123"])
        assert "hello" in svc._dictionary
        assert "test123" not in svc._dictionary

    @pytest.mark.asyncio
    async def test_generate_candidates_empty_dict(self):
        svc = SpellService(cache_client=None, dictionary=set())
        result = await svc.generate_candidates("hello")
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_candidates_with_dict(self):
        svc = SpellService(
            cache_client=None,
            dictionary={"hello", "hell", "help"},
            frequency={"hello": 100, "hell": 50, "help": 30},
        )
        result = await svc.generate_candidates("helo")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_correct_query_cache_hit(self):
        cache = AsyncMock()
        from app.services.spell_service import SpellResult
        cache.get.return_value = SpellResult(
            original="hello world", corrected="hello world",
            confidence=1.0, changed=False, suggestions=None
        ).__dict__
        svc = SpellService(cache_client=cache, dictionary={"hello", "world"})
        result = await svc.correct_query("hello world")
        assert result.changed is False
        cache.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_correct_query_cache_set_failure(self):
        cache = AsyncMock()
        cache.get.return_value = None
        cache.set.side_effect = Exception("cache down")
        svc = SpellService(
            cache_client=cache,
            dictionary={"hello", "world"},
            frequency={"hello": 100, "world": 50},
        )
        # Should not raise — cache set failure is logged, not propagated
        result = await svc.correct_query("helloo world")
        assert result.changed is True


# =============================================================
# WebhookService  (in-memory, no network)
# =============================================================
class TestWebhookService:
    @pytest.mark.asyncio
    async def test_create_webhook(self):
        svc = WebhookService()
        webhook = await svc.create_webhook(
            1, "https://example.com/hook", ["user.created"]
        )
        assert webhook.id == 1
        assert webhook.url == "https://example.com/hook"
        assert webhook.is_active is True

    @pytest.mark.asyncio
    async def test_get_webhook_not_found(self):
        svc = WebhookService()
        result = await svc.get_webhook(999, 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_webhook_wrong_user(self):
        svc = WebhookService()
        webhook = await svc.create_webhook(
            1, "https://example.com/hook", ["user.created"]
        )
        result = await svc.get_webhook(webhook.id, 2)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_webhooks(self):
        svc = WebhookService()
        await svc.create_webhook(
            1, "https://example.com/hook", ["user.created"], description="Desc"
        )
        hooks = await svc.list_webhooks(1)
        assert len(hooks) == 1
        assert hooks[0].description == "Desc"

    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self):
        svc = WebhookService()
        hooks = await svc.list_webhooks(1)
        assert hooks == []

    @pytest.mark.asyncio
    async def test_update_webhook(self):
        svc = WebhookService()
        webhook = await svc.create_webhook(
            1, "https://example.com/hook", ["user.created"]
        )
        updated = await svc.update_webhook(
            webhook.id, 1, url="https://new.example.com/hook"
        )
        assert updated.url == "https://new.example.com/hook"

    @pytest.mark.asyncio
    async def test_update_webhook_not_found(self):
        svc = WebhookService()
        result = await svc.update_webhook(999, 1, url="https://new.example.com/hook")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_webhook_partial(self):
        svc = WebhookService()
        webhook = await svc.create_webhook(
            1, "https://example.com/hook", ["user.created"], description="Old"
        )
        updated = await svc.update_webhook(webhook.id, 1, description="New")
        assert updated.description == "New"
        assert updated.url == "https://example.com/hook"  # unchanged

    @pytest.mark.asyncio
    async def test_delete_webhook(self):
        svc = WebhookService()
        webhook = await svc.create_webhook(
            1, "https://example.com/hook", ["user.created"]
        )
        deleted = await svc.delete_webhook(webhook.id, 1)
        assert deleted is True
        result = await svc.get_webhook(webhook.id, 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_webhook_not_found(self):
        svc = WebhookService()
        result = await svc.delete_webhook(123, 1)
        assert result is False

    @pytest.mark.asyncio
    async def test_test_webhook_not_found(self):
        svc = WebhookService()
        result = await svc.test_webhook(123, 1)
        assert result == {"success": False, "error": "Webhook not found"}

    @pytest.mark.asyncio
    async def test_get_delivery_logs_empty(self):
        svc = WebhookService()
        result = await svc.get_delivery_logs(1, 1)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_delivery_logs_wrong_user(self):
        svc = WebhookService()
        result = await svc.get_delivery_logs(123, 1)
        assert result == []

    @pytest.mark.asyncio
    async def test_trigger_event_no_matching_webhooks(self):
        svc = WebhookService()
        # No webhooks registered — should not raise
        await svc.trigger_event("user.created", {"user_id": 1})
        # No assertion needed — just verifying no exception

    @pytest.mark.asyncio
    async def test_trigger_event_inactive_webhook_skipped(self):
        svc = WebhookService()
        webhook = await svc.create_webhook(
            1, "https://example.com/hook", ["user.created"]
        )
        await svc.update_webhook(webhook.id, 1, is_active=False)
        # Should not raise — inactive webhooks are skipped
        await svc.trigger_event("user.created", {"user_id": 1})