# Nebula Search — API Reference

Base URL: `http://localhost:8000` (dev) / `https://api.nebula.example.com` (prod)

All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

---

## Authentication (`/api/v1/auth`)

### POST `/api/v1/auth/signup`
Register a new account.

**Body**
```json
{ "email": "user@example.com", "password": "StrongPass1!" }
```
**Response** `201`
```json
{ "message": "User created successfully. Please check your email to verify your account." }
```

---

### POST `/api/v1/auth/login`
Authenticate and receive JWT tokens.

**Body**
```json
{ "email": "user@example.com", "password": "StrongPass1!" }
```
**Response** `200`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800
}
```
MFA enabled response `200`:
```json
{ "mfa_required": true, "mfa_pending_token": "...", "message": "MFA verification required" }
```

---

### POST `/api/v1/auth/refresh`
Rotate refresh token and get a new access token.

**Body**
```json
{ "refresh_token": "..." }
```
**Response** `200` — same shape as login.

---

### POST `/api/v1/auth/logout`
Revoke the current session.

**Body**
```json
{ "refresh_token": "..." }
```
**Response** `200`
```json
{ "message": "Logged out" }
```

---

### POST `/api/v1/auth/logout-all`
Revoke all sessions for the authenticated user. Requires auth header.

---

### GET `/api/v1/auth/me`
Return current user info. Requires auth.

**Response** `200`
```json
{ "email": "...", "role": "user", "email_verified": true, "created_at": "...", "last_login": "..." }
```

---

## Unified Search (`/api/v1/search`)

### POST `/api/v1/search/`
Unified search supporting web, vector, hybrid, and AI modes.

**Body**
```json
{
  "query": "machine learning",
  "mode": "hybrid",
  "page": 1,
  "limit": 20,
  "include_ai_answer": true,
  "include_suggestions": true,
  "spell_check": true,
  "include_highlights": true,
  "facets": ["source"],
  "filters": {
    "date_range": {"from": "2024-01-01", "to": "2024-12-31"},
    "document_type": ["pdf"],
    "tags": ["research"]
  }
}
```

`mode` values: `"web"` | `"vector"` | `"hybrid"` | `"ai"`

**Response** `200`
```json
{
  "query": "machine learning",
  "mode": "hybrid",
  "results": [
    {
      "id": 1,
      "title": "Machine learning",
      "snippet": "Machine learning (ML) is a field of AI...",
      "url": "https://en.wikipedia.org/wiki/Machine_learning",
      "source": "wikipedia",
      "score": 0.92,
      "highlights": [{"text": "machine learning", "start": 0, "end": 16}]
    }
  ],
  "ai_answer": {
    "answer": "Machine learning is...",
    "provider": "openai",
    "citations": []
  },
  "suggestions": ["machine learning tutorial", "machine learning python"],
  "facets": [{"field": "source", "value": "wikipedia", "count": 5}],
  "total": 10,
  "response_time_ms": 142.3
}
```

---

### GET `/api/v1/search/suggestions?q=<prefix>&limit=5`
Get search suggestions. Requires auth.

### GET `/api/v1/search/history?limit=20`
Get user's search history. Requires auth.

### DELETE `/api/v1/search/history`
Clear user's search history. Requires auth.

### POST `/api/v1/search/save?query=<q>&mode=<mode>`
Save a search query. Requires auth.

### GET `/api/v1/search/saved?limit=50`
List saved searches. Requires auth.

### DELETE `/api/v1/search/saved/{search_id}`
Delete a saved search. Requires auth.

---

## Enhanced Search v2 (`/api/v2/search`)

### GET `/api/v2/search/?q=<query>&backends=wikipedia&page=1&page_size=10`
Intelligent search with semantic reranking, spell correction, personalization. Requires auth.

Additional params: `enable_semantic`, `enable_personalization`, `enable_spell_check`, `enable_diversity`

### GET `/api/v2/search/autocomplete?q=<prefix>&limit=10`
Fast autocomplete completions.

### GET `/api/v2/search/suggest?q=<prefix>&limit=10`
Rich suggestions (history + trending + spell). Requires auth.

### GET `/api/v2/search/spell-check?q=<query>`
Spell check a query.

### GET `/api/v2/search/trending?limit=10&hours=24`
Get trending queries.

### GET `/api/v2/search/popular?limit=10`
Get most popular queries.

### POST `/api/v2/search/click?query=<q>&position=<n>&url=<url>`
Log a click event for analytics and personalisation. Requires auth.

### GET `/api/v2/search/profile`
Get user's search profile and recent searches. Requires auth.

### GET `/api/v2/search/analytics?query=<q>`
Get CTR and analytics for a query or overall stats.

### GET `/api/v2/search/semantic?q=<query>&top_k=10&threshold=0.5`
Pure semantic (embedding) search. Requires auth.

---

## Documents (`/api/v1/documents`)

### GET `/api/v1/documents/?page=1&page_size=20`
List user's documents with pagination. Requires auth.

**Response** `200`
```json
{
  "documents": [
    { "id": 1, "filename": "report.pdf", "content_type": "application/pdf", "created_at": "...", "indexed_at": "..." }
  ],
  "pagination": { "total": 42, "page": 1, "page_size": 20, "total_pages": 3, "has_next": true, "has_previous": false }
}
```

### POST `/api/v1/documents/`
Upload a document for indexing. Requires auth.

**Body** `multipart/form-data` — field `file`

Allowed types: `.txt .md .json .csv .pdf .html .htm .docx`
Max size: 10 MB

**Response** `200`
```json
{ "id": 42, "filename": "paper.pdf", "content_type": "application/pdf", "created_at": "..." }
```

### DELETE `/api/v1/documents/{doc_id}`
Delete a document and its indexed data. Requires auth.

---

## Vector Search (`/api/v1/vector`)

### POST `/api/v1/vector/search`
Semantic vector search over indexed documents. Requires auth.

**Body**
```json
{ "query": "transformer architecture", "top_k": 10, "filters": {} }
```

### POST `/api/v1/vector/ask`
RAG question answering over indexed documents. Requires auth.

**Body**
```json
{ "query": "What is attention mechanism?", "top_k": 5 }
```

**Response**
```json
{
  "query": "...",
  "answer": "...",
  "citations": [{ "id": 1, "filename": "paper.pdf", "snippet": "...", "score": 0.94 }],
  "sources": ["paper.pdf"]
}
```

### GET `/api/v1/vector/status`
List indexed documents and their status. Requires auth.

### POST `/api/v1/vector/reindex/{doc_id}`
Trigger reindexing of a specific document. Requires auth.

### GET `/api/v1/vector/stats`
Vector store statistics. Requires auth.

### GET `/api/v1/vector/citations`
Get citation history. Requires auth.

### GET `/api/v1/vector/export`
Export citation data as CSV. Requires auth.

---

## AI (`/api/v1/ai`)

### POST `/api/v1/ai/ask`
Ask a question to the AI provider.

**Body**
```json
{ "prompt": "Explain quantum computing in simple terms." }
```

### POST `/api/v1/ai/synthesize`
Synthesise an answer from search snippets.

**Body**
```json
{ "query": "...", "snippets": ["snippet1", "snippet2"] }
```

### GET `/api/v1/ai/history`
Get AI chat history. Requires auth.

### DELETE `/api/v1/ai/history`
Clear AI chat history. Requires auth.

---

## Analytics (`/api/v1/analytics`)

### GET `/api/v1/analytics/usage`
Usage statistics. Requires auth.

### GET `/api/v1/analytics/search?days=30`
Search analytics. Requires admin.

### GET `/api/v1/analytics/performance?days=7`
Performance metrics. Requires admin.

### GET `/api/v1/analytics/export`
Export analytics as CSV. Requires admin.

---


## GraphQL API (`/graphql`)

### POST `/graphql/`
GraphQL endpoint for querying search, AI, history, and suggestions.

**Example Query**
```graphql
query Search($input: SearchInput!) {
  search(input: $input) {
    query
    total
    documents {
      id
      title
      content
      url
      source
      score
    }
  }
}
```

**Available Queries**
- `search(input: SearchInput!)` - Search documents
- `search_history(user_id: String, limit: Int)` - Get search history
- `ai_search(query: String!, context: JSON)` - AI-enhanced search
- `suggest(query: String!, limit: Int)` - Get suggestions
- `knowledge_graph(input: GraphQueryInput!)` - Knowledge graph queries
- `facets(query: String!, field: String!, limit: Int)` - Get facets

**Available Mutations**
- `save_search(query: String!, results_count: Int!, user_id: String)` - Save search
- `clear_search_history(user_id: String)` - Clear history

### GET `/graphql/schema`
Get GraphQL schema as JSON.

### GET `/graphql/playground`
GraphQL playground (disabled in production).

---

## Health

### GET `/health`
Basic health check.

**Response** `200`
```json
{ "status": "ok", "version": "1.1.0" }
```

### GET `/health/detailed`
Detailed health including DB and Redis status.

### GET `/metrics`
Prometheus metrics endpoint.

---


## Push Notifications (`/api/v1/notifications/push`)

### POST `/api/v1/notifications/push/register`
Register a push notification token. Requires auth.

**Body**
```json
{ "token": "fcm_token_or_apns_token", "platform": "android", "device_id": "optional-device-id" }
```

**Response** `200`
```json
{ "message": "Push token registered" }
```

### DELETE `/api/v1/notifications/push/unregister`
Unregister push notification token. Requires auth.

**Response** `200`
```json
{ "message": "Push token unregistered" }
```

### GET `/api/v1/notifications/push/status`
Get push notification registration status. Requires auth.

**Response** `200`
```json
{ "enabled": true, "registered": true, "platform": "android", "updated_at": "2025-01-01T00:00:00Z" }
```

---

## Error Responses

All errors follow this shape:
```json
{ "detail": "Human-readable error message" }
```

| Code | Meaning |
|------|---------|
| 400  | Bad request / validation error |
| 401  | Unauthenticated |
| 403  | Forbidden (insufficient role/permission) |
| 404  | Resource not found |
| 409  | Conflict (e.g. duplicate email) |
| 413  | Payload too large |
| 422  | Unprocessable entity (request schema mismatch) |
| 423  | Account locked (brute-force protection) |
| 429  | Rate limit exceeded |
| 500  | Internal server error |

---

## Rate Limits

| Endpoint category | Limit |
|-------------------|-------|
| Signup | 5 req/min per IP |
| Login | 5 req/min per IP |
| Token refresh | 10 req/min per IP |
| Search | 60 req/min per user |
| Document upload | 60 req/min per user |
| AI ask | 60 req/min per user |

After 5 failed logins the account is locked for 15 minutes.

---

## Authentication Flow

```
POST /signup  →  201  (email verification sent)
POST /login   →  200  access_token + refresh_token
              OR 200  mfa_required=true + mfa_pending_token
POST /mfa/verify  →  200  access_token + refresh_token  (if MFA enabled)

GET  /protected  →  Authorization: Bearer <access_token>

POST /refresh  →  200  new access_token + rotated refresh_token
POST /logout   →  200  session revoked
```
