# Release Checklist — v1.1

## Pre-release

- [ ] `cd backend && pytest` passes
- [ ] `npm run e2e` passes (with backend + frontend running)
- [ ] `cd frontend && npm run build` succeeds
- [ ] Migration 002 applied on staging DB
- [ ] `JWT_SECRET` set in production
- [ ] `CORS_ORIGINS` restricted to production domains
- [ ] Optional: `OPENAI_API_KEY`, `BRAVE_API_KEY` configured

## Docker release

- [ ] `cd docker && docker compose -f docker-compose.prod.yml build`
- [ ] Health check: `curl http://localhost:8000/health`
- [ ] Upload test document and verify vector search

## Mobile release

- [ ] `cd mobile && npm run build`
- [ ] `npx cap sync`
- [ ] Android: `./gradlew assembleRelease` (signing configured)
- [ ] iOS: Archive in Xcode (macOS required)
- [ ] Test offline sync and push permissions on device

## Post-release

- [ ] Monitor `/health` and error logs
- [ ] Verify vector worker processing (if Redis enabled)
- [ ] Publish release notes referencing ROADMAP_v1.1.md
