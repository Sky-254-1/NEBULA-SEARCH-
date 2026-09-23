# Nebula Search — Roadmap

## ✅ Completed (v1.0)

- [x] FastAPI backend with JWT auth
- [x] Wikipedia, Brave, SerpAPI search backends
- [x] AI answers (OpenAI + DuckDuckGo fallback)
- [x] Search result synthesis
- [x] Modular backend architecture
- [x] Docker deployment stack
- [x] Automated test suite
- [x] Security headers and CORS configuration

## ✅ Completed (v1.1)

- [x] Frontend-backend auth integration (React 18 + Vite SPA)
- [x] PostgreSQL support for production databases (Postgres 16, async ORM)
- [x] Redis-backed rate limiting and caching (Redis 7)
- [x] Vector search pipeline (indexing, chunking, embeddings, citations)
- [x] Hybrid search engine (BM25 + semantic fusion)
- [x] Background worker + scheduler for indexing jobs
- [x] Mobile app shell (Capacitor — Android/iOS)
- [x] Service worker and PWA manifest as standalone files
- [x] Split frontend into modular TS/TSX components
- [x] MFA (TOTP), OAuth2 providers, RBAC
- [x] Incremental re-indexing system
- [x] Document upload + RAG (PDF, DOCX, HTML, TXT, MD, JSON, CSV)
- [x] Advanced search features: autocomplete, spell correction, suggestions, analytics

## ✅ Completed (v1.2 — Production Hardening)

- [x] Fixed `_track_search_analytics` bug (get_db generator misuse → connect() direct call)
- [x] Implemented scheduler stubs: nightly reindex, weekly optimisation, scan missing documents
- [x] Implemented metadata sync stubs: `_update_search_index` and `_update_vector_metadata` with real DB writes
- [x] Fixed SearchPage.tsx rendering bug (VectorSearchResult fields vs web result fields)
- [x] Wired `getTrending` / `getPopular` frontend stubs to live backend endpoints
- [x] Implemented full `RBACService` with role hierarchy, permission map, and FastAPI dependency factories
- [x] Replaced placeholder `require_permission` with role-to-permission map (no JWT payload pollution)
- [x] Raised CI coverage threshold: 35% → 85% (backend) and added 85% threshold to vitest
- [x] Lowered mypy error ceiling: 240 → 150
- [x] Added frontend coverage reporting (lcov → Codecov)
- [x] Docker Compose: healthchecks on worker, scheduler, frontend, nginx; scheduler depends on redis
- [x] Worker and scheduler standalone process entrypoints (`worker_entrypoint.py`, `scheduler_entrypoint.py`)
- [x] E2E test suite: auth flow, search flow, document lifecycle (backend/tests/e2e/)
- [x] New backend tests: `test_search_unified.py`, `test_config.py`, `test_documents_routes.py`
- [x] New frontend component tests: SearchPage, AIChatPage, DashboardPage, DocumentsPage, AnalyticsPage
- [x] Full API documentation at `docs/API.md`

## ✅ Completed (v1.2.1)

- [x] SQLite migration compatibility for `014_pgvector_postgres.sql`
- [x] Icon assets for desktop/mobile (`desktop/assets/icon.png`, `desktop/assets/icon.ico`)
- [x] Firebase/APNs push token registration bridge (frontend `AuthContext` + Android FCM token bridge)
- [x] Docker Compose stack validated

## ✅ Completed (v1.3)

- [x] OpenAI embeddings as default — prefers `text-embedding-3-small` when `OPENAI_API_KEY` is set, falls back to sentence-transformers then local-hash
- [x] pgvector for large-scale vector storage — `vector/storage/pgvector_store.py` with cosine similarity search; graceful SQLite fallback for local dev
- [x] Mobile biometric auth — `@capacitor-community/biometric` integrated in `mobile/src/auth.ts`; Face ID / Touch ID on iOS, fingerprint on Android
- [x] Voice search — `@capacitor-community/speech-recognition` wired in mobile shell
- [x] E2E coverage gate — 20-test suite (auth, documents, search); CI job in `.github/workflows/e2e.yml`
- [x] pytest scoped to `backend/tests` — removed `../tests` path conflict, excluded `.txt` artifacts
- [x] Push notification backend (FCM/APNs) — `backend/app/routes/push.py` + frontend registration in SettingsPage
- [x] Document preview in mobile WebView — `backend/app/routes/preview.py`
- [x] Federated search across devices — `backend/app/routes/federated.py` + device management in SettingsPage
- [x] Plugin system for search providers — `backend/app/plugins/` with Brave, Google, Bing, DuckDuckGo
- [x] Enterprise SSO (SAML 2.0) — `backend/app/routes/saml.py` + "Sign in with Enterprise SSO" button on LoginPage
- [x] WebAuthn biometric login — `backend/app/routes/webauthn.py` + biometric button on LoginPage

## In Progress (Release Engineering)

- [ ] Push to origin/main — security fixes pending publication
- [ ] Enable GitHub branch protection with required CI status checks
- [ ] Resolve Dependabot alerts (`eslint@10`, `vitest@4`, `react-syntax-highlighter@16`)
- [ ] Live staging deployment + full release checklist

## Planned (v1.4)

- [ ] Playwright E2E coverage gate at 95% in CI
- [ ] On-device ONNX / local LLM inference
- [ ] Multi-tenant workspace support
- [ ] Advanced analytics dashboard (retention, funnel, heatmaps)
- [ ] Webhook delivery retries with exponential backoff UI

## Non-Goals

- Replacing the Nebula brand or core UI vision
- Removing existing offline-first frontend capabilities
