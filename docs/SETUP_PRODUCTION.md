# Production Setup Guide

This guide covers production deployment of Nebula Search Engine.

---

## Prerequisites

- PostgreSQL 15+ or PostgreSQL 16+
- Redis 7+
- Docker 24+ (recommended)
- SSL/TLS certificate (Let's Encrypt or commercial)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer (AWS ALB, NGINX)           │
└─────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────────┐         ┌──────────────┐
│   Frontend   │          │     Backend      │         │  Vector      │
│   (Nginx)    │          │  (FastAPI)       │         │  Worker      │
└──────────────┘          └──────────────────┘         └──────────────┘
                                    │                           │
        ┌───────────────────────────┼───────────────────────────┘
        │                           │
        ▼                           ▼
┌──────────────┐          ┌──────────────────┐
│  PostgreSQL  │          │     Redis        │
│   (Primary)  │          │   (Cache/Queue)  │
└──────────────┘          └──────────────────┘
        │
        ▼
┌──────────────┐
│ PostgreSQL   │
│  (Replica)   │
└──────────────┘
```

---

## Environment Variables

### Required Variables

```bash
# Application
APP_ENV=production
JWT_SECRET=<generate-with-openssl-rand-hex-32>
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql://nebula:password@postgres:5432/nebula

# Redis (required for production)
REDIS_URL=redis://redis:6379/0
CACHE_TTL_SECONDS=300

# Search APIs (optional but recommended)
BRAVE_API_KEY=<your-brave-key>
SERPAPI_KEY=<your-serpapi-key>

# AI Providers (optional)
OPENAI_API_KEY=<your-openai-key>
OLLAMA_URL=http://ollama:11434

# Security
ENABLE_AUDIT_LOGS=true
ENABLE_REFRESH_REUSE_DETECTION=true
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

## Docker Deployment

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL (primary)
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: nebula
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: nebula
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=en_US.UTF-8 --lc-ctype=en_US.UTF-8
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nebula"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory-policy allkeys-lru --maxmemory 256mb
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Backend
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ../backend/.env
    environment:
      DATABASE_URL: postgresql://nebula:${DB_PASSWORD}@postgres:5432/nebula
      REDIS_URL: redis://redis:6379/0
      APP_ENV: production
      CORS_ORIGINS: https://your-domain.com,https://www.your-domain.com
      STORAGE_ROOT: /app/storage
    volumes:
      - nebula-storage:/app/storage
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s

  # Frontend
  frontend:
    build:
      context: ..
      dockerfile: docker/frontend.Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  # Vector Worker
  vector-worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: ["python", "-m", "vector.worker"]
    env_file:
      - ../backend/.env
    environment:
      DATABASE_URL: postgresql://nebula:${DB_PASSWORD}@postgres:5432/nebula
      REDIS_URL: redis://redis:6379/0
      APP_ENV: production
      STORAGE_ROOT: /app/storage
    volumes:
      - nebula-storage:/app/storage
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
  nebula-storage:
```

---

## NGINX Configuration

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    listen [::]:80;
    
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/nebula.crt;
    ssl_certificate_key /etc/ssl/private/nebula.key;
    
    # TLS Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security Headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Caching
        proxy_cache_valid 200 1d;
        proxy_cache_valid 404 1m;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}
```

---

## Database Setup

### Initial Setup

```sql
-- Create database
CREATE DATABASE nebula;

-- Create user
CREATE USER nebula WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE nebula TO nebula;

-- Run migrations
\c nebula
-- Execute migrations from backend/app/database/migrations/
```

### Production Database Tuning

```sql
-- Connection pool settings (adjust based on your server)
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = 256MB;
ALTER SYSTEM SET effective_cache_size = 1GB;
ALTER SYSTEM SET work_mem = 16MB;
ALTER SYSTEM SET maintenance_work_mem = 64MB;

-- Query planner settings
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- WAL settings
ALTER SYSTEM SET wal_buffers = 16MB;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET max_wal_size = 2GB;
ALTER SYSTEM SET min_wal_size = 1GB;

-- Reload config
SELECT pg_reload_conf();
```

---

## Security Hardening

### Backend Security

```bash
# Generate strong JWT secret
openssl rand -hex 32

# Set environment variables
export APP_ENV=production
export JWT_SECRET=<generated-secret>
export CORS_ORIGINS=https://your-domain.com
```

### Database Security

```sql
-- Revoke public schema access
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO nebula;

-- Audit logging
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    action TEXT,
    table_name TEXT,
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT
);
```

---

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'nebula'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards

Import these dashboards:
- **FastAPI Dashboard** - API performance metrics
- **PostgreSQL Dashboard** - Database metrics
- **Redis Dashboard** - Cache metrics

---

## Backup Strategy

### Automated Backup

```bash
# scripts/backup.sh
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/nebula"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump -h postgres -U nebula nebula | \
  gzip > "$BACKUP_DIR/db-$DATE.sql.gz"

# Keep last 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

# Upload to S3 (if configured)
if [ -n "$S3_BUCKET" ]; then
  aws s3 cp "$BACKUP_DIR/db-$DATE.sql.gz" "s3://$S3_BUCKET/nebula/"
fi
```

---

## Rollback Procedure

### Docker Rollback

```bash
# Stop current version
docker compose down

# Roll back image tag
docker compose pull frontend:1.0.0
docker compose pull backend:1.0.0

# Restart
docker compose up -d

# Verify
docker compose exec backend python -c "from app.main import app; print(app.title)"
curl http://localhost/health
```

### Database Rollback

```sql
-- If migration caused issues, rollback
-- Note: Use migration rollback scripts in production

-- Example: Drop new tables if needed
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS embeddings;
DROP TABLE IF EXISTS citations;
```

---

## Health Check Endpoints

### Application Health

```bash
curl http://localhost/health
# Expected: {"status":"healthy","version":"1.1.0",...}
```

### Database Health

```bash
docker compose exec postgres pg_isready -U nebula
# Expected: postgres:5432 - accepting connections
```

### Redis Health

```bash
docker compose exec redis redis-cli ping
# Expected: PONG
```

---

## Support

For production issues:
- **Email:** ops@nebula-search.example.com
- **PagerDuty:** nebula-ops (if configured)
- **Status Page:** https://status.nebula-search.example.com

---

*Last updated: July 1, 2026*
