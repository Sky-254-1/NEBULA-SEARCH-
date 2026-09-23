# Nebula Search Engine — Enterprise API Guide

## Table of Contents

1. [Overview](#overview)
2. [API Versioning](#api-versioning)
3. [Authentication & Authorization](#authentication--authorization)
4. [Rate Limiting](#rate-limiting)
5. [Response Standardization](#response-standardization)
6. [Pagination](#pagination)
7. [Filtering & Sorting](#filtering--sorting)
8. [Caching](#caching)
9. [Webhooks](#webhooks)
10. [Monitoring & Observability](#monitoring--observability)
11. [Security](#security)
12. [Error Handling](#error-handling)
13. [Best Practices](#best-practices)

---

## Overview

Nebula Search Engine API v2.0 is an enterprise-grade, production-ready API with comprehensive features for scalability, security, and observability.

### Key Features

- ✅ **API Versioning** - URI-based versioning with deprecation policy
- ✅ **Rate Limiting** - Sliding window algorithm with per-user/IP limits
- ✅ **Response Standardization** - Consistent envelope format
- ✅ **Pagination** - Offset and cursor-based pagination
- ✅ **Filtering & Sorting** - Safe, declarative query building
- ✅ **Caching** - Redis with in-memory fallback
- ✅ **Webhooks** - Event notifications with retry logic
- ✅ **Monitoring** - Metrics collection and request tracing
- ✅ **Security** - JWT, CSRF, CORS, security headers
- ✅ **OpenAPI Documentation** - Auto-generated with examples

### Base URL

```
Production: https://api.nebula-search.com/api/v2
Development: http://localhost:8000/api/v2
```

### API Versions

| Version | Status | Sunset Date |
|---------|--------|-------------|
| v1 | Deprecated | 2027-06-30 |
| v2 | Current | N/A |

---

## API Versioning

### URI-Based Versioning

All API endpoints must include a version prefix:

```
/api/v1/...  # Deprecated - migration required by 2027-06-30
/api/v2/...  # Current stable version
```

### Version-Agnostic Endpoints

These endpoints don't require versioning:

- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema

### Deprecation Headers

When using v1 endpoints, responses include deprecation headers:

```http
X-API-Deprecated: true
X-API-Deprecation-Date: 2026-12-31
X-API-Sunset-Date: 2027-06-30
X-API-Migration-Guide: /docs/api-migration-v1-to-v2
```

### Migration Guide

To migrate from v1 to v2:

1. Update base URL from `/api/v1/` to `/api/v2/`
2. Review breaking changes in [Migration Guide](./api-migration-v1-to-v2.md)
3. Test with v2 endpoints in staging
4. Update client applications
5. Deploy to production

---

## Authentication & Authorization

### JWT Authentication

Nebula uses JWT (JSON Web Tokens) for authentication.

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Using the Access Token

Include the access token in the Authorization header:

```http
GET /api/v1/search/web
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Refresh Token

Refresh expired access tokens:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Cookie-Based Authentication

Enable cookie mode for web applications:

```bash
AUTH_COOKIE_MODE=true
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
```

### Roles & Permissions

| Role | Description | Permissions |
|------|-------------|-------------|
| `user` | Standard user | Read/write own data |
| `admin` | Administrator | Full system access |

#### Role-Based Access

```python
from app.services.auth import require_admin, require_user

@router.get("/admin/dashboard")
async def admin_dashboard(email: str = Depends(require_admin)):
    # Only admins can access
    return {"message": "Admin dashboard"}
```

### Brute-Force Protection

- **Max login attempts**: 5
- **Lockout duration**: 15 minutes
- **Exponential backoff**: 1s, 2s, 4s, 8s, 15s

---

## Rate Limiting

### Overview

Nebula implements sliding window rate limiting with multiple identifier types.

### Rate Limit Headers

Every response includes rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1709452800
```

### Rate Limit Tiers

| Identifier Type | Default Limit | Window |
|----------------|---------------|--------|
| Anonymous (IP) | 60 requests | 1 minute |
| Authenticated (User) | 100 requests | 1 minute |
| API Key | 200 requests | 1 minute |
| Signup | 5 requests | 1 hour |
| Login | 5 requests | 15 minutes |
| Refresh | 10 requests | 15 minutes |

### Rate Limit Response

When rate limited:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1709452800
Retry-After: 45

{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Try again shortly.",
  "validation_errors": [],
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": 1709452800.0
}
```

### Burst Limits

Endpoints can have burst limits for short-term spikes:

```python
from app.middleware.rate_limit import rate_limit

# Allow 10 requests in 10 seconds, then 60 per minute
await rate_limit(request, limit=60, window=60, burst_limit=10, burst_window=10)
```

### Custom Rate Limits

Configure per-endpoint limits in environment:

```bash
RATE_LIMIT_PER_MINUTE=60
SIGNUP_RATE_LIMIT=5
LOGIN_RATE_LIMIT=5
REFRESH_RATE_LIMIT=10
```

---

## Response Standardization

### Success Response

All successful responses follow this structure:

```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { ... },
  "metadata": {},
  "timestamp": 1709452800.0
}
```

### Error Response

All errors follow this structure:

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "validation_errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ],
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": 1709452800.0
}
```

### Request ID

Every response includes a unique request ID for tracing:

```http
X-Request-ID: 123e4567-e89b-12d3-a456-426614174000
```

Use this ID when contacting support or debugging issues.

---

## Pagination

### Offset Pagination

Standard page-based pagination:

```http
GET /api/v1/search/history?page=2&page_size=20
```

**Response:**

```json
{
  "items": [...],
  "pagination": {
    "total": 100,
    "page": 2,
    "page_size": 20,
    "total_pages": 5,
    "has_next": true,
    "has_previous": true
  }
}
```

### Cursor Pagination

For large datasets, use cursor-based pagination:

```http
GET /api/v1/documents?cursor=eyJpZCI6MjB9&limit=20
```

**Response:**

```json
{
  "items": [...],
  "pagination": {
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "has_next": true,
    "has_previous": false,
    "cursors": {
      "next": "eyJpZCI6MjB9",
      "previous": "eyJpZCI6MTB9"
    }
  }
}
```

### Pagination Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `page_size` | integer | 20 | Items per page (max: 100) |
| `cursor` | string | null | Pagination cursor |

---

## Filtering & Sorting

### Filtering

Filter results using the `filter` query parameter:

```http
GET /api/v1/documents?filter=status:eq:active,created_at:gte:2024-01-01
```

#### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal | `status:eq:active` |
| `ne` | Not equal | `status:ne:deleted` |
| `gt` | Greater than | `score:gt:0.8` |
| `gte` | Greater than or equal | `created_at:gte:2024-01-01` |
| `lt` | Less than | `score:lt:0.5` |
| `lte` | Less than or equal | `size:lte:1000000` |
| `in` | In list | `status:in:active,pending` |
| `nin` | Not in list | `status:nin:deleted,archived` |
| `like` | LIKE pattern | `filename:like:%.pdf` |
| `ilike` | Case-insensitive LIKE | `title:ilike:%search%` |
| `between` | Between two values | `created_at:between:2024-01-01|2024-12-31` |
| `is_null` | IS NULL | `deleted_at:is_null` |
| `is_not_null` | IS NOT NULL | `deleted_at:is_not_null` |

### Sorting

Sort results using the `sort` query parameter:

```http
GET /api/v1/documents?sort=created_at:desc,name:asc
```

**Default sort:** `id:asc`

### Security

- Field names are validated to prevent SQL injection
- Only allowed fields can be used for sorting
- All values are parameterized (no string concatenation)

---

## Caching

### Cache Architecture

Nebula uses a two-tier caching system:

1. **Redis** (primary) - Distributed cache for multi-instance deployments
2. **In-memory** (fallback) - Local cache when Redis is unavailable

### Cache Configuration

```bash
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300  # 5 minutes default
```

### Cache Keys

| Key Pattern | Description | TTL |
|-------------|-------------|-----|
| `ratelimit:{identifier}:{path}` | Rate limit tracking | 60s |
| `lockout:{ip}:{email}` | Login lockout | 900s |
| `attempts:{ip}:{email}` | Login attempts | 3600s |
| `search:{query_hash}` | Search results | 300s |
| `vector:{query_hash}` | Vector search results | 600s |

### Cache Invalidation

Automatic invalidation on data changes:

- User updates → Invalidate user cache
- Document changes → Invalidate document cache
- Search index updates → Invalidate search cache

### Conditional Requests

Support for ETag and Last-Modified headers (coming in v2.1):

```http
If-None-Match: "abc123"
If-Modified-Since: Wed, 21 Oct 2015 07:28:00 GMT
```

---

## Webhooks

### Overview

Webhooks allow you to receive real-time notifications when events occur in Nebula.

### Creating a Webhook

```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://example.com/webhook",
  "events": [
    "user.created",
    "document.indexed",
    "search.completed"
  ],
  "secret": "your-webhook-secret",
  "description": "Production webhook"
}
```

### Supported Events

#### User Events
- `user.created` - New user registered
- `user.updated` - User profile updated
- `user.deleted` - User account deleted

#### Document Events
- `document.uploaded` - Document uploaded
- `document.indexed` - Document indexed for search
- `document.updated` - Document metadata updated
- `document.deleted` - Document deleted

#### Search Events
- `search.completed` - Web search completed
- `vector.search.completed` - Vector search completed

#### Auth Events
- `auth.login` - User logged in
- `auth.logout` - User logged out
- `auth.password_changed` - Password changed
- `auth.mfa_enabled` - MFA enabled
- `auth.mfa_disabled` - MFA disabled

#### System Events
- `system.alert` - System alert
- `system.rate_limit_exceeded` - Rate limit hit

### Webhook Payload

```json
{
  "event": "user.created",
  "timestamp": "2026-03-15T10:30:00Z",
  "data": {
    "user_id": 123,
    "email": "user@example.com",
    "role": "user"
  }
}
```

### Webhook Security

#### Secret Signing

When you provide a secret, webhooks include an HMAC-SHA256 signature:

```http
X-Webhook-Signature: sha256=abc123...
```

Verify the signature:

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Retry Logic

Failed webhooks are retried with exponential backoff:

- **Attempt 1**: Immediate
- **Attempt 2**: After 2 seconds
- **Attempt 3**: After 4 seconds

### Webhook Headers

```http
Content-Type: application/json
User-Agent: Nebula-Webhook/1.0
X-Webhook-Event: user.created
X-Webhook-ID: 123
X-Webhook-Delivery: 456
X-Webhook-Signature: sha256=abc123...
```

### Testing Webhooks

```http
POST /api/v1/webhooks/{webhook_id}/test
Authorization: Bearer <token>
```

### Delivery Logs

View webhook delivery history:

```http
GET /api/v1/webhooks/{webhook_id}/deliveries?limit=50
Authorization: Bearer <token>
```

---

## Monitoring & Observability

### Metrics

Nebula collects comprehensive metrics:

#### Request Metrics
- Total requests
- Requests per endpoint
- Response time (p50, p95, p99)
- Error rate
- Status code distribution

#### System Metrics
- Cache hit ratio
- Rate limit events
- Webhook delivery success rate
- Database connection pool usage

### Accessing Metrics

```python
from app.services.monitoring import metrics

# Get metrics summary
summary = metrics.get_metrics_summary()
print(summary)
```

**Output:**

```json
{
  "requests": {
    "total": 15234,
    "errors": 123,
    "error_rate": 0.008,
    "avg_response_time_ms": 45.2
  },
  "rate_limits": {
    "total": 12
  },
  "cache": {
    "hits": 5432,
    "misses": 1234,
    "hit_ratio": 0.815
  },
  "webhooks": {
    "deliveries": 456,
    "failures": 3
  }
}
```

### Request Tracing

Every request has a unique ID:

```http
X-Request-ID: 123e4567-e89b-12d3-a456-426614174000
```

Use this ID to trace requests across logs and metrics.

### Structured Logging

All logs include context:

```json
{
  "timestamp": "2026-03-15T10:30:00Z",
  "level": "info",
  "name": "nebula.search",
  "message": "Search completed",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user@example.com",
  "query": "example search",
  "duration_ms": 123.45
}
```

---

## Security

### Security Headers

All responses include security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; ...
```

### CORS Configuration

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://app.example.com
```

### CSRF Protection

CSRF protection is enabled for cookie-based authentication:

```http
POST /api/v1/auth/logout
X-CSRF-Token: <csrf-token>
```

### Request Size Limits

```bash
# Default: 10MB
MAX_REQUEST_SIZE=10485760
```

### Input Validation

All inputs are validated using Pydantic schemas:

- Type checking
- Length constraints
- Format validation (email, URL, etc.)
- Custom validators

### SQL Injection Prevention

- Parameterized queries only
- Field name validation
- No string concatenation in SQL

### XSS Prevention

- Output sanitization
- Content-Type enforcement
- CSP headers

---

## Error Handling

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required |
| `INVALID_TOKEN` | 401 | Token is invalid or expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Response Format

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "validation_errors": [
    {
      "field": "email",
      "message": "Invalid email format",
      "type": "value_error"
    }
  ],
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": 1709452800.0
}
```

---

## Best Practices

### 1. Always Use Versioned Endpoints

```http
✅ GET /api/v2/search/web
❌ GET /search/web
```

### 2. Handle Rate Limits Gracefully

```python
import time

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

### 3. Use Pagination for Large Datasets

```http
✅ GET /api/v1/documents?page=1&page_size=20
❌ GET /api/v1/documents  # Returns all documents
```

### 4. Verify Webhook Signatures

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 5. Log Request IDs

```python
request_id = response.headers.get('X-Request-ID')
logger.info(f"Operation completed", extra={"request_id": request_id})
```

### 6. Use Cursor Pagination for Real-Time Data

```http
✅ GET /api/v1/notifications?cursor=eyJpZCI6MTB9&limit=20
❌ GET /api/v1/notifications?page=1&page_size=20  # May miss new data
```

### 7. Implement Proper Error Handling

```python
try:
    response = requests.get(url)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    request_id = e.response.headers.get('X-Request-ID')
    logger.error(f"API error: {error_data}", extra={"request_id": request_id})
```

### 8. Cache Aggressively

```python
# Cache search results
cache_key = f"search:{hash(query)}"
cached = await cache.get(cache_key)
if cached:
    return cached

results = await perform_search(query)
await cache.set(cache_key, results, ttl=300)
```

---

## Support

- **Documentation**: https://docs.nebula-search.com
- **API Status**: https://status.nebula-search.com
- **Support Email**: support@nebula-search.com
- **GitHub Issues**: https://github.com/Sky-254-1/Nebula-search-engine-/issues

---

## Changelog

### v2.0.0 (2026-03-15)

- ✨ API versioning with deprecation policy
- ✨ Enhanced rate limiting with sliding window
- ✨ Response standardization
- ✨ Pagination framework (offset + cursor)
- ✨ Filtering and sorting system
- ✨ Webhook system with retry logic
- ✨ Monitoring and metrics collection
- ✨ Enhanced OpenAPI documentation
- 🔒 Security headers and CSRF protection
- 🔒 Brute-force protection

### v1.1.0 (2026-01-15)

- Vector search and RAG
- Audio transcription
- MFA support
- OAuth integration

### v1.0.0 (2025-12-01)

- Initial release
- Basic search functionality
- JWT authentication
- File upload