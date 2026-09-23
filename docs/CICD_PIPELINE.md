# CI/CD Pipeline Documentation

## Overview

The Nebula Search Engine uses GitHub Actions for continuous integration and deployment. The pipeline automates testing, security scanning, building, and deployment to staging and production environments.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `master` branches
- Pull requests to `main` or `master` branches

**Jobs:**

#### Test Job
- **Runs on:** Ubuntu latest
- **Python versions:** 3.11, 3.12 (matrix strategy)
- **Steps:**
  1. Checkout code
  2. Set up Python environment
  3. Install dependencies from `backend/requirements-dev.txt`
  4. Run tests with coverage (75% minimum threshold)
  5. Run new API domain tests
  6. Verify app imports
  7. Upload coverage reports to Codecov

**Coverage Requirements:**
- Minimum 75% coverage for existing tests
- New tests in `test_new_api_domains.py` are included
- Coverage reports uploaded to Codecov for tracking

#### Frontend Job
- **Runs on:** Ubuntu latest
- **Steps:**
  1. Checkout code
  2. Set up Node.js 20
  3. Install dependencies
  4. Build frontend

#### E2E Test Job
- **Runs on:** Ubuntu latest
- **Depends on:** Test and Frontend jobs
- **Timeout:** 30 minutes
- **Steps:**
  1. Checkout code
  2. Set up Python 3.11
  3. Install backend dependencies
  4. Set up Node.js 20
  5. Install root and frontend dependencies
  6. Install Playwright browsers
  7. Run E2E tests
  8. Upload Playwright report (retained for 14 days)

### 2. Deployment Workflow (`.github/workflows/deploy.yml`)

**Triggers:**
- Push to `main` or `master` branches
- Manual workflow dispatch (for staging/production selection)

**Jobs:**

#### Security Scan Job
- **Runs on:** Ubuntu latest
- **Steps:**
  1. Checkout code
  2. Run Trivy vulnerability scanner (filesystem scan)
  3. Upload Trivy results to GitHub Security
  4. Run Snyk security scan (Python dependencies)
  5. Continue on error (non-blocking)

#### Test Job
- **Runs on:** Ubuntu latest
- **Depends on:** Security Scan
- **Steps:**
  1. Checkout code
  2. Set up Python 3.11
  3. Install dependencies
  4. Run all tests with 80% coverage threshold
  5. Upload coverage to Codecov (fail on error)

#### Performance Test Job
- **Runs on:** Ubuntu latest
- **Depends on:** Test job
- **Steps:**
  1. Checkout code
  2. Set up Python 3.11
  3. Install dependencies + Locust
  4. Start backend server
  5. Run load test (10 users, 2 spawn rate, 1 minute)
  6. Upload performance results (retained for 30 days)

#### Build Job
- **Runs on:** Ubuntu latest
- **Depends on:** Test and Performance Test jobs
- **Steps:**
  1. Checkout code
  2. Set up Docker Buildx
  3. Login to Docker Hub
  4. Extract metadata (SHA, tag, date, version)
  5. Build and push Docker image with caching

**Docker Image Tags:**
- `nebula-search:{version}` (e.g., `main-20260704-abc1234`)
- `nebula-search:latest`

#### Deploy to Staging Job
- **Runs on:** Ubuntu latest
- **Depends on:** Build job
- **Conditions:** Push to main OR manual trigger with staging selection
- **Environment:** staging
- **Steps:**
  1. Checkout code
  2. Deploy via SSH to staging server
  3. Pull latest Docker images
  4. Restart services
  5. Clean up Docker system
  6. Run smoke tests (health checks)

#### Deploy to Production Job
- **Runs on:** Ubuntu latest
- **Depends on:** Build and Deploy to Staging jobs
- **Conditions:** Push to main branch only
- **Environment:** production
- **Steps:**
  1. Checkout code
  2. Create GitHub Deployment
  3. Deploy via SSH to production server
  4. Pull latest Docker images
  5. Restart services
  6. Clean up Docker system
  7. Update deployment status
  8. Notify team via Slack (on success)
  9. Trigger rollback via webhook (on failure)

## Required Secrets

### GitHub Repository Secrets

Configure these in your GitHub repository settings (Settings → Secrets and variables → Actions):

#### Docker Hub
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password or access token

#### Staging Environment
- `STAGING_HOST` - Staging server hostname/IP
- `STAGING_USERNAME` - SSH username for staging
- `STAGING_SSH_KEY` - SSH private key for staging access

#### Production Environment
- `PRODUCTION_HOST` - Production server hostname/IP
- `PRODUCTION_USERNAME` - SSH username for production
- `PRODUCTION_SSH_KEY` - SSH private key for production access

#### Notifications
- `SLACK_WEBHOOK_URL` - Slack webhook URL for deployment notifications
- `ROLLBACK_WEBHOOK_URL` - Webhook URL to trigger rollback on failure

#### Security Scanning (Optional)
- `SNYK_TOKEN` - Snyk API token for security scanning

## Environment Setup

### Staging Environment

**Server Requirements:**
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- SSH access configured
- Minimum 2GB RAM, 2 CPU cores
- 20GB disk space

**Deployment Directory:** `/opt/nebula-search`

**Access:**
```bash
ssh -i ~/.ssh/nebula-staging staging-user@staging-server
cd /opt/nebula-search
```

### Production Environment

**Server Requirements:**
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- SSH access configured
- Minimum 4GB RAM, 4 CPU cores
- 50GB disk space
- SSL certificates configured
- Domain name pointing to server

**Deployment Directory:** `/opt/nebula-search`

**Access:**
```bash
ssh -i ~/.ssh/nebula-prod prod-user@prod-server
cd /opt/nebula-search
```

## Pipeline Flow

### Normal Flow (Push to Main)

```
Push to main
    ↓
CI Workflow (ci.yml)
    ↓
├─ Test Job (Python 3.11, 3.12)
│  ├─ Run tests with coverage
│  └─ Upload to Codecov
├─ Frontend Job
│  └─ Build frontend
└─ E2E Job
   └─ Run Playwright tests
    ↓
Deploy Workflow (deploy.yml)
    ↓
├─ Security Scan
│  ├─ Trivy scan
│  └─ Snyk scan
├─ Test Job (full suite)
│  └─ 80% coverage requirement
├─ Performance Test
│  └─ Load test with Locust
├─ Build Job
│  └─ Build & push Docker image
├─ Deploy to Staging
│  ├─ SSH deploy
│  └─ Smoke tests
└─ Deploy to Production
   ├─ Create GitHub Deployment
   ├─ SSH deploy
   ├─ Health checks
   └─ Slack notification
```

### Manual Deployment

To manually trigger a deployment:

1. Go to GitHub repository
2. Click "Actions" tab
3. Select "Deploy to Production" workflow
4. Click "Run workflow"
5. Select environment (staging or production)
6. Click "Run workflow"

## Monitoring

### GitHub Actions Dashboard

View workflow runs:
- **CI:** https://github.com/Sky-254-1/Nebula-search-engine-/actions/workflows/ci.yml
- **Deploy:** https://github.com/Sky-254-1/Nebula-search-engine-/actions/workflows/deploy.yml

### Codecov Dashboard

View coverage reports:
- https://codecov.io/gh/Sky-254-1/Nebula-search-engine-

### Deployment History

View deployments in GitHub:
- Repository → Deployments tab

## Troubleshooting

### Common Issues

#### 1. Tests Fail in CI but Pass Locally

**Cause:** Environment differences, missing dependencies, or database issues

**Solution:**
- Check CI logs for specific error
- Ensure `requirements-dev.txt` is up to date
- Verify test database setup in CI environment

#### 2. Docker Build Fails

**Cause:** Missing dependencies, Dockerfile issues, or Docker Hub authentication

**Solution:**
- Check Docker Hub credentials in secrets
- Review Dockerfile for errors
- Check Docker build logs in Actions

#### 3. Deployment Fails

**Cause:** SSH access issues, server problems, or health check failures

**Solution:**
- Verify SSH keys in secrets
- Check server status and logs
- Ensure services are running on server
- Review deployment logs in Actions

#### 4. Coverage Below Threshold

**Cause:** New code without tests or broken tests

**Solution:**
- Add tests for new code
- Fix broken tests
- Update coverage threshold if necessary (currently 75% for CI, 80% for deploy)

## Best Practices

1. **Always run tests locally before pushing**
   ```bash
   cd backend
   pytest --cov=app --cov-report=term-missing
   ```

2. **Monitor CI/CD pipeline on every push**
   - Fix failing tests immediately
   - Don't ignore warnings

3. **Keep dependencies updated**
   - Regularly update `requirements.txt` and `requirements-dev.txt`
   - Review Dependabot alerts

4. **Use feature branches**
   - Don't push directly to main
   - Create PRs for review
   - Let CI validate before merging

5. **Tag releases**
   - Use semantic versioning
   - Tag releases in Git
   - Docker images are automatically tagged

## Performance Targets

### Test Execution Time
- Unit tests: < 2 minutes
- E2E tests: < 30 minutes
- Full pipeline: < 45 minutes

### Coverage Targets
- Overall: 80%
- New code: 90%
- Critical paths: 100%

### Performance Benchmarks
- API response time: < 200ms (p95)
- Search query: < 500ms (p95)
- Document upload: < 2s for 10MB file

## Rollback Procedure

If production deployment fails:

1. **Automatic Rollback** (configured in workflow)
   - Slack notification sent
   - Rollback webhook triggered

2. **Manual Rollback**
   ```bash
   # SSH to production server
   ssh -i ~/.ssh/nebula-prod prod-user@prod-server
   
   # Navigate to deployment directory
   cd /opt/nebula-search
   
   # Rollback to previous version
   docker-compose down
   docker-compose pull nebula-search:previous-version
   docker-compose up -d
   
   # Verify health
   curl -f https://nebula-search.example.com/health
   ```

3. **GitHub Deployment Rollback**
   - Go to repository → Deployments
   - Find the previous successful deployment
   - Click "Redeploy" or manually trigger deployment with previous SHA

## Maintenance

### Weekly Tasks
- Review Codecov reports
- Check security scan results
- Review performance test results
- Clean up old Docker images

### Monthly Tasks
- Update dependencies
- Review and update CI/CD workflows
- Audit secrets and access
- Review deployment logs for issues

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Snyk Documentation](https://docs.snyk.io/)

---

**Last Updated:** 2026-07-04  
**Maintained by:** Nebula Search Engine Team