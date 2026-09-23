# Nebula Search v1.0 — Production Deployment

## Quick Deploy (Docker Compose)

```bash
cd docker
cp ../backend/.env.example ../backend/.env
# Edit ../backend/.env — set JWT_SECRET, API keys

docker compose up --build -d
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Legacy UI | http://localhost:3000/legacy/index.html |

## Production Checklist

- [ ] Set strong `JWT_SECRET` (32+ random bytes)
- [ ] Configure `DATABASE_URL=postgresql://...`
- [ ] Configure `REDIS_URL=redis://...`
- [ ] Set `APP_ENV=production`
- [ ] Add `OPENAI_API_KEY`, `BRAVE_API_KEY`, or `SERPAPI_KEY` as needed
- [ ] Configure TLS termination (nginx / cloud LB)
- [ ] Set up PostgreSQL backups (daily pg_dump)
- [ ] Monitor `/health` endpoint
- [ ] Configure log aggregation

## Scaling Guide

### Single Node (default)
Docker Compose with 1 backend worker — suitable for ≤100 concurrent users.

### Multi-Worker Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
Requires `REDIS_URL` for shared cache and rate limiting.

### Horizontal Scaling
- Run multiple backend containers behind nginx load balancer
- Shared PostgreSQL + Redis + storage volume (NFS/S3 for uploads)
- Sticky sessions not required (stateless JWT)

## TLS Example (nginx)

See `docker/nginx.conf` and `docs/DEPLOYMENT.md` for full TLS configuration.

## Backup Strategy

| Component | Method | Frequency |
|-----------|--------|-----------|
| PostgreSQL | `pg_dump nebula > backup.sql` | Daily |
| Redis | RDB snapshots (optional) | Hourly |
| Storage volume | Volume snapshot / rsync | Daily |
| SQLite (dev) | Copy `nebula.db` | On demand |

## Rollback

1. Stop containers: `docker compose down`
2. Restore PostgreSQL from backup
3. Redeploy previous image tag
4. Verify `/health` returns `status: ok`

## Observability

- **Logs:** Structured stdout from uvicorn (JSON in production recommended)
- **Health:** `GET /health` — checks database + cache connectivity
- **Metrics:** v1.1 will add Prometheus `/metrics` endpoint

## Environment Variables (Production)

```env
APP_ENV=production
DATABASE_URL=postgresql://nebula:SECRET@postgres:5432/nebula
REDIS_URL=redis://redis:6379/0
JWT_SECRET=<generate-with-openssl-rand-hex-32>
CORS_ORIGINS=https://your-domain.com
STORAGE_ROOT=/app/storage
RATE_LIMIT_PER_MINUTE=120
```
