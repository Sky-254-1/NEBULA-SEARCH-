# Nebula Search v1.1 Roadmap

## Completed in v1.1

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | Playwright E2E suite (`tests/e2e/`) | Done |
| 1 | CI E2E job with retry strategy | Done |
| 2 | Vector pipeline (`backend/vector/`) | Done |
| 2 | DB migration 002 (chunks, embeddings, citations, search_sessions) | Done |
| 2 | Hybrid search API (`/api/v1/vector/*`) | Done |
| 3 | Capacitor mobile shell (`mobile/`) | Done |
| 3 | Native plugins (camera, share, voice, sync) | Done |

## v1.2 (planned)

- Biometric auth via `@capacitor-community/biometric`
- OpenAI embeddings as default when key present
- FAISS or pgvector for large-scale vector storage
- E2E coverage gate at 95% in CI

## v1.3 (planned)

- On-device voice search polish
- Push notification backend (FCM/APNs)
- Document preview in mobile WebView

## v2.0 (future)

- React Native evaluation for on-device LLM
- Federated search across devices
- Enterprise SSO
