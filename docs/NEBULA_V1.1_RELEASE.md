# Nebula Search Engine v1.1 — Release Package

**Version:** 1.1.0  
**Date:** July 1, 2026  
**Status:** Production-ready extension of v1.0 MVP

---

## Success Condition

```
Search → AI → Documents → Offline → Mobile → Production
```

All layers are implemented and validated. v1.0 systems are preserved; v1.1 extends only.

---

## 1. Folder Structure

```
Nebula-search-engine-/
├── backend/
│   ├── app/                    # FastAPI (auth, search, AI, storage, vector routes)
│   ├── vector/
│   │   ├── ingestion/          # PDF, DOCX, HTML, TXT, MD parsing
│   │   ├── chunking/           # Semantic chunks with overlap
│   │   ├── embeddings/         # Local hash + OpenAI provider abstraction
│   │   ├── storage/            # Vector file paths
│   │   ├── retrieval/          # Hybrid vector + keyword retrieval
│   │   ├── ranking/            # Score reranking
│   │   ├── citations/          # Evidence tracking
│   │   ├── pipeline/           # Full ingest → embed → store pipeline
│   │   └── worker.py           # Background indexing worker
│   └── test_helpers/           # API client + seed utilities for E2E
├── frontend/                   # React + Vite PWA
├── mobile/
│   ├── android/                # Android shell (Capacitor)
│   ├── ios/                    # iOS shell (Capacitor)
│   ├── src/                    # Auth, search, app shell
│   ├── plugins/                # Camera, share, network, clipboard
│   ├── sync/                   # Offline queue → reconnect → merge
│   └── capacitor.config.ts
├── storage/
│   ├── uploads/                # User document uploads
│   ├── vector/                 # Embedding JSON files (runtime)
│   ├── vectors/                # Alias directory (reserved)
│   ├── indexes/                # Per-user index manifests
│   ├── cache/                  # Transient cache
│   └── exports/                # Vector/data exports
├── tests/
│   └── e2e/
│       ├── auth/               # login, signup, logout, token refresh, expired sessions
│       ├── search/             # query, pagination, filters, empty state, retries
│       ├── ai/                 # ask, stream, conversation restore, disconnect recovery
│       ├── offline/            # PWA install, offline mode, reconnect
│       ├── documents/          # upload, index, vector search, summarize
│       ├── mobile/             # viewport, gestures, responsive
│       ├── errors/             # server failures, timeout recovery
│       ├── fixtures/           # auth + test context
│       ├── utils/              # helpers + storage
│       ├── config/             # env + global setup
│       └── playwright.config.ts
├── docker/                     # Existing Docker setup (preserved)
├── docs/                       # API, deployment, mobile, integration
└── .github/workflows/ci.yml    # Python tests + frontend build + E2E
```

---

## 2. Implementation Roadmap (Sprints)

| Sprint | Focus | Status |
|--------|-------|--------|
| 1 | Playwright E2E automation | ✅ Complete |
| 2 | Vector document indexing | ✅ Complete |
| 3 | Document search + RAG ask | ✅ Complete |
| 4 | Capacitor mobile shell | ✅ Complete |
| 5 | Optimization + CI hardening | ✅ Complete |

---

## 3. Database Migrations

| Migration | Scope |
|-----------|-------|
| `001_*.sql` | Core users, sessions, documents, search history |
| `002_*.sql` | **v1.1** — `chunks`, `embeddings`, `citations`, `search_sessions`; document status columns |
| `003_*.sql` | Security RBAC, audit logs, session rotation |

Run automatically on startup via `init_db()`. For manual migration:

```bash
cd backend
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"
```

---

## 4. APIs (v1.1 additions)

### Vector pipeline

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/storage/documents` | Upload → auto-queue index |
| `GET /api/v1/vector/documents/{id}/status` | Index lifecycle status |
| `POST /api/v1/vector/documents/{id}/index-now` | Sync index |
| `POST /api/v1/vector/search` | Hybrid retrieval |
| `POST /api/v1/vector/ask` | **RAG answer + citations + sources** |
| `GET /api/v1/vector/citations` | Citation history |
| `POST /api/v1/vector/export` | Export chunks |

Full reference: [docs/API_V1.1.md](./API_V1.1.md)

### Indexing lifecycle

```
Upload → Parse → Chunk → Embed → Store → Retrieve → Rank → Generate
         │        │       │        │         │        │        │
    ingestion  chunking embeddings storage retrieval ranking  /vector/ask
```

---

## 5. Integration Steps

### Local development

```bash
# Backend
cd backend && pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Vector worker (optional, Redis or in-process queue)
npm run vector:worker

# E2E
npm install && npm run e2e:install && npm run e2e
```

### Mobile

```bash
cd frontend && npm run build
cd mobile && npm install && npm run sync
npm run mobile:android   # or mobile:ios
```

### Environment variables

```env
JWT_SECRET=your-secret
DATABASE_URL=nebula.db
OPENAI_API_KEY=           # optional — enables OpenAI embeddings + AI
REDIS_URL=                # optional — persistent job queue
STORAGE_ROOT=../storage
```

---

## 6. Tests

### E2E commands

| Command | Purpose |
|---------|---------|
| `npm run e2e` | Full suite (parallel, CI retries) |
| `npm run e2e:ui` | Playwright UI mode |
| `npm run e2e:headed` | Headed browser |
| `npm run e2e:report` | HTML report |

### Coverage areas

- **Auth:** login, signup, logout, token refresh, expired sessions
- **Search:** query, pagination, filters, empty state, retries
- **AI:** ask, stream, conversation restore, disconnect recovery
- **PWA:** install prompt, offline, reconnect
- **Documents:** upload, index, vector search, summarize with citations
- **Mobile:** viewport, gestures, responsive (phone + tablet projects)
- **Errors:** 401/404/502, network interruption, timeout recovery

### Outputs

- HTML report: `tests/e2e/playwright-report/`
- Screenshots: on failure
- Trace: on failure
- Video: on failure

### Retry strategy

- Local: 0 retries
- CI: 2 retries, 4 workers, `forbidOnly` enabled

---

## 7. Deployment

Existing Docker and K8s configs preserved under `docker/` and `infrastructure/k8s/`.

### Production checklist

1. Set `JWT_SECRET`, `APP_ENV=production`
2. Use PostgreSQL (`DATABASE_URL=postgresql://...`)
3. Enable Redis for job queue (`REDIS_URL=...`)
4. Run vector worker as separate process or K8s deployment
5. Mount persistent volume at `STORAGE_ROOT`
6. Run E2E against staging before promote

See [docs/DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 8. Release Checklist

- [x] v1.0 FastAPI backend preserved
- [x] JWT auth + refresh preserved
- [x] Search + AI routes preserved
- [x] Docker docs preserved
- [x] Playwright E2E suite with CI
- [x] Vector pipeline (ingest → chunk → embed → store)
- [x] Hybrid search + citations
- [x] `/vector/ask` RAG endpoint
- [x] Capacitor mobile shell (Android + iOS)
- [x] Offline sync queue
- [x] Storage directory layout
- [x] Migration 002 applied
- [x] API documentation updated

### Mobile release (APK)

```bash
cd frontend && npm run build
cd mobile && npm install && npx cap sync
cd android && ./gradlew assembleDebug
# APK: mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

### Store packaging

1. Generate signed release keystore (Android) / provisioning profile (iOS)
2. Update `appId` in `mobile/capacitor.config.ts` if needed
3. Build release APK/AAB or Xcode archive
4. Submit with PWA-equivalent privacy policy

See [docs/MOBILE.md](./MOBILE.md)

---

## Critical Fix Applied (v1.1.0)

Removed stub modules `backend/vector/pipeline.py` and `backend/vector/citations.py` that shadowed the full package implementations. The production pipeline now uses:

- `backend/vector/pipeline/__init__.py` — full ingest/chunk/embed/hybrid search
- `backend/vector/citations/__init__.py` — citation tracking

---

## End State

**Nebula Search Engine v1.1** — Reliable, tested, semantic, offline-capable, mobile-ready, production-ready.
