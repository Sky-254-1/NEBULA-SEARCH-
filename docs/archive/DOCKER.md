# Nebula Search Engine - Docker Guide

## Overview

This guide covers Docker-specific operations for Nebula Search Engine development and production.

## Prerequisites

- Docker Engine 24+
- Docker Compose 2.20+
- 8GB RAM minimum
- 50GB disk space

## Quick Reference

### Development
```bash
docker compose up -d
docker compose logs -f
docker compose down
```

### Production
```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml down
```

## Dockerfiles

### Backend (Dockerfile.prod)

Multi-stage build:
1. **Builder stage**: Install Python dependencies
2. **Runtime stage**: Minimal runtime with non-root user

Key features:
- Multi-stage build for smaller image size
- Non-root user (nebula) for security
- Gunicorn + Uvicorn workers for production
- Health checks built-in
- Read-only filesystem with tmpfs for /tmp

Build:
```bash
docker build -f docker/Dockerfile.prod -t nebula-backend:latest .
```

### Frontend (frontend.Dockerfile)

Multi-stage build:
1. **Build stage**: Node.js build environment
2. **Production stage**: Nginx serving static files

Key features:
- Optimized React build
- Gzip compression enabled
- Non-root nginx user
- Read-only filesystem

Build:
```bash
docker build -f docker/frontend.Dockerfile -t nebula-frontend:latest .
```

## Docker Compose

### Development (docker-compose.yml)

Services:
- PostgreSQL
- Redis
- Backend (with hot reload)
- Frontend (Vite dev server)
- MinIO

Usage:
```bash
docker compose up -d
```

### Production (docker-compose.prod.yml)

Services:
- PostgreSQL 16 (with pg_stat_statements)
- Redis 7 (with AOF persistence)
- Backend (Gunicorn + Uvicorn workers)
- Worker (background indexing)
- Scheduler (incremental indexing)
- Frontend (Nginx serving built assets)
- Nginx (reverse proxy with SSL)
- MinIO (object storage)
- Prometheus (metrics collection)
- Grafana (visualization)

Features:
- Health checks for all services
- Resource limits and reservations
- Read-only containers where possible
- Non-root users
-tmpfs for temporary files
- Network isolation (internal + public networks)
- Persistent volumes for data

Usage:
```bash
docker compose -f docker-compose.prod.yml up -d
```

## Volumes

### Named Volumes

```yaml
volumes:
  postgres-data:     # PostgreSQL data
  redis-data:        # Redis persistence
  nebula-storage:    # Application uploads
  minio-data:        # MinIO objects
  prometheus-data:   # Metrics history
  grafana-data:      # Dashboard configs
  backend-logs:      # Backend application logs
  worker-logs:       # Worker logs
  scheduler-logs:    # Scheduler logs
  nginx-logs:        # Nginx access/error logs
```

### Bind Mounts

```yaml
# Configuration files (read-only)
- ./docker/nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro
- ./infra/prometheus.yml:/etc/prometheus/prometheus.yml:ro

# SSL certificates (read-only)
- ./docker/ssl:/etc/nginx/ssl:ro

# Database migrations
- ./database/migrations:/docker-entrypoint-initdb.d:ro

# Backups (read-write)
- ./database/backups:/backups:rw
```

## Networking

### Networks

```yaml
networks:
  nebula-internal:
    driver: bridge
    internal: true  # No internet access
  
  nebula-public:
    driver: bridge  # Internet access via Nginx
```

### Service Communication

Services communicate via Docker DNS:
```python
# Backend connects to PostgreSQL
DATABASE_URL=postgresql://nebula:pass@postgres:5432/nebula

# Backend connects to Redis
REDIS_URL=redis://redis:6379/0

# Nginx proxies to backend
proxy_pass http://backend:8000
```

## Security

### Non-Root Users

All services run as non-root users:

```yaml
# Backend
user: nebula

# Nginx
user: nginx

# PostgreSQL
# Runs as postgres user by default
```

### Read-Only Filesystems

Services mount filesystems as read-only where possible:

```yaml
backend:
  read_only: true
  tmpfs:
    - /tmp

nginx:
  read_only: true
  tmpfs:
    - /tmp
    - /var/cache/nginx
    - /var/run
```

### Capability Dropping

```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
```

## Resource Management

### Limits

```yaml
deploy:
  resources:
    limits:
      cpus: "4"
      memory: 2G
    reservations:
      cpus: "2"
      memory: 1G
```

### Monitoring Resource Usage

```bash
# Real-time stats
docker stats

# One-time stats
docker stats --no-stream

# Specific service
docker stats nebula-backend
```

## Health Checks

All services include health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 15s
```

Check health status:
```bash
docker compose -f docker-compose.prod.yml ps
```

## Logging

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Last N lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Log Drivers

Configure logging in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Troubleshooting

### Common Issues

**Issue: Container won't start**
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service>

# Check configuration
docker compose -f docker-compose.prod.yml config

# Inspect container
docker inspect <container>
```

**Issue: Out of disk space**
```bash
# Clean up
docker system prune -a --volumes

# Check disk usage
docker system df
```

**Issue: Port already in use**
```bash
# Find process using port
lsof -i :80
lsof -i :443

# Stop conflicting service
sudo systemctl stop nginx
```

**Issue: Permission denied**
```bash
# Check file permissions
ls -la docker/ssl/

# Fix ownership
sudo chown -R $USER:$USER docker/ssl/
```

### Debug Mode

Run container interactively:
```bash
docker compose -f docker-compose.prod.yml run --rm backend bash
```

## Performance Optimization

### Build Cache

Use build cache for faster builds:
```bash
docker build --cache-from nebula-backend:latest -f docker/Dockerfile.prod .
```

### Layer Caching

Order Dockerfile commands from least to most frequently changed:
```dockerfile
COPY requirements.txt .  # Changes rarely
RUN pip install -r requirements.txt
COPY app/ .              # Changes frequently
```

### Image Size

Check image sizes:
```bash
docker images | grep nebula
```

Optimize:
- Use Alpine/slim base images
- Multi-stage builds
- Remove unnecessary packages
- Use `.dockerignore`

## Updates

### Update Base Images

```bash
# Pull latest base images
docker compose -f docker-compose.prod.yml pull

# Rebuild with new base
docker compose -f docker-compose.prod.yml build --no-cache

# Deploy
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

### Zero-Downtime Updates

```bash
# Scale up
docker compose -f docker-compose.prod.yml up -d --scale backend=3

# Wait for new containers to be healthy
sleep 30

# Scale down
docker compose -f docker-compose.prod.yml scale backend=1
```

## Backup

### Backup Volumes

```bash
# PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U nebula nebula | gzip > backup.sql.gz

# Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE
docker cp nebula-redis:/data/dump.rdb ./backup.rdb

# MinIO
docker run --rm --volumes-from nebula-storage -v $(pwd):/backup alpine tar czf /backup/minio.tar.gz /data
```

### Restore Volumes

```bash
# Restore PostgreSQL
docker compose -f docker-compose.prod.yml exec -T postgres psql -U nebula nebula < backup.sql

# Restore Redis
docker cp ./backup.rdb nebula-redis:/data/dump.rdb
docker compose -f docker-compose.prod.yml restart redis
```

## CI/CD Integration

### GitHub Actions

The project includes:
- `.github/workflows/ci.yml` - Testing workflow
- `.github/workflows/deploy.yml` - Production deployment

### Docker Hub

Build and push:
```bash
# Login
docker login

# Tag
docker tag nebula-backend:latest username/nebula-backend:latest

# Push
docker push username/nebula-backend:latest
```

## Best Practices

1. **Never run as root** - Use non-root users
2. **Read-only filesystems** - Mount as read-only where possible
3. **Resource limits** - Set CPU and memory limits
4. **Health checks** - Include health checks for all services
5. **Secrets management** - Never commit secrets to version control
6. **Multi-stage builds** - Use multi-stage builds to reduce image size
7. **Layer caching** - Order Dockerfile commands for optimal caching
8. **Logging** - Use structured logging (JSON in production)
9. **Monitoring** - Include metrics and health endpoints
10. **Documentation** - Document all Docker-specific operations

## Support

- Docker Documentation: https://docs.docker.com
- Docker Compose: https://docs.docker.com/compose/
- Project Docs: [docs/](./docs/)