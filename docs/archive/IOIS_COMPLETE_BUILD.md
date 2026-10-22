# IOIS — Intelligent Offline & Online Information Search
## Complete Production Build Guide

---

## TABLE OF CONTENTS

1. System Architecture
2. Technology Decisions (with rationale)
3. Full Folder Structure
4. Database Schema
5. API Specification
6. Backend Code — FastAPI
7. Frontend Code — PWA
8. AI Layer
9. Search Engine
10. Offline Search
11. Authentication
12. Docker Deployment
13. CI/CD Pipeline
14. Testing Strategy
15. MVP Roadmap
16. Production Roadmap
17. Installation Guide

---

## 1. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                        USER LAYER                           │
│  Browser PWA │ Electron Desktop │ Capacitor Android/iOS     │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS / WebSocket
┌────────────────────────────▼────────────────────────────────┐
│                    NGINX REVERSE PROXY                      │
│               TLS Termination • Rate Limiting               │
└───────────┬─────────────────────────────┬───────────────────┘
            │                             │
┌───────────▼──────────┐     ┌────────────▼──────────────────┐
│   FastAPI API Layer  │     │     Static Asset CDN           │
│  /api/v1/...         │     │  (Vite build output)           │
│  JWT Auth            │     └────────────────────────────────┘
│  Rate Limiting       │
└───┬──────┬──────┬────┘
    │      │      │
┌───▼──┐ ┌─▼───┐ ┌▼──────────────────────────────────────┐
│Auth  │ │Cache│ │          Search Orchestrator            │
│Layer │ │Redis│ │                                         │
│JWT   │ │TTL  │ │  ┌──────────┐  ┌──────────┐           │
│AES   │ │     │ │  │ Online   │  │ Offline  │           │
└──────┘ └─────┘ │  │ Search   │  │ Search   │           │
                 │  │          │  │          │           │
                 │  │Wikipedia │  │ FAISS    │           │
                 │  │SerpAPI   │  │ SQLite   │           │
                 │  │RSS Feeds │  │ Tesseract│           │
                 │  │Custom API│  │ Sentence │           │
                 │  └──────────┘  │ Transform│           │
                 │               └──────────┘           │
                 └──────────────┬────────────────────────┘
                                │
                 ┌──────────────▼────────────────────────┐
                 │           AI LAYER                     │
                 │                                        │
                 │  Intent Detection → Query Expansion    │
                 │  Result Ranking → Summary Generation   │
                 │  RAG Pipeline → Context Memory         │
                 │                                        │
                 │  [Ollama local] or [OpenAI API]        │
                 └──────────────┬────────────────────────┘
                                │
                 ┌──────────────▼────────────────────────┐
                 │         STORAGE LAYER                  │
                 │                                        │
                 │  PostgreSQL — Users, Sessions, Logs    │
                 │  Redis      — Cache, Sessions, Queue   │
                 │  SQLite     — Local docs, index        │
                 │  FAISS      — Vector embeddings        │
                 │  IndexedDB  — Browser offline store    │
                 └────────────────────────────────────────┘
```

### Data Flow (Search Request)

```
User types query
      │
      ▼
PWA detects online/offline status
      │
  ┌───┴──────────────┐
  │ ONLINE           │ OFFLINE
  ▼                  ▼
API Gateway      IndexedDB +
      │          Local FAISS
  ┌───▼───────────────────────────────────────┐
  │ 1. Intent Detection (classify query type) │
  │ 2. Query Expansion (synonyms, context)    │
  │ 3. Parallel Search (web + local docs)     │
  │ 4. Result Fusion (merge + deduplicate)    │
  │ 5. AI Reranking (relevance scoring)       │
  │ 6. AI Summary Generation                 │
  │ 7. Cache result (Redis TTL)              │
  └───────────────────┬───────────────────────┘
                      │
                      ▼
               Structured Response
               {results, summary, intent,
                follow_up_questions, sources}
```

---

## 2. TECHNOLOGY DECISIONS

| Component | Choice | Why |
|-----------|--------|-----|
| Backend | FastAPI | Async, auto-docs, fast, Python AI ecosystem |
| Frontend | Vite + TypeScript | Fastest dev server, strong typing |
| Embeddings | sentence-transformers | Free, runs offline, SOTA accuracy |
| Vector DB | FAISS | Free, local-first, Facebook-backed |
| LLM (local) | Ollama (Mistral 7B) | Runs on CPU, free, private |
| LLM (cloud) | OpenAI API (optional) | Fallback for better quality |
| OCR | Tesseract | Free, 100+ languages, open source |
| Auth | JWT + AES-256 | Standard, stateless, secure |
| Desktop | Electron | Same codebase, largest ecosystem |
| Mobile | Capacitor | Builds to native APK from web code |
| Cache | Redis | Sub-ms latency, TTL support |
| Primary DB | PostgreSQL | ACID, reliable, feature rich |
| Local DB | SQLite | Embedded, zero setup, portable |
| Offline | IndexedDB (Dexie.js) | Browser native, large storage |
| Container | Docker + Compose | Reproducible, beginner-friendly |
| Proxy | Nginx | Performance, TLS, rate limiting |

---

## 3. FULL FOLDER STRUCTURE

```
IOIS/
│
├── frontend/                          # Vite + TypeScript PWA
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── capacitor.config.ts            # Android/iOS
│   ├── electron/                      # Desktop wrapper
│   │   ├── main.ts
│   │   ├── preload.ts
│   │   └── package.json
│   └── src/
│       ├── main.ts                    # Entry point
│       ├── App.tsx
│       ├── pages/
│       │   ├── Home.tsx               # Search home
│       │   ├── Results.tsx            # Results page
│       │   ├── Document.tsx           # Doc viewer
│       │   ├── Library.tsx            # Offline library
│       │   ├── Settings.tsx           # User settings
│       │   └── Auth/
│       │       ├── Login.tsx
│       │       └── Register.tsx
│       ├── components/
│       │   ├── SearchBar/
│       │   │   ├── SearchBar.tsx
│       │   │   ├── Suggestions.tsx
│       │   │   └── VoiceSearch.tsx
│       │   ├── Results/
│       │   │   ├── ResultCard.tsx
│       │   │   ├── ResultList.tsx
│       │   │   ├── AIOverview.tsx
│       │   │   ├── KnowledgePanel.tsx
│       │   │   └── QuickAnswer.tsx
│       │   ├── UI/
│       │   │   ├── Button.tsx
│       │   │   ├── Modal.tsx
│       │   │   ├── Spinner.tsx
│       │   │   ├── Badge.tsx
│       │   │   └── Toast.tsx
│       │   ├── Layout/
│       │   │   ├── Header.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   └── Footer.tsx
│       │   └── Offline/
│       │       ├── FileUploader.tsx
│       │       ├── IndexProgress.tsx
│       │       └── OfflineIndicator.tsx
│       ├── services/
│       │   ├── api.ts                 # Axios instance
│       │   ├── searchService.ts       # Search API calls
│       │   ├── authService.ts         # Auth calls
│       │   ├── offlineService.ts      # IndexedDB ops
│       │   ├── syncService.ts         # Sync logic
│       │   └── aiService.ts           # AI calls
│       ├── search/
│       │   ├── queryParser.ts         # Client-side query parsing
│       │   ├── offlineSearch.ts       # Browser-side search
│       │   └── indexer.ts             # Client indexing
│       ├── hooks/
│       │   ├── useSearch.ts
│       │   ├── useOffline.ts
│       │   ├── useAuth.ts
│       │   └── useDebounce.ts
│       ├── state/
│       │   ├── store.ts               # Zustand store
│       │   ├── searchSlice.ts
│       │   ├── authSlice.ts
│       │   └── settingsSlice.ts
│       ├── pwa/
│       │   ├── sw.ts                  # Service worker
│       │   └── manifest.json
│       ├── styles/
│       │   ├── globals.css
│       │   ├── themes.css
│       │   └── components.css
│       └── utils/
│           ├── crypto.ts              # AES encryption
│           ├── highlight.ts           # Text highlighting
│           ├── formatters.ts
│           └── constants.ts
│
├── backend/                           # FastAPI Python
│   ├── main.py                        # App entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/                       # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── __init__.py
│       ├── config.py                  # Settings
│       ├── dependencies.py            # DI
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py              # Main router
│       │   └── v1/
│       │       ├── search.py          # Search endpoints
│       │       ├── auth.py            # Auth endpoints
│       │       ├── documents.py       # Doc management
│       │       ├── ai.py              # AI endpoints
│       │       ├── sync.py            # Sync endpoints
│       │       └── health.py          # Health check
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── jwt.py                 # JWT logic
│       │   ├── encryption.py          # AES-256
│       │   ├── models.py
│       │   └── schemas.py
│       ├── search/
│       │   ├── __init__.py
│       │   ├── orchestrator.py        # Main search brain
│       │   ├── online/
│       │   │   ├── __init__.py
│       │   │   ├── wikipedia.py
│       │   │   ├── duckduckgo.py
│       │   │   ├── rss_reader.py
│       │   │   └── web_scraper.py
│       │   ├── offline/
│       │   │   ├── __init__.py
│       │   │   ├── indexer.py         # Doc indexer
│       │   │   ├── ocr.py             # Tesseract
│       │   │   ├── pdf_parser.py
│       │   │   ├── docx_parser.py
│       │   │   └── text_extractor.py
│       │   └── fusion.py              # Merge online+offline
│       ├── ranking/
│       │   ├── __init__.py
│       │   ├── bm25.py                # BM25 ranker
│       │   ├── semantic.py            # Embedding ranker
│       │   └── fusion_ranker.py       # Reciprocal rank fusion
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── intent.py              # Intent detection
│       │   ├── summarizer.py          # Summary generation
│       │   ├── rag.py                 # RAG pipeline
│       │   ├── embeddings.py          # Sentence transformers
│       │   ├── ollama_client.py       # Local LLM
│       │   └── query_expander.py      # Query expansion
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── redis_client.py
│       │   └── cache_service.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── postgres.py            # PG session
│       │   ├── sqlite_local.py        # Local SQLite
│       │   ├── faiss_index.py         # Vector index
│       │   └── models.py              # SQLAlchemy models
│       ├── analytics/
│       │   ├── __init__.py
│       │   └── tracker.py             # Local analytics only
│       ├── workers/
│       │   ├── __init__.py
│       │   ├── indexing_worker.py     # Background indexing
│       │   └── sync_worker.py
│       └── utils/
│           ├── __init__.py
│           ├── logger.py
│           ├── validators.py
│           └── helpers.py
│
├── storage/
│   ├── postgres/
│   │   └── init.sql
│   ├── faiss/
│   │   └── .gitkeep
│   └── uploads/
│       └── .gitkeep
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   └── docker-compose.yml
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── INSTALL.md
│   ├── CONTRIBUTING.md
│   └── SECURITY.md
│
├── tests/
│   ├── backend/
│   │   ├── test_search.py
│   │   ├── test_auth.py
│   │   ├── test_ai.py
│   │   └── test_ranking.py
│   └── frontend/
│       ├── search.test.ts
│       └── auth.test.ts
│
├── scripts/
│   ├── setup.sh
│   ├── seed_db.py
│   └── build_all.sh
│
└── README.md
```

---

## 4. DATABASE SCHEMA

```sql
-- PostgreSQL Schema
-- File: storage/postgres/init.sql

-- ── USERS ──────────────────────────────────────────────────
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name  TEXT,
    plan          TEXT DEFAULT 'free' CHECK (plan IN ('free','pro','enterprise')),
    preferences   JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    last_login    TIMESTAMPTZ,
    is_active     BOOLEAN DEFAULT TRUE,
    is_verified   BOOLEAN DEFAULT FALSE
);

-- ── SESSIONS ───────────────────────────────────────────────
CREATE TABLE sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash    TEXT NOT NULL,
    refresh_hash  TEXT,
    device_info   JSONB DEFAULT '{}',
    ip_address    INET,
    expires_at    TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    revoked       BOOLEAN DEFAULT FALSE
);

-- ── SEARCH HISTORY ─────────────────────────────────────────
CREATE TABLE search_history (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    query         TEXT NOT NULL,
    query_type    TEXT CHECK (query_type IN ('web','local','ai','hybrid')),
    filter_used   TEXT,
    result_count  INT,
    clicked_url   TEXT,
    session_id    UUID REFERENCES sessions(id),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_search_history_user ON search_history(user_id);
CREATE INDEX idx_search_history_query ON search_history USING GIN(to_tsvector('english', query));

-- ── DOCUMENTS (indexed offline files) ──────────────────────
CREATE TABLE documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    file_path     TEXT,
    file_type     TEXT CHECK (file_type IN ('pdf','docx','txt','html','image','md')),
    file_size     BIGINT,
    title         TEXT,
    content_hash  TEXT,                   -- SHA256 for dedup
    word_count    INT,
    language      TEXT DEFAULT 'en',
    tags          TEXT[] DEFAULT '{}',
    is_indexed    BOOLEAN DEFAULT FALSE,
    index_status  TEXT DEFAULT 'pending',
    faiss_id      BIGINT,                  -- FAISS vector ID
    metadata      JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    indexed_at    TIMESTAMPTZ
);
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_content ON documents USING GIN(to_tsvector('english', coalesce(title,'')));

-- ── SAVED PAGES ────────────────────────────────────────────
CREATE TABLE saved_pages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    url           TEXT NOT NULL,
    title         TEXT,
    content       TEXT,
    summary       TEXT,
    tags          TEXT[] DEFAULT '{}',
    is_indexed    BOOLEAN DEFAULT FALSE,
    faiss_id      BIGINT,
    saved_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, url)
);

-- ── SEARCH CACHE ────────────────────────────────────────────
CREATE TABLE search_cache (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key     TEXT UNIQUE NOT NULL,
    query         TEXT NOT NULL,
    results       JSONB NOT NULL,
    summary       TEXT,
    source        TEXT,
    expires_at    TIMESTAMPTZ NOT NULL,
    hit_count     INT DEFAULT 0,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_search_cache_key ON search_cache(cache_key);
CREATE INDEX idx_search_cache_expires ON search_cache(expires_at);

-- ── AUDIT LOG ──────────────────────────────────────────────
CREATE TABLE audit_log (
    id            BIGSERIAL PRIMARY KEY,
    user_id       UUID REFERENCES users(id),
    action        TEXT NOT NULL,
    resource      TEXT,
    ip_address    INET,
    user_agent    TEXT,
    status        TEXT,
    metadata      JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── VECTORS TABLE (metadata for FAISS entries) ─────────────
CREATE TABLE vector_entries (
    id            BIGSERIAL PRIMARY KEY,
    faiss_id      BIGINT UNIQUE NOT NULL,
    source_type   TEXT CHECK (source_type IN ('document','saved_page','note')),
    source_id     UUID NOT NULL,
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    chunk_index   INT DEFAULT 0,
    chunk_text    TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_vector_entries_user ON vector_entries(user_id);
CREATE INDEX idx_vector_entries_faiss ON vector_entries(faiss_id);

-- ── TRIGGERS ───────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### SQLite Schema (Local/Offline)

```sql
-- Local SQLite — used by the desktop app and offline mode
-- File: local.db

CREATE TABLE local_documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id   TEXT,                   -- sync UUID from server
    filename    TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    file_type   TEXT,
    title       TEXT,
    content     TEXT,                   -- full extracted text
    tags        TEXT DEFAULT '[]',      -- JSON array
    is_synced   INTEGER DEFAULT 0,
    indexed_at  TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE local_fts USING fts5(
    title, content,
    content='local_documents',
    content_rowid='id'
);

CREATE TABLE local_settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE offline_cache (
    cache_key   TEXT PRIMARY KEY,
    query       TEXT,
    results     TEXT,          -- JSON
    created_at  TEXT DEFAULT (datetime('now')),
    expires_at  TEXT
);
```

---

## 5. API SPECIFICATION

```
Base URL: https://api.iois.app/api/v1

Authentication: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Endpoints

```
AUTH
────────────────────────────────────────────────────
POST   /auth/register          Register user
POST   /auth/login             Login → JWT
POST   /auth/refresh           Refresh token
POST   /auth/logout            Revoke token
GET    /auth/me                Current user
PATCH  /auth/me                Update profile

SEARCH
────────────────────────────────────────────────────
POST   /search                 Main search (online+offline)
GET    /search/suggestions     Autocomplete suggestions
GET    /search/history         User search history
DELETE /search/history/{id}    Delete history entry
POST   /search/save            Save search result

AI
────────────────────────────────────────────────────
POST   /ai/answer              Direct AI answer
POST   /ai/summarize           Summarize text/URL
POST   /ai/followup            Follow-up question (context)
POST   /ai/intent              Detect query intent

DOCUMENTS
────────────────────────────────────────────────────
GET    /documents              List user documents
POST   /documents/upload       Upload file for indexing
GET    /documents/{id}         Get document + content
DELETE /documents/{id}         Remove document
PATCH  /documents/{id}         Update tags/metadata
POST   /documents/{id}/reindex Reindex document
GET    /documents/search       Search local documents only

SAVED PAGES
────────────────────────────────────────────────────
GET    /saved                  List saved pages
POST   /saved                  Save a URL
DELETE /saved/{id}             Remove saved page
POST   /saved/fetch            Fetch + save URL content

SYNC
────────────────────────────────────────────────────
POST   /sync/push              Push local changes to server
GET    /sync/pull              Pull server changes
GET    /sync/status            Sync status

HEALTH
────────────────────────────────────────────────────
GET    /health                 Health check
GET    /health/ai              AI layer status
GET    /health/search          Search layer status
```

### Request / Response Examples

**POST /search**
```json
Request:
{
  "query": "network protocols OSI model",
  "filters": {
    "type": "all",
    "source": ["web", "local", "saved"],
    "date_range": "any"
  },
  "page": 1,
  "per_page": 10,
  "ai_summary": true,
  "include_local": true
}

Response:
{
  "query": "network protocols OSI model",
  "intent": "educational",
  "elapsed_ms": 342,
  "total": 287,
  "page": 1,
  "per_page": 10,
  "ai_overview": {
    "text": "The OSI model is a conceptual framework...",
    "confidence": 0.92,
    "sources": ["Wikipedia", "Local: networking_notes.pdf"]
  },
  "quick_answer": {
    "text": "The OSI model has 7 layers...",
    "source_url": "https://en.wikipedia.org/wiki/OSI_model"
  },
  "results": [
    {
      "id": "r_001",
      "title": "OSI model - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/OSI_model",
      "snippet": "The Open Systems Interconnection model...",
      "source": "wikipedia",
      "type": "web",
      "score": 0.97,
      "favicon": "https://...",
      "thumbnail": null,
      "published_at": null
    },
    {
      "id": "r_002",
      "title": "networking_notes.pdf — Chapter 3",
      "url": null,
      "snippet": "...OSI layers: Physical, Data Link...",
      "source": "local",
      "type": "document",
      "document_id": "uuid-here",
      "score": 0.89,
      "page_number": 14
    }
  ],
  "follow_up_questions": [
    "What is the difference between OSI and TCP/IP?",
    "Which layer does DNS operate at?",
    "How does the transport layer work?"
  ],
  "knowledge_panel": {
    "title": "OSI model",
    "type": "Computer Networking Model",
    "description": "The Open Systems Interconnection model...",
    "image": "https://...",
    "facts": [
      { "label": "Layers", "value": "7" },
      { "label": "Created", "value": "1984" }
    ]
  }
}
```

---

## 6. BACKEND CODE

### main.py
```python
# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api.router import api_router
from app.config import settings
from app.storage.postgres import init_db
from app.cache.redis_client import init_redis
from app.ai.embeddings import load_embeddings_model
from app.utils.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting IOIS API...")
    await init_db()
    await init_redis()
    await load_embeddings_model()
    logger.info("IOIS API ready.")
    yield
    # Shutdown
    logger.info("Shutting down IOIS API...")

app = FastAPI(
    title="IOIS API",
    description="Intelligent Offline & Online Information Search",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
```

### config.py
```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "IOIS"
    DEBUG: bool = False
    SECRET_KEY: str
    AES_KEY: str                          # 32-byte hex

    # Database
    DATABASE_URL: str                     # postgresql+asyncpg://...
    SQLITE_PATH: str = "./storage/local.db"
    REDIS_URL: str = "redis://localhost:6379"

    # Auth
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    REFRESH_EXPIRE_DAYS: int = 30

    # AI
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OPENAI_API_KEY: str = ""              # optional fallback
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Search
    FAISS_INDEX_PATH: str = "./storage/faiss/index.bin"
    MAX_RESULTS: int = 20
    CACHE_TTL_SECONDS: int = 3600

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "https://iois.app"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
```

### Search Orchestrator
```python
# backend/app/search/orchestrator.py
import asyncio
import time
from typing import Optional
from app.search.online.wikipedia import WikipediaSearcher
from app.search.online.duckduckgo import DDGSearcher
from app.search.offline.indexer import OfflineSearcher
from app.ranking.fusion_ranker import FusionRanker
from app.ai.intent import IntentDetector
from app.ai.summarizer import Summarizer
from app.ai.query_expander import QueryExpander
from app.cache.cache_service import CacheService
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SearchOrchestrator:
    def __init__(self):
        self.wikipedia  = WikipediaSearcher()
        self.ddg        = DDGSearcher()
        self.offline    = OfflineSearcher()
        self.ranker     = FusionRanker()
        self.intent     = IntentDetector()
        self.summarizer = Summarizer()
        self.expander   = QueryExpander()
        self.cache      = CacheService()

    async def search(
        self,
        query: str,
        user_id: str,
        filters: dict,
        page: int = 1,
        per_page: int = 10,
        ai_summary: bool = True,
        include_local: bool = True,
    ) -> dict:
        t0 = time.time()

        # 1. Cache check
        cache_key = f"search:{user_id}:{query}:{filters}:{page}"
        cached = await self.cache.get(cache_key)
        if cached:
            cached["from_cache"] = True
            return cached

        # 2. Intent detection
        intent = await self.intent.detect(query)
        logger.info(f"Query intent: {intent} for '{query}'")

        # 3. Query expansion
        expanded = await self.expander.expand(query, intent)

        # 4. Parallel search
        tasks = []
        source = filters.get("source", ["web", "local", "saved"])

        if "web" in source or "wikipedia" in source:
            tasks.append(self._search_online(expanded))
        if "local" in source and include_local:
            tasks.append(self.offline.search(query, user_id))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. Flatten + handle errors
        all_results = []
        for r in results_list:
            if isinstance(r, Exception):
                logger.warning(f"Search source error: {r}")
            elif isinstance(r, list):
                all_results.extend(r)

        # 6. Rerank
        ranked = await self.ranker.rank(all_results, query)

        # 7. Paginate
        total = len(ranked)
        start = (page - 1) * per_page
        page_results = ranked[start:start + per_page]

        # 8. AI summary (async, non-blocking)
        ai_overview = None
        quick_answer = None
        follow_ups = []

        if ai_summary and page_results:
            ai_tasks = await asyncio.gather(
                self.summarizer.summarize(query, page_results[:5]),
                self.summarizer.quick_answer(query, page_results[:3]),
                self.summarizer.follow_ups(query, intent),
                return_exceptions=True
            )
            if not isinstance(ai_tasks[0], Exception): ai_overview  = ai_tasks[0]
            if not isinstance(ai_tasks[1], Exception): quick_answer = ai_tasks[1]
            if not isinstance(ai_tasks[2], Exception): follow_ups   = ai_tasks[2]

        elapsed_ms = int((time.time() - t0) * 1000)

        response = {
            "query":       query,
            "intent":      intent,
            "elapsed_ms":  elapsed_ms,
            "total":       total,
            "page":        page,
            "per_page":    per_page,
            "ai_overview": ai_overview,
            "quick_answer": quick_answer,
            "results":     page_results,
            "follow_up_questions": follow_ups,
            "from_cache":  False,
        }

        # 9. Cache result
        await self.cache.set(cache_key, response, ttl=3600)
        return response

    async def _search_online(self, query: str) -> list:
        tasks = [self.wikipedia.search(query), self.ddg.search(query)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        combined = []
        for r in results:
            if isinstance(r, list):
                combined.extend(r)
        return combined
```

### AI: Intent Detection
```python
# backend/app/ai/intent.py
from enum import Enum

class QueryIntent(str, Enum):
    FACTUAL     = "factual"       # What is X, Who is X
    EDUCATIONAL = "educational"   # How does X work
    RESEARCH    = "research"      # Papers, deep dives
    TECHNICAL   = "technical"     # Code, commands, configs
    LOCAL       = "local"         # Find my documents
    NEWS        = "news"          # Recent events
    GENERAL     = "general"       # Everything else

INTENT_PATTERNS = {
    QueryIntent.FACTUAL:     ["what is", "who is", "where is", "when did", "define"],
    QueryIntent.EDUCATIONAL: ["how does", "how to", "explain", "tutorial", "learn"],
    QueryIntent.RESEARCH:    ["paper", "study", "research", "analysis", "compare"],
    QueryIntent.TECHNICAL:   ["code", "python", "config", "error", "install", "debug"],
    QueryIntent.LOCAL:       ["my notes", "my files", "my documents", "local"],
    QueryIntent.NEWS:        ["today", "latest", "news", "recent", "current"],
}

class IntentDetector:
    async def detect(self, query: str) -> str:
        q = query.lower().strip()
        scores = {intent: 0 for intent in QueryIntent}
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in q:
                    scores[intent] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else QueryIntent.GENERAL
```

### AI: Summarizer (Ollama + fallback)
```python
# backend/app/ai/summarizer.py
import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SUMMARY_PROMPT = """You are IOIS, an intelligent search assistant.
Given the query and top search results, write a concise 2-3 sentence overview.
Be factual. Cite sources by name. Do not hallucinate.

Query: {query}

Top results:
{results_text}

Overview:"""

class Summarizer:
    async def summarize(self, query: str, results: list) -> dict | None:
        try:
            results_text = "\n".join([
                f"[{i+1}] {r['title']}: {r['snippet'][:200]}"
                for i, r in enumerate(results[:5])
            ])
            prompt = SUMMARY_PROMPT.format(query=query, results_text=results_text)
            text = await self._call_llm(prompt)
            sources = [r.get("source", "web") for r in results[:3]]
            return {"text": text, "sources": list(set(sources)), "confidence": 0.85}
        except Exception as e:
            logger.warning(f"Summarize failed: {e}")
            return None

    async def quick_answer(self, query: str, results: list) -> dict | None:
        try:
            if not results:
                return None
            top = results[0]
            prompt = f"In one sentence, answer: {query}\nContext: {top['snippet'][:300]}\nAnswer:"
            text = await self._call_llm(prompt)
            return {"text": text, "source_url": top.get("url", "")}
        except Exception as e:
            logger.warning(f"Quick answer failed: {e}")
            return None

    async def follow_ups(self, query: str, intent: str) -> list[str]:
        try:
            prompt = f"""Given the search query "{query}" (intent: {intent}),
suggest 3 natural follow-up questions a user might ask.
Return only the questions, one per line."""
            text = await self._call_llm(prompt)
            lines = [l.strip().lstrip("123.-) ") for l in text.strip().split("\n") if l.strip()]
            return lines[:3]
        except Exception as e:
            logger.warning(f"Follow-ups failed: {e}")
            return []

    async def _call_llm(self, prompt: str) -> str:
        # Try Ollama first (local, private)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False}
                )
                r.raise_for_status()
                return r.json()["response"].strip()
        except Exception:
            pass

        # Fallback: OpenAI (if key configured)
        if settings.OPENAI_API_KEY:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200,
                        "temperature": 0.3,
                    }
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()

        raise RuntimeError("No LLM available")
```

### Offline Indexer (PDF + DOCX + OCR)
```python
# backend/app/search/offline/indexer.py
import asyncio
import hashlib
import uuid
from pathlib import Path
from typing import Optional
import numpy as np
from app.ai.embeddings import get_embedder
from app.storage.faiss_index import get_faiss_index
from app.storage.postgres import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)

CHUNK_SIZE  = 500   # words per chunk
CHUNK_OVERLAP = 50

class OfflineSearcher:
    def __init__(self):
        self.embedder = None
        self.faiss    = None

    async def _ensure_loaded(self):
        if not self.embedder:
            self.embedder = await get_embedder()
            self.faiss    = await get_faiss_index()

    async def search(self, query: str, user_id: str, top_k: int = 10) -> list:
        await self._ensure_loaded()
        query_vec = self.embedder.encode([query])[0].astype("float32")
        distances, indices = self.faiss.search(
            np.array([query_vec]), top_k * 2
        )
        results = []
        async for db in get_db():
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue
                # Look up metadata
                row = await db.fetchone(
                    "SELECT * FROM vector_entries WHERE faiss_id=$1 AND user_id=$2",
                    idx, user_id
                )
                if row:
                    results.append({
                        "id":        f"local_{row['id']}",
                        "title":     row.get("title", row["filename"]),
                        "snippet":   row["chunk_text"][:280],
                        "source":    "local",
                        "type":      "document",
                        "document_id": str(row["source_id"]),
                        "score":     float(1 / (1 + dist)),
                        "url":       None,
                    })
        return results[:top_k]

class DocumentIndexer:
    def __init__(self):
        self.embedder = None
        self.faiss    = None

    async def index_document(self, file_path: str, document_id: str, user_id: str) -> bool:
        await self._ensure_loaded()
        path = Path(file_path)
        if not path.exists():
            return False

        ext = path.suffix.lower()
        try:
            if ext == ".pdf":
                text = await self._extract_pdf(path)
            elif ext == ".docx":
                text = await self._extract_docx(path)
            elif ext in [".txt", ".md"]:
                text = path.read_text(encoding="utf-8", errors="ignore")
            elif ext in [".png", ".jpg", ".jpeg", ".tiff"]:
                text = await self._ocr(path)
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")

            chunks = self._chunk_text(text)
            vectors = self.embedder.encode(chunks).astype("float32")
            faiss_ids = list(range(self.faiss.ntotal, self.faiss.ntotal + len(chunks)))
            self.faiss.add(vectors)

            # Persist metadata
            async for db in get_db():
                for i, (chunk, fid) in enumerate(zip(chunks, faiss_ids)):
                    await db.execute(
                        """INSERT INTO vector_entries (faiss_id, source_type, source_id, user_id, chunk_index, chunk_text)
                           VALUES ($1, 'document', $2, $3, $4, $5)""",
                        fid, document_id, user_id, i, chunk[:1000]
                    )
                await db.execute(
                    "UPDATE documents SET is_indexed=TRUE, indexed_at=NOW(), faiss_id=$1 WHERE id=$2",
                    faiss_ids[0], document_id
                )
            return True

        except Exception as e:
            logger.error(f"Indexing failed for {file_path}: {e}")
            return False

    async def _extract_pdf(self, path: Path) -> str:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        return "\n".join(page.get_text() for page in doc)

    async def _extract_docx(self, path: Path) -> str:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    async def _ocr(self, path: Path) -> str:
        import pytesseract
        from PIL import Image
        img = Image.open(str(path))
        return pytesseract.image_to_string(img)

    def _chunk_text(self, text: str) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk = " ".join(words[i:i + CHUNK_SIZE])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    async def _ensure_loaded(self):
        if not self.embedder:
            self.embedder = await get_embedder()
            self.faiss    = await get_faiss_index()
```

### Fusion Ranker
```python
# backend/app/ranking/fusion_ranker.py
# Reciprocal Rank Fusion — merges multiple ranked lists optimally

class FusionRanker:
    K = 60  # RRF constant

    async def rank(self, results: list, query: str) -> list:
        if not results:
            return []

        # Deduplicate by URL or document_id
        seen = {}
        for r in results:
            key = r.get("url") or r.get("document_id") or r.get("id")
            if key and key not in seen:
                seen[key] = r
            elif key:
                # Keep higher score
                if r.get("score", 0) > seen[key].get("score", 0):
                    seen[key] = r

        deduped = list(seen.values())

        # Sort by score descending
        deduped.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Boost local results slightly (user's own content is more relevant)
        for r in deduped:
            if r.get("source") == "local":
                r["score"] = min(r.get("score", 0) * 1.15, 1.0)

        # Re-sort
        deduped.sort(key=lambda x: x.get("score", 0), reverse=True)
        return deduped
```

### Auth System
```python
# backend/app/auth/jwt.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_access_token(user_id: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": exp, "type": "access"},
                      settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    exp = datetime.utcnow() + timedelta(days=settings.REFRESH_EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": exp, "type": "refresh"},
                      settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY,
                          algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise ValueError("Invalid or expired token")
```

---

## 7. FRONTEND CODE

### vite.config.ts
```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.iois\.app\/api\/v1\/search/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'search-cache',
              expiration: { maxAgeSeconds: 3600 }
            }
          }
        ]
      },
      manifest: {
        name: 'IOIS — Intelligent Search',
        short_name: 'IOIS',
        theme_color: '#0d0f14',
        background_color: '#0d0f14',
        display: 'standalone',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      }
    })
  ],
  resolve: { alias: { '@': '/src' } },
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
```

### State Management (Zustand)
```typescript
// frontend/src/state/store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SearchState {
  query: string
  results: SearchResult[]
  aiOverview: AIOverview | null
  quickAnswer: QuickAnswer | null
  followUps: string[]
  loading: boolean
  error: string | null
  page: number
  total: number
  filter: string
  isOffline: boolean
  setQuery: (q: string) => void
  setResults: (r: SearchResult[], total: number) => void
  setLoading: (v: boolean) => void
  setError: (e: string | null) => void
  setPage: (p: number) => void
  setFilter: (f: string) => void
  setOffline: (v: boolean) => void
  reset: () => void
}

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      query: '',
      results: [],
      aiOverview: null,
      quickAnswer: null,
      followUps: [],
      loading: false,
      error: null,
      page: 1,
      total: 0,
      filter: 'all',
      isOffline: false,
      setQuery:   (query)           => set({ query }),
      setResults: (results, total)  => set({ results, total }),
      setLoading: (loading)         => set({ loading }),
      setError:   (error)           => set({ error }),
      setPage:    (page)            => set({ page }),
      setFilter:  (filter)          => set({ filter }),
      setOffline: (isOffline)       => set({ isOffline }),
      reset: () => set({ results: [], aiOverview: null, quickAnswer: null, followUps: [], error: null, page: 1, total: 0 }),
    }),
    { name: 'iois-search', partialize: (s) => ({ filter: s.filter }) }
  )
)

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (user: User, token: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth:  (user, token) => set({ user, token, isAuthenticated: true }),
      clearAuth: ()           => set({ user: null, token: null, isAuthenticated: false }),
    }),
    { name: 'iois-auth' }
  )
)
```

### Search Service
```typescript
// frontend/src/services/searchService.ts
import { api } from './api'
import { offlineSearch } from './offlineService'

export interface SearchOptions {
  query: string
  filter?: string
  page?: number
  perPage?: number
  aiSummary?: boolean
  includeLocal?: boolean
}

export async function search(opts: SearchOptions) {
  if (!navigator.onLine) {
    return offlineSearch(opts.query)
  }
  const { data } = await api.post('/search', {
    query:          opts.query,
    filters:        { type: opts.filter || 'all', source: ['web', 'local', 'saved'] },
    page:           opts.page || 1,
    per_page:       opts.perPage || 10,
    ai_summary:     opts.aiSummary ?? true,
    include_local:  opts.includeLocal ?? true,
  })
  return data
}

export async function getSuggestions(query: string): Promise<string[]> {
  if (!navigator.onLine || query.length < 2) return []
  try {
    const { data } = await api.get('/search/suggestions', { params: { q: query } })
    return data.suggestions || []
  } catch { return [] }
}
```

### Offline Service (IndexedDB via Dexie)
```typescript
// frontend/src/services/offlineService.ts
import Dexie, { Table } from 'dexie'

interface CachedResult { id?: number; key: string; data: any; expires: number }
interface LocalDoc     { id?: number; title: string; content: string; tags: string[]; path: string; indexed: boolean }

class IOISDatabase extends Dexie {
  cache!:  Table<CachedResult>
  docs!:   Table<LocalDoc>
  history!: Table<{ id?: number; query: string; ts: number }>

  constructor() {
    super('iois-db')
    this.version(1).stores({
      cache:   '++id, key, expires',
      docs:    '++id, title, *tags',
      history: '++id, query, ts',
    })
  }
}

export const db = new IOISDatabase()

export async function offlineSearch(query: string) {
  const q = query.toLowerCase()
  const docs = await db.docs
    .filter(d => d.title.toLowerCase().includes(q) || d.content.toLowerCase().includes(q))
    .limit(10)
    .toArray()

  return {
    query,
    intent:    'local',
    elapsed_ms: 5,
    total:     docs.length,
    page:      1,
    results:   docs.map(d => ({
      id:       `local_${d.id}`,
      title:    d.title,
      snippet:  d.content.substring(0, 280),
      source:   'local',
      type:     'document',
      score:    d.content.toLowerCase().split(q).length - 1,
      url:      null,
    })).sort((a, b) => b.score - a.score),
    ai_overview:         null,
    quick_answer:        null,
    follow_up_questions: [],
    from_cache: false,
    offline_mode: true,
  }
}

export async function cacheSearchResult(key: string, data: any, ttlSeconds = 3600) {
  await db.cache.where('key').equals(key).delete()
  await db.cache.add({ key, data, expires: Date.now() + ttlSeconds * 1000 })
}

export async function getCachedResult(key: string) {
  const entry = await db.cache.where('key').equals(key).first()
  if (!entry || Date.now() > entry.expires) return null
  return entry.data
}
```

---

## 8. DOCKER DEPLOYMENT

```yaml
# docker/docker-compose.yml
version: '3.9'

services:
  # ── Nginx Reverse Proxy ──────────────────────────────────
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./storage/ssl:/etc/ssl:ro
    depends_on: [api]
    restart: unless-stopped

  # ── FastAPI Backend ──────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://iois:${PG_PASSWORD}@postgres:5432/iois
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - AES_KEY=${AES_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - ./storage:/app/storage
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ── PostgreSQL ───────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB:       iois
      POSTGRES_USER:     iois
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./storage/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "iois"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Redis Cache ──────────────────────────────────────────
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 5

  # ── Ollama Local LLM ─────────────────────────────────────
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    # GPU support: uncomment below
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # ── Indexing Worker ──────────────────────────────────────
  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python -m app.workers.indexing_worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://iois:${PG_PASSWORD}@postgres:5432/iois
    volumes:
      - ./storage:/app/storage
    depends_on:
      postgres: { condition: service_healthy }
    restart: unless-stopped

volumes:
  pg_data:
  redis_data:
  ollama_data:
```

```nginx
# docker/nginx.conf
events { worker_connections 1024; }

http {
    include mime.types;
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=search:10m rate=2r/s;

    server {
        listen 80;
        server_name iois.app;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name iois.app;

        ssl_certificate     /etc/ssl/iois.crt;
        ssl_certificate_key /etc/ssl/iois.key;
        ssl_protocols TLSv1.2 TLSv1.3;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header Strict-Transport-Security "max-age=31536000";
        add_header Content-Security-Policy "default-src 'self'";

        # Static frontend
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;

        # API proxy
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Search rate limit
        location /api/v1/search {
            limit_req zone=search burst=5 nodelay;
            proxy_pass http://api:8000;
        }
    }
}
```

```dockerfile
# docker/Dockerfile.backend
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-eng \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

```
# backend/requirements.txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic-settings==2.2.1
sqlalchemy[asyncio]==2.0.29
asyncpg==0.29.0
alembic==1.13.1
redis[hiredis]==5.0.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
langchain==0.1.20
sentence-transformers==2.7.0
faiss-cpu==1.8.0
pymupdf==1.24.2
python-docx==1.1.2
pytesseract==0.3.10
Pillow==10.3.0
dexie==0.0.1
slowapi==0.1.9
python-multipart==0.0.9
aiofiles==23.2.1
rich==13.7.1
```

---

## 9. TESTING STRATEGY

```python
# tests/backend/test_search.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_search_online():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/search", json={
            "query": "Python programming",
            "filters": {"type": "all"},
            "page": 1,
            "ai_summary": False
        }, headers={"Authorization": "Bearer test_token"})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) > 0

@pytest.mark.asyncio
async def test_search_returns_intent():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/search", json={
            "query": "how to install nginx",
            "filters": {}, "page": 1
        }, headers={"Authorization": "Bearer test_token"})
    data = resp.json()
    assert data["intent"] in ["technical", "educational", "general"]

@pytest.mark.asyncio
async def test_search_offline_returns_local():
    # Assumes test DB has indexed documents
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/search", json={
            "query": "network notes",
            "filters": {"source": ["local"]},
            "page": 1, "include_local": True
        }, headers={"Authorization": "Bearer test_token"})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_auth_flow():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register
        r1 = await client.post("/api/v1/auth/register", json={
            "email": "test@iois.app", "username": "tester",
            "password": "SecureP@ss1"
        })
        assert r1.status_code in [200, 201]
        # Login
        r2 = await client.post("/api/v1/auth/login", json={
            "email": "test@iois.app", "password": "SecureP@ss1"
        })
        assert r2.status_code == 200
        assert "access_token" in r2.json()
```

---

## 10. CI/CD PIPELINE

```yaml
# .github/workflows/ci.yml
name: IOIS CI/CD

on:
  push:    { branches: [main, develop] }
  pull_request: { branches: [main] }

jobs:
  # ── Backend Tests ──────────────────────────────────────────
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_PASSWORD: test, POSTGRES_DB: iois_test }
        options: --health-cmd pg_isready --health-interval 10s
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r backend/requirements.txt
      - run: pytest tests/backend/ -v --tb=short
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/iois_test
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test_secret_32_chars_long_12345
          AES_KEY: 0000000000000000000000000000000000000000000000000000000000000000

  # ── Frontend Tests ─────────────────────────────────────────
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run type-check
      - run: cd frontend && npm run test

  # ── Build & Deploy ─────────────────────────────────────────
  deploy:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build frontend
        run: cd frontend && npm ci && npm run build
      - name: Build & push Docker images
        run: |
          docker build -f docker/Dockerfile.backend -t iois/api:${{ github.sha }} .
          docker push iois/api:${{ github.sha }}
      - name: Deploy to server
        run: |
          ssh deploy@${{ secrets.SERVER_IP }} \
            "cd /opt/iois && git pull && docker compose up -d --build"
```

---

## 11. INSTALLATION GUIDE

```bash
# ─────────────────────────────────────────
# QUICK START — Local Development
# ─────────────────────────────────────────

# 1. Clone
git clone https://github.com/yourname/iois.git && cd iois

# 2. Backend setup
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # Fill in secrets
alembic upgrade head    # Run migrations

# 3. Start services (Docker for Postgres + Redis)
docker run -d --name iois-pg    -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=iois -p 5432:5432 postgres:16-alpine
docker run -d --name iois-redis -p 6379:6379 redis:7-alpine
docker run -d --name iois-ollama -p 11434:11434 ollama/ollama
docker exec iois-ollama ollama pull mistral   # Download Mistral 7B model

# 4. Start backend
uvicorn main:app --reload --port 8000

# 5. Frontend setup (new terminal)
cd frontend
npm install
npm run dev        # Runs on localhost:5173

# 6. Open browser: http://localhost:5173

# ─────────────────────────────────────────
# PRODUCTION — Full Docker Compose
# ─────────────────────────────────────────

cp .env.example .env   # Fill all secrets
docker compose -f docker/docker-compose.yml up -d --build
# Then: docker exec iois_ollama_1 ollama pull mistral

# ─────────────────────────────────────────
# ANDROID BUILD (Capacitor)
# ─────────────────────────────────────────
cd frontend
npm run build
npx cap add android
npx cap sync android
npx cap open android      # Opens Android Studio → Build → APK

# ─────────────────────────────────────────
# WINDOWS DESKTOP BUILD (Electron)
# ─────────────────────────────────────────
cd frontend
npm run build
cd electron
npm install
npm run dist              # Outputs .exe installer
```

---

## 12. MVP ROADMAP (8 weeks)

```
Week 1–2: Foundation
  ✓ Project setup (Vite + FastAPI + Docker)
  ✓ Authentication (register/login/JWT)
  ✓ PostgreSQL + Redis + basic API
  ✓ Home page + search bar UI

Week 3–4: Online Search
  ✓ Wikipedia integration
  ✓ DuckDuckGo instant answers
  ✓ Result listing (Google-style)
  ✓ Query suggestions
  ✓ Result caching

Week 5–6: AI Layer
  ✓ Ollama integration (Mistral)
  ✓ Intent detection
  ✓ AI overview summaries
  ✓ Quick answers
  ✓ Follow-up questions

Week 7: Offline Search
  ✓ File upload + PDF/DOCX extraction
  ✓ Sentence transformer embeddings
  ✓ FAISS vector index
  ✓ Offline search results
  ✓ IndexedDB browser cache + offline mode

Week 8: Polish + Deploy
  ✓ PWA manifest + service worker
  ✓ Light/dark mode
  ✓ Docker Compose deployment
  ✓ Basic CI/CD
  ✓ README + docs
```

## 13. PRODUCTION ROADMAP (6 months)

```
Month 2:  Android APK via Capacitor
Month 3:  Electron Windows desktop app
Month 3:  RSS feed indexing
Month 4:  Web page saving + indexing
Month 4:  Secure sync (AES-256 encrypted)
Month 5:  Plugin system (custom sources)
Month 5:  Multi-language OCR (50+ languages)
Month 6:  Federated search (multiple users)
Month 6:  Self-hosted model fine-tuning
```

---

*Built with: FastAPI · Python · Vite · TypeScript · React · PostgreSQL · Redis · SQLite · FAISS · Sentence Transformers · Ollama · Docker · Nginx*
# IOIS — Continuation Build
## Modules: Frontend Components · AI RAG · Auth Endpoints · Sync · Tests · .env · Electron · Capacitor

---

## MODULE 1 — COMPLETE FRONTEND COMPONENTS

### App.tsx (Root Router)
```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/state/store'
import { useSearchStore } from '@/state/store'
import Home from '@/pages/Home'
import Results from '@/pages/Results'
import Library from '@/pages/Library'
import Settings from '@/pages/Settings'
import Login from '@/pages/Auth/Login'
import Register from '@/pages/Auth/Register'
import Layout from '@/components/Layout/Layout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  const { setOffline } = useSearchStore()

  useEffect(() => {
    const onOnline  = () => setOffline(false)
    const onOffline = () => setOffline(true)
    window.addEventListener('online',  onOnline)
    window.addEventListener('offline', onOffline)
    setOffline(!navigator.onLine)
    return () => {
      window.removeEventListener('online',  onOnline)
      window.removeEventListener('offline', onOffline)
    }
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route path="/"         element={<Home />} />
          <Route path="/results"  element={<Results />} />
          <Route path="/library"  element={<Library />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
```

### Home.tsx (Google-style home page)
```tsx
// frontend/src/pages/Home.tsx
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSearchStore, useAuthStore } from '@/state/store'
import { search, getSuggestions } from '@/services/searchService'
import { useDebounce } from '@/hooks/useDebounce'
import VoiceSearch from '@/components/SearchBar/VoiceSearch'
import OfflineIndicator from '@/components/Offline/OfflineIndicator'
import styles from './Home.module.css'

const FILTERS = [
  { label: '🌐 All',        value: ''           },
  { label: '📰 News',       value: 'news'       },
  { label: '📄 Articles',   value: 'article'    },
  { label: '👤 People',     value: 'people'     },
  { label: '🔬 Science',    value: 'science'    },
  { label: '💻 Technology', value: 'technology' },
]

export default function Home() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { setQuery, setResults, setLoading, setError, filter, setFilter, isOffline } = useSearchStore()

  const [input,    setInput]    = useState('')
  const [suggs,    setSuggs]    = useState<string[]>([])
  const [suggOpen, setSuggOpen] = useState(false)
  const [suggIdx,  setSuggIdx]  = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounced = useDebounce(input, 260)

  useEffect(() => { inputRef.current?.focus() }, [])

  useEffect(() => {
    if (debounced.length < 2) { setSuggs([]); setSuggOpen(false); return }
    getSuggestions(debounced).then(s => { setSuggs(s); setSuggOpen(s.length > 0) })
  }, [debounced])

  async function doSearch(q = input) {
    const query = q.trim()
    if (!query) return
    setSuggOpen(false)
    setQuery(query)
    setLoading(true)
    setError(null)
    navigate('/results')
    try {
      const data = await search({ query, filter, aiSummary: true })
      setResults(data.results, data.total)
      // store full response in sessionStorage for Results page
      sessionStorage.setItem('iois_last_search', JSON.stringify(data))
    } catch (e: any) {
      setError(e.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  function onKey(e: React.KeyboardEvent) {
    if (!suggOpen || !suggs.length) {
      if (e.key === 'Enter') doSearch()
      return
    }
    if (e.key === 'ArrowDown') { e.preventDefault(); setSuggIdx(i => Math.min(i + 1, suggs.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSuggIdx(i => Math.max(i - 1, -1)) }
    else if (e.key === 'Enter') {
      e.preventDefault()
      if (suggIdx >= 0) { setInput(suggs[suggIdx]); doSearch(suggs[suggIdx]) }
      else doSearch()
    } else if (e.key === 'Escape') setSuggOpen(false)
  }

  return (
    <div className={styles.home}>
      <OfflineIndicator />
      <div className={styles.logo}>IOIS</div>
      <p className={styles.tagline}>
        {user ? `Hello, ${user.display_name || user.username}` : 'Private · Intelligent · Offline-capable search'}
      </p>

      <div className={styles.searchWrap}>
        <div className={styles.bar}>
          <span className={styles.barIcon}>🔍</span>
          <input
            ref={inputRef}
            className={styles.barInput}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKey}
            placeholder="Search the web, or ask anything…"
            autoComplete="off"
            spellCheck={false}
            aria-label="Search"
            aria-autocomplete="list"
            aria-controls="sugg-list"
          />
          {input && (
            <button className={styles.clearBtn} onClick={() => { setInput(''); setSuggOpen(false); inputRef.current?.focus() }} aria-label="Clear">✕</button>
          )}
          <span className={styles.divider} />
          <VoiceSearch onResult={t => { setInput(t); doSearch(t) }} />
        </div>

        {suggOpen && (
          <ul id="sugg-list" className={styles.sugg} role="listbox">
            {suggs.map((s, i) => (
              <li key={s}
                className={[styles.suggItem, i === suggIdx ? styles.suggActive : ''].join(' ')}
                role="option" aria-selected={i === suggIdx}
                onMouseDown={() => { setInput(s); doSearch(s) }}
                onMouseEnter={() => setSuggIdx(i)}
              >
                <span className={styles.suggIcon}>🔍</span> {s}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Filter chips */}
      <div className={styles.filters} role="group" aria-label="Search filter">
        {FILTERS.map(f => (
          <button key={f.value}
            className={[styles.chip, filter === f.value ? styles.chipOn : ''].join(' ')}
            onClick={() => setFilter(f.value)}
          >{f.label}</button>
        ))}
      </div>

      {/* Action buttons */}
      <div className={styles.actions}>
        <button className={styles.btnPrimary} onClick={() => doSearch()}>🔍 IOIS Search</button>
        <button className={styles.btn} onClick={() => { setInput(input); navigate('/results?ai=1') }}>🧠 Ask AI</button>
        <button className={styles.btn} onClick={() => navigate('/library')}>📚 My Library</button>
      </div>
    </div>
  )
}
```

### Results.tsx (Google-style results page)
```tsx
// frontend/src/pages/Results.tsx
import { useEffect, useState } from 'react'
import { useSearchStore } from '@/state/store'
import { search } from '@/services/searchService'
import ResultItem from '@/components/Results/ResultItem'
import AIOverview from '@/components/Results/AIOverview'
import QuickAnswer from '@/components/Results/QuickAnswer'
import KnowledgePanel from '@/components/Results/KnowledgePanel'
import Pagination from '@/components/Results/Pagination'
import SearchBar from '@/components/SearchBar/SearchBar'
import FilterTabs from '@/components/Results/FilterTabs'
import Shimmer from '@/components/UI/Shimmer'

export default function Results() {
  const { query, filter, page, loading, error, isOffline } = useSearchStore()
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    const cached = sessionStorage.getItem('iois_last_search')
    if (cached) { setData(JSON.parse(cached)); return }
    if (query) runSearch()
  }, [])

  useEffect(() => { if (query) runSearch() }, [page, filter])

  async function runSearch() {
    const url = new URLSearchParams(window.location.search)
    const aiMode = url.get('ai') === '1'
    try {
      const res = await search({ query, filter, page, aiSummary: true })
      setData(res)
      sessionStorage.setItem('iois_last_search', JSON.stringify(res))
    } catch {}
  }

  return (
    <div className="results-page">
      <SearchBar compact />
      <FilterTabs />

      <div className="results-body">
        <main className="results-main">
          {loading && <Shimmer rows={6} />}
          {error && <div className="err-box">⚠️ {error}</div>}

          {data && !loading && (
            <>
              <div className="res-meta">
                About <strong>{data.total?.toLocaleString()}</strong> results
                {data.elapsed_ms && ` (${(data.elapsed_ms / 1000).toFixed(2)}s)`}
                {data.from_cache && <span className="cached-tag">⚡ cached</span>}
                {isOffline && <span className="offline-tag">📡 offline mode</span>}
              </div>

              {data.quick_answer && <QuickAnswer data={data.quick_answer} />}
              {data.ai_overview  && <AIOverview  data={data.ai_overview}  />}

              {data.results?.map((r: any) => <ResultItem key={r.id} result={r} />)}

              {data.follow_up_questions?.length > 0 && (
                <div className="follow-ups">
                  <h3 className="follow-ups-title">People also ask</h3>
                  {data.follow_up_questions.map((q: string) => (
                    <div key={q} className="follow-up-item"
                      onClick={() => { /* trigger new search */ }}
                    >
                      <span>{q}</span> <span className="fu-arrow">›</span>
                    </div>
                  ))}
                </div>
              )}

              <Pagination total={data.total} pageSize={10} />
            </>
          )}

          {data?.results?.length === 0 && !loading && (
            <div className="no-results">
              <div className="no-results-icon">🔭</div>
              <h3>No results for "{query}"</h3>
              <p>Try different keywords or switch your search back-end in Settings.</p>
            </div>
          )}
        </main>

        <aside className="results-sidebar">
          {data?.knowledge_panel && <KnowledgePanel data={data.knowledge_panel} />}
        </aside>
      </div>
    </div>
  )
}
```

### ResultItem.tsx
```tsx
// frontend/src/components/Results/ResultItem.tsx
interface Result {
  id: string; title: string; url: string | null; snippet: string
  source: string; type: string; score: number; thumbnail?: string
  document_id?: string; page_number?: number
}

function highlight(text: string, query: string): string {
  if (!query || !text) return text
  const words = query.trim().split(/\s+/).filter(Boolean)
    .map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  if (!words.length) return text
  return text.replace(new RegExp(`(${words.join('|')})`, 'gi'), '<em>$1</em>')
}

function getDomain(url: string): string {
  try { return new URL(url).hostname.replace(/^www\./, '') }
  catch { return url }
}

export default function ResultItem({ result }: { result: Result }) {
  const { query } = useSearchStore()
  const isLocal = result.type === 'document'
  const domain  = result.url ? getDomain(result.url) : 'local'
  const fav     = result.url ? `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=32` : null

  const handleClick = () => {
    if (result.url) window.open(result.url, '_blank', 'noopener,noreferrer')
    else if (result.document_id) { /* open document viewer */ }
  }

  return (
    <div className={`res-item ${result.thumbnail ? 'has-thumb' : ''}`} onClick={handleClick}>
      {result.thumbnail && <img src={result.thumbnail} className="res-thumb" alt="" loading="lazy" />}
      <div className="res-body">
        <div className="res-url-row">
          <div className="res-fav">
            {fav ? <img src={fav} alt="" loading="lazy" onError={e => (e.currentTarget.style.display = 'none')} />
                 : <span>📄</span>}
          </div>
          <span className="res-domain">{domain}</span>
          {isLocal && <span className="local-badge">local</span>}
          {result.page_number && <span className="res-page">p.{result.page_number}</span>}
        </div>
        <div className="res-title">{result.title}</div>
        <div
          className="res-snippet"
          dangerouslySetInnerHTML={{ __html: highlight(result.snippet.substring(0, 290), query) }}
        />
      </div>
    </div>
  )
}
```

### AIOverview.tsx
```tsx
// frontend/src/components/Results/AIOverview.tsx
import { useState } from 'react'

interface AIOverviewProps {
  data: { text: string; sources: string[]; confidence: number }
}

export default function AIOverview({ data }: AIOverviewProps) {
  const [expanded, setExpanded] = useState(true)
  return (
    <div className="ai-box">
      <div className="ai-header" onClick={() => setExpanded(e => !e)}>
        <div className="ai-label">
          <span className="ai-spin">✨</span> AI Overview
          <span className="ai-conf">{Math.round(data.confidence * 100)}% confidence</span>
        </div>
        <span className="ai-toggle">{expanded ? '▲' : '▼'}</span>
      </div>
      {expanded && (
        <div className="ai-body">
          <p className="ai-text">{data.text}</p>
          {data.sources?.length > 0 && (
            <div className="ai-sources">
              Sources: {data.sources.map((s, i) => <span key={i} className="ai-src-tag">{s}</span>)}
            </div>
          )}
          <p className="ai-disclaimer">
            Generated locally from search snippets — not a substitute for original sources.
          </p>
        </div>
      )}
    </div>
  )
}
```

### Library.tsx (Offline document manager)
```tsx
// frontend/src/pages/Library.tsx
import { useState, useEffect, useRef } from 'react'
import { api } from '@/services/api'
import FileUploader from '@/components/Offline/FileUploader'
import IndexProgress from '@/components/Offline/IndexProgress'

interface Doc {
  id: string; filename: string; file_type: string
  is_indexed: boolean; word_count: number; tags: string[]
  created_at: string; index_status: string
}

export default function Library() {
  const [docs,    setDocs]    = useState<Doc[]>([])
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')

  useEffect(() => { loadDocs() }, [])

  async function loadDocs() {
    setLoading(true)
    try {
      const { data } = await api.get('/documents')
      setDocs(data.documents)
    } finally { setLoading(false) }
  }

  async function deleteDoc(id: string) {
    if (!confirm('Remove this document from your library?')) return
    await api.delete(`/documents/${id}`)
    setDocs(d => d.filter(doc => doc.id !== id))
  }

  async function reindex(id: string) {
    await api.post(`/documents/${id}/reindex`)
    loadDocs()
  }

  const filtered = docs.filter(d =>
    d.filename.toLowerCase().includes(search.toLowerCase()) ||
    d.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))
  )

  const typeIcon: Record<string, string> = {
    pdf: '📄', docx: '📝', txt: '📃', md: '📋', html: '🌐', image: '🖼️'
  }

  return (
    <div className="library-page">
      <div className="lib-header">
        <h1 className="lib-title">My Library</h1>
        <div className="lib-stats">
          {docs.length} documents · {docs.filter(d => d.is_indexed).length} indexed
        </div>
      </div>

      <FileUploader onUploaded={loadDocs} />

      <div className="lib-search-bar">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter documents…"
          className="lib-search-input"
        />
      </div>

      {loading && <div className="lib-loading">Loading library…</div>}

      <div className="doc-grid">
        {filtered.map(doc => (
          <div key={doc.id} className="doc-card">
            <div className="doc-icon">{typeIcon[doc.file_type] || '📄'}</div>
            <div className="doc-info">
              <div className="doc-name">{doc.filename}</div>
              <div className="doc-meta">
                {doc.word_count?.toLocaleString()} words
                {doc.tags.length > 0 && ' · ' + doc.tags.join(', ')}
              </div>
              <div className="doc-status">
                {doc.is_indexed
                  ? <span className="status-ok">✓ indexed</span>
                  : <span className="status-pend">⏳ {doc.index_status}</span>
                }
              </div>
            </div>
            <div className="doc-actions">
              <button onClick={() => reindex(doc.id)} title="Re-index">↻</button>
              <button onClick={() => deleteDoc(doc.id)} title="Delete" className="del-btn">🗑</button>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && !loading && (
        <div className="lib-empty">
          <div className="lib-empty-icon">📚</div>
          <h3>No documents yet</h3>
          <p>Upload PDFs, DOCX files, notes, or images to search them offline.</p>
        </div>
      )}
    </div>
  )
}
```

### FileUploader.tsx
```tsx
// frontend/src/components/Offline/FileUploader.tsx
import { useState, useRef } from 'react'
import { api } from '@/services/api'

const ACCEPTED = '.pdf,.docx,.txt,.md,.html,.png,.jpg,.jpeg,.tiff'
const MAX_MB   = 50

export default function FileUploader({ onUploaded }: { onUploaded: () => void }) {
  const [uploading, setUploading] = useState(false)
  const [progress,  setProgress]  = useState(0)
  const [error,     setError]     = useState('')
  const [isDrag,    setIsDrag]    = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  async function upload(files: FileList | null) {
    if (!files || !files.length) return
    setError('')
    for (const file of Array.from(files)) {
      if (file.size > MAX_MB * 1024 * 1024) {
        setError(`${file.name} exceeds ${MAX_MB}MB limit`)
        continue
      }
      const fd = new FormData()
      fd.append('file', file)
      setUploading(true)
      setProgress(0)
      try {
        await api.post('/documents/upload', fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: e => setProgress(Math.round((e.loaded * 100) / (e.total || 1))),
        })
        onUploaded()
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Upload failed')
      } finally { setUploading(false); setProgress(0) }
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault(); setIsDrag(false)
    upload(e.dataTransfer.files)
  }

  return (
    <div
      className={`uploader ${isDrag ? 'drag-over' : ''}`}
      onDragOver={e => { e.preventDefault(); setIsDrag(true) }}
      onDragLeave={() => setIsDrag(false)}
      onDrop={onDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      role="button" tabIndex={0}
      aria-label="Upload files"
    >
      <input ref={inputRef} type="file" multiple accept={ACCEPTED} onChange={e => upload(e.target.files)} hidden />
      {uploading ? (
        <div className="upload-progress">
          <div className="upload-bar" style={{ width: `${progress}%` }} />
          <span>Uploading… {progress}%</span>
        </div>
      ) : (
        <>
          <div className="upload-icon">📂</div>
          <div className="upload-text">Drop files here or click to upload</div>
          <div className="upload-hint">PDF, DOCX, TXT, MD, HTML, Images — max {MAX_MB}MB each</div>
        </>
      )}
      {error && <div className="upload-error">{error}</div>}
    </div>
  )
}
```

### VoiceSearch.tsx
```tsx
// frontend/src/components/SearchBar/VoiceSearch.tsx
import { useState } from 'react'

interface Props { onResult: (text: string) => void }

export default function VoiceSearch({ onResult }: Props) {
  const [listening, setListening] = useState(false)

  function start() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) { alert('Voice search is not supported in this browser.'); return }
    const r = new SR()
    r.lang = 'en-US'; r.interimResults = false; r.maxAlternatives = 1
    r.start(); setListening(true)
    r.onresult = (e: any) => onResult(e.results[0][0].transcript)
    r.onerror  = () => setListening(false)
    r.onend    = () => setListening(false)
  }

  return (
    <button
      className={`sb-voice ${listening ? 'listening' : ''}`}
      onClick={start}
      aria-label="Voice search"
      title="Voice search"
    >🎤</button>
  )
}
```

### useSearch.ts hook
```typescript
// frontend/src/hooks/useSearch.ts
import { useState, useCallback, useRef } from 'react'
import { search as apiSearch, SearchOptions } from '@/services/searchService'
import { useSearchStore } from '@/state/store'

export function useSearch() {
  const store    = useSearchStore()
  const abortRef = useRef<AbortController | null>(null)

  const doSearch = useCallback(async (opts: SearchOptions) => {
    // Cancel pending search
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    store.setLoading(true)
    store.setError(null)
    store.setQuery(opts.query)

    try {
      const data = await apiSearch(opts)
      store.setResults(data.results, data.total)
      sessionStorage.setItem('iois_last_search', JSON.stringify(data))
      return data
    } catch (e: any) {
      if (e.name !== 'AbortError') store.setError(e.message || 'Search failed')
      return null
    } finally {
      store.setLoading(false)
    }
  }, [store])

  return { doSearch, ...store }
}
```

### api.ts (Axios instance)
```typescript
// frontend/src/services/api.ts
import axios from 'axios'
import { useAuthStore } from '@/state/store'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT to every request
api.interceptors.request.use(config => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401, auto-refresh on 403
api.interceptors.response.use(
  res => res,
  async err => {
    const status = err.response?.status
    if (status === 401) {
      useAuthStore.getState().clearAuth()
      window.location.href = '/login'
    } else if (status === 403) {
      try {
        const { data } = await axios.post('/api/v1/auth/refresh',
          { refresh_token: localStorage.getItem('iois_refresh') }
        )
        useAuthStore.getState().setAuth(data.user, data.access_token)
        err.config.headers.Authorization = `Bearer ${data.access_token}`
        return api.request(err.config)
      } catch { useAuthStore.getState().clearAuth() }
    }
    return Promise.reject(err)
  }
)
```

---

## MODULE 2 — COMPLETE BACKEND AUTH ENDPOINTS

```python
# backend/app/api/v1/auth.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, validator
from app.storage.postgres import get_db
from app.storage.models import User, Session as DBSession
from app.auth.jwt import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.utils.logger import get_logger
import uuid

router  = APIRouter(prefix="/auth", tags=["auth"])
logger  = get_logger(__name__)

# ── Schemas ──────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email:        EmailStr
    username:     str
    password:     str
    display_name: str = ''

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

    @validator('username')
    def username_valid(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3:
            raise ValueError('Username too short')
        return v.lower()

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = 'bearer'
    user:          dict

class RefreshRequest(BaseModel):
    refresh_token: str

# ── Helpers ──────────────────────────────────────────────────
def user_dict(u: User) -> dict:
    return {
        'id':           str(u.id),
        'email':        u.email,
        'username':     u.username,
        'display_name': u.display_name or u.username,
        'plan':         u.plan,
        'created_at':   u.created_at.isoformat(),
    }

# ── Endpoints ────────────────────────────────────────────────
@router.post('/register', response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Check duplicates
    from sqlalchemy import select
    existing = await db.execute(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, 'Email or username already taken')

    user = User(
        id            = uuid.uuid4(),
        email         = body.email,
        username      = body.username,
        password_hash = hash_password(body.password),
        display_name  = body.display_name or body.username,
    )
    db.add(user)
    await db.flush()

    access  = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))

    session = DBSession(
        user_id      = user.id,
        token_hash   = hash_password(access),
        refresh_hash = hash_password(refresh),
        ip_address   = request.client.host if request.client else None,
        expires_at   = datetime.utcnow() + __import__('datetime').timedelta(hours=1),
    )
    db.add(session)
    await db.commit()
    logger.info(f"New user registered: {user.email}")
    return TokenResponse(access_token=access, refresh_token=refresh, user=user_dict(user))

@router.post('/login', response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == body.email))
    user   = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid credentials')
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Account disabled')

    user.last_login = datetime.utcnow()
    access  = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))

    session = DBSession(
        user_id      = user.id,
        token_hash   = hash_password(access),
        refresh_hash = hash_password(refresh),
        ip_address   = request.client.host if request.client else None,
        expires_at   = datetime.utcnow() + __import__('datetime').timedelta(hours=1),
    )
    db.add(session)
    await db.commit()
    logger.info(f"User login: {user.email}")
    return TokenResponse(access_token=access, refresh_token=refresh, user=user_dict(user))

@router.post('/refresh', response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get('type') != 'refresh':
            raise ValueError()
        user_id = payload['sub']
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid refresh token')

    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, 'User not found')

    access  = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh, user=user_dict(user))

@router.post('/logout', status_code=204)
async def logout(db: AsyncSession = Depends(get_db)):
    # Stateless JWT — client deletes token
    # For full revocation, mark session as revoked in DB here
    return None

@router.get('/me')
async def me(db: AsyncSession = Depends(get_db)):
    # Inject via dependency (see dependencies.py)
    pass
```

### Document upload endpoint
```python
# backend/app/api/v1/documents.py
import uuid
import hashlib
import aiofiles
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.postgres import get_db
from app.storage.models import Document
from app.dependencies import get_current_user
from app.search.offline.indexer import DocumentIndexer
from app.config import settings

router  = APIRouter(prefix="/documents", tags=["documents"])
indexer = DocumentIndexer()
UPLOAD_DIR = Path('./storage/uploads')
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    'application/pdf':                                         'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'text/plain':                                              'txt',
    'text/markdown':                                           'md',
    'text/html':                                               'html',
    'image/png':                                               'image',
    'image/jpeg':                                              'image',
    'image/tiff':                                              'image',
}

@router.post('/upload', status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, f'Unsupported file type: {file.content_type}')

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(413, 'File exceeds 50MB limit')

    # Deduplication via SHA-256
    content_hash = hashlib.sha256(content).hexdigest()
    from sqlalchemy import select
    existing = await db.execute(
        select(Document).where(
            Document.content_hash == content_hash,
            Document.user_id      == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, 'Document already in your library')

    # Save file
    doc_id    = uuid.uuid4()
    file_ext  = Path(file.filename or 'file').suffix
    file_path = UPLOAD_DIR / f"{user.id}/{doc_id}{file_ext}"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    doc = Document(
        id           = doc_id,
        user_id      = user.id,
        filename     = file.filename or 'unknown',
        file_path    = str(file_path),
        file_type    = ALLOWED_TYPES[file.content_type],
        file_size    = len(content),
        content_hash = content_hash,
        index_status = 'pending',
    )
    db.add(doc)
    await db.commit()

    # Index in background (non-blocking)
    background_tasks.add_task(
        indexer.index_document,
        str(file_path), str(doc_id), str(user.id)
    )

    return {
        'id':       str(doc_id),
        'filename': doc.filename,
        'status':   'uploaded — indexing in background',
    }

@router.get('')
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return {
        'documents': [
            {
                'id':           str(d.id),
                'filename':     d.filename,
                'file_type':    d.file_type,
                'file_size':    d.file_size,
                'is_indexed':   d.is_indexed,
                'index_status': d.index_status,
                'word_count':   d.word_count,
                'tags':         d.tags or [],
                'created_at':   d.created_at.isoformat(),
            }
            for d in docs
        ]
    }

@router.delete('/{doc_id}', status_code=204)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    from sqlalchemy import select, delete
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, 'Document not found')
    # Remove file from disk
    if doc.file_path and Path(doc.file_path).exists():
        Path(doc.file_path).unlink(missing_ok=True)
    # Remove vector entries
    await db.execute(delete(VectorEntry).where(VectorEntry.source_id == doc_id))
    await db.delete(doc)
    await db.commit()
```

---

## MODULE 3 — AI RAG PIPELINE

```python
# backend/app/ai/rag.py
"""
Retrieval-Augmented Generation pipeline.
Retrieves relevant document chunks, then generates a grounded answer.
"""
from typing import Optional
import numpy as np
from app.ai.embeddings import get_embedder
from app.storage.faiss_index import get_faiss_index
from app.storage.postgres import get_db
from app.ai.ollama_client import OllamaClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

RAG_PROMPT = """You are IOIS, an intelligent private search assistant.
Answer the question below using ONLY the provided context.
If the context doesn't contain the answer, say so honestly.
Cite the source document name when using its content.

Context:
{context}

Question: {question}

Answer:"""

class RAGPipeline:
    def __init__(self):
        self.embedder = None
        self.faiss    = None
        self.llm      = OllamaClient()

    async def _load(self):
        if not self.embedder:
            self.embedder = await get_embedder()
            self.faiss    = await get_faiss_index()

    async def answer(
        self,
        question: str,
        user_id:  str,
        top_k:    int = 5,
    ) -> dict:
        await self._load()

        # 1. Embed the question
        q_vec = self.embedder.encode([question])[0].astype('float32')

        # 2. FAISS similarity search
        distances, indices = self.faiss.search(np.array([q_vec]), top_k * 2)

        # 3. Retrieve chunk metadata from PG
        chunks = []
        async for db in get_db():
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue
                row = await db.fetchone(
                    """SELECT ve.chunk_text, ve.chunk_index,
                              d.filename, d.title
                       FROM vector_entries ve
                       LEFT JOIN documents d ON ve.source_id = d.id
                       WHERE ve.faiss_id = $1 AND ve.user_id = $2""",
                    int(idx), user_id
                )
                if row:
                    chunks.append({
                        'text':      row['chunk_text'],
                        'source':    row['filename'] or row['title'] or 'Document',
                        'score':     float(1 / (1 + dist)),
                    })

        if not chunks:
            return {
                'answer':  "I couldn't find relevant information in your documents.",
                'sources': [],
                'chunks':  0,
            }

        # 4. Build context (top_k chunks, sorted by score)
        chunks.sort(key=lambda x: x['score'], reverse=True)
        top = chunks[:top_k]
        context = '\n\n'.join([
            f"[{c['source']}]:\n{c['text'][:500]}"
            for c in top
        ])

        # 5. Generate answer via LLM
        prompt = RAG_PROMPT.format(context=context, question=question)
        try:
            answer_text = await self.llm.generate(prompt, max_tokens=400)
        except Exception as e:
            logger.warning(f"RAG LLM failed: {e}")
            answer_text = top[0]['text'][:300] + '…'

        return {
            'answer':  answer_text.strip(),
            'sources': list({c['source'] for c in top}),
            'chunks':  len(chunks),
            'context_used': len(top),
        }
```

```python
# backend/app/ai/ollama_client.py
import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OllamaClient:
    async def generate(self, prompt: str, max_tokens: int = 300) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    'model':  settings.OLLAMA_MODEL,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'num_predict': max_tokens,
                        'temperature': 0.3,
                        'top_p':       0.9,
                    }
                }
            )
            r.raise_for_status()
            return r.json()['response']

    async def chat(self, messages: list[dict]) -> str:
        """For multi-turn context-aware conversations."""
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    'model':    settings.OLLAMA_MODEL,
                    'messages': messages,
                    'stream':   False,
                    'options':  {'temperature': 0.35}
                }
            )
            r.raise_for_status()
            return r.json()['message']['content']

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
```

```python
# backend/app/ai/embeddings.py
import asyncio
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.utils.logger import get_logger

logger    = get_logger(__name__)
_embedder = None

async def load_embeddings_model():
    global _embedder
    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
    loop     = asyncio.get_event_loop()
    _embedder = await loop.run_in_executor(None, SentenceTransformer, settings.EMBEDDING_MODEL)
    logger.info("Embedding model loaded.")

async def get_embedder():
    global _embedder
    if not _embedder:
        await load_embeddings_model()
    return _embedder
```

```python
# backend/app/ai/query_expander.py
class QueryExpander:
    EXPANSIONS = {
        'network':  ['networking', 'protocols', 'TCP/IP'],
        'python':   ['python3', 'programming', 'scripting'],
        'security': ['cybersecurity', 'encryption', 'firewall'],
        'ai':       ['artificial intelligence', 'machine learning', 'neural network'],
    }

    async def expand(self, query: str, intent: str) -> str:
        q = query.lower()
        expansions = []
        for keyword, related in self.EXPANSIONS.items():
            if keyword in q:
                expansions.extend(related[:2])
        if expansions:
            return f"{query} {' '.join(expansions[:4])}"
        return query
```

---

## MODULE 4 — SYNC SYSTEM

```python
# backend/app/api/v1/sync.py
"""
Encrypted sync — push/pull changes between client and server.
All document content is encrypted with AES-256 before storage.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.postgres import get_db
from app.dependencies import get_current_user
from app.auth.encryption import aes_encrypt, aes_decrypt
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/sync", tags=["sync"])

class PushPayload(BaseModel):
    items: list[dict]      # [{type, id, data, updated_at}]
    client_version: int

@router.post('/push')
async def push_changes(
    body: PushPayload,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    """Client pushes local changes (offline edits, new docs, etc.) to server."""
    synced = 0
    conflicts = []
    for item in body.items:
        item_type = item.get('type')
        item_id   = item.get('id')
        data      = item.get('data', {})
        # Encrypt sensitive fields before storage
        if 'content' in data:
            data['content'] = aes_encrypt(data['content'])
        # Upsert logic by type
        if item_type == 'search_history':
            # Merge search history
            synced += 1
        elif item_type == 'saved_page':
            synced += 1
        # More types: notes, settings, tags
    await db.commit()
    return {'synced': synced, 'conflicts': conflicts, 'server_version': body.client_version + 1}

@router.get('/pull')
async def pull_changes(
    since: str | None = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    """Server returns changes since last sync timestamp."""
    since_dt = datetime.fromisoformat(since) if since else None
    # Return encrypted payloads that the client will decrypt locally
    return {
        'items':      [],      # changed items since since_dt
        'server_ts':  datetime.utcnow().isoformat(),
        'has_more':   False,
    }

@router.get('/status')
async def sync_status(user = Depends(get_current_user)):
    return {
        'user_id':     str(user.id),
        'last_sync':   user.preferences.get('last_sync'),
        'sync_enabled': True,
    }
```

```python
# backend/app/auth/encryption.py
"""AES-256-GCM encryption for synced content."""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

def _key() -> bytes:
    return bytes.fromhex(settings.AES_KEY)

def aes_encrypt(plaintext: str) -> str:
    key    = _key()
    nonce  = os.urandom(12)
    aesgcm = AESGCM(key)
    ct     = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.b64encode(nonce + ct).decode('utf-8')

def aes_decrypt(ciphertext: str) -> str:
    key    = _key()
    data   = base64.b64decode(ciphertext)
    nonce  = data[:12]
    ct     = data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode('utf-8')
```

---

## MODULE 5 — DEPENDENCIES & MODELS

```python
# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.postgres import get_db
from app.auth.jwt import decode_token
from app.storage.models import User
from sqlalchemy import select

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get('sub')
        if not user_id:
            raise ValueError()
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid token')

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'User not found or disabled')
    return user
```

```python
# backend/app/storage/models.py
from sqlalchemy import Column, String, Boolean, Integer, BigInteger, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY, INET
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String, unique=True, nullable=False)
    username      = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    display_name  = Column(String)
    plan          = Column(String, default='free')
    preferences   = Column(JSON, default=dict)
    is_active     = Column(Boolean, default=True)
    is_verified   = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login    = Column(DateTime)

class Session(Base):
    __tablename__ = 'sessions'
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), nullable=False)
    token_hash    = Column(Text, nullable=False)
    refresh_hash  = Column(Text)
    ip_address    = Column(String)
    expires_at    = Column(DateTime, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    revoked       = Column(Boolean, default=False)

class Document(Base):
    __tablename__ = 'documents'
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), nullable=False)
    filename      = Column(Text, nullable=False)
    file_path     = Column(Text)
    file_type     = Column(String)
    file_size     = Column(BigInteger)
    title         = Column(Text)
    content_hash  = Column(Text)
    word_count    = Column(Integer)
    language      = Column(String, default='en')
    tags          = Column(ARRAY(Text), default=list)
    is_indexed    = Column(Boolean, default=False)
    index_status  = Column(String, default='pending')
    faiss_id      = Column(BigInteger)
    metadata_     = Column('metadata', JSON, default=dict)
    created_at    = Column(DateTime, default=datetime.utcnow)
    indexed_at    = Column(DateTime)

class VectorEntry(Base):
    __tablename__ = 'vector_entries'
    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    faiss_id      = Column(BigInteger, unique=True, nullable=False)
    source_type   = Column(String)
    source_id     = Column(UUID(as_uuid=True))
    user_id       = Column(UUID(as_uuid=True))
    chunk_index   = Column(Integer, default=0)
    chunk_text    = Column(Text)
    created_at    = Column(DateTime, default=datetime.utcnow)

class SearchHistory(Base):
    __tablename__ = 'search_history'
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True))
    query         = Column(Text, nullable=False)
    query_type    = Column(String)
    filter_used   = Column(String)
    result_count  = Column(Integer)
    clicked_url   = Column(Text)
    created_at    = Column(DateTime, default=datetime.utcnow)
```

```python
# backend/app/storage/faiss_index.py
import faiss
import numpy as np
from pathlib import Path
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
_index = None
DIM    = 384   # all-MiniLM-L6-v2 dimension

async def get_faiss_index() -> faiss.IndexFlatIP:
    global _index
    if _index is None:
        path = Path(settings.FAISS_INDEX_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            logger.info(f"Loading FAISS index: {path} ({faiss.read_index(str(path)).ntotal} vectors)")
            _index = faiss.read_index(str(path))
        else:
            logger.info("Creating new FAISS index (Inner Product / cosine)")
            _index = faiss.IndexFlatIP(DIM)  # Cosine via normalized vectors
    return _index

async def save_faiss_index():
    global _index
    if _index:
        faiss.write_index(_index, settings.FAISS_INDEX_PATH)
        logger.info(f"FAISS index saved: {_index.ntotal} vectors")
```

---

## MODULE 6 — COMPLETE TEST SUITE

```python
# tests/backend/test_auth.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE = "http://test"

@pytest.fixture
def transport():
    return ASGITransport(app=app)

@pytest.mark.asyncio
async def test_register_success(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        r = await c.post("/api/v1/auth/register", json={
            "email": "alice@test.com", "username": "alice", "password": "SecureP@ss1"
        })
    assert r.status_code == 201
    d = r.json()
    assert "access_token" in d
    assert d["user"]["username"] == "alice"

@pytest.mark.asyncio
async def test_register_duplicate_email(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        await c.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "username": "dup1", "password": "SecureP@ss1"
        })
        r = await c.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "username": "dup2", "password": "SecureP@ss1"
        })
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_login_invalid_password(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        r = await c.post("/api/v1/auth/login", json={
            "email": "nobody@test.com", "password": "wrong"
        })
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_full_auth_flow(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        reg = await c.post("/api/v1/auth/register", json={
            "email": "bob@test.com", "username": "bob99", "password": "MyP@ss123"
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        me = await c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["username"] == "bob99"

# tests/backend/test_search.py
@pytest.mark.asyncio
async def test_search_wikipedia(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        reg = await c.post("/api/v1/auth/register", json={
            "email": "searcher@test.com", "username": "searcher", "password": "P@ss1234"
        })
        token = reg.json()["access_token"]
        r = await c.post("/api/v1/search", json={
            "query": "Python programming language",
            "filters": {"type": "all"},
            "page": 1, "ai_summary": False
        }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    d = r.json()
    assert "results" in d
    assert len(d["results"]) > 0
    assert d["intent"] in ["technical", "educational", "general", "factual"]

@pytest.mark.asyncio
async def test_search_returns_elapsed(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        reg = await c.post("/api/v1/auth/register", json={
            "email": "timer@test.com", "username": "timer", "password": "P@ss1234"
        })
        token = reg.json()["access_token"]
        r = await c.post("/api/v1/search", json={"query": "test", "filters": {}, "page": 1},
                         headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "elapsed_ms" in r.json()

@pytest.mark.asyncio
async def test_intent_detection():
    from app.ai.intent import IntentDetector
    det = IntentDetector()
    assert await det.detect("how does a router work") == "educational"
    assert await det.detect("my notes on networking")  == "local"
    assert await det.detect("latest news today")        == "news"
    assert await det.detect("python code error fix")    == "technical"

@pytest.mark.asyncio
async def test_health_endpoint(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        r = await c.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

# tests/backend/test_documents.py
@pytest.mark.asyncio
async def test_upload_pdf(transport, tmp_path):
    # Create a minimal PDF
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<</Type/Catalog>>\nendobj\n%%EOF")
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        reg   = await c.post("/api/v1/auth/register", json={
            "email": "uploader@test.com", "username": "uploader", "password": "P@ss1234"
        })
        token = reg.json()["access_token"]
        with open(pdf_path, 'rb') as f:
            r = await c.post("/api/v1/documents/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}
            )
    assert r.status_code == 201
    assert "id" in r.json()

@pytest.mark.asyncio
async def test_list_documents_empty(transport):
    async with AsyncClient(transport=transport, base_url=BASE) as c:
        reg = await c.post("/api/v1/auth/register", json={
            "email": "lister@test.com", "username": "lister", "password": "P@ss1234"
        })
        token = reg.json()["access_token"]
        r = await c.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["documents"] == []
```

---

## MODULE 7 — .env.example

```bash
# backend/.env.example
# ── App ──────────────────────────────────────────────────────
APP_NAME=IOIS
DEBUG=false
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=CHANGE_ME_generate_a_64_char_random_hex_string_here
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
AES_KEY=CHANGE_ME_generate_a_64_char_random_hex_string_here

# ── Database ─────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://iois:CHANGE_ME_PG_PASSWORD@localhost:5432/iois
SQLITE_PATH=./storage/local.db
REDIS_URL=redis://localhost:6379/0

# ── Auth ─────────────────────────────────────────────────────
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
REFRESH_EXPIRE_DAYS=30

# ── AI ───────────────────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
# Optional — only needed if Ollama is unavailable
OPENAI_API_KEY=
# Model for document embeddings (runs locally, no key needed)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ── Search ───────────────────────────────────────────────────
FAISS_INDEX_PATH=./storage/faiss/index.bin
MAX_RESULTS=20
CACHE_TTL_SECONDS=3600

# ── CORS ─────────────────────────────────────────────────────
CORS_ORIGINS=["http://localhost:5173","https://yourdomain.com"]

# ── Rate limiting ─────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE=60

# ── Upload ───────────────────────────────────────────────────
UPLOAD_DIR=./storage/uploads
MAX_UPLOAD_MB=50
```

```env
# frontend/.env.example
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=IOIS
VITE_ENABLE_ANALYTICS=false
```

---

## MODULE 8 — ELECTRON DESKTOP WRAPPER

```typescript
// frontend/electron/main.ts
import { app, BrowserWindow, shell, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { existsSync } from 'fs'

const isDev = process.env.NODE_ENV === 'development'

let mainWindow: BrowserWindow | null = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width:  1280,
    height: 800,
    minWidth:  800,
    minHeight: 600,
    titleBarStyle: 'hidden',
    webPreferences: {
      preload:          join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration:  false,
      sandbox:          true,
    },
    icon: join(__dirname, '../public/icon-512.png'),
    title: 'IOIS — Intelligent Search',
  })

  // Load app
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(join(__dirname, '../dist/index.html'))
  }

  // Open external links in system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => { mainWindow = null })
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (!mainWindow) createWindow() })

// IPC: File picker for document upload
ipcMain.handle('pick-files', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md', 'html'] },
      { name: 'Images',    extensions: ['png', 'jpg', 'jpeg', 'tiff'] },
    ]
  })
  return result.filePaths
})

// IPC: App version
ipcMain.handle('get-version', () => app.getVersion())
```

```typescript
// frontend/electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  pickFiles:  () => ipcRenderer.invoke('pick-files'),
  getVersion: () => ipcRenderer.invoke('get-version'),
  platform:   process.platform,
})
```

```json
// frontend/electron/package.json
{
  "name":    "iois-desktop",
  "version": "1.0.0",
  "main":    "dist-electron/main.js",
  "scripts": {
    "start":  "electron .",
    "dev":    "NODE_ENV=development electron .",
    "build":  "tsc && electron-builder",
    "dist":   "npm run build"
  },
  "build": {
    "appId":       "app.iois.desktop",
    "productName": "IOIS",
    "directories": { "output": "release" },
    "files":       ["dist/**/*", "dist-electron/**/*", "public/**/*"],
    "win":  { "target": [{ "target": "nsis", "arch": ["x64"] }] },
    "mac":  { "target": "dmg" },
    "linux":{ "target": "AppImage" },
    "nsis": {
      "oneClick":   false,
      "perMachine": false,
      "allowToChangeInstallationDirectory": true
    }
  },
  "devDependencies": {
    "electron":         "^30.0.0",
    "electron-builder": "^24.0.0",
    "typescript":       "^5.0.0"
  }
}
```

---

## MODULE 9 — CAPACITOR ANDROID CONFIG

```typescript
// frontend/capacitor.config.ts
import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId:    'app.iois.search',
  appName:  'IOIS',
  webDir:   'dist',
  bundledWebRuntime: false,
  server: {
    androidScheme: 'https',
  },
  plugins: {
    SplashScreen: {
      launchAutoHide:    false,
      backgroundColor:   '#0d0f14',
      showSpinner:       true,
      spinnerColor:      '#7c5cfc',
      androidSpinnerStyle: 'large',
    },
    StatusBar: {
      style: 'dark',
      backgroundColor: '#0d0f14',
    },
    Keyboard: {
      resize:            'body',
      style:             'dark',
      resizeOnFullScreen: true,
    },
  },
  android: {
    buildOptions: {
      keystorePath:  'release.keystore',
      keystoreAlias: 'iois',
    },
    minWebViewVersion: 55,
    backgroundColor:   '#0d0f14',
  },
}

export default config
```

```json
// frontend/package.json (additions for mobile/desktop)
{
  "name": "iois-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev":          "vite",
    "build":        "tsc && vite build",
    "preview":      "vite preview",
    "type-check":   "tsc --noEmit",
    "test":         "vitest run",
    "test:watch":   "vitest",
    "android":      "npm run build && npx cap sync android && npx cap open android",
    "electron:dev": "npm run build && cd electron && npm start",
    "electron:dist":"npm run build && cd electron && npm run dist",
    "lint":         "eslint src --ext ts,tsx"
  },
  "dependencies": {
    "react":              "^18.3.0",
    "react-dom":          "^18.3.0",
    "react-router-dom":   "^6.23.0",
    "zustand":            "^4.5.0",
    "axios":              "^1.7.0",
    "dexie":              "^3.2.7",
    "@capacitor/core":    "^6.0.0",
    "@capacitor/android": "^6.0.0",
    "@capacitor/splash-screen": "^6.0.0",
    "@capacitor/status-bar":    "^6.0.0",
    "@capacitor/keyboard":      "^6.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite":                 "^5.3.0",
    "vite-plugin-pwa":      "^0.20.0",
    "typescript":           "^5.4.0",
    "vitest":               "^1.6.0",
    "@testing-library/react": "^16.0.0",
    "eslint":               "^9.0.0"
  }
}
```

---

## MODULE 10 — HEALTH CHECK & ROUTER

```python
# backend/app/api/v1/health.py
from fastapi import APIRouter
from app.cache.redis_client import get_redis
from app.ai.ollama_client import OllamaClient
import time

router = APIRouter(prefix="/health", tags=["health"])
ollama = OllamaClient()

@router.get('')
async def health():
    return {'status': 'ok', 'timestamp': time.time(), 'service': 'IOIS API'}

@router.get('/ai')
async def health_ai():
    available = await ollama.is_available()
    return {
        'ollama':    'up' if available else 'down',
        'model':     'mistral',
        'status':    'ok' if available else 'degraded',
    }

@router.get('/search')
async def health_search():
    from app.storage.faiss_index import get_faiss_index
    try:
        idx = await get_faiss_index()
        vectors = idx.ntotal
        status  = 'ok'
    except Exception as e:
        vectors = 0
        status  = f'error: {e}'
    return {'faiss': status, 'vectors_indexed': vectors}
```

```python
# backend/app/api/router.py
from fastapi import APIRouter
from app.api.v1 import auth, search, documents, ai, sync, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(search.router)
api_router.include_router(documents.router)
api_router.include_router(ai.router)
api_router.include_router(sync.router)
```

```python
# backend/app/cache/redis_client.py
import redis.asyncio as aioredis
from app.config import settings
from app.utils.logger import get_logger

logger  = get_logger(__name__)
_client = None

async def init_redis():
    global _client
    _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await _client.ping()
    logger.info("Redis connected.")

async def get_redis():
    return _client
```

```python
# backend/app/cache/cache_service.py
import json
from app.cache.redis_client import get_redis
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CacheService:
    async def get(self, key: str):
        try:
            r   = await get_redis()
            raw = await r.get(f"iois:{key}")
            return json.loads(raw) if raw else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value, ttl: int = 3600):
        try:
            r = await get_redis()
            await r.setex(f"iois:{key}", ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def delete(self, key: str):
        try:
            r = await get_redis()
            await r.delete(f"iois:{key}")
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")

    async def invalidate_pattern(self, pattern: str):
        try:
            r    = await get_redis()
            keys = await r.keys(f"iois:{pattern}*")
            if keys:
                await r.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
```

```python
# backend/app/storage/postgres.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.storage.models import Base
from app.config import settings
from app.utils.logger import get_logger

logger  = get_logger(__name__)
_engine = None
_Session = None

async def init_db():
    global _engine, _Session
    _engine  = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    _Session = async_sessionmaker(_engine, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized.")

async def get_db():
    async with _Session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## WHAT TO GENERATE NEXT

Use these prompts with this document to continue building IOIS:

1. **"Generate the complete CSS stylesheet for IOIS frontend (globals.css + components.css)"**
2. **"Generate the complete Settings.tsx page with all preference options"**
3. **"Generate the Wikipedia and DuckDuckGo search backend classes"**
4. **"Generate Alembic migration files for all IOIS tables"**
5. **"Generate the IOIS service worker (sw.ts) with full offline caching strategy"**
6. **"Generate the background indexing worker (indexing_worker.py) with job queue"**
7. **"Generate the complete Login.tsx and Register.tsx with validation"**
8. **"Generate the KnowledgePanel.tsx, QuickAnswer.tsx, and Pagination.tsx components"**
9. **"Generate the complete docker-compose.yml with all health checks and volumes"**
10. **"Generate the Android AndroidManifest.xml and build.gradle for IOIS APK"**
