# Deployment Strategy — NEBULA-SEARCH

This document defines the **primary deployment path** and **when to use each configuration** for the Nebula Search Engine.

## Overview

Nebula Search supports multiple deployment approaches, but **only one should be the primary path** for production workloads.

**Recommendation:**

- **Primary Deployment:** Docker Compose (specifically `docker-compose.prod.yml`)
- **Kubernetes:** Only for specific orchestration needs (see [When to Use Kubernetes](#when-to-use-kubernetes))
- **Frontend:** Keep Vercel deployment

## Deployment Configurations

### File Locations

All Docker Compose files are at the project root:
- `docker-compose.yml` — Full stack development
- `docker-compose.dev.yml` — Development overrides
- `docker-compose.prod.yml` — **Production stack (primary recommended)**
- `docker-compose.staging.yml` — Staging environment
- `docker-compose.scale.yml` — Scaled deployment modifiers

Additional configurations:
- `docker/` — Dockerfiles and Nginx configurations
- `infra/kubernetes/` — Kubernetes manifests (for reference, not primary)
- `vercel.json` — Frontend deployment (Vercel)

## Primary Deployment Path: Docker Compose

### Production: `docker-compose.prod.yml`

**Use this for production deployments.**

**Why this is the primary configuration:**
- Complete production stack in a single file
- Production-optimized resource limits (CPU/memory)
- Security hardening (`read_only: true`, `cap_drop: ALL`, `security_opt`)
- Health checks for all services
- SSL/TLS termination via Nginx
- Multi-tier networking (`nebula-public` and `nebula-internal`)
- Production-grade database and cache configurations

**Services included:**
- PostgreSQL 16 with pgvector and advanced tuning
- Redis 7 with persistence and memory limits
- FastAPI backend (production Dockerfile, read-only filesystem)
- Background worker for document indexing
- Scheduler for recurring tasks
- Frontend via Nginx reverse proxy
- MinIO for object storage
- Elasticsearch 8 for vector and full-text search
- RabbitMQ for message queues
- Kafka for event streaming
- Prometheus + Grafana for observability
- Certbot for Let's Encrypt SSL

**Deployment:**

```bash
# Set production environment variables
cp .env.example .env
# Edit .env with production values (see below)

# Deploy
docker compose -f docker-compose.prod.yml up -d --build

# Run database migrations
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# Verify
docker compose -f docker-compose.prod.yml ps
```

**Required Production Environment Variables:**

```env
# Security (generate strong random values)
JWT_SECRET=<32+ character random string>
SESSION_SECRET=<32+ character random string>
ENCRYPTION_KEY=<32 character random string>

# Database
POSTGRES_PASSWORD=<secure password>
POSTGRES_USER=nebula
POSTGRES_DB=nebula

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO (object storage)
MINIO_ROOT_USER=<access key>
MINIO_ROOT_PASSWORD=<secure password>

# Storage backend (s3 or local)
STORAGE_BACKEND=s3

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200

# RabbitMQ
RABBITMQ_USER=<user>
RABBITMQ_PASSWORD=<secure password>

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# CORS (restrict to your domain)
CORS_ORIGINS=https://your-domain.com

# Optional AI providers
OPENAI_API_KEY=<your-key>
OLLAMA_URL=http://ollama:11434

# Monitoring
GRAFANA_ADMIN_PASSWORD=<secure password>
```

**Recommended nginx configuration:**
- Use `docker/nginx.prod.conf` (includes rate limiting, security headers)
- Configure SSL certificates via Certbot
- Set up HTTPS redirect

### Development: `docker-compose.yml`

**Use this for local development and testing.**

This is a simplified version of the production stack without:
- Security hardening (read-only filesystem, cap_drop)
- Production resource limits
- Kafka and RabbitMQ
- Redis appendonly persistence
- Many observability services

**Services:**
- PostgreSQL 16
- Redis (no persistence)
- FastAPI backend
- React frontend
- Nginx reverse proxy
- MinIO storage
- Prometheus (basic)

**Deployment:**

```bash
# Quick start
docker compose up -d --build

# Stop
docker compose down

# View logs
docker compose logs -f
```

### Development Overrides: `docker-compose.dev.yml`

**Use this for development with hot reload.**

This file is designed to be combined with other compose files using the `-f` flag:

```bash
# Development with hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

**Overrides:**
- Backend with `Dockerfile.dev` and volume mounts for hot reload
- Frontend with hot reload enabled
- Environment: `APP_ENV=development`, `LOG_LEVEL=debug`
- Debug ports exposed for all services

### Staging: `docker-compose.staging.yml`

**Use this for staging/pre-production testing.**

This configuration mirrors production but with:
- Separate database (`nebula_staging`)
- Reduced resource limits
- Two backend replicas for load testing
- Docker image registry references (`ECR_REGISTRY`)

**Deployment:**

```bash
# Set environment variables
cp .env.staging.example .env.staging

# Deploy
docker compose -f docker-compose.staging.yml up -d
```

### Scaling: `docker-compose.scale.yml`

**Use this to scale the production stack.**

This file is designed to be merged with `docker-compose.prod.yml`:

```bash
# Scale backend to 3 replicas and worker to 2
docker compose -f docker-compose.prod.yml -f docker-compose.scale.yml up -d \
  --scale backend=3 \
  --scale worker=2
```

**Scaling effects:**
- Backend: 2 CPU / 2GB memory per replica (max 4 workers)
- Worker: 2 CPU / 1GB memory per replica
- Scheduler: 1 CPU / 512MB
- PostgreSQL: 4 CPU / 4GB memory
- Redis: 2 CPU / 2GB memory

## When to Use Kubernetes

**Kubernetes should NOT be your primary deployment path.**

Use Kubernetes only if you have specific orchestration needs:
- **Multi-region deployments** requiring sophisticated traffic management
- **Complex multi-tenant architectures** with per-tenant isolation
- **Existing Kubernetes infrastructure** where consistency matters more than simplicity
- **Advanced autoscaling requirements** beyond Docker's built-in capabilities

### Why Not Kubernetes as Primary?

- **Complexity:** Requires cluster management, Helm charts, ingress controllers
- **Overkill:** Docker Compose handles most use cases simpler and more directly
- **Cost:** Managed Kubernetes (EKS, GKE, AKS) is significantly more expensive
- **Maintenance:** Additional operational burden (cluster upgrades, node management)
- **Startup Time:** Longer deployment cycles for small teams

### Current Kubernetes Status

The `infra/kubernetes/` manifests exist for:
- Reference architecture
- Potential future migration
- Teams that already use Kubernetes

**Current issues with Kubernetes manifests:**
- `infra/kubernetes/secrets.yaml` contains base64-encoded secrets (security risk)
- No Helm chart (requires manual manifest editing)
- No CI/CD integration documented

### If You Must Use Kubernetes

1. **Move secrets to external management:**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets with external secrets operator

2. **Use Helm charts:**
   ```bash
   helm install nebula ./charts/nebula \
     --set secrets.jwtSecret=$(openssl rand -base64 32) \
     --set secrets.databasePassword=$(openssl rand -base64 24)
   ```

3. **Automate with CI/CD:**
   - Use Argo CD or Flux for GitOps
   - Deploy from CI/CD, not locally

## Frontend Deployment: Vercel

**Keep frontend deployment on Vercel.**

The `vercel.json` is already configured for:
- Next.js/React build optimization
- PWA manifest and service worker
- Security headers (CSP, HSTS, XSS protection)
- Cache optimization (immutable assets)
- Rewrites for SPA routing

**Deployment:**
1. Connect your repository to Vercel
2. Add environment variables (from `frontend/.env.example`)
3. Deploy

## Development vs Production Recommendations

### Development

**Recommended Setup:**
```bash
# Use the combined dev configuration
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

**Why:**
- Hot reload for backend (FastAPI + Uvicorn `--reload`)
- Hot reload for frontend (Vite dev server)
- Environment variables from `.env.development`
- Debug logging enabled
- All ports exposed for local testing

**Alternative (Manual):**
```bash
# Backend (optional)
cd backend
uvicorn app.main:app --reload

# Frontend (optional)
cd frontend
npm run dev
```

### Production

**Recommended Setup:**
```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up -d
```

**Why:**
- Security hardening (read-only filesystem, dropped capabilities)
- Resource limits (CPU/memory)
- Multi-tier networking
- Production Docker images
- Health checks and restart policies
- Observability stack included
- SSL/TLS termination

**Not Recommended:**
- Manual deployment without Docker (too many moving parts)
- Kubernetes without existing infrastructure
- Development compose files in production

## Deployment Checklist

### Production Pre-Deployment

- [ ] Generate all secrets (JWT_SECRET, SESSION_SECRET, ENCRYPTION_KEY, etc.)
- [ ] Set `CORS_ORIGINS` to production domain only
- [ ] Configure SSL certificates (Certbot or external)
- [ ] Set up log rotation
- [ ] Configure backup for PostgreSQL and MinIO volumes
- [ ] Set up monitoring alerts (Grafana + Prometheus)
- [ ] Test failover (stop services, verify restart)
- [ ] Run security scan (`docker scan` or Trivy)
- [ ] Verify database migrations run successfully
- [ ] Test file uploads and storage backend
- [ ] Verify search functionality

### Production Post-Deployment

- [ ] Verify all health checks pass
- [ ] Check Prometheus metrics are being collected
- [ ] Verify Grafana dashboards are accessible
- [ ] Test search queries
- [ ] Verify email functionality (SMTP)
- [ ] Check error tracking (Sentry if configured)
- [ ] Verify backups are working
- [ ] Test scaling commands (`--scale`)

## Troubleshooting

### Common Issues

1. **Database connection failures**
   - Verify `POSTGRES_PASSWORD` matches in environment and `DATABASE_URL`
   - Check PostgreSQL container logs: `docker compose logs postgres`
   - Ensure `POSTGRES_INITDB_ARGS` are valid

2. **Redis connection refused**
   - Verify Redis container is healthy: `docker compose ps redis`
   - Check Redis logs: `docker compose logs redis`
   - Ensure `REDIS_URL` format is correct

3. **MinIO access denied**
   - Verify `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`
   - Check MinIO logs: `docker compose logs storage`
   - Ensure bucket exists in MinIO

4. **Search not returning results**
   - Verify Elasticsearch is running: `docker compose ps elasticsearch`
   - Check Elasticsearch logs: `docker compose logs elasticsearch`
   - Verify document indexing worker is running: `docker compose ps worker`

5. **Frontend 502 Bad Gateway**
   - Verify Nginx is running: `docker compose ps nginx`
   - Check Nginx logs: `docker compose logs nginx`
   - Ensure backend is healthy: `docker compose ps backend`

### Useful Commands

```bash
# List all services
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Stop all services
docker compose -f docker-compose.prod.yml down

# Restart a specific service
docker compose -f docker-compose.prod.yml restart backend

# Run one-off command
docker compose -f docker-compose.prod.yml exec backend python -m app.main

# View resource usage
docker compose -f docker-compose.prod.yml stats
```

## Migration Guide: From Multiple Configurations to Single Primary

If you currently use multiple deployment configurations:

1. **Audit current usage:**
   - Which compose files are actually in use?
   - Are there manual deployments?
   - Is Kubernetes being actively used?

2. **Migrate to `docker-compose.prod.yml`:**
   - Copy any custom configurations to `.env` or override files
   - Update CI/CD pipelines to use the new primary file
   - Deprecate other compose files gradually

3. **Update documentation:**
   - Point all deployment guides to this document
   - Update CI/CD workflows
   - Update onboarding documentation

4. **Deprecate Kubernetes (optional):**
   - If not using Kubernetes, archive or remove manifests
   - Document why Docker Compose was chosen

## Summary

| Configuration | Use Case | Status |
|--------------|----------|--------|
| `docker-compose.prod.yml` | Production | **Primary** |
| `docker-compose.yml` | Local development | Secondary |
| `docker-compose.dev.yml` | Dev with hot reload | Optional override |
| `docker-compose.staging.yml` | Staging environment | Optional |
| `docker-compose.scale.yml` | Scaling production | Optional override |
| `infra/kubernetes/` | Advanced orchestration | Reference only |
| `vercel.json` | Frontend deployment | Primary (frontend only) |

**Recommendation:** Use `docker-compose.prod.yml` as the single source of truth for production deployments. Keep Vercel for frontend hosting. Only consider Kubernetes if you have specific orchestration requirements beyond Docker's capabilities.