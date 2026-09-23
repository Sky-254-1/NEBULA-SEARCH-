# Disaster Recovery Guide

## Overview

This document outlines the disaster recovery procedures for Nebula Search Engine. It covers backup strategies, recovery procedures, and business continuity planning.

## Backup Strategy

### Automated Backups

**Schedule:**
- **Daily automated backups** at 2:00 AM UTC
- **Retention period**: 30 days
- **Backup location**: Local (`database/backups/`) + Cloud (optional)

**Backup Components:**
1. **PostgreSQL database** - Full logical backup via `pg_dump`
2. **Storage files** - Document uploads and exports (if using local storage)
3. **Configuration files** - Environment configurations and secrets

### Backup Script

```powershell
# Windows - Create daily backup with cloud upload
.\scripts\backup.ps1 -Compress -RetentionDays 30 -UploadToCloud s3 -CloudBucket "nebula-backups"

# Linux/Mac - Use backup.sh
./scripts/backup.sh --compress --retention-days 30
```

### Cloud Storage Integration

**Supported Providers:**
- **AWS S3**: `aws s3 cp <backup> s3://<bucket>/nebula-backups/`
- **Azure Blob Storage**: `az storage blob upload --container-name <bucket>`
- **Google Cloud Storage**: `gsutil cp <backup> gs://<bucket>/nebula-backups/`

**Configuration:**
```powershell
# S3 Setup
.\scripts\backup.ps1 -UploadToCloud s3 -CloudBucket "my-backup-bucket" -CloudPath "prod/nebula"

# Azure Setup
.\scripts\backup.ps1 -UploadToCloud azure -CloudBucket "nebulabackups" -CloudPath "backups"

# GCS Setup
.\scripts\backup.ps1 -UploadToCloud gcs -CloudBucket "nebula-backups-prod"
```

### Encryption

**Enable encryption for sensitive data:**
```powershell
.\scripts\backup.ps1 -Encrypt -Password "SecurePassword123" -Compress -RetentionDays 30
```

**Security:**
- AES-256 encryption with PBKDF2 key derivation
- 10,000 iterations for key stretching
- Salt: `NebulaSearchEngine2024`

## Recovery Procedures

### Scenario 1: Complete System Failure

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 24 hours (last backup)

**Steps:**

1. **Provision new infrastructure** (2 hours)
   ```bash
   # Deploy using Docker Compose
   docker-compose up -d postgres redis
   ```

2. **Restore database** (30 minutes)
   ```powershell
   # Windows
   .\scripts\restore.ps1 -BackupFile ".\database\backups\nebula_20240101_120000.sql.gz"
   
   # Linux/Mac
   gunzip -c database/backups/nebula_20240101_120000.sql.gz | docker exec -i nebula-postgres psql -U nebula nebula
   ```

3. **Verify data integrity** (30 minutes)
   ```sql
   -- Check table counts
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM documents;
   SELECT COUNT(*) FROM search_logs;
   
   -- Check indexes
   SELECT indexname FROM pg_indexes WHERE tablename = 'documents';
   ```

4. **Deploy application** (1 hour)
   ```bash
   # Pull latest image
   docker-compose up -d backend frontend
   
   # Run migrations
   make migrate
   
   # Verify health
   curl https://nebula.example.com/health/detailed
   ```

### Scenario 2: Data Corruption

**Symptoms:**
- Database errors in logs
- Search functionality broken
- Inconsistent query results

**Recovery Steps:**

1. **Stop write operations**
   ```bash
   docker-compose stop backend
   ```

2. **Identify last known good backup**
   ```powershell
   # List available backups
   Get-ChildItem database\backups\nebula_*.sql.gz | Sort-Object LastWriteTime -Descending
   ```

3. **Restore to staging environment first**
   ```powershell
   .\scripts\restore.ps1 -BackupFile "database\backups\nebula_20240101_120000.sql.gz" -SkipValidation $false
   ```

4. **Validate data**
   ```sql
   -- Check document counts
   SELECT status, COUNT(*) FROM documents GROUP BY status;
   
   -- Verify search logs
   SELECT COUNT(*) FROM search_logs WHERE searched_at > NOW() - INTERVAL '7 days';
   ```

5. **Promote to production**
   ```powershell
   # Repeat restore on production
   .\scripts\restore.ps1 -BackupFile "database\backups\nebula_20240101_120000.sql.gz"
   docker-compose start backend
   ```

### Scenario 3: Accidental Data Deletion

**Recovery Steps:**

1. **Identify deletion timestamp**
   ```sql
   -- Check audit logs for deletion events
   SELECT * FROM audit_logs 
   WHERE action IN ('document_deleted', 'user_deleted') 
   AND created_at > NOW() - INTERVAL '1 hour';
   ```

2. **Restore to temporary database**
   ```powershell
   .\scripts\restore.ps1 -BackupFile "database\backups\nebula_20240101_120000.sql.gz" -DatabaseName "nebula_recovery"
   ```

3. **Export deleted records**
   ```sql
   -- Export deleted documents
   COPY (SELECT * FROM nebula_prod.documents WHERE id IN (...)) TO '/tmp/deleted_docs.csv';
   ```

4. **Restore specific records**
   ```sql
   -- Insert recovered documents
   INSERT INTO documents SELECT * FROM nebula_recovery.documents WHERE id IN (...);
   ```

## Backup Verification

### Automated Verification

**Daily backup health check:**
```powershell
.\scripts\verify-backup.ps1 -BackupFile "database\backups\nebula_latest.sql.gz"
```

**Verification checks:**
- ✅ Backup file integrity (checksum)
- ✅ Valid SQL syntax
- ✅ Required tables present
- ✅ Foreign key constraints valid
- ✅ Row counts within expected ranges

### Manual Verification

**Weekly manual verification:**
```bash
# 1. Create test database
docker-compose exec postgres createdb nebula_test

# 2. Restore latest backup
gunzip -c database/backups/nebula_latest.sql.gz | docker exec -i nebula-postgres psql -U nebula nebula_test

# 3. Run sanity checks
docker-compose exec postgres psql -U nebula -d nebula_test -c "SELECT COUNT(*) FROM users;"
docker-compose exec postgres psql -U nebula -d nebula_test -c "SELECT COUNT(*) FROM documents;"

# 4. Cleanup
docker-compose exec postgres dropdb nebula_test
```

## Monitoring & Alerts

### Backup Monitoring

**Metrics to track:**
- ✅ Backup completion status
- ✅ Backup file size (alert if < 1 MB)
- ✅ Backup duration (alert if > 1 hour)
- ✅ Cloud upload success/failure
- ✅ Disk space availability

**Alert thresholds:**
```yaml
alerts:
  - name: BackupFailed
    condition: backup_status != "success"
    severity: critical
    notification: ops-team@nebula.example.com
  
  - name: BackupSizeTooSmall
    condition: backup_size_mb < 1
    severity: warning
    notification: ops-team@nebula.example.com
  
  - name: DiskSpaceLow
    condition: disk_usage_percent > 80
    severity: warning
    notification: ops-team@nebula.example.com
```

### Recovery Testing

**Monthly recovery drill:**
1. Restore backup to staging environment
2. Run automated test suite
3. Verify search functionality
4. Document recovery time
5. Update recovery procedures

**Quarterly full disaster recovery test:**
1. Simulate complete system failure
2. Restore from latest backup
3. Validate data integrity
4. Measure RTO and RPO
5. Update disaster recovery plan

## Business Continuity

### Service Level Agreements

| Metric | Target | Minimum |
|--------|--------|---------|
| RTO (Recovery Time Objective) | 4 hours | 8 hours |
| RPO (Recovery Point Objective) | 24 hours | 48 hours |
| Backup Success Rate | 99.5% | 95% |
| Data Integrity | 100% | 99.9% |

### Escalation Procedures

**Severity 1 - Complete Outage:**
1. On-call engineer (15 min response)
2. Engineering lead (30 min response)
3. CTO (1 hour response)

**Severity 2 - Data Loss:**
1. On-call engineer (30 min response)
2. Engineering lead (2 hour response)

**Severity 3 - Backup Failure:**
1. On-call engineer (1 hour response)
2. Engineering lead (24 hour response)

## Appendix

### Backup Checklist

- [ ] Daily backup completed successfully
- [ ] Backup uploaded to cloud storage
- [ ] Backup size within expected range
- [ ] Retention policy applied
- [ ] Disk space adequate
- [ ] Backup verification passed
- [ ] Alert notifications working

### Recovery Checklist

- [ ] Infrastructure provisioned
- [ ] Database restored from backup
- [ ] Data integrity verified
- [ ] Application deployed
- [ ] Migrations run
- [ ] Health checks passing
- [ ] Search functionality tested
- [ ] Monitoring enabled
- [ ] Stakeholders notified

### Useful Commands

```bash
# List all backups
ls -lh database/backups/

# Test backup restoration
gunzip -c database/backups/nebula_20240101_120000.sql.gz | docker exec -i nebula-postgres psql -U nebula nebula_test

# Verify database integrity
docker-compose exec postgres psql -U nebula -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Check disk space
df -h database/backups/

# Monitor backup logs
tail -f logs/backup.log
```

## Contact Information

**Emergency Contacts:**
- On-call Engineer: [PagerDuty link]
- Engineering Lead: [Contact info]
- DevOps Team: [Contact info]

**Documentation:**
- Runbooks: [Link]
- Architecture: [Link]
- Monitoring: [Link]

---

**Last Updated:** 2024-01-15
**Next Review:** 2024-04-15
**Owner:** Operations Team