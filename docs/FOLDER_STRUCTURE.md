# Nebula Search v1.1 — Folder Structure

```
Nebula-search-engine-/
├── backend/
│   ├── app/                    # FastAPI application
│   │   ├── database/           # Engine, migrations, repositories
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── providers/
│   │   ├── routes/             # auth, search, ai, storage, vector
│   │   ├── search/
│   │   └── services/
│   ├── vector/                 # v1.1 vector indexing pipeline
│   │   ├── ingestion/          # pdf, txt, md, docx, html extractors
│   │   ├── chunking/
│   │   ├── embeddings/
│   │   ├── storage/
│   │   ├── retrieval/
│   │   ├── ranking/
│   │   ├── citations/
│   │   ├── pipeline/
│   │   └── worker.py           # Background indexing worker
│   └── test_helpers/           # E2E seed users, API helpers
├── frontend/                   # React + Vite PWA (preserved)
├── mobile/                     # Capacitor v1.1 shell
│   ├── android/
│   ├── ios/
│   ├── src/                    # auth, search, app shell
│   ├── plugins/                # camera, share, clipboard, etc.
│   ├── sync/                   # offline sync queue
│   ├── assets/
│   └── capacitor.config.ts
├── tests/
│   ├── e2e/                    # Playwright E2E (v1.1)
│   │   ├── auth/
│   │   ├── search/
│   │   ├── ai/
│   │   ├── offline/
│   │   ├── mobile/
│   │   ├── documents/
│   │   ├── errors/
│   │   ├── fixtures/
│   │   ├── utils/
│   │   ├── config/
│   │   └── playwright.config.ts
│   ├── test_vector.py
│   └── ...                     # Existing pytest suite
├── storage/
│   ├── uploads/
│   ├── vector/
│   ├── indexes/
│   ├── cache/
│   └── exports/
├── docker/
├── docs/
└── package.json                # Root scripts: e2e, vector, mobile
```
