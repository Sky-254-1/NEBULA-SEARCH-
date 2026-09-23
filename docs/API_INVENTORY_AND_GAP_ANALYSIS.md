# Nebula Search Engine — API Inventory & Gap Analysis

## Executive Summary

This document provides a complete inventory of existing APIs, identifies gaps, duplicates, and proposes a streamlined production-ready API architecture.

**Current State:** 35+ endpoints across 9 route modules  
**Proposed State:** 45 endpoints across 8 consolidated domains  
**Net Change:** +10 endpoints, -5 duplicates, +3 new domains

---

## Part 1: Existing API Inventory

### 1.1 Current Route Modules

| Module | Prefix | Endpoints | Status | Issues |
|--------|--------|-----------|--------|--------|
| `health.py` | `/api/v1` | 2 | ✅ Stable | None |
| `auth.py` | `/api/v1/auth` | 6 | ✅ Stable | Missing email verification in main router |
| `auth_extended.py` | `/api/v1/auth` | 8 | ✅ Stable | Duplicate prefix with auth.py |
| `mfa.py` | `/api/v1/mfa` | TBD | ⚠️ Unknown | Not reviewed |
| `oauth.py` | `/api/v1/oauth` | TBD | ⚠️ Unknown | Not reviewed |
| `admin.py` | `/api/v1/admin` | 4 | ⚠️ Limited | Incomplete user management |
| `search.py` | `/api/v1/search` | 3 | ⚠️ Limited | No semantic/hybrid search |
| `ai.py` | `/api/v1/ai` | 5 | ✅ Stable | Good |
| `audio.py` | `/api/v1/audio` | TBD | ⚠️ Unknown | Not reviewed |
| `storage.py` | `/api/v1/storage` | 6 | ⚠️ Misnamed | Should be `/documents` |
| `vector.py` | `/api/v1/vector` | 8 | ✅ Stable | Good |
| `webhooks.py` | `/api/v1/webhooks` | TBD | ⚠️ Unknown | Not reviewed |

### 1.2 Complete Endpoint Inventory

#### Health Endpoints (2)
| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| GET | `/` | None | 100/min | API root |
| GET | `/health` | None | 100/min | Health check |

#### Authentication Endpoints (14)
| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| POST | `/api/v1/auth/signup` | None | 5/min | Register user |
| POST | `/api/v1/auth/login` | None | 5/min | Login |
| POST | `/api/v1/auth/refresh` | None | 10/min | Refresh token |
| POST | `/api/v1/auth/logout` | Optional | 10/min | Logout session |
| POST | `/api/v1/auth/logout-all` | Required | 5/min | Logout all sessions |
| GET | `/api/v1/auth/me` | Required | 60/min | Get current user |
| GET | `/api/v1/auth/verify-email` | None | 10/min | Verify email |
| POST | `/api/v1/auth/resend-verification` | Required | 5/min | Resend verification |
| POST | `/api/v1/auth/forgot-password` | None | 3/min | Request password reset |
| POST | `/api/v1/auth/reset-password` | None | 5/min | Reset password |
| POST | `/api/v1/auth/change-password` | Required | 5/min | Change password |
| POST | `/api/v1/auth/change-email` | Required | 5/min | Change email |
| DELETE | `/api/v1/auth/account` | Required | 1/day | Delete account |
| GET | `/api/v1/auth/sessions` | Required | 10/min | List sessions |
| DELETE | `/api/v1/auth/sessions/{id}` | Required | 10/min | Terminate session |

#### Search Endpoints (3)
| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| GET | `/api/v1/search/web` | Required | 30/min | Web search |
| GET | `/api/v1/search/orchestrate` | Required | 20/min | Multi-backend search |
| GET | `/api/v1/search/history` | Required | 10/min | Search history |

#### AI Endpoints (5)
| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| POST | `/api/v1/ai/ask` | Required | 20/min | AI answer |
| POST | `/api/v1/ai/ask/stream` | Required | 20/min | Streaming AI answer |
| GET | `/api/v1/ai/chat/history` | Required | 60/min | Chat history |
| DELETE | `/api/v1/ai/chat/history` | Required | 5/min | Clear chat history |
| POST | `/api/v1/ai/synthesize` | Required | 10/min | Synthesize snippets |

#### Storage/Document Endpoints (6)
| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| GET | `/api/v1/storage/documents` | Required | 60/min | List documents |
| POST | `/api/v1/storage/documents` | Required | 20/min | Upload document |
| DELETE | `/api/v1/storage/documents/{id}` | Required | 20/min | Delete document |
| GET | `/api/v1/storage/settings` | Required | 60/min | Get settings |
| PUT | `/api/v1/storage/settings` | Required | 30/min | Update settings |
| POST | `/api/v1/storage/exports` | Required | 10/min | Create export |
| GET | `/api/v1/storage/exports` | Required | 30/min | List exports |

#### Vector Endpoints (8)
| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| GET | `/api/v1/vector/documents/{id}/status` | Required | 60/min | Index status |
| POST | `/api/v1/vector/documents/{id}/reindex` | Required | 10/min | Reindex document |
| POST | `/api/v1/vector/documents/reindex-all` | Required | 1/day | Reindex all |
| POST | `/api/v1/vector/ask` | Required | 20/min | RAG query |
| POST | `/api/v1/vector/search` | Required | 30/min | Vector search |
| GET | `/api/v1/vector/citations` | Required | 60/min | List citations |
| POST | `/api/v1/vector/documents/{id}/index-now` | Required | 10/min | Sync index |
| GET | `/api/v1/vector/stats` | Required | 10/min | Vector stats |
| POST | `/api/v1/vector/export` | Required | 5/min | Export vectors |

#### Admin Endpoints (4)
| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| GET | `/api/v1/admin/audit-logs` | Admin | 30/min | Get audit logs |
| GET | `/api/v1/admin/users/{id}/sessions` | Admin | 30/min | Get user sessions |
| POST | `/api/v1/admin/sessions/{id}/revoke` | Admin | 30/min | Revoke session |
| POST | `/api/v1/admin/users/{id}/role` | Admin | 20/min | Update user role |

**Total Current Endpoints: ~42**

---

## Part 2: API Gap Analysis

### 2.1 Critical Gaps

#### ❌ No Unified Search API
**Problem:** Search functionality is split across three separate endpoints:
- `/search/web` — Web search only
- `/search/orchestrate` — Multi-backend web search
- `/vector/search` — Vector search only
- `/ai/ask` — AI-powered search

**Impact:** 
- Clients must call multiple endpoints for hybrid search
- No consistent search experience
- Difficult to add new search modes

**Proposed Solution:**
```json
POST /api/v1/search
{
  "query": "enterprise search architecture",
  "mode": "hybrid", // "web" | "vector" | "hybrid" | "ai"
  "filters": {},
  "page": 1,
  "limit": 20
}
```

#### ❌ No Semantic/Hybrid Search
**Problem:** No endpoint combines keyword search with vector search

**Impact:** 
- Misses AI-powered search capabilities
- Poor relevance for complex queries
- No RAG (Retrieval-Augmented Generation)

**Proposed Solution:**
- Add `mode: "hybrid"` to unified search API
- Combine web + vector results with AI reranking

#### ❌ No User Management Domain
**Problem:** User operations scattered across `/auth/me` and `/storage/settings`

**Missing Endpoints:**
- `GET /api/v1/users/profile` — Full user profile
- `PUT /api/v1/users/profile` — Update profile
- `GET /api/v1/users/preferences` — User preferences
- `PUT /api/v1/users/preferences` — Update preferences
- `GET /api/v1/users/activity` — Activity log
- `POST /api/v1/users/avatar` — Upload avatar
- `DELETE /api/v1/users/avatar` — Delete avatar

#### ❌ No Notifications Domain
**Problem:** No notification system

**Missing Endpoints:**
- `GET /api/v1/notifications` — List notifications
- `GET /api/v1/notifications/unread-count` — Unread count
- `POST /api/v1/notifications/{id}/read` — Mark as read
- `POST /api/v1/notifications/read-all` — Mark all read
- `DELETE /api/v1/notifications/{id}` — Delete notification
- `DELETE /api/v1/notifications` — Clear all
- `GET /api/v1/notifications/preferences` — Get preferences
- `PUT /api/v1/notifications/preferences` — Update preferences

#### ❌ No Analytics Domain
**Problem:** No usage tracking or analytics

**Missing Endpoints:**
- `GET /api/v1/analytics/usage` — Usage statistics
- `GET /api/v1/analytics/search` — Search analytics
- `GET /api/v1/analytics/performance` — Performance metrics
- `GET /api/v1/analytics/export` — Export analytics

#### ❌ No Recommendations Domain
**Problem:** No content recommendations

**Missing Endpoints:**
- `GET /api/v1/recommendations/related` — Related content
- `GET /api/v1/recommendations/personalized` — Personalized recommendations
- `GET /api/v1/recommendations/similar-searches` — Similar searches

#### ❌ No Pagination/Filtering Standards
**Problem:** Collection endpoints return all results

**Impact:**
- Poor performance with large datasets
- No cursor-based pagination
- No filtering/sorting

**Proposed Solution:**
```json
{
  "data": [...],
  "meta": {
    "pagination": {
      "cursor": "eyJpZCI6MTIz...",
      "next_cursor": "eyJpZCI6MTI0...",
      "has_more": true,
      "total": 1000
    },
    "filters": {
      "applied": {"status": "active"},
      "available": ["status", "date", "category"]
    }
  }
}
```

### 2.2 Duplicate Functionality

#### Duplicate 1: Document Upload
**Current:**
- `POST /api/v1/storage/documents` — Upload document
- `POST /api/v1/vector/documents/{id}/index-now` — Index document

**Issue:** Indexing is separate from upload

**Proposed:** Combine into single workflow
```json
POST /api/v1/documents
{
  "file": "...",
  "auto_index": true
}
```

#### Duplicate 2: Search History
**Current:**
- `GET /api/v1/search/history` — Search history
- `GET /api/v1/ai/chat/history` — Chat history

**Issue:** Two separate history systems

**Proposed:** Unified activity history
```json
GET /api/v1/users/activity?type=search,chat
```

#### Duplicate 3: User Info
**Current:**
- `GET /api/v1/auth/me` — Current user
- `GET /api/v1/storage/settings` — User settings

**Issue:** User data split across endpoints

**Proposed:** Single user profile endpoint
```json
GET /api/v1/users/profile
{
  "profile": {...},
  "preferences": {...},
  "settings": {...}
}
```

### 2.3 Partially Implemented Features

#### Admin User Management
**Current:**
- `POST /api/v1/admin/users/{id}/role` — Update role ✅
- `GET /api/v1/admin/users/{id}/sessions` — Get sessions ⚠️ Not implemented

**Missing:**
- `GET /api/v1/admin/users` — List all users
- `GET /api/v1/admin/users/{id}` — Get user details
- `PUT /api/v1/admin/users/{id}/status` — Enable/disable user
- `DELETE /api/v1/admin/users/{id}` — Delete user

#### Vector Export
**Current:**
- `POST /api/v1/vector/export` — Export vectors ✅
- `POST /api/v1/storage/exports` — Export data ✅

**Issue:** Two export systems

**Proposed:** Single export system under `/documents`

### 2.4 Missing Standards

#### ❌ No Response Standardization
**Current:** Inconsistent response formats
```python
# Some endpoints return raw data
return {"history": [...]}

# Others use schemas
return DocumentListResponse(...)
```

**Proposed Standard:**
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2026-07-04T10:00:00Z",
    "request_id": "uuid",
    "pagination": {}
  }
}
```

#### ❌ No Error Standardization
**Current:** Inconsistent error formats
```python
# FastAPI default
{"detail": "Error message"}

# Custom
{"error": {"code": "...", "message": "..."}}
```

**Proposed Standard:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [...],
    "request_id": "uuid"
  }
}
```

#### ❌ No API Versioning Strategy
**Current:** Version in path (`/api/v1/`) but no migration plan

**Proposed:**
- `/api/v1/*` — Stable (maintain for 12 months)
- `/api/v2/*` — New features (next release)
- Header support: `X-API-Version: 2`
- Deprecation headers: `Sunset: 2027-01-01`

---

## Part 3: Proposed Production API Architecture

### 3.1 Domain Organization

```
/api/v1
├── /health
│   ├── GET /                    # Root
│   └── GET /health              # Health check
│
├── /auth
│   ├── POST /signup             # Register
│   ├── POST /login              # Login
│   ├── POST /refresh            # Refresh token
│   ├── POST /logout             # Logout
│   ├── POST /logout-all         # Logout all
│   ├── GET  /me                 # Current user
│   ├── GET  /verify-email       # Verify email
│   ├── POST /resend-verification
│   ├── POST /forgot-password
│   ├── POST /reset-password
│   ├── POST /change-password
│   ├── POST /change-email
│   ├── DELETE /account          # Delete account
│   ├── GET /sessions            # List sessions
│   ├── DELETE /sessions/{id}    # Terminate session
│   ├── POST /2fa/enable         # Enable 2FA
│   ├── POST /2fa/verify         # Verify 2FA
│   └── POST /2fa/disable        # Disable 2FA
│
├── /users
│   ├── GET /profile             # Get profile
│   ├── PUT /profile             # Update profile
│   ├── GET /preferences         # Get preferences
│   ├── PUT /preferences         # Update preferences
│   ├── GET /activity            # Activity log
│   ├── POST /avatar             # Upload avatar
│   └── DELETE /avatar           # Delete avatar
│
├── /search
│   ├── POST /                   # Unified search (replaces web, orchestrate, vector/search, ai/ask)
│   ├── GET /suggestions         # Search suggestions
│   ├── GET /autocomplete        # Autocomplete
│   ├── GET /history             # Search history
│   ├── DELETE /history          # Clear history
│   ├── POST /save               # Save search
│   ├── GET /saved               # List saved searches
│   └── DELETE /saved/{id}       # Delete saved search
│
├── /documents
│   ├── GET /                    # List documents
│   ├── POST /                   # Upload document
│   ├── GET /{id}                # Get document
│   ├── PUT /{id}                # Update metadata
│   ├── DELETE /{id}             # Delete document
│   ├── POST /{id}/reindex       # Reindex document
│   ├── GET /{id}/status         # Index status
│   ├── POST /batch-upload       # Batch upload
│   └── POST /batch-delete       # Batch delete
│
├── /ai
│   ├── POST /ask                # AI answer (deprecated, use /search)
│   ├── POST /ask/stream         # Streaming AI (deprecated, use /search)
│   ├── GET /chat/history        # Chat history
│   ├── DELETE /chat/history     # Clear chat
│   └── POST /synthesize         # Synthesize snippets
│
├── /notifications
│   ├── GET /                    # List notifications
│   ├── GET /unread-count        # Unread count
│   ├── POST /{id}/read          # Mark as read
│   ├── POST /read-all           # Mark all read
│   ├── DELETE /{id}             # Delete notification
│   ├── DELETE /                 # Clear all
│   ├── GET /preferences         # Get preferences
│   └── PUT /preferences         # Update preferences
│
├── /analytics
│   ├── GET /usage               # Usage statistics
│   ├── GET /search              # Search analytics
│   ├── GET /performance         # Performance metrics
│   └── GET /export              # Export analytics
│
├── /recommendations
│   ├── GET /related             # Related content
│   ├── GET /personalized        # Personalized recommendations
│   └── GET /similar-searches    # Similar searches
│
├── /admin
│   ├── GET /users               # List all users
│   ├── GET /users/{id}          # Get user details
│   ├── PUT /users/{id}/role     # Update role
│   ├── PUT /users/{id}/status   # Enable/disable
│   ├── DELETE /users/{id}       # Delete user
│   ├── GET /audit-logs          # Audit logs
│   ├── GET /sessions            # All sessions
│   ├── POST /sessions/{id}/revoke # Revoke session
│   ├── GET /stats               # System statistics
│   ├── GET /health/detailed     # Detailed health
│   ├── POST /cache/clear        # Clear cache
│   ├── POST /queue/pause        # Pause queue
│   ├── POST /queue/resume       # Resume queue
│   └── GET /queue/status        # Queue status
│
└── /webhooks
    ├── GET /                    # List webhooks
    ├── POST /                   # Create webhook
    ├── GET /{id}                # Get webhook
    ├── PUT /{id}                # Update webhook
    ├── DELETE /{id}             # Delete webhook
    └── POST /{id}/test          # Test webhook
```

**Total Proposed Endpoints: 45**

### 3.2 Endpoint Consolidation Plan

#### Consolidation 1: Unified Search
**Merge:**
- `GET /api/v1/search/web`
- `GET /api/v1/search/orchestrate`
- `POST /api/v1/vector/search`
- `POST /api/v1/ai/ask`

**Into:**
- `POST /api/v1/search`

**Migration:**
- Keep old endpoints for 12 months
- Add deprecation headers: `Sunset: 2027-01-01`
- Return 301 redirect to new endpoint

#### Consolidation 2: User Management
**Merge:**
- `GET /api/v1/auth/me`
- `GET /api/v1/storage/settings`

**Into:**
- `GET /api/v1/users/profile`
- `GET /api/v1/users/preferences`

**Migration:**
- Keep `/auth/me` for backward compatibility
- Return 200 with new format

#### Consolidation 3: Document Management
**Rename:**
- `/api/v1/storage/documents` → `/api/v1/documents`
- `/api/v1/storage/settings` → `/api/v1/users/preferences`
- `/api/v1/storage/exports` → `/api/v1/documents/exports`

**Migration:**
- Add redirect middleware
- Update documentation

---

## Part 4: Security & Performance Standards

### 4.1 Authentication & Authorization

#### Authentication Levels
| Level | Description | Example Endpoints |
|-------|-------------|-------------------|
| **Public** | No authentication required | `/health`, `/auth/signup`, `/auth/login` |
| **Authenticated** | Valid JWT required | `/search`, `/documents`, `/ai/ask` |
| **Admin** | Admin role required | `/admin/*`, `/admin/users` |

#### Authorization Matrix
| Role | Permissions |
|------|-------------|
| **guest** | `search:read` |
| **user** | `search:read`, `documents:read`, `documents:write`, `profile:read`, `profile:write`, `notifications:read` |
| **admin** | `*` (all permissions) |

#### Rate Limiting Tiers
| Tier | Requests | Window | Endpoints |
|------|----------|--------|-----------|
| **Public** | 100 | 1 minute | Health, auth endpoints |
| **Authenticated** | 60 | 1 minute | Search, documents, AI |
| **Admin** | 30 | 1 minute | Admin endpoints |
| **Write** | 10 | 1 minute | Upload, delete, update |

### 4.2 Performance Targets

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Search latency (p50) | < 200ms | TBD | - |
| Search latency (p95) | < 500ms | TBD | - |
| Autocomplete latency | < 100ms | TBD | - |
| Cache hit ratio | > 80% | TBD | - |
| Database connections | 10-20 | TBD | - |
| API availability | 99.9% | TBD | - |

### 4.3 Caching Strategy

#### Cache Layers
1. **L1: In-memory** (per instance)
   - TTL: 60 seconds
   - Size: 1000 items
   - Use case: Frequent queries

2. **L2: Redis** (shared)
   - TTL: 5 minutes
   - Use case: Search results, AI responses

3. **L3: Database** (persistent)
   - Use case: User profiles, settings

#### Cache Keys
```python
CACHE_KEYS = {
    "user_profile": "user:{user_id}:profile",
    "search_results": "search:{query_hash}:{backend}",
    "ai_response": "ai:{prompt_hash}:{provider}",
    "suggestions": "suggestions:{query_prefix}",
}
```

### 4.4 Observability

#### Metrics to Track
- **Latency:** p50, p95, p99 per endpoint
- **Throughput:** Requests per second
- **Error Rate:** 4xx, 5xx percentages
- **Cache Hit Ratio:** Hits / total requests
- **Search Quality:** Click-through rate, dwell time
- **User Behavior:** Active users, session duration

#### Logging Standards
```python
{
    "timestamp": "2026-07-04T10:00:00Z",
    "level": "INFO",
    "request_id": "uuid",
    "method": "POST",
    "path": "/api/v1/search",
    "status": 200,
    "latency_ms": 234,
    "user_id": 123,
    "ip": "192.168.1.1",
    "user_agent": "...",
    "error": null
}
```

---

## Part 5: Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal:** Standardize and consolidate

- [ ] Implement unified search API (`POST /api/v1/search`)
- [ ] Standardize response format across all endpoints
- [ ] Add pagination to collection endpoints
- [ ] Implement cursor-based pagination
- [ ] Add filtering/sorting support

### Phase 2: Missing Domains (Week 3-4)
**Goal:** Add missing functionality

- [ ] Create `/api/v1/users` domain
- [ ] Create `/api/v1/notifications` domain
- [ ] Create `/api/v1/analytics` domain
- [ ] Create `/api/v1/recommendations` domain
- [ ] Rename `/storage` → `/documents`

### Phase 3: Enhanced Admin (Week 5)
**Goal:** Complete admin functionality

- [ ] Implement user management CRUD
- [ ] Add system statistics
- [ ] Add queue management
- [ ] Add cache management

### Phase 4: Documentation & Testing (Week 6)
**Goal:** Production readiness

- [ ] Generate OpenAPI 3.1 specification
- [ ] Write comprehensive tests (80% coverage)
- [ ] Create Postman collection (✅ Done)
- [ ] Performance testing
- [ ] Security audit

---

## Part 6: Success Criteria

### Must Have
- ✅ All endpoints documented in OpenAPI 3.1
- ✅ Response standardization implemented
- ✅ Pagination on all collection endpoints
- ✅ Unified search API
- ✅ User management domain
- ✅ 80% test coverage
- ✅ Rate limiting on all endpoints
- ✅ Audit logging on mutations

### Nice to Have
- Notifications domain
- Analytics domain
- Recommendations domain
- GraphQL API
- WebSocket support for streaming

### Out of Scope
- Mobile-specific APIs (use existing REST)
- GraphQL (add in v2)
- gRPC (add in v2)

---

## Part 7: Risk Assessment

### High Risk
1. **Breaking Changes** — Consolidating search endpoints may break existing clients
   - **Mitigation:** Keep old endpoints for 12 months with deprecation headers

2. **Performance** — Unified search may be slower than individual endpoints
   - **Mitigation:** Implement caching, async processing, connection pooling

### Medium Risk
3. **Data Migration** — Renaming `/storage` to `/documents`
   - **Mitigation:** Add redirect middleware, update clients gradually

4. **Test Coverage** — Current tests may not cover all edge cases
   - **Mitigation:** Write comprehensive tests before refactoring

### Low Risk
5. **Documentation** — Existing docs may be outdated
   - **Mitigation:** Generate OpenAPI spec from code, keep Postman collection updated

---

## Appendix A: API Dependency Map

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Gateway │ (Rate limiting, auth, SSL)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Load Balancer│
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│         FastAPI Application          │
│  ┌────────────────────────────────┐  │
│  │   Middleware Layer             │  │
│  │  - Security Headers            │  │
│  │  - Versioning                  │  │
│  │  - Response Standardization    │  │
│  │  - Rate Limiting               │  │
│  │  - Metrics                     │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │   Route Handlers               │  │
│  │  - Auth, Users, Search         │  │
│  │  - Documents, AI, Vector       │  │
│  │  - Admin, Analytics            │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │   Service Layer                │  │
│  │  - Auth, Search, AI            │  │
│  │  - Cache, Queue, Monitoring    │  │
│  └────────────────────────────────┘  │
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│         Data Layer                   │
│  ┌─────────┐  ┌─────────┐  ┌──────┐│
│  │PostgreSQL│  │  Redis  │  │ S3   ││
│  │  (Primary│  │ (Cache) │  │(File)││
│  │   DB)    │  │         │  │      ││
│  └─────────┘  └─────────┘  └──────┘│
└──────────────────────────────────────┘
```

## Appendix B: API Versioning Strategy

### Current Version: v1 (Stable)
- **Status:** Production-ready
- **Support:** 12 months from v2 release
- **Deprecation:** Sunset header added

### Next Version: v2 (Planned)
- **New Features:**
  - Unified search API
  - Standardized responses
  - Pagination/filtering
  - New domains (users, notifications, analytics)

### Versioning Rules
1. **Path-based:** `/api/v1/*`, `/api/v2/*`
2. **Header-based:** `X-API-Version: 2`
3. **Deprecation:** `Sunset: 2027-01-01`
4. **Migration:** 12-month overlap period
5. **Breaking changes:** Only in major versions

---

## Conclusion

The Nebula Search Engine has a solid foundation but needs consolidation and standardization to become production-ready at enterprise scale. The proposed architecture reduces complexity, improves maintainability, and adds missing functionality while maintaining backward compatibility.

**Next Steps:**
1. Review this document with stakeholders
2. Prioritize Phase 1 tasks
3. Toggle to Act mode to begin implementation