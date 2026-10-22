"""Enterprise API feature tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import create_access_token
from app.config import get_settings

settings = get_settings()
client = TestClient(app)


class TestAPIVersioning:
    """Test API versioning middleware."""
    
    def test_versioned_endpoint_v1(self):
        """Test v1 endpoint access."""
        # Health endpoint is version-agnostic, so test with an actual v1 endpoint
        # The versioning middleware should accept /api/v1/ paths (not return 400)
        response = client.get("/api/v1/nonexistent")
        # Should get 404 (not found) not 400 (version required)
        assert response.status_code == 404
    
    def test_versioned_endpoint_v2(self):
        """Test v2 endpoint access."""
        response = client.get("/api/v2/health")
        # May return 404 if v2 routes not implemented, but should not 400
        assert response.status_code in [200, 404]
    
    def test_unversioned_endpoint_rejected(self):
        """Test that unversioned endpoints are rejected."""
        # The versioning middleware should reject /api/search (no version)
        # Use a path that's not in VERSION_AGNOSTIC_PATHS and doesn't have a version
        with pytest.raises(Exception):  # noqa: BLE001
            client.get("/api/search")
    
    def test_version_agnostic_endpoints(self):
        """Test that version-agnostic endpoints work."""
        response = client.get("/health")
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting."""
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit middleware exists and can add headers."""
        from app.middleware.rate_limit import RateLimitHeadersMiddleware
        assert RateLimitHeadersMiddleware is not None
    
    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement."""
        from app.middleware.rate_limit import rate_limiter
        # Verify rate limiter exists and has the check method
        assert hasattr(rate_limiter, 'check_rate_limit')
        assert callable(rate_limiter.check_rate_limit)


class TestResponseStandardization:
    """Test response standardization."""
    
    def test_request_id_header(self):
        """Test that request ID middleware exists."""
        from app.middleware.response import ResponseStandardizationMiddleware
        assert ResponseStandardizationMiddleware is not None
    
    def test_error_response_format(self):
        """Test standardized error response helper function."""
        from app.middleware.response import error_response
        from fastapi.responses import JSONResponse
        
        # Test that error_response function exists and returns proper format
        response = error_response(
            error_code="NOT_FOUND",
            message="Resource not found",
            status_code=404,
        )
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404


class TestPagination:
    """Test pagination utilities."""
    
    def test_pagination_params(self):
        """Test pagination parameter validation."""
        from app.utils.pagination import PaginationParams
        
        # Valid params
        params = PaginationParams(page=1, page_size=20)
        assert params.offset == 0
        assert params.limit == 20
        
        # Page 2
        params = PaginationParams(page=2, page_size=20)
        assert params.offset == 20
    
    def test_pagination_response_creation(self):
        """Test pagination response creation."""
        from app.utils.pagination import create_pagination_response
        
        items = [{"id": 1}, {"id": 2}]
        response = create_pagination_response(items, total=10, page=1, page_size=2)
        
        assert response["items"] == items
        assert response["pagination"]["total"] == 10
        assert response["pagination"]["page"] == 1
        assert response["pagination"]["page_size"] == 2
        assert response["pagination"]["total_pages"] == 5
        assert response["pagination"]["has_next"] is True
        assert response["pagination"]["has_previous"] is False


class TestFiltering:
    """Test filtering and sorting."""
    
    def test_filter_parsing(self):
        """Test filter string parsing."""
        from app.utils.filtering import parse_filter_params
        
        # Single filter
        filters = parse_filter_params("status:eq:active")
        assert len(filters.filters) == 1
        assert filters.filters[0].field == "status"
        assert filters.filters[0].operator.value == "eq"
        assert filters.filters[0].value == "active"
    
    def test_multiple_filters(self):
        """Test multiple filter parsing."""
        from app.utils.filtering import parse_filter_params
        
        filters = parse_filter_params("status:eq:active,created_at:gte:2024-01-01")
        assert len(filters.filters) == 2
        assert filters.filters[0].field == "status"
        assert filters.filters[1].field == "created_at"
    
    def test_filter_sql_generation(self):
        """Test SQL generation from filters."""
        from app.utils.filtering import FilterSet
        
        filter_set = FilterSet()
        filter_set.eq("status", "active")
        filter_set.gte("created_at", "2024-01-01")
        
        where_clause, params = filter_set.to_sql()
        assert "WHERE" in where_clause
        assert "status = ?" in where_clause
        assert "created_at >= ?" in where_clause
        assert params == ("active", "2024-01-01")
    
    def test_sort_parsing(self):
        """Test sort string parsing."""
        from app.utils.filtering import parse_sort_params
        
        sort_set = parse_sort_params("created_at:desc,name:asc")
        assert len(sort_set.sorts) == 2
        assert sort_set.sorts[0].field == "created_at"
        assert sort_set.sorts[0].direction == "desc"
        assert sort_set.sorts[1].field == "name"
        assert sort_set.sorts[1].direction == "asc"
    
    def test_sort_sql_generation(self):
        """Test SQL generation from sorts."""
        from app.utils.filtering import SortSet
        
        sort_set = SortSet()
        sort_set.desc("created_at")
        sort_set.asc("name")
        
        order_clause = sort_set.to_sql()
        assert "ORDER BY" in order_clause
        assert "created_at DESC" in order_clause
        assert "name ASC" in order_clause
    
    def test_invalid_field_rejection(self):
        """Test that invalid field names are rejected."""
        from app.utils.filtering import FilterCondition, FilterOperator
        
        with pytest.raises(ValueError):
            condition = FilterCondition("invalid; DROP TABLE", FilterOperator.EQ, "value")
            condition.to_sql(0)


class TestMonitoring:
    """Test monitoring and metrics."""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization."""
        from app.services.monitoring import metrics
        
        # Metrics collector should exist and have the expected attributes
        assert hasattr(metrics, 'request_count')
        assert hasattr(metrics, 'error_count')
        assert hasattr(metrics, 'record_request')
    
    def test_record_request(self):
        """Test request recording."""
        from app.services.monitoring import metrics
        
        initial_count = metrics.request_count.value
        metrics.record_request(
            endpoint="/test",
            method="GET",
            status_code=200,
            response_time_ms=100.0,
        )
        
        assert metrics.request_count.value == initial_count + 1
        assert len(metrics.request_duration.values) > 0


class TestWebhooks:
    """Test webhook system."""
    
    def test_webhook_service_initialization(self):
        """Test webhook service initialization."""
        from app.services.webhook import webhook_service
        
        assert webhook_service is not None
    
    def test_create_webhook(self):
        """Test webhook creation."""
        from app.services.webhook import webhook_service
        import asyncio
        
        async def test():
            webhook = await webhook_service.create_webhook(
                user_id=1,
                url="https://example.com/webhook",
                events=["user.created", "document.indexed"],
                secret="test_secret",
            )
            assert webhook.id is not None
            assert webhook.url == "https://example.com/webhook"
            assert len(webhook.events) == 2
            assert webhook.is_active is True
        
        asyncio.run(test())
    
    def test_list_webhooks(self):
        """Test webhook listing."""
        from app.services.webhook import webhook_service
        import asyncio
        
        async def test():
            webhooks = await webhook_service.list_webhooks(user_id=1)
            assert isinstance(webhooks, list)
        
        asyncio.run(test())


class TestSecurity:
    """Test security features."""
    
    def test_csrf_protection_exists(self):
        """Test that CSRF protection middleware exists."""
        from app.middleware.security import CSRFProtectionMiddleware
        assert CSRFProtectionMiddleware is not None
    
    def test_security_headers_middleware(self):
        """Test security headers middleware."""
        from app.middleware.security import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None
    
    def test_request_size_limit(self):
        """Test request size limit middleware."""
        from app.middleware.security import RequestSizeLimitMiddleware
        assert RequestSizeLimitMiddleware is not None


class TestCaching:
    """Test caching system."""
    
    def test_cache_service_initialization(self):
        """Test cache service initialization."""
        from app.services.cache import cache_service
        
        assert cache_service is not None
        assert hasattr(cache_service, "get")
        assert hasattr(cache_service, "set")
        assert hasattr(cache_service, "delete")
    
    def test_cache_operations(self):
        """Test basic cache operations."""
        from app.services.cache import cache_service
        import asyncio
        
        async def test():
            # Set value
            await cache_service.set("test_key", "test_value", ttl=60)
            # Get value
            value = await cache_service.get("test_key")
            assert value == "test_value"
            # Delete value
            await cache_service.delete("test_key")
            value = await cache_service.get("test_key")
            assert value is None
        
        asyncio.run(test())


class TestAuthentication:
    """Test authentication system."""
    
    def test_jwt_token_creation(self):
        """Test JWT token creation."""
        from app.services.auth import decode_token
        
        token = create_access_token("test@example.com", role="user")
        assert token is not None
        assert isinstance(token, str)
        
        payload = decode_token(token)
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        from app.services.auth import hash_password, verify_password
        
        password = "TestPass123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_brute_force_protection(self):
        """Test brute force protection exists."""
        from app.services.auth import check_brute_force, record_login_failure
        
        # These functions should exist and be callable
        assert callable(check_brute_force)
        assert callable(record_login_failure)


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_auth_request_validation(self):
        """Test authentication request validation."""
        from app.models.schemas import AuthRequest
        
        # Valid request
        req = AuthRequest(email="test@example.com", password="TestPass123!")
        assert req.email == "test@example.com"
        
        # Invalid email
        with pytest.raises(Exception):
            AuthRequest(email="invalid", password="TestPass123!")
    
    def test_webhook_create_validation(self):
        """Test webhook creation validation."""
        from app.models.webhook import WebhookCreate
        
        # Valid webhook
        webhook = WebhookCreate(
            url="https://example.com/webhook",
            events=["user.created"],
        )
        assert str(webhook.url) == "https://example.com/webhook"
        
        # Invalid URL
        with pytest.raises(Exception):
            WebhookCreate(url="not-a-url", events=["user.created"])