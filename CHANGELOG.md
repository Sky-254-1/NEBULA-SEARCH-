# Changelog

All notable changes to Nebula Search will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-08-07

### Added

- **Enterprise SSO (SAML 2.0)** - Support for Azure AD, Okta, Auth0, Keycloak
- **WebAuthn Biometric Auth** - Production-grade FIDO2 verification
- **Push Notifications** - FCM/APNs backend routes + frontend registration + Android FCM token bridge
- **Federated Search** - Search across connected devices
- **Plugin System** - Search providers (Brave, Google, Bing, DuckDuckGo)
- **Document Preview** - Mobile WebView document preview routes
- **Native Mobile Apps** - Android (Kotlin) + iOS (Swift) apps
- **Desktop App** - Electron desktop wrapper
- **RBAC** - Full role-based access control with role hierarchy
- **Icon Assets** - desktop/mobile app icons
- **Push Token API Docs** - `/api/v1/notifications/push/*` documented in docs/API.md

### Changed

- **Dependencies** - Updated `eslint@10`, `react-syntax-highlighter@16`
- **Documentation** - README, ROADMAP, API docs, task_progress all updated to match current state
- **Test Setup** - Fixed ESM compatibility in vitest setup

### Fixed

- **SQLite Migration Compatibility** - `014_pgvector_postgres.sql` skipped on SQLite, `IF NOT EXISTS` stripped, `vector(1536)` mapped to `BLOB`
- **Backend Tests** - 923 passing
- **Frontend Tests** - 58 passing

### Security

- Dependency security updates (Dependabot alerts addressed)

---

## [1.1.0] - 2026-07-28

### Added

- **Vector Search Pipeline** - Complete document indexing with text extraction
  - Supports PDF, DOCX, HTML, TXT, MD, JSON, CSV
  - Automatic text chunking (800 chars, 200 overlap)
  - Content hash deduplication
- **Citation Tracking** - Source attribution for search results
  - Track which chunks were cited in answers
  - APA/MLA/Chicago citation formatting helpers
- **Hybrid Search API** - `/api/v1/vector/*` endpoints
  - Document indexing: `POST /api/v1/vector/documents/{id}/index-now`
  - Vector search: `POST /api/v1/vector/search`
  - Citation listing: `GET /api/v1/vector/citations`
  - Export vectors: `POST /api/v1/vector/export`
- **Document Upload UI** - React components for document management
- **Mobile Capacitor Shell** - iOS/Android support
  - Camera, Filesystem, Network, Preferences plugins
  - Voice recognition integration
- **Background Worker** - `vector/worker.py` for async document processing
- **Migration 002** - Add document_chunks, embeddings, citations, search_sessions tables
- **MFA Support** - TOTP-based multi-factor authentication with backup codes
- **Postgres Migration Parity** - All 12 migrations now support both SQLite and Postgres
- **Migration Idempotency** - `schema_migrations` tracking table prevents duplicate application
- **E2E Test Skip Guards** - Tests requiring external API keys now properly skip when keys are unset

### Changed

- **Search Orchestrator** - Improved result deduplication and ranking
- **AI Provider Router** - Better fallback logic for provider selection
- **Rate Limiting** - Path-specific rate limiting keys
- **Security Headers** - HSTS added for production environments
- **Migration Runner** - Now uses `schema_migrations` tracking table (standard Alembic-style pattern)
- **Postgres Migrations** - All `ALTER TABLE ADD COLUMN` use `IF NOT EXISTS`; all `CREATE INDEX` use `IF NOT EXISTS`

### Fixed

- **Security** - SQL injection in audit.py (placeholder substitution)
- **Session Management** - Session family revocation on logout
- **CORS Configuration** - Default localhost origins
- **Postgres Migration 003** - Missing MFA columns (`mfa_enabled`, `mfa_secret`, `mfa_backup_codes`) and auth columns now properly added
- **StopWordRemover** - `'StopWordRemover' object has no attribute 'remove'` crash in query pipeline (added missing `remove()` method)
- **npm Audit** - 5 moderate findings accepted as non-breaking (react-router SSR CVE does not apply to SPA; prismjs requires breaking upgrade)

### Security

- Added Content-Security-Policy headers
- Enhanced password policy enforcement
- Improved brute-force protection
- TOTP-based MFA with encrypted backup codes

---

## [1.0.0] - 2026-06-15

### Added

- **Backend API** - FastAPI with 7 routers, 41+ endpoints
- **Authentication** - JWT + refresh tokens with rotation
- **Search Backends** - Wikipedia, Brave Search, SerpAPI
- **AI Integration** - OpenAI, Ollama, GGUF, DuckDuckGo
- **Caching** - Redis + in-memory fallback
- **Docker Stack** - Full stack deployment (postgres, redis, backend, frontend)
- **Documentation** - 13 markdown files including API docs
- **Testing** - Pytest + Playwright E2E

### Security

- PBKDF2-SHA256 password hashing (200k iterations)
- Rate limiting with Redis
- Security headers middleware
- SQL injection prevention
- XSS protection via input validation

---

## [Unreleased] - v1.2.0 (Planned)

### Planned

- Biometric auth via `@capacitor-community/biometric`
- OpenAI embeddings as default
- FAISS or pgvector for large-scale vector storage
- E2E coverage gate at 95% in CI
- OAuth2 providers (Google, GitHub)

---

## Migration Guide

### v1.0 → v1.1

1. Apply database migration `002_add_vector_tables.sql`
2. Configure `REDIS_URL` for production (recommended)
3. Set `STORAGE_ROOT` environment variable
4. Run vector worker: `npm run vector:worker`

### v1.1 → v1.1.1

1. Run `python run_migrations.py` — the new `schema_migrations` tracking table ensures idempotent re-application
2. No breaking changes. All existing endpoints remain stable.

### Breaking Changes

None in v1.1 upgrade. All new features are additive.

---

## Deprecations

None currently. All existing endpoints remain stable.

---

*For support, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)*
