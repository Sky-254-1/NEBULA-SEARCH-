# Nebula Search v1.0 — Implementation Plan

## Current State (v1.0)

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Frontend ↔ Backend | **Complete** | Auth, search, AI streaming, history, pagination, protected routes |
| 2 Frontend Modularization | **Complete** | React + Vite, lazy routes, modular API layer |
| 3 Database Evolution | **Complete** | SQLite + PostgreSQL, 7 tables, full repositories |
| 4 Redis Platform | **Complete** | Cache, rate limiting, job queue with memory fallback |
| 5 Offline AI | **Complete** | OpenAI, Ollama, GGUF, DuckDuckGo with failover + streaming |
| 6 Search Orchestrator | **Complete** | Expand → parallel → rank → dedupe → cache |
| 7 Complete PWA | **Complete** | manifest, SW, install prompt, offline search cache |
| 8 Storage Platform | **Complete** | Upload, settings, exports API + storage dirs |
| 9 Production Deployment | **Complete** | Docker, prod compose, CI, deploy guide |
| 10 Mobile Roadmap | **Doc** | See [MOBILE.md](MOBILE.md) — Capacitor path for v1.1 |

**Full architecture:** See [V1.0_COMPLETE.md](V1.0_COMPLETE.md)

## Rollout Phases

1. **v1.0-alpha** — Backend platform + React shell ✅
2. **v1.0-beta** — Full integration + storage API ✅
3. **v1.0-rc** — Production hardening, CI frontend build ✅
4. **v1.0 GA** — Current release target ✅
5. **v1.1** — Capacitor mobile, vector search, Playwright E2E

## Quick Start

```bash
# Dev
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# Production-like
cd docker && docker compose up --build
```
