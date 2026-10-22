# Nebula Search — Docker Architecture and Operations

## 1. Services

| Service   | Image/Build               | Ports               | Role                            |
|-----------|---------------------------|---------------------|---------------------------------|
| postgres  | postgres:16-alpine        | 5432                | Primary relational database     |
| redis     | redis:7-alpine            | 6379                | Distributed cache & queues      |
| backend   | docker/Dockerfile         | 8000                | FastAPI REST server             |
| worker    | docker/Dockerfile         | internal            | Background indexing jobs        |
| scheduler | docker/Dockerfile         | internal            | Periodic background heartbeat   |
| frontend  | docker/frontend.Dockerfile| 3000 (prod) / 5173 (dev) | Vite dev or nginx static |
| nginx     | nginx:1.25-alpine         | 80                  | Reverse proxy / static hosting  |
| storage   | minio/minio               | 9000/9001           | S3-compatible object storage    |
| monitoring| prom/prometheus           | 9090                | Metrics scrape & alerting       |

## 2. Networking

* `nebula-internal` (bridge, `internal: true`) — postgres, redis, backend, worker, scheduler, storage  
* `nebula-public` (bridge) — backend, frontend, nginx, storage, monitoring

Only `backend` and `nginx` expose ports externally. All service-to-service traffic stays on the internal bridge.

## 3. Startup Order

1. infrastructure: postgres, redis
2. data: storage (minio)
3. compute: backend (waits for postgres + redis health)
4. background: worker, scheduler
5. edge: frontend
6. proxy: nginx (waits for frontend + backend)
7. monitoring: prometheus

Startup is enforced by `depends_on` with `condition: service_healthy` on every dependent service.

## 4. Data Volumes

| Volume         | Service   | Backup Strategy               | Restore                        |
|----------------|-----------|-------------------------------|--------------------------------|
| postgres-data  | postgres  | Nightly `pg_dump` to `.sql`   | Restore via `psql < backup.sql` |
| nebula-storage | backend   | Included in `database/backups`| Restore from backup archive    |
| minio-data     | storage   | Recurring minio mirror batch  | Replace volume or remote copy   |
| prometheus-data| monitoring | Remote write / snapshots     | Restore from snapshot          |

Backups are stored under `database/backups/`. Use `scripts/backup.ps1`.

## 5. Security Hardening

* **Non-root execution**: backend (user `nebula`), frontend (user `nginx`), nginx (user `nginx`).
* **Multi-stage images**: backend uses `python:3.11-slim` with a builder stage; frontend uses `node:20-alpine` build + `nginx:1.25-alpine`.
* **Read-only mounts**: in production, source code is mounted read-only.
* **Security headers**: nginx sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy`.
* **Secrets handling**: environment variables injected via `.env` (never committed). Production should use Docker Secrets or Vault.
* **Network isolation**: internal services are unreachable from outside the bridge.
* **Health checks**: every service has a healthcheck to enforce startup ordering.
* **Image minimization**: one service per container, minimal base images, no build tools in runtime images.

## 6. Development Workflow

```powershell
# First-time setup
copy backend\.env.example backend\.env

# Start all services in hot-reload mode
.\scripts\start.ps1

# Tail logs
.\scripts\logs.ps1                  # all services
.\scripts\logs.ps1 backend          # single service

# Apply database migrations
.\scripts\migrations.ps1

# Run tests inside the backend container
.\scripts\test.ps1

# Stop services
.\scripts\stop.ps1

# Nuclear reset (removes volumes, rebuilds images)
.\scripts\reset.ps1

# Backup current database
.\scripts\backup.ps1

# Restore from backup
.\scripts\restore.ps1 .\database\backups\nebula_20240101_120000.sql
```

The dev override (`docker/docker-compose.dev.yml`) enables:
* Hot-reload backend via `uvicorn --reload`
* Editable mounts for `backend/`, `backend/vector/`, `frontend/`, and `tests/`
* Vite dev server on `frontend:5173` (proxied through nginx on `:3000`)
* Faster health checks (5–10s intervals)

## 7. Production Workflow

```powershell
# Configure secrets
copy .env.example .env
notepad .env
notepad backend\.env

# Build and start in production mode
.\scripts\start.ps1 prod

# Tail logs
.\scripts\logs.ps1

# Apply migrations
.\scripts\migrations.ps1

# Backup
.\scripts\backup.ps1
```

The production override (`docker-compose.prod.yml`) adds:
* 2 backend replicas (Scaling via `deploy.replicas`)
* 2 worker replicas
* Resource limits on every service
* Log rotation (`json-file`, max 10MB × 3 files)
* `restart_policy` with automatic failure recovery
* `failure_action: rollback` for zero-downtime updates

## 8. Container Dependency Map

```
postgres <-- backend
postgres <-- worker
postgres <-- scheduler
redis     <-- backend
redis     <-- worker
backend   <-- frontend
backend   <-- nginx
frontend  <-- nginx
```

## 9. Deployment Checklist

* [ ] `backend/.env` configured with production secrets (`JWT_SECRET`, `DATABASE_URL`, etc.)
* [ ] `POSTGRES_PASSWORD` rotated from default
* [ ] `.env` and `backend/.env` are not committed to version control
* [ ] Images tagged with git SHA + `latest` and pushed to registry
* [ ] PostgreSQL backups scheduled (e.g., GitHub Actions cron, host cron)
* [ ] Restore procedure verified on a staging database
* [ ] Resource limits set in `docker-compose.prod.yml`
* [ ] Logging configured (docker json-file, external ELK/Grafana/Loki)
* [ ] Health checks return `healthy` for all services
* [ ] Nginx SSL/TLS termination configured (Let's Encrypt / cloud LB)
* [ ] CI/CD pipeline: build → test → scan → push → deploy
* [ ] Image scanning: run Trivy or Grype on final images before deployment
* [ ] Rollback procedure documented and tested

## 10. Common Failure Points

* **Port conflicts**: Ensure ports 80, 3000, 5173, 5432, 6379, 8000, 9000, 9001, 9090 are free on the host or remap in `.env`.
* **Out of memory**: Reduce `deploy.resources.limits.memory` or worker replicas on low-RAM hosts.
* **Slow builds**: Enable BuildKit (`DOCKER_BUILDKIT=1`) for layer caching.
* **CORS mismatch**: Ensure `CORS_ORIGINS` matches the frontend origin exactly. Nginx proxies `/api/` to backend.
* **PostgreSQL readiness**: Backend waits for healthy postgres. If migrations fail, verify `DATABASE_URL` and that the volume directory permissions are correct.
* **Missing `JWT_SECRET`**: Fatal in production — tokens will be invalidated on every restart. Set explicitly in `backend/.env`.
* **Tests running in container without source**: Ensure `tests/` is mounted in dev override or run pytest on the host.
* **Redis SSL**: Some architectures require `rediss://` TLS URLs. Configure TLS if required.
* **File permissions on volumes**: On some hosts, bind-mounted files may be owned by root. Fix with `chown` or disable user namespace remap in Docker daemon.

## 11. CI/CD Integration

Build and test pipeline example (GitHub Actions / GitLab CI):

```yaml
env:
  DOCKER_BUILDKIT: 1

steps:
  - run: docker compose -f docker/docker-compose.yml -f docker-compose.prod.yml build
  - run: docker compose -f docker/docker-compose.yml -f docker-compose.prod.yml up -d
  - run: .\scripts\migrations.ps1
  - run: .\scripts\test.ps1
  - run: docker tag nebula-backend:latest registry.example.com/nebula-backend:$GITHUB_SHA
  - run: docker push registry.example.com/nebula-backend:$GITHUB_SHA
```

Container registry strategy:
* Tag images with git SHA + `latest`.
* In production manifests (Swarm / K8s / Compose), pin by digest (`image: registry/nebula-backend@sha256:...`) for reproducibility.
* Scan images with Trivy or Grype before push.

## 12. BuildKit Optimization

BuildKit is enabled by default in Docker Desktop and recent Docker Engine releases. For extra speed:

```powershell
$env:DOCKER_BUILDKIT = "1"
docker compose -f docker/docker-compose.yml -f docker-compose.override.yml build --no-cache
```

Caching mounts (`--mount=type=cache`) are built into the `Dockerfile` for `pip`.

## 13. Monitoring and Observability

Prometheus (`monitoring:9090`) scrapes:
* `backend:8000/metrics` (if exposed)
* `postgres:9187` (requires `postgres_exporter`)
* `redis:9121` (requires `redis_exporter`)
* `node-exporter:9100` (requires host agent)

Extend `infra/prometheus.yml` with additional scrape configs as needed.

## 14. Cross-Platform Scripts

For CI/CD or WSL / Linux / macOS environments, equivalent `bash` scripts are provided in `scripts/`:

```bash
./scripts/start.sh            # dev mode
./scripts/start.sh prod       # production mode
./scripts/stop.sh
./scripts/logs.sh              # all services
./scripts/logs.sh backend      # single service
./scripts/migrations.sh prod   # migrations in prod
./scripts/test.sh
./scripts/reset.sh prod        # nuclear reset for prod
./scripts/backup.sh
./scripts/restore.sh <file.sql>
./scripts/build.sh prod        # production build
./scripts/build.sh             # dev build
```

PowerShell scripts remain the primary interface on Windows. Bash scripts require `bash` (WSL, Git Bash, or native) and Docker CLI access.
