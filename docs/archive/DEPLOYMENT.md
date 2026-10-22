# Nebula Search Engine - Production Deployment Guide

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Deployment Steps](#deployment-steps)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Scaling](#scaling)
- [Backup & Recovery](#backup--recovery)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

This guide covers production deployment of Nebula Search Engine using Docker Compose.

**Services:**
- Frontend (React + Nginx)
- Backend (FastAPI + Gunicorn)
- PostgreSQL 16
- Redis 7
- MinIO (Object Storage)
- Nginx (Reverse Proxy)
- Prometheus + Grafana (Monitoring)
- Loki + Promtail (Logging)

## Prerequisites

- Docker Engine 24+
- Docker Compose 2.20+
- 8GB RAM minimum (16GB recommended)
- 50GB disk space
- Linux server (Ubuntu 22.04 LTS recommended)
- Domain name with DNS access

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Sky-254-1/Nebula-search-engine-.git
cd Nebula-search-engine-
```

### 2. Configure Environment

```bash
# Copy production environment template
cp .env.example .env.production

# Edit with your values
nano .env.production
```

**Critical values to change:**
- `POSTGRES_PASSWORD`
- `JWT_SECRET` (generate with: `openssl rand -hex 32`)
- `MINIO_ROOT_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`
- `SESSION_SECRET`
- `ENCRYPTION_KEY`

### 3. Deploy Stack

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Verify all services are running
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### 4. Verify Deployment

```bash
# Health checks
curl https://your-domain.com/health
curl https://your-domain.com/health/ready
curl https://your-domain.com/health/detailed

# API health
curl https://your-domain.com/api/v1/health
```

## Architecture

```
┌─────────────┐
│   Internet  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Nginx Reverse Proxy (Port 80/443) │
│   - SSL/TLS Termination             │
│   - Rate Limiting                    │
│   - Static Assets                    │
└─────┬───────────────────────┬───────┘
      │                       │
      ▼                       ▼
┌──────────┐         ┌──────────────┐
│ Frontend │         │    Backend    │
│ (React)  │         │  (FastAPI)   │
└──────────┘         └──────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐    ┌──────────┐
    │ Postgres │      │   Redis  │    │  MinIO   │
    │   (16)   │      │    (7)   │    │ (Storage)│
    └──────────┘      └──────────┘    └──────────┘
                            │
                    ┌───────┴────────┐
                    │  Monitoring    │
                    │  ┌───────────┐ │
                    │  │Prometheus │ │
                    │  ├───────────┤ │
                    │  │  Grafana  │ │
                    │  ├───────────┤ │
                    │  │   Loki    │ │
                    │  └───────────┘ │
                    └────────────────┘
```

## Deployment Steps

### Environment Configuration

1. **Generate secrets:**
   ```bash
   # Generate JWT secret
   openssl rand -hex 32
   
   # Generate session secret
   openssl rand -hex 32
   
   # Generate encryption key
   openssl rand -hex 32
   ```

2. **Edit .env.production:**
   ```bash
   nano .env.production
   ```

3. **Validate configuration:**
   ```bash
   docker compose -f docker-compose.prod.yml config
   ```

### Initialize Databases

The stack automatically runs migrations on first startup via the entrypoint script.

```bash
# Watch migration logs
docker compose -f docker-compose.prod.yml logs -f backend | grep -i migration
```

### SSL/HTTPS Setup

#### Option 1: Let's Encrypt (Recommended for Production)

```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d nebula-search.example.com

# Copy certificates
sudo mkdir -p docker/ssl/live/nebula-search
sudo cp /etc/letsencrypt/live/nebula-search/fullchain.pem docker/ssl/live/nebula-search/
sudo cp /etc/letsencrypt/live/nebula-search/privkey.pem docker/ssl/live/nebula-search/

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * 1 certbot renew --quiet && cp /etc/letsencrypt/live/nebula-search/*.pem docker/ssl/live/nebula-search/ && docker compose -f docker-compose.prod.yml restart nginx
```

#### Option 2: Self-Signed (Development)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/live/nebula-search/privkey.pem \
  -out docker/ssl/live/nebula-search/fullchain.pem \
  -subj "/CN=localhost"
```

### Scaling

#### Horizontal Scaling

Edit `docker-compose.prod.yml` to scale services:

```yaml
services:
  backend:
    deploy:
      replicas: 3
  
  worker:
    deploy:
      replicas: 2
```

Scale on the fly:
```bash
docker compose -f docker-compose.prod.yml up -d --scale backend=3
```

#### Resource Limits

Adjust in `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 2G
    reservations:
      cpus: '2'
      memory: 1G
```

### Backup & Recovery

#### Automated Daily Backups

Add to crontab:
```bash
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /opt/nebula-search && ./scripts/backup.sh all

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 cd /opt/nebula-search && ./scripts/backup.sh all && tar -czf backups/weekly_$(date +\%Y\%m\%d).tar.gz backups/
```

#### Manual Backup

```bash
# Backup all services
./scripts/backup.sh all

# Backup specific service
./scripts/backup.sh postgres
./scripts/backup.sh redis
./scripts/backup.sh minio

# List backups
ls -lh backups/
```

#### Restore

```bash
# Restore PostgreSQL
./scripts/restore.sh backups/postgres_20240101_120000.sql.gz

# Restore Redis
./scripts/restore.sh backups/redis_20240101_120000.rdb.gz

# Restore MinIO
./scripts/restore.sh backups/minio_20240101_120000.tar.gz
```

## Monitoring

### Access Dashboards

**Prometheus:** https://your-domain.com:9090
**Grafana:** https://grafana.nebula-search.example.com
  - Default credentials from `.env.production`

### Key Metrics

- Request rate (req/sec)
- Response time (p95, p99)
- Error rate (5xx)
- Database connections
- Redis memory usage
- Search latency
- AI request latency

### Logs

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Access Loki via Grafana: Explore > Logs
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service-name>

# Verify configuration
docker compose -f docker-compose.prod.yml config

# Check disk space
df -h

# Check resource usage
docker stats
```

### Database connection issues

```bash
# Verify PostgreSQL is running
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U nebula

# Check credentials
docker compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL

# Test connection
docker compose -f docker-compose.prod.yml exec backend python -c "import asyncpg; print(asyncpg.connect('postgresql://nebula:PASSWORD@postgres:5432/nebula'))"
```

### SSL certificate issues

```bash
# Verify certificate
openssl x509 -in docker/ssl/live/nebula-search/fullchain.pem -text -noout

# Test SSL configuration
openssl s_client -connect localhost:443 -servername nebula-search.example.com

# Check Nginx config
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Out of disk space

```bash
# Clean Docker
docker system prune -a --volumes

# Remove old logs
find logs/ -name "*.log" -mtime +7 -delete

# Remove old backups
find backups/ -mtime +30 -delete
```

### High memory usage

```bash
# Check memory per container
docker stats

# Adjust resource limits in docker-compose.prod.yml
# Reduce worker count
export MAX_WORKERS=2
docker compose -f docker-compose.prod.yml up -d
```

## Maintenance

### Update to new version

```bash
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --force-recreate
docker compose -f docker-compose.prod.yml exec backend python -m app.database.migrations.run_migrations
```

### Zero-downtime deployment

```bash
# Rolling update
docker compose -f docker-compose.prod.yml up -d --scale backend=3 --scale worker=2
docker compose -f docker-compose.prod.yml scale backend=0
```

### Security updates

```bash
# Scan for vulnerabilities
docker scout cves nebula-backend:latest

# Update base images
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml build --no-cache
```

## Rollback Procedure

```bash
# Rollback to previous version
git log --oneline  # Find previous commit
git reset --hard HEAD~1
docker compose -f docker-compose.prod.yml up -d --force-recreate

# Or restore from backup
./scripts/restore.sh backups/postgres_YYYYMMDD_HHMMSS.sql.gz
```

## Support

- Documentation: [docs/](./docs/)
- Issues: https://github.com/Sky-254-1/Nebula-search-engine-/issues