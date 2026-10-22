# Nebula Search Engine - Backup and Restore Guide

## Overview

This guide covers backup strategies, procedures, and disaster recovery for Nebula Search Engine.

## What to Backup

1. **PostgreSQL Database** - All data including users, documents, search indexes metadata
2. **Redis Data** - Cache, sessions, job queues
3. **MinIO Storage** - Uploaded documents, vector embeddings, exports
4. **Configuration** - Environment files, SSL certificates

## Automated Backups

### Setup Daily Backups

Add to crontab:
```bash
crontab -e

# Daily backup at 2:00 AM
0 2 * * * cd /opt/nebula-search && ./scripts/backup.sh all >> /var/log/nebula/backup.log 2>&1

# Weekly verification on Sundays at 4:00 AM
0 4 * * 0 cd /opt/nebula-search && ./scripts/backup.sh postgres >> /var/log/nebula/backup.log 2>&1
```

### Backup Script Usage

```bash
# Backup everything
./scripts/backup.sh all

# Backup specific component
./scripts/backup.sh postgres
./scripts/backup.sh redis
./scripts/backup.sh minio

# List backups
ls -lh backups/

# Check backup ages
find backups/ -name "*.gz" -exec ls -lh {} \;
```

### Backup Retention

Default retention: 30 days

Configure in `scripts/backup.sh`:
```bash
RETENTION_DAYS=30
```

## Manual Backup Procedures

### PostgreSQL Backup

```bash
# Full database dump
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U nebula nebula | gzip > backups/postgres_$(date +%Y%m%d_%H%M%S).sql.gz

# Specific table
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U nebula -t users nebula | gzip > backups/users.sql.gz

# With custom format (smaller, faster restore)
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U nebula -Fc nebula > backups/postgres_$(date +%Y%m%d).dump
```

### Redis Backup

```bash
# Trigger background save
docker compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE

# Wait for completion
sleep 2

# Copy RDB file
docker compose -f docker-compose.prod.yml exec redis cat /data/dump.rdb | gzip > backups/redis_$(date +%Y%m%d_%H%M%S).rdb.gz

# Alternative: RDB file directly
docker cp nebula-redis:/data/dump.rdb backups/redis_$(date +%Y%m%d).rdb
```

### MinIO Backup

```bash
# Using tar (all buckets)
docker run --rm \
  --volumes-from nebula-storage \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Using mc (MinIO client) for specific buckets
docker compose -f docker-compose.prod.yml exec minio mc mirror /data/uploads backups/minio-uploads
```

### Configuration Backup

```bash
# Create backup of config
tar -czf backups/config_$(date +%Y%m%d).tar.gz \
  .env.production \
  docker/ \
  infra/ \
  database/migrations/

# Include SSL certificates
tar -czf backups/ssl_$(date +%Y%m%d).tar.gz docker/ssl/
```

## Restore Procedures

### Full System Restore

**⚠️ WARNING: This will overwrite all data!**

```bash
# 1. Stop all services
docker compose -f docker-compose.prod.yml down

# 2. Restore PostgreSQL
./scripts/restore.sh backups/postgres_20240101_120000.sql.gz

# 3. Restore Redis
./scripts/restore.sh backups/redis_20240101_120000.rdb.gz

# 4. Restore MinIO
./scripts/restore.sh backups/minio_20240101_120000.tar.gz

# 5. Start services
docker compose -f docker-compose.prod.yml up -d

# 6. Verify
curl https://your-domain.com/health/detailed
```

### PostgreSQL Restore

```bash
# Stop backend
docker compose -f docker-compose.prod.yml stop backend worker scheduler

# Drop and recreate database
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "DROP DATABASE IF EXISTS nebula;"
docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -c "CREATE DATABASE nebula;"

# Restore from SQL dump
gunzip -c backups/postgres_20240101_120000.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres psql -U nebula nebula

# Start services
docker compose -f docker-compose.prod.yml start backend worker scheduler
```

### Redis Restore

```bash
# Stop Redis
docker compose -f docker-compose.prod.yml stop redis

# Restore RDB file
gunzip -c backups/redis_20240101_120000.rdb.gz > /tmp/dump.rdb
docker cp /tmp/dump.rdb nebula-redis:/data/dump.rdb
rm /tmp/dump.rdb

# Start Redis
docker compose -f docker-compose.prod.yml start redis

# Verify
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### MinIO Restore

```bash
# Stop MinIO
docker compose -f docker-compose.prod.yml stop storage

# Restore backup
docker run --rm \
  --volumes-from nebula-storage \
  -v $(pwd)/backups:/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/minio_20240101_120000.tar.gz -C /data"

# Start MinIO
docker compose -f docker-compose.prod.yml start storage

# Verify buckets
docker compose -f docker-compose.prod.yml exec storage ls /data
```

## Backup Strategies

### 3-2-1 Backup Strategy

- **3 copies** of your data (original + 2 backups)
- **2 different storage types** (local disk + cloud)
- **1 offsite backup** (S3, Glacier, etc.)

### Recommended Schedule

| Backup Type | Frequency | Retention | Storage |
|-------------|-----------|-----------|---------|
| Daily incremental | Daily | 7 days | Local |
| Weekly full | Weekly | 4 weeks | Local |
| Monthly archive | Monthly | 12 months | S3/Glacier |
| Configuration | On change | Permanent | Git |

### Cloud Backup (AWS S3)

```bash
# Install AWS CLI
sudo apt install awscli

# Configure
aws configure

# Daily sync to S3
aws s3 sync backups/ s3://nebula-backups/$(date +%Y%m%d)/

# Lifecycle policy for Glacier
# Configure in AWS Console:
# - Move to Glacier after 30 days
# - Delete after 1 year
```

## Verification

### Test Backup Integrity

```bash
# Verify PostgreSQL backup
gunzip -c backups/postgres_20240101.sql.gz | head -n 20

# Check file size
ls -lh backups/

# Verify checksums
md5sum backups/postgres_*.sql.gz > checksums.txt
```

### Test Restore Procedure

Monthly restore test to a staging environment:
```bash
# 1. Deploy to staging
docker compose -f docker-compose.staging.yml up -d

# 2. Restore backup
./scripts/restore.sh backups/postgres_latest.sql.gz

# 3. Verify
curl https://staging.nebula-search.example.com/health/detailed

# 4. Clean up
docker compose -f docker-compose.staging.yml down -v
```

## Disaster Recovery

### Recovery Time Objectives (RTO)

- **Database corruption**: 30 minutes
- **Server failure**: 1 hour
- **Data center failure**: 4 hours

### Recovery Point Objectives (RPO)

- **Daily backups**: 24 hours maximum data loss
- **Continuous replication**: < 1 hour (future enhancement)

### Disaster Recovery Plan

#### Scenario 1: Complete Server Loss

```bash
# 1. Provision new server
# 2. Install Docker
curl -fsSL https://get.docker.com | sh

# 3. Clone repository
git clone https://github.com/Sky-254-1/Nebula-search-engine-.git
cd Nebula-search-engine-

# 4. Copy latest backup from S3
aws s3 sync s3://nebula-backups/latest/ backups/

# 5. Configure environment
cp .env.example .env.production
nano .env.production

# 6. Restore data
./scripts/restore.sh backups/postgres_latest.sql.gz

# 7. Deploy
docker compose -f docker-compose.prod.yml up -d

# 8. Update DNS
```

#### Scenario 2: Database Corruption

```bash
# 1. Stop services
docker compose -f docker-compose.prod.yml down

# 2. Restore from backup
./scripts/restore.sh backups/postgres_yesterday.sql.gz

# 3. Replay WAL (if using continuous archiving)
# (Requires PostgreSQL WAL archiving configuration)

# 4. Start services
docker compose -f docker-compose.prod.yml up -d

# 5. Verify data integrity
```

#### Scenario 3: Accidental Data Deletion

```bash
# 1. Stop services immediately
docker compose -f docker-compose.prod.yml down

# 2. Restore from most recent backup
./scripts/restore.sh backups/postgres_latest.sql.gz

# 3. Point-in-time recovery (if needed)
# Requires PostgreSQL WAL archiving

# 4. Start services
docker compose -f docker-compose.prod.yml up -d
```

## Monitoring Backups

### Backup Success Monitoring

```bash
# Check backup log
tail -f /var/log/nebula/backup.log

# Verify backup files exist
ls -lh backups/*$(date +%Y%m%d)*
```

### Disk Space Monitoring

```bash
# Check backup directory size
du -sh backups/

# Monitor disk space
df -h

# Alert if backup dir > 50GB
if [ $(du -sm backups/ | cut -f1) -gt 50000 ]; then
    echo "WARNING: Backup directory exceeds 50GB"
fi
```

### Grafana Alerts

Add alerts for:
- Backup job failures
- Insufficient disk space
- Old backups (> 35 days)

## Security

### Encrypt Backups

```bash
# Encrypt with GPG
gpg --symmetric --cipher-algo AES256 backups/postgres_20240101.sql.gz

# Decrypt
gpg --decrypt backups/postgres_20240101.sql.gz.gpg | gunzip > restore.sql
```

### Secure Backup Storage

```bash
# Set restrictive permissions
chmod 700 backups/
chmod 600 backups/*

# Use encrypted filesystem
# Or cloud storage with encryption at rest
```

### Backup Integrity

```bash
# Generate checksums
md5sum backups/*.sql.gz > checksums.md5

# Verify on restore
md5sum -c checksums.md5

# Or use SHA256
sha256sum backups/*.sql.gz > checksums.sha256
```

## Best Practices

1. **Test regularly** - Monthly restore tests to staging
2. **Multiple copies** - Follow 3-2-1 strategy
3. **Encrypt sensitive data** - Use GPG for backups
4. **Document procedures** - This guide
5. **Monitor backups** - Automated alerts
6. **Store offsite** - S3, Glacier, remote server
7. **Version control config** - Keep .env.example updated
8. **Retention policy** - Regular cleanup of old backups

## Support

- Restore Scripts: [scripts/restore.sh](./scripts/restore.sh)
- Backup Scripts: [scripts/backup.sh](./scripts/backup.sh)
- Operations Guide: [PRODUCTION.md](./PRODUCTION.md)