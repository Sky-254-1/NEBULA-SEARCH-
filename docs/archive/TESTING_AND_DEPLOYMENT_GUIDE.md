# 🧪 CI/CD Pipeline & Testing Guide

## Overview

This guide documents the complete testing and deployment pipeline for Nebula Search Engine, including automated testing strategies, validation procedures, and deployment checks.

## 📋 Table of Contents

### 1. CI/CD Pipeline Configuration
   - GitHub Actions workflow
   - Job dependencies
   - Trigger conditions

### 2. Testing Strategy
   - Unit Testing
   - Integration Testing
   - End-to-End (E2E) Testing
   - Performance Testing
   - Security Testing

### 3. Test Environments
   - Development
   - Staging
   - Production

### 4. Deployment Validation
   - Health Checks
   - Smoke Tests
   - Load Testing
   - Performance Monitoring

### 5. Test Data & Fixtures
   - Database setup
   - Test seeds
   - Configuration

### 6. Test Reports & Metrics
   - Coverage reports
   - Performance benchmarks
   - Security scan results

## 🛠️ CI/CD Pipeline Overview

### Version Control<br>
**Primary Branch:** `main`<br>
**Development Branch:** `develop`<br>
**Feature Branches:** Branch-specific names (e.g., `feature/auth-ui`, `bugfix/search-performance`)

### GitHub Actions Workflow (`.github/workflows/deploy.yml`)

| Job | Dependencies | Triggers | Description |
|-----|--------------|----------|-------------|
| **lint** | None | Push/Pull Requests | Code quality checks (ruff, mypy, TypeScript) |
| **test-backend** | `[lint]` | Push/Pull Requests | Backend unit tests (Python 3.10-3.12) |
| **test-frontend** | `[lint]` | Push/Pull Requests | Frontend unit tests (Vitest) |
| **e2e** | `[test-backend, test-frontend]` | Push/Pull Requests | End-to-end testing with Playwright |
| **security** | `[lint]` | Push/Pull Requests | Security scanning (CodeQL, Bandit) |
| **build** | `[test-backend, test-frontend, security]` | Push (Tags/Branches) | Docker image build and push |
| **deploy-staging** | `[build]` | Push to `main` | Deploy to staging environment |
| **deploy-production** | `[deploy-staging]` | Tags | Deploy to production |
| **load-test** | `[deploy-staging]` | Schedule/Condition | Automated load testing |

## 🧪 Testing Strategy

### 1. Unit Tests

**Location:** `backend/tests/` and `tests/`

#### Backend Unit Tests (`backend/tests/`)
- **Framework:** pytest
- **Python Versions:** 3.10, 3.11, 3.12
- **Coverage Threshold:** 35%
- **Key Test Categories:**
  - Authentication & Authorization (`test_auth.py`, `test_auth_service.py`)
  - Search & Indexing (`test_search.py`, `test_search_service.py`)
  - Vector Search (`test_vector.py`, `test_hybrid_search.py`)
  - AI & LLM Integration (`test_ai_service.py`)
  - Caching & Performance (`test_cache_service.py`)
  - Database Operations (`test_database.py`)

#### Frontend Unit Tests (`tests/`)
- **Framework:** Vitest
- **Runtime:** Node.js 20
- **Coverage:** Automatically reported

#### E2E Tests (`tests/e2e/`)
- **Framework:** Playwright
- **Environment:** Requires running backend
- **Test Scenarios:**
  - Authentication flows
  - Search functionality
  - Document management
  - User profiles & settings

### 2. Integration Tests

**Purpose:** Verify system interactions between components

#### Database Integration
- Schema validation
- Migration testing
- Seed data verification

#### Service Integration
- API endpoint testing
- Authentication integration
- Search integration

### 3. Performance Testing

**Framework:** Locust + pytest-benchmark

#### Performance Benchmarks (`tests/performance/`)
- **Target Response Times:**
  - Authentication: <200ms (p95)
  - Web Search: <500ms (p95)
  - Document Operations: <200ms (p95)
  - Admin Stats: <300ms (p95)
- **Load Testing:** 100 concurrent users
- **Stress Testing:** Spikes up to 1000 users

### 4. Security Testing

**Components:**
- **Static Analysis:** CodeQL (GitHub)
- **Dynamic Analysis:** Bandit (Python security)
- **Dependency Scanning:** Safety (dependency vulnerabilities)
- **Configuration Security:** Environment validation

## 🌍 Test Environments

### 1. Development Environment
```bash
# Local development
# docker compose -f docker-compose.dev.yml up -d
# cd backend && python -m pytest
```

**Key Features:**
- SQLite database (or PostgreSQL with env vars)
- In-memory Redis
- Auto-reloading backend
- Hot module replacement frontend

### 2. Staging Environment
**Triggered by:** Push to `main` branch

**Setup:**
```bash
# Kubernetes cluster with services:
- PostgreSQL
- Redis
- MinIO
- Load balancer
```

**Validation:**
- Health checks (`/health`, `/health/ready`)
- Smoke tests (search, auth endpoints)
- Performance benchmarks

### 3. Production Environment
**Triggered by:** Tag release (e.g., `v1.0.0`)

**Controls:**
- Manual environment approval
- Zero-downtime deployment
- Post-deployment health checks
- Monitoring integration

## 🚀 Deployment Validation

### 1. Health Checks
```bash
# Basic health
# curl https://your-domain.com/health

# Readiness (Kubernetes)
# curl https://your-domain.com/health/ready

# Liveness (Kubernetes)
# curl https://your-domain.com/health/live

# Detailed health
# curl https://your-domain.com/health/detailed
```

### 2. Smoke Tests
```bash
# Post-deployment validation
# curl -f https://your-domain.com/api/v1/search?q=test
# curl -f https://your-domain.com/api/v1/auth/me
# curl -f https://your-domain.com/metrics
```

### 3. Load Testing
```bash
# Automated via GitHub Actions
# locust -f tests/load/locustfile.py --headless
# --users 100 --spawn-rate 10 --run-time 5m
```

### 4. Performance Validation
```bash
# Query Prometheus for metrics
# https://your-domain.com:9090

# Check key indicators:
# - Request rate (req/sec)
# - Response time (p95, p99)
# - Error rate (5xx)
# - Database connections
# - Cache hit rate
```

## 📊 Test Reports & Metrics

### 1. Coverage Reports
- **Tool:** pytest-cov with XML output
- **Integration:** codecov.io
- **Threshold:** 35% minimum
- **Metrics:** Line, branch, and function coverage

### 2. Performance Reports
- **Format:** JSON/CSV with historical comparison
- **Metrics:** Latency, throughput, error rates
- **Thresholds:** Endpoint-specific p95/p99 targets

### 3. Security Reports
- **Format:** SARIF/JSON for tooling
- **Findings:** Vulnerability severity levels
- **Compliance:** OWASP Top 10 alignment

### 4. Test Summary Dashboard
Generate status badges and summaries:
```markdown
[![Nebula Search CI](https://github.com/Sky-254-1/Nebula-search-engine-/actions/workflows/deploy.yml/badge.svg)](https://github.com/Sky-254-1/Nebula-search-engine-/actions/workflows/deploy.yml)
```

## 🔧 Test Data & Fixtures

### 1. Database Seeds
**Location:** `database/seeds/`

| File | Purpose |
|------|---------|
| `001_roles.sql` | Role definitions (admin, user) |
| `002_permissions.sql` | Permission mappings |
| `003_settings.sql` | System settings |
| `004_feature_flags.sql` | Feature toggles |

### 2. Test Environment Configuration
**Files:**
- `.env.example` - Development template
- `.env.development` - Local overrides
- `.env.production` - Production secrets (DO NOT COMMIT)

### 3. Database Schema
**Location:** `database/schema/`
- `001_initial_schema.sql` - Core database structure
- Supports both SQLite (dev) and PostgreSQL (prod)

## 📈 Metrics Collection

### 1. Metrics Exported
**Backend (`/metrics` endpoint):**
- HTTP request counts (per status code)
- Response time percentiles
- Database connection pool stats
- Cache hit/miss ratios
- Active connections

### 2. Monitoring Stack
**Components:**
- **Prometheus:** Metrics collection and alerting
- **Grafana:** Dashboards and visualizations
- **Loki:** Structured log aggregation
- **Alertmanager:** Notification routing

### 3. Alerting Thresholds
```yaml
# Examples for alerting setup
services:
  api:
    response_time_p95: 500ms  # Alert if exceeded
    error_rate: 1%             # Alert if >1% errors
    cpu_usage: 80%             # Alert if >80% CPU
  database:
    connection_pool: 90%       # Alert if >90% utilized
    query_time_p95: 200ms      # Alert if slow queries
```

## 🔄 Feedback & Continuous Improvement

### 1. Test Failure Analysis
```bash
# Detailed failure reporting
python -m pytest --verbose --tb=long --capture=no

# Coverage analysis
coverage report -m --include="src/*"

# Performance analysis
python tests/performance/benchmarks.py --compare
```

### 2. Improvement Tracking
Maintain a log of:
- Performance regressions
- Test failures analysis
- Security vulnerabilities
- Deployment issues

### 3. Metrics Dashboard
Track key indicators:
- Test pass rates (target: 95%+)
- Coverage trends
- Performance benchmarks
- Security scan status

## ⚡ Quick Start Guide

### For Developers
```bash
# Run all tests
make test

# Run specific test suite
make test-backend
make test-frontend
make test-e2e

# Lint and format
make lint
make format
make typecheck

# Run performance benchmarks
make test-performance
```

### For Contributors
```bash
# PR Checklist
- [ ] Code passes linting (ruff, mypy, TypeScript)
- [ ] Backend tests pass (including coverage)
- [ ] Frontend tests pass
- [ ] New E2E tests added when testing UI/UX
- [ ] Security scans pass
- [ ] Documentation updated (if changes affect API)
```

## 📞 Support & Troubleshooting

### Common Test Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL
pg_isready -U nebula -d nebula

# Start local PostgreSQL
brew install postgresql
postgresql -D /usr/local/var/postgres start
```

#### 2. Memory Issues
```bash
# Increase Node.js memory for frontend tests
docker run --rm -v $(pwd)/frontend:/src -w /src node:20-alpine sh -c "npm ci && npx vitest run --reporter=verbose --max-old-space-size=4096"
```

#### 3. Playwright Browser Setup
```bash
# Install browsers globally
npm run e2e:install

# Or locally
npx playwright install
```

## 🔗 Related Links

- [GitHub Actions Status](https://github.com/Sky-254-1/Nebula-search-engine-/actions)
- [Documentation](https://docs.nebula-search.io)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security Guide](docs/SECURITY.md)

---

**Generated:** $(date) | **Maintainer:** DevOps Team | **Last Updated:** $(date +%Y-%m-%d)
