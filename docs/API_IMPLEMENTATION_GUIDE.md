# IOIS API — Implementation Guide & Quick Reference

## 📋 Document Overview

This guide provides a quick reference for implementing the IOIS (Nebula) production-ready API architecture. It complements the detailed `PRODUCTION_API_ARCHITECTURE.md` document and the Postman collection.

**Related Documents:**
- `PRODUCTION_API_ARCHITECTURE.md` — Complete architecture specification
- `postman/IOIS_API_Collection.json` — Postman collection for testing
- `API_V1.1.md` — Existing API documentation

---

## 🚀 Quick Start

### 1. Import Postman Collection

```bash
# 1. Open Postman
# 2. Click "Import" → "Upload Files"
# 3. Select: docs/postman/IOIS_API_Collection.json
# 4. Configure environments:
#    - Local: http://localhost:8000
#    - Staging: https://staging-api.nebula-search.io
#    - Production: https://api.nebula-search.io
```

### 2. Environment Variables

The collection uses these variables (pre-configured):

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `access_token` | (empty) | JWT access token (auto-set by Login) |
| `refresh_token` | (empty) | Refresh token (auto-set by Login) |
| `user_id` | (empty) | Current user ID |
| `email` | `test@example.com` | Test user email |
| `password` | `TestPass123!` | Test user password |

### 3. Authentication Flow

```
1. Run "Auth → Signup" (first time only)
   ↓
2. Run "Auth → Login"
   → Tokens auto-saved to environment
   ↓
3. Run any authenticated request
   → Authorization header auto-injected
   ↓
4. Token auto-refreshes when expiring
```

---

## 🏗️ Architecture Summary

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | FastAPI | Async Python web framework |
| **Database** | PostgreSQL 15+ | Primary data store |
| **Cache** | Redis 7+ | Session & API caching |
| **Storage** | S3 / MinIO | File uploads |
| **Queue** | Redis / RabbitMQ | Async job processing |
| **API Gateway** | Kong / AWS API Gateway | Rate limiting, routing |
| **Load Balancer** | nginx | Traffic distribution |
| **Monitoring** | Prometheus + Grafana | Metrics & dashboards |
| **Logging** | ELK / Loki | Log aggregation |
| **Error Tracking** | Sentry | Error monitoring |

### Service Architecture

```
┌─────────────────────────────────────────┐
│         API Gateway (Kong)              │
│  • Rate Limiting  • Auth  • SSL         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Load Balancer (nginx)              │
│  • Health Checks  • Circuit Breaker     │
└─────────────────────────────────────────┘
                  ↓
        ┌─────────┼─────────┐
        ↓         ↓         ↓
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Instance│ │ Instance│ │ Instance│
   │    1    │ │    2    │ │    3    │
   └─────────┘ └─────────┘ └─────────┘
        ↓         ↓         ↓
   ┌─────────────────────────────┐
   │   FastAPI Service Layer     │
   │  ┌───────────────────────┐  │
   │  │ Auth Service          │  │
   │  │ User Service          │  │
   │  │ Search Service        │  │
   │  │ Vector Service        │  │
   │  │ Notification Service  │  │
   │  │ Analytics Service     │  │
   │  └───────────────────────┘  │
   └─────────────────────────────┘
        ↓         ↓         ↓
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │PostgreSQL│ │  Redis  │ │  S3     │
   │         │ │  Cache  │ │ Storage │
   └─────────┘ └─────────┘ └─────────┘
```

---

## 📡 API Endpoints Summary

### Authentication (13 endpoints)
- `POST /api/v1/auth/signup` — Register
- `POST /api/v1/auth/login` — Login
- `POST /api/v1/auth/refresh` — Refresh token
- `POST /api/v1/auth/logout` — Logout
- `POST /api/v1/auth/logout-all` — Logout all devices
- `GET /api/v1/auth/me` — Current user
- `POST /api/v1/auth/forgot-password` — Request reset
- `POST /api/v1/auth/reset-password` — Reset password
- `POST /api/v1/auth/verify-email` — Verify email
- `POST /api/v1/auth/2fa/enable` — Enable 2FA
- `POST /api/v1/auth/2fa/verify` — Verify 2FA
- `POST /api/v1/auth/2fa/disable` — Disable 2FA
- `GET /api/v1/auth/sessions` — List sessions

### Users (9 endpoints)
- `GET /api/v1/users/profile` — Get profile
- `PUT /api/v1/users/profile` — Update profile
- `DELETE /api/v1/users/account` — Delete account
- `GET /api/v1/users/activity` — Activity log
- `PUT /api/v1/users/password` — Change password
- `GET /api/v1/users/preferences` — Get preferences
- `PUT /api/v1/users/preferences` — Update preferences
- `POST /api/v1/users/avatar` — Upload avatar
- `DELETE /api/v1/users/avatar` — Delete avatar

### Search (7 endpoints)
- `GET /api/v1/search/web` — Web search
- `GET /api/v1/search/orchestrate` — Multi-backend search
- `GET /api/v1/search/history` — Search history
- `DELETE /api/v1/search/history` — Clear history
- `GET /api/v1/search/suggestions` — Suggestions
- `POST /api/v1/search/save` — Save search
- `GET /api/v1/search/saved` — List saved

### Files (9 endpoints)
- `GET /api/v1/storage/documents` — List documents
- `POST /api/v1/storage/documents` — Upload
- `GET /api/v1/storage/documents/{id}` — Get metadata
- `DELETE /api/v1/storage/documents/{id}` — Delete
- `GET /api/v1/storage/documents/{id}/download` — Download
- `POST /api/v1/storage/documents/{id}/reindex` — Reindex
- `GET /api/v1/storage/documents/{id}/status` — Index status
- `POST /api/v1/storage/batch-upload` — Batch upload
- `POST /api/v1/storage/batch-delete` — Batch delete

### Vector (8 endpoints)
- `POST /api/v1/vector/search` — Hybrid search
- `POST /api/v1/vector/ask` — RAG query
- `GET /api/v1/vector/citations` — Recent citations
- `GET /api/v1/vector/stats` — Statistics
- `POST /api/v1/vector/export` — Export data
- `POST /api/v1/vector/documents/{id}/reindex` — Reindex
- `POST /api/v1/vector/documents/reindex-all` — Reindex all
- `DELETE /api/v1/vector/cache` — Clear cache

### Notifications (8 endpoints)
- `GET /api/v1/notifications` — List notifications
- `GET /api/v1/notifications/unread-count` — Unread count
- `POST /api/v1/notifications/{id}/read` — Mark as read
- `POST /api/v1/notifications/read-all` — Mark all read
- `DELETE /api/v1/notifications/{id}` — Delete
- `DELETE /api/v1/notifications` — Clear all
- `GET /api/v1/notifications/preferences` — Get preferences
- `PUT /api/v1/notifications/preferences` — Update preferences

### Projects (8 endpoints) — New
- `GET /api/v1/projects` — List projects
- `POST /api/v1/projects` — Create project
- `GET /api/v1/projects/{id}` — Get project
- `PUT /api/v1/projects/{id}` — Update project
- `DELETE /api/v1/projects/{id}` — Delete project
- `POST /api/v1/projects/{id}/collaborators` — Add collaborator
- `DELETE /api/v1/projects/{id}/collaborators/{user_id}` — Remove collaborator
- `GET /api/v1/projects/{id}/documents` — List documents

### Admin (14 endpoints)
- `GET /api/v1/admin/audit-logs` — Audit logs
- `GET /api/v1/admin/users` — List all users
- `GET /api/v1/admin/users/{id}` — User details
- `PUT /api/v1/admin/users/{id}/role` — Update role
- `PUT /api/v1/admin/users/{id}/status` — Enable/disable
- `DELETE /api/v1/admin/users/{id}` — Delete user
- `GET /api/v1/admin/sessions` — List sessions
- `POST /api/v1/admin/sessions/{id}/revoke` — Revoke session
- `GET /api/v1/admin/stats` — System stats
- `GET /api/v1/admin/health` — Detailed health
- `POST /api/v1/admin/cache/clear` — Clear cache
- `POST /api/v1/admin/queue/pause` — Pause queue
- `POST /api/v1/admin/queue/resume` — Resume queue
- `GET /api/v1/admin/queue/status` — Queue status

### Analytics (7 endpoints) — New
- `GET /api/v1/analytics/usage` — Usage stats
- `GET /api/v1/analytics/search` — Search analytics
- `GET /api/v1/analytics/performance` — Performance metrics
- `GET /api/v1/analytics/export` — Export analytics
- `GET /api/v1/admin/analytics/overview` — System overview
- `GET /api/v1/admin/analytics/users` — User analytics
- `GET /api/v1/admin/analytics/errors` — Error analytics

### Health (4 endpoints)
- `GET /api/v1/health` — Basic health
- `GET /api/v1/health/detailed` — Detailed health
- `GET /api/v1/health/ready` — Readiness probe
- `GET /api/v1/health/live` — Liveness probe

**Total: 69 endpoints**

---

## 🔐 Security Implementation

### JWT Authentication

```python
# Access Token: 15 minutes - 24 hours
# Refresh Token: 7 - 30 days
# Rotation: Every refresh creates new token pair
# Reuse Detection: Revokes entire session family
```

### Rate Limits

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Auth (login/signup) | 5 requests | 1 minute |
| Auth (refresh) | 10 requests | 1 minute |
| Search | 30 requests | 1 minute |
| File Upload | 20 requests | 1 minute |
| Admin | 30 requests | 1 minute |
| Health | 100 requests | 1 minute |

### Security Headers

All responses include:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000 (production only)
```

### Input Validation

- All inputs validated with Pydantic
- SQL injection prevented (parameterized queries)
- XSS prevented (input sanitization + output encoding)
- CSRF protection for cookie-based auth
- File type validation for uploads
- File size limits (10MB default)

---

## 🗄️ Database Schema

### Core Tables

| Table | Records | Purpose |
|-------|---------|---------|
| `users` | ~1M | User accounts |
| `sessions` | ~10M | Active sessions |
| `documents` | ~10M | Uploaded files |
| `search_history` | ~100M | Search logs |
| `notifications` | ~1M | User notifications |
| `analytics_events` | ~1B | Event tracking (partitioned) |
| `audit_logs` | ~10M | Security audit trail |
| `vector_documents` | ~1M | Vector index metadata |
| `vector_chunks` | ~100M | Vector embeddings |

### Indexes

- Primary keys: Automatic
- Unique: email, uuid, session_id, token_hash
- Foreign keys: All relationships indexed
- Composite: Common query patterns
- Full-text: GIN indexes on text fields
- Vector: IVFFlat for similarity search

---

## 🚢 Deployment Checklist

### Pre-Deployment

- [ ] Set `JWT_SECRET` (64+ random chars)
- [ ] Configure `DATABASE_URL` (PostgreSQL)
- [ ] Set `REDIS_URL`
- [ ] Configure `CORS_ORIGINS`
- [ ] Set `APP_ENV=production`
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Run security scan

### Database

- [ ] Run migrations
- [ ] Create indexes
- [ ] Set up backups
- [ ] Configure connection pooling
- [ ] Enable pg_stat_statements

### Testing

- [ ] Unit tests: `pytest` (80% coverage)
- [ ] Integration tests
- [ ] Load tests: `locust`
- [ ] Security scan: `bandit`
- [ ] Postman collection tests
- [ ] Penetration testing

---

## 📊 Monitoring & Observability

### Health Checks

```bash
# Basic (load balancer)
GET /api/v1/health

# Detailed (monitoring)
GET /api/v1/health/detailed

# Kubernetes probes
GET /api/v1/health/ready  # Readiness
GET /api/v1/health/live   # Liveness
```

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Response Time (p50) | < 200ms | > 500ms |
| Response Time (p95) | < 500ms | > 1000ms |
| Response Time (p99) | < 1000ms | > 2000ms |
| Error Rate | < 0.1% | > 1% |
| CPU Usage | < 70% | > 85% |
| Memory Usage | < 80% | > 90% |
| Database Connections | < 80% | > 90% |
| Cache Hit Rate | > 80% | < 60% |

### Logs to Monitor

- Authentication failures
- Rate limit hits
- Database slow queries
- External API errors
- Unhandled exceptions
- Security alerts

---

## 🔧 Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/Sky-254-1/Nebula-search-engine-.git
cd Nebula-search-engine-
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Security scan
bandit -r backend/app/

# Type checking
mypy backend/app/
```

---

## 📦 Folder Structure

```
nebula-search-engine/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # App factory
│   │   ├── config.py                  # Settings
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py              # DB connection
│   │   │   ├── migrate.py             # Migrations
│   │   │   └── repositories/          # Data access
│   │   │       ├── user.py
│   │   │       ├── session.py
│   │   │       ├── document.py
│   │   │       ├── audit.py
│   │   │       ├── search.py
│   │   │       ├── notification.py
│   │   │       └── analytics.py
│   │   ├── models/
│   │   │   ├── schemas.py             # Pydantic models
│   │   │   └── domain.py              # Domain models
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── search.py
│   │   │   ├── projects.py
│   │   │   ├── files.py
│   │   │   ├── vector.py
│   │   │   ├── notifications.py
│   │   │   ├── admin.py
│   │   │   ├── analytics.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── search.py
│   │   │   ├── ai.py
│   │   │   ├── vector.py
│   │   │   ├── files.py
│   │   │   ├── notifications.py
│   │   │   ├── analytics.py
│   │   │   ├── cache.py
│   │   │   └── queue.py
│   │   ├── middleware/
│   │   │   ├── security.py
│   │   │   ├── rate_limit.py
│   │   │   ├── auth.py
│   │   │   ├── rbac.py
│   │   │   ├── validation.py
│   │   │   ├── xss.py
│   │   │   ├── csrf.py
│   │   │   ├── audit.py
│   │   │   └── cors.py
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_auth.py
│   │       ├── test_users.py
│   │       ├── test_search.py
│   │       └── ...
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── stores/
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── API_V1.md
│   ├── API_V1.1.md
│   ├── PRODUCTION_API_ARCHITECTURE.md
│   ├── API_IMPLEMENTATION_GUIDE.md (this file)
│   ├── postman/
│   │   └── IOIS_API_Collection.json
│   └── OPENAPI.yaml
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── deploy/
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── scripts/
    ├── migrate.sh
    ├── seed.py
    └── deploy.sh
```

---

## 🎯 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Set up production infrastructure

- [ ] PostgreSQL database setup
- [ ] Redis cache configuration
- [ ] S3/MinIO storage setup
- [ ] API Gateway (Kong) configuration
- [ ] Load balancer (nginx) setup
- [ ] CI/CD pipeline

**Deliverables:**
- Production database running
- Caching layer operational
- File storage configured
- Deployment pipeline working

### Phase 2: Core Services (Weeks 3-4)
**Goal:** Implement essential services

- [ ] User Service (profile, preferences, avatar)
- [ ] Notification Service (in-app, email)
- [ ] Analytics Service (event tracking)
- [ ] RBAC middleware
- [ ] Enhanced security headers
- [ ] User-based rate limiting

**Deliverables:**
- User management endpoints
- Notification system
- Analytics tracking
- RBAC implemented

### Phase 3: New Endpoints (Weeks 5-6)
**Goal:** Complete API endpoint implementation

- [ ] Users endpoints (9 endpoints)
- [ ] Projects endpoints (8 endpoints)
- [ ] Notifications endpoints (8 endpoints)
- [ ] Analytics endpoints (7 endpoints)
- [ ] Enhanced validation
- [ ] Request/response logging

**Deliverables:**
- All endpoints implemented
- Input validation complete
- Logging operational

### Phase 4: Testing & Documentation (Weeks 7-8)
**Goal:** Ensure quality and document

- [ ] Unit tests (80% coverage)
- [ ] Integration tests
- [ ] Load tests
- [ ] Security audit
- [ ] OpenAPI spec generation
- [ ] Postman collection finalization
- [ ] API documentation

**Deliverables:**
- Test suite (80%+ coverage)
- OpenAPI specification
- Complete Postman collection
- API documentation

### Phase 5: Production Readiness (Weeks 9-10)
**Goal:** Prepare for production

- [ ] Monitoring (Prometheus/Grafana)
- [ ] Alerting (PagerDuty/OpsGenie)
- [ ] Logging (ELK/Loki)
- [ ] Error tracking (Sentry)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Disaster recovery plan

**Deliverables:**
- Monitoring dashboards
- Alert rules configured
- Log aggregation working
- Error tracking enabled

### Phase 6: Deployment (Week 11)
**Goal:** Deploy to production

- [ ] Deploy to staging
- [ ] Smoke tests
- [ ] Load testing
- [ ] Security penetration test
- [ ] Deploy to production
- [ ] Monitor for 48 hours
- [ ] Document lessons learned

**Deliverables:**
- Staging environment
- Production deployment
- Monitoring active
- Documentation complete

---

## 🧪 Testing Strategy

### Unit Tests

```bash
# Run all tests
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=app --cov-report=html

# Specific test file
pytest backend/tests/test_auth.py -v

# Specific test
pytest backend/tests/test_auth.py::test_login -v
```

### Integration Tests

```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest backend/tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### Load Tests

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# Set number of users and spawn rate
```

### Security Tests

```bash
# Bandit (security linting)
bandit -r backend/app/ -f json -o security-report.json

# Safety (dependency vulnerabilities)
safety check -r backend/requirements.txt

# OWASP ZAP (penetration testing)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 -r zap-report.html
```

---

## 🔍 Common Issues & Solutions

### Issue: JWT Token Expired

**Solution:** The Postman collection auto-refreshes tokens. If manual refresh needed:
```bash
POST /api/v1/auth/refresh
Body: { "refresh_token": "..." }
```

### Issue: Rate Limited

**Solution:** Wait for retry period or use different IP. Check headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1625123456
```

### Issue: Database Connection Pool Exhausted

**Solution:** Increase pool size in config:
```python
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Issue: Redis Cache Miss

**Solution:** Check Redis connection and TTL settings:
```bash
redis-cli ping
redis-cli info memory
```

---

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Tools
- [Postman](https://www.postman.com/) — API testing
- [pgAdmin](https://www.pgadmin.org/) — PostgreSQL management
- [Redis Insight](https://redis.io/insight/) — Redis GUI
- [Prometheus](https://prometheus.io/) — Monitoring
- [Grafana](https://grafana.com/) — Dashboards

### Support
- **Email:** support@nebula-search.io
- **GitHub Issues:** https://github.com/Sky-254-1/Nebula-search-engine-/issues
- **Documentation:** https://docs.nebula-search.io

---

## 📝 Changelog

### Version 1.0.0 (2026-07-01)
- Initial production-ready architecture
- 69 API endpoints designed
- Postman collection created
- Security framework defined
- Database schema designed
- Implementation roadmap created

---

## ✅ Next Steps

1. **Review** this document with your team
2. **Import** the Postman collection
3. **Set up** development environment
4. **Run** the existing backend: `uvicorn app.main:app --reload`
5. **Test** endpoints with Postman
6. **Prioritize** features from the roadmap
7. **Begin** Phase 1 implementation

---

**Document Version:** 1.0
**Last Updated:** 2026-07-01
**Author:** Senior API Architect
**Status:** Ready for Implementation