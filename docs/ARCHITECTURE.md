# Nebula Search — Architecture

## Overview

Nebula Search is a privacy-first hybrid search platform with a vanilla JavaScript frontend and a FastAPI backend. The frontend runs primarily in the browser with IndexedDB for offline storage; the backend provides authenticated web search, AI answers, and search logging.

## Layers

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Frontend | HTML, CSS, JS, IndexedDB, PWA | UI, offline search, local history |
| API | FastAPI | Auth, web search proxy, AI synthesis |
| Storage | SQLite (dev), PostgreSQL (planned) | Users, search logs |
| External | Wikipedia, Brave, SerpAPI, OpenAI, DuckDuckGo | Search and AI providers |

## Backend Module Layout

```
backend/app/
├── main.py           # App factory, middleware, error handlers
├── config.py         # Environment settings
├── database.py       # SQLite schema and connection
├── models/schemas.py # Pydantic request/response models
├── routes/           # HTTP endpoints (auth, search, ai, health)
├── services/         # Business logic (auth, search, ai)
└── middleware/       # Rate limiting, security headers
```

## Request Flow

1. Client sends JWT in `Authorization: Bearer <token>` header.
2. `get_current_user` validates the token.
3. Route handler delegates to a service module.
4. Service calls external APIs with sanitized, URL-encoded queries.
5. Results are logged (when authenticated) and returned as JSON.

## Security Model

- Passwords hashed with PBKDF2-SHA256 (200k iterations).
- JWT signed with HS256; secret required in production.
- CORS restricted via `CORS_ORIGINS` environment variable.
- Rate limiting per IP (in-memory; Redis planned).
- Security headers on all responses.

## Deployment

See [SETUP.md](SETUP.md) and [../docker/docker-compose.yml](../docker/docker-compose.yml).
