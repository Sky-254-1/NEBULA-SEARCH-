# Nebula Search Engine - Production Deployment Validation

## Deployment Checklist

This checklist ensures all production components are properly configured and operational.

## Pre-Deployment Verification

### Environment Setup
```bash
# [ ] .env.production exists with all required variables
[ ] POSTGRES_PASSWORD set
[ ] JWT_SECRET set (min 32 chars)
[ ] MINIO_ROOT_PASSWORD set
[ ] GRAFANA_ADMIN_PASSWORD set
[ ] SESSION_SECRET set
[ ] ENCRYPTION_KEY set

# [ ] Environment files not committed to git
[ ] .env.production in .gitignore
[ ] No secrets in git history
```

### SSL Certificates
```bash
# [ ] SSL directory exists
[ ] mkdir -p docker/ssl/live/nebula-search

# [ ] Certificates present (for production)
[ ] fullchain.pem exists
[ ] privkey.pem exists

# [ ] Certificate valid
openssl x509 -in docker/ssl/live/nebula-search/fullchain.pem -noout -dates

# [ ] For development (self-signed)
[ ] Self-signed cert generated (if using)
```

## Infrastructure Validation

### Docker Setup
```bash
# [ ] Docker installed
docker --version  # Should be 24+

# [ ] Docker Compose installed
docker compose version  # Should be 2.20+

# [ ] Docker daemon running
docker info

# [ ] Sufficient disk space
df -h  # Should have 50GB+ free

# [ ] Sufficient memory
free -h  # Should have 8GB+ RAM
```

### Network Configuration
```bash
# [ ] Required ports available
lsof -i :80    # Should not be in use (or use NGINX_HTTP_PORT)
lsof -i :443   # Should not be in use (or use NGINX_HTTPS_PORT)
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9000  # MinIO
lsof -i :3001  # Grafana
lsof -i :9090  # Prometheus

# [ ] DNS configured
# Point domain to server IP
nslookup your-domain.com
```

### Firewall Configuration
```bash
# [ ] Required ports open (example for Ubuntu UFW)
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH
sudo ufw enable

# [ ] Internal ports blocked from external access
# PostgreSQL, Redis, MinIO should NOT be exposed externally
```

## Docker Compose Deployment

### Initial Deployment
```bash
# [ ] Validate configuration
docker compose -f docker-compose.prod.yml config

# [ ] Start services
docker compose -f docker-compose.prod.yml up -d

# [ ] All services started
docker compose -f docker-compose.prod.yml ps

# Expected output:
# nebula-postgres      running
# nebula-redis         running
# nebula-backend       running
# nebula-worker        running
# nebula-scheduler     running
# nebula-frontend      running
# nebula-nginx         running
# nebula-storage       running
# nebula-prometheus    running
# nebula-grafana       running
```

### Service Health Verification
```bash
# [ ] PostgreSQL healthy
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U nebula

# [ ] Redis healthy
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# [ ] Backend healthy
curl -f https://your-domain.com/health

# [ ] Frontend healthy
curl -I https://your-domain.com

# [ ] MinIO healthy
curl -f http://localhost:9000/minio/health/live

# [ ] Prometheus running
curl -f https://your-domain.com:9090/-/healthy

# [ ] Grafana running
curl -f https://grafana.nebula-search.example.com/api/health
```

### Health Check Endpoints
```bash
# [ ] Basic health
curl https://your-domain.com/health
# Expected: {"status":"healthy","service":"nebula-backend",...}

# [ ] Detailed health
curl https://your-domain.com/health/detailed
# Expected: All checks "healthy"

# [ ] Readiness check
curl https://your-domain.com/health/ready
# Expected: HTTP 200

# [ ] Liveness check
curl https://your-domain.com/health/live
# Expected: HTTP 200
```

## Functional Testing

### API Testing
```bash
# [ ] API documentation accessible
curl -I https://your-domain.com/docs
# Expected: HTTP 200

# [ ] Search API working
curl -X POST https://your-domain.com/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'

# [ ] Authentication working
curl -X POST https://your-domain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### Frontend Testing
```bash
# [ ] Frontend loads
curl https://your-domain.com | grep -i "Nebula"

# [ ] Static assets loading
curl -I https://your-domain.com/assets/index.js
# Expected: HTTP 200, Content-Encoding: gzip

# [ ] React app functional
# Open browser and verify UI loads without console errors
```

### Database Verification
```bash
# [ ] Can connect to PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "SELECT 1"

# [ ] Tables created
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "\dt"

# [ ] Sample data exists (if seeded)
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "SELECT * FROM users LIMIT 1;"

# [ ] Migrations ran
docker compose -f docker-compose.prod.yml logs backend | grep -i migration
```

### Cache Verification
```bash
# [ ] Redis accessible
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
# Expected: PONG

# [ ] Can set/get keys
docker compose -f docker-compose.prod.yml exec redis redis-cli set test "value"
docker compose -f docker-compose.prod.yml exec redis redis-cli get test
# Expected: "value"
```

## Monitoring Verification

### Prometheus
```bash
# [ ] Prometheus accessible
curl -f https://your-domain.com:9090/api/v1/query?query=up

# [ ] Targets being scraped
curl https://your-domain.com:9090/api/v1/targets | grep -o '"health":"up"' | wc -l
# Expected: At least 5 targets

# [ ] Metrics endpoint working
curl https://your-domain.com/metrics | head -n 5
# Expected: Prometheus metrics format

# [ ] Specific metrics present
curl https://your-domain.com/metrics | grep nebula_http_requests_total
```

### Grafana
```bash
# [ ] Grafana accessible
curl -I https://grafana.nebula-search.example.com
# Expected: HTTP 200

# [ ] Data source configured
# Visit: https://grafana.nebula-search.example.com/datasources

# [ ] Dashboards loaded
# Visit: https://grafana.nebula-search.example.com/dashboards
# Should see "Nebula Overview" dashboard

# [ ] Dashboard renders data
# Open Nebula Overview dashboard
# Should see graphs with data (not empty)
```

### Logs
```bash
# [ ] Application logs visible
docker compose -f docker-compose.prod.yml logs backend --tail=10

# [ ] Access logs present (if configured)
docker compose -f docker-compose.prod.yml logs nginx --tail=10

# [ ] Promtail running (if using Loki)
docker compose -f docker-compose.prod.yml logs promtail --tail=10

# [ ] Loki accessible (if configured)
curl -f https://your-domain.com:3100/ready
```

## Security Verification

### SSL/TLS
```bash
# [ ] HTTPS working
curl -I https://your-domain.com
# Expected: HTTP 200, connection secure

# [ ] SSL certificate valid
openssl s_client -connect your-domain.com:443 -servername your-domain.com </dev/null 2>/dev/null | openssl x509 -noout -dates

# [ ] TLS 1.3 enabled
openssl s_client -connect your-domain.com:443 -tls1_3 </dev/null 2>/dev/null | grep -q "TLSv1.3" && echo "TLS 1.3 enabled"

# [ ] Strong ciphers
nmap --script ssl-enum-ciphers -p 443 your-domain.com

# [ ] HSTS header present
curl -I https://your-domain.com | grep -i "strict-transport-security"

# [ ] Security headers present
curl -I https://your-domain.com | grep -i "x-frame-options"
curl -I https://your-domain.com | grep -i "x-content-type-options"
curl -I https://your-domain.com | grep -i "content-security-policy"
```

### Container Security
```bash
# [ ] Running as non-root
docker compose -f docker-compose.prod.yml exec backend id -u
# Expected: Not 0 (not root)

# [ ] Read-only filesystem
docker compose -f docker-compose.prod.yml inspect backend | grep -A 5 ReadonlyRootfs
# Expected: "ReadonlyRootfs": true

# [ ] Capabilities dropped
docker compose -f docker-compose.prod.yml inspect backend | grep -A 10 CapDrop

# [ ] No new privileges
docker compose -f docker-compose.prod.yml inspect backend | grep NoNewPrivileges
```

### Secrets Management
```bash
# [ ] Secrets not in environment (should be)
docker compose -f docker-compose.prod.yml exec backend env | grep -i secret
# Should not expose sensitive values

# [ ] .env.production not in git
git ls-files | grep .env.production
# Expected: (no output, file not tracked)

# [ ] .dockerignore excludes secrets
cat .dockerignore | grep -i env
# Should include .env*.production
```

## Performance Verification

### Response Times
```bash
# [ ] API response time < 200ms
time curl -s https://your-domain.com/health > /dev/null
# Expected: < 200ms

# [ ] Search response time < 1s (p95)
# Run multiple searches and check Grafana dashboard

# [ ] Frontend load time < 2s
time curl -s https://your-domain.com > /dev/null
# Expected: < 2s
```

### Resource Usage
```bash
# [ ] Check container stats
docker stats --no-stream

# Backend: < 2GB RAM, < 4 CPU
# Frontend: < 256MB RAM, < 0.5 CPU
# PostgreSQL: < 2GB RAM, < 2 CPU
# Redis: < 512MB RAM, < 1 CPU

# [ ] Database connections
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "SELECT count(*) FROM pg_stat_activity;"
# Expected: < 50

# [ ] Redis memory
docker compose -f docker-compose.prod.yml exec redis redis-cli INFO memory | grep used_memory_human
```

### Caching
```bash
# [ ] Response headers include cache
curl -I https://your-domain.com/assets/index.js | grep -i cache

# [ ] Gzip compression enabled
curl -I https://your-domain.com | grep -i "content-encoding: gzip"

# [ ] Redis caching working
docker compose -f docker-compose.prod.yml exec backend python -c "from app.services.cache import cache_service; print('Cache:', cache_service._redis or 'memory')"
```

## Backup & Recovery Verification

### Backup Creation
```bash
# [ ] Backup directory exists
mkdir -p backups
ls -la backups/

# [ ] PostgreSQL backup works
./scripts/backup.sh postgres
ls -lh backups/postgres_*.sql.gz

# [ ] Redis backup works
./scripts/backup.sh redis
ls -lh backups/redis_*.rdb.gz

# [ ] MinIO backup works
./scripts/backup.sh minio
ls -lh backups/minio_*.tar.gz

# [ ] Backup valid
gunzip -c backups/postgres_*.sql.gz | head -n 5
# Expected: PostgreSQL dump header
```

### Backup Restoration Test
```bash
# [ ] Can restore PostgreSQL (test in staging)
# ./scripts/restore.sh backups/postgres_latest.sql.gz

# [ ] Backup integrity
grep -c "INSERT INTO" backups/postgres_*.sql.gz
# Expected: > 0 (has data)
```

## Scaling Verification

### Horizontal Scaling
```bash
# [ ] Can scale backend
docker compose -f docker-compose.prod.yml up -d --scale backend=2

# [ ] Multiple instances running
docker compose -f docker-compose.prod.yml ps | grep backend
# Expected: 2 backend containers

# [ ] Load balanced
curl https://your-domain.com/health -H "X-Request-ID: test1"
curl https://your-domain.com/health -H "X-Request-ID: test2"
# Check request IDs in logs

# [ ] Scale back down
docker compose -f docker-compose.prod.yml up -d --scale backend=1
```

### Resource Limits
```bash
# [ ] Resource limits configured
docker compose -f docker-compose.prod.yml exec backend cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us

# [ ] Limits not exceeded
docker stats --no-stream | grep nebula
# Should stay within configured limits
```

## Logging Verification

### Structured Logging
```bash
# [ ] JSON logs in production
docker compose -f docker-compose.prod.yml logs backend --tail=1 | python -m json.tool
# Expected: Valid JSON

# [ ] Request ID present
docker compose -f docker-compose.prod.yml logs backend --tail=1 | grep -o '"request_id": "[^"]*"'

# [ ] Log levels working
docker compose -f docker-compose.prod.yml logs backend | grep -E "(INFO|WARNING|ERROR)"
```

### Log Rotation
```bash
# [ ] Log files not growing unbounded
du -sh docker/nginx/logs/
# Expected: < 100MB

# [ ] Old logs rotated
ls -la docker/nginx/logs/
# Expected: access.log, error.log, *.log-*
```

## CI/CD Verification

### GitHub Actions
```bash
# [ ] Workflows exist
ls -la .github/workflows/
# Expected: ci.yml, deploy.yml

# [ ] CI passing
# Visit: https://github.com/Sky-254-1/Nebula-search-engine-/actions

# [ ] Security scans configured
# Check for: Trivy, Snyk, CodeQL in workflows

# [ ] Docker build passing
# Check GitHub Actions for successful Docker builds
```

### Deployment Pipeline
```bash
# [ ] Staging deployment working
# Check staging environment

# [ ] Production deployment process documented
cat DEPLOYMENT.md

# [ ] Rollback procedure tested
# In staging environment:
git reset --hard HEAD~1
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## Final Checks

### Documentation
```bash
# [ ] All documentation present
[ ] DEPLOYMENT.md exists
[ ] PRODUCTION.md exists
[ ] DOCKER.md exists
[ ] BACKUP.md exists
[ ] MONITORING.md exists

# [ ] Documentation complete
grep -l "Quick Start\|Prerequisites\|Troubleshooting" DEPLOYMENT.md PRODUCTION.md DOCKER.md BACKUP.md MONITORING.md
# Expected: All 5 files
```

### No Secrets Committed
```bash
# [ ] Check git history
git log --all --full-history -- .env.production
# Expected: No commits found

# [ ] Check for password patterns
git log -p --all | grep -i "password.*=" | grep -v "CHANGE_ME\|EXAMPLE"
# Expected: No hardcoded passwords

# [ ] .gitignore includes secrets
cat .gitignore | grep -E "^\.env|^secrets|^docker/ssl"
# Expected: All present
```

### Backup Completeness
```bash
# [ ] Recent backup exists
ls -lh backups/*$(date +%Y%m%d)*

# [ ] Backup includes all components
backups/postgres_*.sql.gz    # PostgreSQL
backups/redis_*.rdb.gz       # Redis
backups/minio_*.tar.gz       # MinIO

# [ ] Backups tested (monthly)
# Document in BACKUP.md: Last tested YYYY-MM-DD
```

## Production Readiness Criteria

### Must Pass
- [x] All Docker services running and healthy
- [x] HTTPS working with valid certificate
- [x] Health endpoints returning 200
- [x] Database accessible with data
- [x] Redis accessible and caching
- [x] Frontend loading (React app)
- [x] API endpoints working
- [x] Monitoring (Prometheus) scraping metrics
- [x] Grafana dashboards loading with data
- [x] Backups automated and tested
- [x] No secrets in git
- [x] Documentation complete
- [x] SSL labs rating A or better

### Should Pass
- [x] Response times < 200ms (p95)
- [x] Error rate < 1%
- [x] Cache hit rate > 70%
- [x] Security headers present
- [x] Container security (non-root, read-only)
- [x] Resource limits within bounds
- [x] Logs structured (JSON)
- [x] CI/CD passing

### Nice to Have
- [ ] CDN configured for static assets
- [ ] WAF (Web Application Firewall) enabled
- [ ] Automated security scanning in CI
- [ ] DDoS protection
- [ ] Multi-region backup
- [ ] Blue-green deployment setup
- [ ] Automated rollback on failures
- [ ] Performance testing automated

## Sign-Off

**Deployed by:** ___________________
**Date:** ___________________
**Platform:** ___________________
**Domain:** ___________________

**Pre-production checklist complete:**
- [ ] All mandatory checks passing
- [ ] Staging environment tested
- [ ] Team notified
- [ ] Monitoring dashboards reviewed
- [ ] Runbooks accessible
- [ ] Backup schedule configured
- [ ] On-call rotation set

**Production deployment approved:**
- [ ] Engineering Lead
- [ ] DevOps
- [ ] Security (if applicable)

## Incident Response

If issues arise post-deployment:

1. **Check health endpoints**
   ```bash
   curl https://your-domain.com/health/detailed
   ```

2. **Review logs**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f
   ```

3. **Check monitoring**
   - Grafana: https://grafana.nebula-search.example.com
   - Look for anomalies in metrics

4. **Rollback if needed**
   ```bash
   ./scripts/restore.sh backups/postgres_latest.sql.gz
   docker compose -f docker-compose.prod.yml restart
   ```

5. **Escalate**
   - Notify on-call team
   - Create incident ticket
   - Document timeline

## Support Contacts

- **DevOps Team**: devops@example.com
- **Emergency**: PagerDuty / On-call rotation
- **Documentation**: https://github.com/Sky-254-1/Nebula-search-engine-/wiki