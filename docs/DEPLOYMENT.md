# Nebula Search — Deployment Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Manual Production Deployment](#manual-production-deployment)
- [CI/CD Pipelines](#cicd-pipelines)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/Sky-254-1/NEBULA-SEARCH-.git
cd NEBULA-SEARCH-

# Run quick start script
bash scripts/quick-start.sh

# Or using Make
make install
make dev
```

Access the application:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Docker Deployment

### Development Environment

```bash
# Start development environment with hot reload
docker compose -f docker-compose.dev.yml up --build

# Stop development environment
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs -f
```

### Production Environment

```bash
# Set up environment
cp .env.example .env
# Edit .env with production values

# Deploy using PowerShell script (Windows)
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1

# Or deploy manually
docker compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# Verify deployment
powershell -ExecutionPolicy Bypass -File scripts/verify-deployment.ps1
```

### Docker Compose Services

The production stack includes:
- **Backend**: FastAPI application (port 8000)
- **Frontend**: Nginx serving React build (port 3000)
- **PostgreSQL**: Database (port 5432)
- **Redis**: Cache and session store (port 6379)
- **Elasticsearch**: Vector and full-text search (port 9200)
- **MinIO**: S3-compatible storage (port 9000)
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Monitoring dashboards (port 3001)
- **RabbitMQ**: Message queue (port 5672)
- **Kafka**: Event streaming (port 9092)
- **Nginx**: Reverse proxy and SSL termination (ports 80/443)

## Manual Production Deployment

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Elasticsearch 8.x (optional, for vector search)
- Nginx (for reverse proxy)
- SSL certificate

### Backend Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://user:pass@localhost:5432/nebula
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET=your-secret-key

# Run migrations
alembic upgrade head

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Setup

```bash
cd frontend
npm ci
npm run build
```

### Nginx Configuration

See `docker/nginx.prod.conf` for production Nginx configuration.

```bash
# Copy configuration
sudo cp docker/nginx.prod.conf /etc/nginx/sites-available/nebula
sudo ln -s /etc/nginx/sites-available/nebula /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## CI/CD Pipelines

### GitHub Actions Workflows

The project includes comprehensive CI/CD workflows:

1. **ci.yml** - Main CI pipeline
   - Runs on all PRs and pushes to main
   - Backend tests (pytest)
   - Frontend tests (vitest)
   - Linting (flake8, eslint)
   - Type checking (mypy, TypeScript)
   - Security scanning (Trivy, CodeQL)
   - Coverage reporting (Codecov)

2. **deploy.yml** - Production deployment
   - Triggers on push to main
   - Runs full test suite
   - Builds Docker image
   - Provisions AWS infrastructure (Terraform)
   - Deploys to Kubernetes
   - Sends Slack notifications

3. **frontend_deploy.yml** - Frontend deployment
   - Triggers on push to main
   - Builds and deploys to Vercel

4. **mobile_deploy.yml** - Android deployment
   - Triggers on version tags
   - Builds AAB for Google Play Store

5. **ios_deploy.yml** - iOS deployment
   - Triggers on version tags
   - Deploys to TestFlight

6. **desktop_deploy.yml** - Desktop deployment
   - Triggers on version tags
   - Builds for Linux, Windows, macOS

7. **staging.yml** - Staging environment
   - Triggers on push to develop
   - Deploys to staging Kubernetes namespace
   - Runs smoke tests

8. **e2e.yml** - E2E testing
   - Runs Playwright tests
   - Tests full user flows

9. **release.yml** - Release automation
   - Triggers on version tags
   - Creates GitHub releases
   - Uploads artifacts

### Setting Up CI/CD

1. Fork the repository
2. Enable GitHub Actions
3. Configure secrets in repository settings:
   - `VERCEL_TOKEN` - For frontend deployment
   - `SLACK_WEBHOOK_URL` - For notifications
   - `STAGING_ECR_REGISTRY` - For staging deployments
   - `STAGING_KUBE_CONFIG` - For staging Kubernetes access
4. Enable branch protection on main:
   - Require CI checks to pass
   - Require code review
   - Dismiss stale approvals

### Dependabot

Dependabot is configured to automatically update dependencies:
- **npm** packages (weekly)
- **pip** packages (weekly)
- **Docker** images (weekly)

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

### Required Production Settings

```env
# Security
JWT_SECRET=your-strong-secret-key-here
SECRET_KEY=your-encryption-key-here

# Database
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgresql://nebula:password@postgres:5432/nebula

# CORS (restrict to your domain)
CORS_ORIGINS=https://your-domain.com

# Storage
STORAGE_BACKEND=s3  # or local
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=nebula-storage

# Optional
OPENAI_API_KEY=your-openai-key
SENTRY_DSN=your-sentry-dsn
```

## Monitoring

### Health Checks

- **Backend**: http://your-domain.com/health
- **MinIO**: http://your-domain.com:9000/minio/health/live
- **Redis**: `redis-cli ping` (should return PONG)
- **PostgreSQL**: `pg_isready`

### Metrics

- **Prometheus**: http://your-domain.com:9090
- **Grafana**: http://your-domain.com:3001
  - Default credentials: admin / (check secrets)

### Logs

```bash
# Docker Compose
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f worker

# Kubernetes
kubectl logs -n nebula -l app=nebula-backend --tail=100 -f
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check DATABASE_URL is correct
   - Verify PostgreSQL is running
   - Run migrations: `make db-migrate`

2. **CORS errors**
   - Update CORS_ORIGINS in .env
   - Ensure frontend and backend URLs match

3. **JWT token errors**
   - Verify JWT_SECRET is set
   - Check token expiration

4. **Elasticsearch connection errors**
   - Elasticsearch is optional for basic search
   - Set ELASTICSEARCH_URL if using vector search

### Useful Commands

```bash
# Make commands
make help              # Show all available commands
make test              # Run all tests
make logs              # View logs
make shell             # Open backend shell
make db-migrate        # Run migrations
make db-shell          # Open database shell
make backup-db         # Backup database
make health            # Check service health

# Docker Compose
docker compose ps      # List running services
docker compose logs    # View logs
docker compose exec    # Execute command in service
docker compose down    # Stop services
```

### Performance Tuning

1. **Backend workers**: Adjust `MAX_WORKERS` (default: 4)
2. **Database connections**: Set `POSTGRES_MAX_CONNECTIONS` (default: 200)
3. **Redis memory**: Configure `REDIS_MAXMEMORY` (default: 512mb)
4. **Elasticsearch heap**: Adjust `ES_JAVA_OPTS` (default: 1g)

### Backup and Recovery

```bash
# Backup PostgreSQL
make backup-db

# Restore PostgreSQL
make restore-db FILE=backups/backup_20240101_120000.sql

# Backup volumes
docker compose -f docker-compose.prod.yml down
tar -czf nebula-backup.tar.gz docker-volumes/
```

## Security

See [SECURITY.md](SECURITY.md) for security policy and best practices.

## Additional Documentation

- [Infrastructure Guide](INFRASTRUCTURE.md) - AWS and Kubernetes setup
- [Staging Guide](STAGING.md) - Staging environment documentation
- [API Documentation](API.md) - REST API reference
- [Contributing Guide](CONTRIBUTING.md) - Development workflow