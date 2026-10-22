# Nebula Search Engine - Production Operations Guide

## Overview

This guide covers day-to-day operations, monitoring, and maintenance procedures for production deployments.

## Architecture

### Services
- **Frontend**: React + Nginx (port 80/443)
- **Backend**: FastAPI + Uvicorn workers (internal port 8000)
- **Database**: PostgreSQL 16 (port 5432)
- **Cache**: Redis 7 (port 6379)
- **Storage**: MinIO (port 9000)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Loki + Promtail

### Network Topology
```
Internet → Nginx (80/443) → [Frontend | Backend]
Backend → PostgreSQL (5432)
Backend → Redis (6379)
Backend → MinIO (9000)
Monitoring → Prometheus (9090) → Grafana (3001)
```

## Environment Management

### File Structure
```
.env.example          # Template for all environments
.env.development      # Development overrides
.env.production       # Production secrets (NEVER commit)
```

### Secret Management

**Critical**: Never commit `.env.production` to version control.

Generate production secrets:
```bash
# JWT Secret (min 32 characters)
openssl rand -hex 32

# Session Secret
openssl rand -hex 32

# Encryption Key (min 32 chars)
openssl rand -hex 32

# Database passwords (use strong passwords)
openssl rand -base64 32
```

### Loading Secrets
Use `.env.production` for local Docker Compose deployments, or Docker secrets for Swarm/Kubernetes:

```yaml
# Example Docker secrets
secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  db_password:
    file: ./secrets/db_password.txt
```

## Service Management

### Start Services
```bash
# Production
docker compose -f docker-compose.prod.yml up -d

# Development
docker compose -f docker-compose.yml up -d
```

### Stop Services
```bash
docker compose -f docker-compose.prod.yml down
```

### Restart Services
```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

## Monitoring

### Health Checks

```bash
# Basic health
curl https://your-domain.com/health

# Detailed health
curl https://your-domain.com/health/detailed

# Readiness check (Kubernetes)
curl https://your-domain.com/health/ready

# Liveness check (Kubernetes)
curl https://your-domain.com/health/live
```

### Key Metrics (Prometheus)

Access Prometheus: `https://your-domain.com:9090`

**Essential Queries:**
```promql
# Request rate
sum(rate(nebula_http_requests_total[5m])) by (method, status)

# Error rate
sum(rate(nebula_http_requests_total{status=~"5.."}[5m])) / sum(rate(nebula_http_requests_total[5m])) * 100

# Response time p95
histogram_quantile(0.95, sum(rate(nebula_http_request_duration_seconds_bucket[5m])) by (le))

# Active requests
nebula_http_active_requests

# Database connections
nebula_db_pool_size

# Cache hit rate
sum(nebula_cache_hits_total) / (sum(nebula_cache_hits_total) + sum(nebula_cache_misses_total))
```

### Grafana Dashboards

Access Grafana: `https://grafana.nebula-search.example.com`

**Pre-configured Dashboards:**
1. **Nebula Overview** - Main system metrics
2. **Search Performance** - Search latency and throughput
3. **Database** - PostgreSQL metrics
4. **Redis** - Cache performance
5. **Infrastructure** - CPU, memory, disk

### Log Queries (Loki)

Access via Grafana: **Explore** → **Logs**

**Common Queries:**
```
# All errors
{job="nebula-backend"} |= "ERROR"

# Specific request
{job="nebula-backend"} |= "request_id=abc123"

# Search requests
{job="nebula-backend"} |= "search" |= "POST"

# Slow requests (>1s)
{job="nebula-backend"} |= "duration=1."
```

## Backup & Recovery

### Automated Backups

Crontab configuration (`crontab -e`):
```cron
# Daily backup at 2 AM
0 2 * * * cd /opt/nebula-search && ./scripts/backup.sh all >> /var/log/nebula/backup.log 2>&1

# Weekly verification (test restore)
0 4 * * 0 cd /opt/nebula-search && ./scripts/backup.sh postgres

# Monthly archive to S3 (configure as needed)
0 3 1 * * aws s3 sync backups/ s3://nebula-backups/$(date +\%Y\%m)/
```

### Manual Backups

```bash
# Create backup
./scripts/backup.sh all

# Verify backups created
ls -lh backups/

# Check backup sizes
du -sh backups/
```

### Restore Procedures

```bash
# 1. Stop services
docker compose -f docker-compose.prod.yml down

# 2. Restore PostgreSQL
./scripts/restore.sh backups/postgres_20240101_120000.sql.gz

# 3. Restore Redis (optional)
./scripts/restore.sh backups/redis_20240101_120000.rdb.gz

# 4. Restore MinIO (optional)
./scripts/restore.sh backups/minio_20240101_120000.tar.gz

# 5. Start services
docker compose -f docker-compose.prod.yml up -d

# 6. Verify
curl https://your-domain.com/health/detailed
```

## Scaling

### Horizontal Scaling

Scale backend instances:
```bash
docker compose -f docker-compose.prod.yml up -d --scale backend=3 --scale worker=2
```

Update `docker-compose.prod.yml` for persistent scaling:
```yaml
services:
  backend:
    deploy:
      replicas: 3
```

### Resource Limits

Monitor resource usage:
```bash
docker stats
```

Adjust limits in `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: "4"
      memory: 4G
```

### Database Scaling

**PostgreSQL:**
- Current: Single primary
- Future: Add read replicas for read-heavy workloads
- Connection pooling: pgBouncer (already configured in backend)

**Redis:**
- Current: Single instance with persistence
- Future: Redis Cluster for horizontal scaling

## SSL/TLS Management

### Check Certificate Expiry
```bash
openssl x509 -in docker/ssl/live/nebula-search/fullchain.pem -noout -enddate
```

### Renew Certificate
```bash
# For Let's Encrypt
sudo certbot renew
sudo cp /etc/letsencrypt/live/nebula-search/*.pem docker/ssl/live/nebula-search/
docker compose -f docker-compose.prod.yml restart nginx
```

### Test SSL Configuration
```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### Verify SSL Labs Rating
Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service-name>

# Verify configuration
docker compose -f docker-compose.prod.yml config

# Check disk space
df -h

# Restart Docker daemon
sudo systemctl restart docker
```

#### 2. Database Connection Errors
```bash
# Check PostgreSQL is running
docker compose -f docker-compose.prod.yml exec postgres pg_isready

# Verify credentials in .env.production
grep POSTGRES .env.production

# Test connection
docker compose -f docker-compose.prod.yml exec backend python -c "import asyncpg; asyncpg.connect('${DATABASE_URL}')"
```

#### 3. High Memory Usage
```bash
# Check per-container usage
docker stats

# Reduce workers
echo "MAX_WORKERS=2" >> .env.production
docker compose -f docker-compose.prod.yml up -d
```

#### 4. Disk Space Full
```bash
# Clean Docker
docker system prune -a --volumes

# Remove old logs
find logs/ -name="*.log" -mtime +7 -delete

# Backup and old backups
tar -czf old-backups.tar.gz backups/
rm backups/*.sql.gz backups/*.rdb.gz
```

### Diagnostic Commands

```bash
# Docker system info
docker info
docker system df

# Service status
docker compose -f docker-compose.prod.yml ps

# Service resource usage
docker stats --no-stream

# Network connectivity
docker compose -f docker-compose.prod.yml exec backend ping postgres
docker compose -f docker-compose.prod.yml exec backend ping redis

# Database queries
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "SELECT * FROM pg_stat_activity;"

# Redis info
docker compose -f docker-compose.prod.yml exec redis redis-cli INFO
```

### Performance Tuning

```bash
# Database query analysis
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Redis slow log
docker compose -f docker-compose.prod.yml exec redis redis-cli SLOWLOG GET 10

# Application profiling
docker compose -f docker-compose.prod.yml exec backend python -m py-spy top --pid 1
```

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- Automated backups run at 2 AM
- Monitor Grafana for anomalies
- Check disk space

**Weekly:**
- Review slow query logs
- Validate backup integrity
- Review security updates

**Monthly:**
- Update base Docker images
- Review and rotate logs
- Capacity planning review

### Zero-Downtime Updates

```bash
# Pull latest code
git pull origin main

# Build new images
docker compose -f docker-compose.prod.yml build

# Rolling update (gradual)
docker compose -f docker-compose.prod.yml up -d --scale backend=3
docker compose -f docker-compose.prod.yml scale backend=1

# Verify
curl https://your-domain.com/health
```

### Emergency Procedures

**Incident Response:**
1. Check health endpoints
2. Review Grafana dashboards
3. Check logs in Loki
4. Identify affected service
5. Roll back if needed: `git reset --hard HEAD~1 && docker compose up -d --force-recreate`

**Data Loss:**
1. Stop services immediately
2. Restore from latest backup
3. Verify data integrity
4. Resume services

**Performance Degradation:**
1. Check resource usage (`docker stats`)
2. Review slow queries
3. Scale horizontally if needed
4. Consider caching strategies

## Cost Optimization

### Right-sizing Resources

Monitor actual usage and adjust:
```bash
# Get actual usage for 24 hours
docker stats --no-stream > stats.txt

# Adjust limits based on actual usage
# Typical production: 2-4 CPU cores, 2-4GB RAM per service
```

### Storage Costs

```bash
# Compress old logs
gzip logs/*.log

# Move backups to S3/Glacier
aws s3 sync backups/ s3://backup-bucket/ --storage-class GLACIER
```

### Backup Retention Policy

```bash
# Daily backups: 30 days
# Weekly backups: 90 days
# Monthly backups: 1 year

find backups/ -name "*.sql.gz" -mtime +30 -delete
```

## Compliance & Security

### Security Headers Verification

```bash
curl -I https://your-domain.com | grep -i "x-frame-options"
curl -I https://your-domain.com | grep -i "strict-transport"
curl -I https://your-domain.com | grep -i "content-security-policy"
```

### Dependency Scanning

```bash
# Scan Docker images
docker scout cves nebula-backend:latest

# Scan Python dependencies
cd backend && pip install safety && safety check

# Scan Node dependencies
cd frontend && npm audit
```

### Access Control

- Rotate secrets quarterly
- Use RBAC for Grafana
- Limit SSH access
- Enable 2FA for all access
- Regular security training

## Disaster Recovery

### RTO (Recovery Time Objective): 1 hour
### RPO (Recovery Point Objective): 24 hours

### Recovery Plan

1. **Infrastructure failure** (15 min)
   - Deploy to new server
   - Restore latest backup
   - Update DNS

2. **Data corruption** (30 min)
   - Stop services
   - Restore from backup
   - Verify integrity
   - Resume

3. **Security breach** (1 hour)
   - Isolate affected systems
   - Rotate all credentials
   - Restore from clean backup
   - Security audit

## Support

- **Documentation**: [docs/](./docs/)
- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Backup Guide**: [scripts/backup.sh](./scripts/backup.sh)
- **Monitoring**: https://grafana.nebula-search.example.com