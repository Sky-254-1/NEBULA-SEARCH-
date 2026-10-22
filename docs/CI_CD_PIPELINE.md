# Nebula Search Engine - CI/CD Pipeline

## Overview

The Nebula Search Engine uses a comprehensive CI/CD pipeline built on GitHub Actions with automated deployment and rollback support. The pipeline supports both Docker Compose and Kubernetes deployment targets.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline Flow                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │ Security │───▶│   Test   │───▶│  Build   │               │
│  │  Scan    │    │  Suite   │    │  Images  │               │
│  └──────────┘    └──────────┘    └──────────┘               │
│                       │              │                       │
│                       ▼              ▼                       │
│                 ┌──────────┐    ┌──────────┐               │
│                 │   DB     │    │  Docker  │               │
│                 │Migration │    │  Build   │               │
│                 │  Check   │    │          │               │
│                 └──────────┘    └──────────┘               │
│                       │              │                       │
│                       └──────┬───────┘                       │
│                              ▼                               │
│                       ┌──────────┐                          │
│                       │ Staging  │                          │
│                       │  Deploy  │                          │
│                       └──────────┘                          │
│                              │                               │
│                              ▼                               │
│                       ┌──────────┐                          │
│                       │Production│                          │
│                       │  Deploy  │                          │
│                       └──────────┘                          │
│                              │                               │
│                              ▼                               │
│                       ┌──────────┐                          │
│                       │  Post-   │                          │
│                       │  Deploy  │                          │
│                       │  Monitor │                          │
│                       └──────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Files

### 1. CI Workflow (`.github/workflows/ci.yml`)
- Triggered on push/PR to main/master
- Runs unit tests, frontend build, and E2E tests
- Uploads coverage reports

### 2. Deploy Workflow (`.github/workflows/deploy.yml`)
- Triggered on push to main/master or manual dispatch
- **Jobs:**
  - `rollback` - Manual rollback to previous version
  - `security-scan` - Trivy, Snyk, and secret scanning
  - `test` - Full test suite with PostgreSQL and Redis services
  - `frontend` - Frontend build and test
  - `db-migration-check` - Database migration validation
  - `build` - Docker image build and push to GHCR
  - `deploy-staging` - Deploy to staging environment
  - `deploy-production` - Deploy to production (with concurrency lock)
  - `post-deploy-monitor` - Post-deployment monitoring

## Deployment Strategies

### Docker Compose (Staging/Production)
- **Rolling Update**: Services are updated one at a time
- **Blue/Green**: New containers are started before old ones are stopped
- **Health Check**: Each service is verified before proceeding

### Kubernetes
- **Rolling Update**: Kubernetes native rolling update strategy
- **Max Surge**: 1 extra pod during update
- **Max Unavailable**: 0 (zero-downtime deployments)
- **Rollback**: `kubectl rollout undo` to previous revision

## Rollback Support

### Manual Rollback via GitHub Actions
```bash
# Trigger rollback from GitHub UI
# Go to Actions → Deploy to Production → Run workflow
# Set force_rollback: true
```

### Automated Rollback Script
```bash
# Docker Compose rollback
./scripts/rollback.sh --environment docker-compose --backup ./backups/nebula_20240101.sql.gz

# Kubernetes rollback to specific revision
./scripts/rollback.sh --environment kubernetes --revision 5

# Kubernetes auto-detect previous revision
./scripts/rollback.sh --environment kubernetes

# Production rollback (with database restore)
./scripts/rollback.sh --environment production --backup ./backups/nebula_20240101.sql.gz

# Dry run (show what would happen)
./scripts/rollback.sh --environment kubernetes --dry-run
```

### Rollback Process
1. **Pre-rollback backup**: Creates emergency database snapshot
2. **Database restoration**: Restores from specified backup file
3. **Service redeployment**: Restarts services with previous images
4. **Health verification**: Runs comprehensive health checks
5. **Notification**: Sends Slack notification on completion/failure

## Health Checks

### Health Check Script
```bash
# Run comprehensive health checks
./scripts/health_check.sh

# Check specific services
HEALTH_CHECK_TIMEOUT=5 ./scripts/health_check.sh
```

### What's Checked
- **System Health**: Disk space, memory, CPU load
- **Docker Services**: Container status and health
- **API Endpoints**: Health, API v1, docs, search
- **Database Services**: PostgreSQL and Redis connectivity
- **Smoke Tests**: JSON response format, CORS headers, response time, frontend serving

## Required Secrets

### GitHub Secrets
| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | IAM role for EKS access |
| `AWS_REGION` | AWS region (default: us-east-1) |
| `STAGING_HOST` | Staging server hostname |
| `STAGING_USERNAME` | Staging SSH username |
| `STAGING_SSH_KEY` | Staging SSH private key |
| `PRODUCTION_HOST` | Production server hostname |
| `PRODUCTION_USERNAME` | Production SSH username |
| `PRODUCTION_SSH_KEY` | Production SSH private key |
| `SLACK_WEBHOOK_URL` | Slack notification webhook |
| `ROLLBACK_WEBHOOK_URL` | Rollback trigger webhook |
| `SNYK_TOKEN` | Snyk security scan token |
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub password |

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `REGISTRY` | Container registry | `ghcr.io` |
| `K8S_NAMESPACE` | Kubernetes namespace | `nebula` |
| `DEPLOY_TIMEOUT` | Deployment timeout (seconds) | `300` |
| `HEALTH_CHECK_RETRIES` | Health check retry count | `12` |
| `HEALTH_CHECK_INTERVAL` | Health check interval (seconds) | `10` |

## Database Migrations

### Migration Pipeline
1. **Validation**: Migrations are tested against a clean database
2. **Idempotency**: Verified that running migrations twice is safe
3. **Index Verification**: All required indexes are created
4. **Pre-deploy**: Migrations run before service restart
5. **Rollback**: Database can be restored from pre-deploy backup

### Migration Commands
```bash
# Run migrations
python backend/run_migrations.py

# Verify indexes
python backend/verify_indexes.py
```

## Monitoring & Alerts

### Post-Deployment Monitoring
- **Error Rate**: Queries Prometheus for 5xx error rates
- **API Latency**: Measures response times (threshold: 2000ms)
- **Database Connectivity**: Verifies database health endpoint
- **Metrics Stabilization**: 60-second wait before monitoring

### Alerting
- **Slack Notifications**: Success/failure notifications
- **GitHub Deployments**: Deployment status tracking
- **Prometheus Alerts**: Configured in `infra/prometheus-alerts.yml`

## Quick Reference

### Manual Deployment
```bash
# Trigger deployment from GitHub UI
# Go to Actions → Deploy to Production → Run workflow
# Select environment: production or staging
```

### Check Deployment Status
```bash
# Docker Compose
docker compose ps
docker compose logs --tail=50 backend

# Kubernetes
kubectl get pods -n nebula
kubectl rollout status deployment/nebula-backend -n nebula
```

### Emergency Rollback
```bash
# 1. SSH to production server
ssh user@production-host

# 2. Run rollback script
cd /opt/nebula-search
./scripts/rollback.sh --environment production

# 3. Verify health
./scripts/health_check.sh
```

## Pipeline Diagram

```
Git Push/PR
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│                    CI Pipeline                                │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │ Lint & Test │  │ Build       │  │ Security Scan        │ │
│  │ - Python    │  │ - Frontend  │  │ - Trivy              │ │
│  │ - Frontend  │  │ - Backend   │  │ - Snyk               │ │
│  │ - E2E       │  │ - Docker    │  │ - Secrets            │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (main branch only)
┌──────────────────────────────────────────────────────────────┐
│                    CD Pipeline                                │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │ Staging     │  │ Production  │  │ Post-Deploy          │ │
│  │ - Backup    │  │ - Backup    │  │ - Error Check        │ │
│  │ - Migrate   │  │ - Migrate   │  │ - Latency Check      │ │
│  │ - Deploy    │  │ - Deploy    │  │ - DB Check           │ │
│  │ - Smoke Test│  │ - Verify    │  │ - Dashboard Update   │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (on failure)
┌──────────────────────────────────────────────────────────────┐
│                    Rollback                                   │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ 1. Create emergency backup                               ││
│  │ 2. Restore database from backup                          ││
│  │ 3. Redeploy previous version                             ││
│  │ 4. Verify health                                         ││
│  │ 5. Notify team                                           ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

1. **Deployment fails at health check**
   ```bash
   # Check service logs
   docker compose logs --tail=100 backend
   
   # Check database connectivity
   docker compose exec postgres pg_isready -U nebula
   
   # Restart service
   docker compose restart backend
   ```

2. **Migration fails**
   ```bash
   # Check migration status
   docker compose exec postgres psql -U nebula -c "SELECT * FROM migrations;"
   
   # Run migration manually
   docker compose run --rm backend python run_migrations.py
   ```

3. **Rollback fails**
   ```bash
   # Check rollback script logs
   cat database/backups/rollback-records/rollback_*.log
   
   # Manual database restore
   gunzip -c database/backups/nebula_*.sql.gz | docker compose exec -T postgres psql -U nebula
   ```

4. **Kubernetes pod stuck**
   ```bash
   # Describe pod for details
   kubectl describe pod -n nebula -l app.kubernetes.io/name=nebula-backend
   
   # Check pod logs
   kubectl logs -n nebula -l app.kubernetes.io/name=nebula-backend --tail=100
   
   # Force restart
   kubectl rollout restart deployment/nebula-backend -n nebula