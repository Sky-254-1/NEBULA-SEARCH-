# Nebula Search Engine — Testing Strategy

## Executive Summary

This document defines the comprehensive testing strategy for the Nebula Search Engine API. The strategy ensures production readiness through automated testing at multiple levels: unit, integration, API, security, and load testing.

**Testing Goals:**
- ✅ 80% code coverage minimum
- ✅ All critical paths tested
- ✅ Security vulnerabilities identified and fixed
- ✅ Performance benchmarks met
- ✅ Zero regression bugs in production

---

## Table of Contents

1. [Testing Principles](#testing-principles)
2. [Test Pyramid](#test-pyramid)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [API Testing](#api-testing)
6. [Security Testing](#security-testing)
7. [Performance Testing](#performance-testing)
8. [Test Automation](#test-automation)
9. [CI/CD Integration](#cicd-integration)
10. [Test Coverage](#test-coverage)

---

## Testing Principles

### 1. Test Early, Test Often
- Write tests before or during implementation (TDD)
- Run tests on every commit
- Fail fast on test failures

### 2. Isolate Tests
- Each test should be independent
- Use fixtures for shared setup/teardown
- Mock external dependencies (APIs, databases)

### 3. Test Behavior, Not Implementation
- Focus on public APIs, not internal methods
- Test user-facing behavior
- Avoid testing private methods directly

### 4. Keep Tests Fast
- Unit tests: < 1ms each
- Integration tests: < 100ms each
- API tests: < 500ms each
- Total test suite: < 5 minutes

### 5. Make Tests Readable
- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- Add comments for complex scenarios

---

## Test Pyramid

```
        ┌─────────────┐
        │   E2E Tests │  ← 5% (Critical user journeys)
        └─────────────┘
      ┌─────────────────┐
      │  API Tests      │  ← 15% (Endpoint contracts)
      └─────────────────┘
    ┌─────────────────────┐
    │ Integration Tests   │  ← 30% (Service interactions)
    └─────────────────────┘
  ┌─────────────────────────┐
  │ Unit Tests              │  ← 50% (Business logic)
  └─────────────────────────┘
```

### Distribution
- **Unit Tests (50%):** Fast, isolated, test individual functions/classes
- **Integration Tests (30%):** Test service interactions, database operations
- **API Tests (15%):** Test HTTP endpoints, request/response contracts
- **E2E Tests (5%):** Test complete user workflows

---

## Unit Testing

### Scope
Test individual functions, classes, and modules in isolation.

### Tools
- **Framework:** pytest
- **Mocking:** unittest.mock, pytest-mock
- **Coverage:** pytest-cov

### Test Structure

```python
# tests/unit/test_auth.py
import pytest
from app.services.auth import hash_password, verify_password

class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        result = hash_password("SecurePass123!")
        assert isinstance(result, str)
    
    def test_hash_password_contains_salt(self):
        """Test that hash contains salt separator."""
        result = hash_password("SecurePass123!")
        assert "$" in result
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with wrong password."""
        password = "SecurePass123!"
        wrong_password = "WrongPass456!"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        hashed = hash_password("SecurePass123!")
        assert verify_password("", hashed) is False
```

### Unit Test Examples

#### Authentication Service
```python
# tests/unit/test_auth_service.py
import pytest
from datetime import datetime, timezone
from app.services.auth import (
    create_access_token,
    decode_token,
    validate_password,
)

class TestJWTTokens:
    def test_create_access_token_contains_claims(self):
        """Test JWT contains required claims."""
        token = create_access_token("user@example.com", role="user")
        payload = decode_token(token)
        
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_expires(self):
        """Test JWT has expiration."""
        token = create_access_token("user@example.com")
        payload = decode_token(token)
        
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        assert exp > iat
        assert (exp - iat).total_seconds() == 900  # 15 minutes

class TestPasswordValidation:
    def test_valid_password(self):
        """Test valid password passes validation."""
        validate_password("SecurePass123!")  # Should not raise
    
    def test_password_too_short(self):
        """Test password too short fails validation."""
        with pytest.raises(HTTPException) as exc:
            validate_password("Short1!")
        assert exc.value.status_code == 400
    
    def test_password_missing_uppercase(self):
        """Test password missing uppercase fails."""
        with pytest.raises(HTTPException):
            validate_password("securepass123!")
    
    def test_password_missing_number(self):
        """Test password missing number fails."""
        with pytest.raises(HTTPException):
            validate_password("SecurePass!")
```

#### Search Service
```python
# tests/unit/test_search_service.py
import pytest
from app.services.search import run_web_search

class TestWebSearch:
    @pytest.mark.asyncio
    async def test_run_web_search_returns_results(self):
        """Test web search returns results."""
        results = await run_web_search("test query", "wikipedia", 1, 10)
        assert isinstance(results, list)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_run_web_search_invalid_backend(self):
        """Test web search with invalid backend raises error."""
        with pytest.raises(HTTPException) as exc:
            await run_web_search("test", "invalid_backend", 1, 10)
        assert exc.value.status_code == 400
```

### Unit Test Coverage Targets
| Module | Target Coverage | Critical Paths |
|--------|----------------|----------------|
| `app/services/auth.py` | 95% | Password hashing, JWT creation/validation |
| `app/services/search.py` | 90% | Web search, orchestration |
| `app/services/ai.py` | 90% | AI answer generation, streaming |
| `app/search/semantic/` | 85% | Vector search, hybrid search |
| `app/middleware/` | 90% | Rate limiting, security headers |

---

## Integration Testing

### Scope
Test interactions between services, databases, and external APIs.

### Tools
- **Framework:** pytest
- **Database:** Test database (SQLite in-memory or PostgreSQL test instance)
- **Fixtures:** pytest fixtures for setup/teardown

### Test Structure

```python
# tests/integration/test_auth_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Setup test database."""
        self.db = db
        yield
        # Cleanup
    
    def test_signup_login_logout_flow(self):
        """Test complete signup → login → logout flow."""
        # 1. Signup
        signup_response = client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert signup_response.status_code == 201
        
        # 2. Login
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # 3. Get current user
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "test@example.com"
        
        # 4. Logout
        logout_response = client.post("/api/v1/auth/logout", json={
            "refresh_token": tokens["refresh_token"]
        }, headers=headers)
        assert logout_response.status_code == 200
```

### Integration Test Examples

#### Database Operations
```python
# tests/integration/test_document_repository.py
import pytest
from app.database.repositories.document import DocumentRepository

class TestDocumentRepository:
    @pytest.mark.asyncio
    async def test_create_document(self, db):
        """Test document creation."""
        repo = DocumentRepository(db)
        doc_id = await repo.create(
            user_id=1,
            filename="test.pdf",
            content_type="application/pdf",
            storage_path="/tmp/test.pdf"
        )
        assert doc_id > 0
    
    @pytest.mark.asyncio
    async def test_list_documents_for_user(self, db):
        """Test listing documents for user."""
        repo = DocumentRepository(db)
        docs = await repo.list_for_user(user_id=1)
        assert isinstance(docs, list)
```

#### Search Flow
```python
# tests/integration/test_search_flow.py
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

class TestSearchFlow:
    def test_web_search_authenticated(self):
        """Test web search requires authentication."""
        # Without auth
        response = client.get("/api/v1/search/web?q=test")
        assert response.status_code == 401
        
        # With auth
        headers = self.get_auth_headers()
        response = client.get("/api/v1/search/web?q=test", headers=headers)
        assert response.status_code == 200
        assert "results" in response.json()
```

### Integration Test Coverage Targets
| Module | Target Coverage | Critical Paths |
|--------|----------------|----------------|
| Authentication flow | 100% | Signup, login, refresh, logout |
| Document management | 95% | Upload, list, delete, reindex |
| Search flow | 90% | Web search, vector search, hybrid |
| AI flow | 85% | Ask, stream, synthesize |

---

## API Testing

### Scope
Test HTTP endpoints, request/response contracts, status codes, headers.

### Tools
- **Framework:** pytest + TestClient
- **Validation:** JSON schema validation
- **Coverage:** pytest-cov

### Test Structure

```python
# tests/api/test_auth_endpoints.py
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_signup_success(self):
        """Test successful signup."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "user" in data
    
    def test_signup_duplicate_email(self):
        """Test signup with duplicate email."""
        # Create user first
        client.post("/api/v1/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "SecurePass123!"
        })
        
        # Try to create again
        response = client.post("/api/v1/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 409
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "email": "user@example.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 401
```

### API Test Examples

#### Search Endpoints
```python
# tests/api/test_search_endpoints.py
class TestSearchEndpoints:
    def test_web_search_success(self):
        """Test successful web search."""
        headers = self.get_auth_headers()
        response = client.get(
            "/api/v1/search/web?q=artificial+intelligence&backend=wikipedia",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_web_search_missing_query(self):
        """Test web search with missing query parameter."""
        headers = self.get_auth_headers()
        response = client.get("/api/v1/search/web", headers=headers)
        assert response.status_code == 422  # Validation error
    
    def test_web_search_invalid_backend(self):
        """Test web search with invalid backend."""
        headers = self.get_auth_headers()
        response = client.get(
            "/api/v1/search/web?q=test&backend=invalid",
            headers=headers
        )
        assert response.status_code == 400
```

#### Document Endpoints
```python
# tests/api/test_document_endpoints.py
class TestDocumentEndpoints:
    def test_upload_document_success(self):
        """Test successful document upload."""
        headers = self.get_auth_headers()
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post(
            "/api/v1/storage/documents",
            files=files,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_upload_document_too_large(self):
        """Test upload with file too large."""
        headers = self.get_auth_headers()
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large.txt", large_content, "text/plain")}
        response = client.post(
            "/api/v1/storage/documents",
            files=files,
            headers=headers
        )
        assert response.status_code == 413
    
    def test_list_documents_pagination(self):
        """Test document list pagination."""
        headers = self.get_auth_headers()
        response = client.get(
            "/api/v1/storage/documents?page=1&page_size=10",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
```

### API Test Checklist
- [ ] All endpoints return correct status codes
- [ ] Request validation works (400, 422)
- [ ] Authentication works (401, 403)
- [ ] Response format is consistent
- [ ] Headers are correct (Content-Type, RateLimit)
- [ ] Pagination works correctly
- [ ] Filtering works correctly
- [ ] Error messages are helpful

---

## Security Testing

### Scope
Test authentication, authorization, rate limiting, input validation, injection attacks.

### Tools
- **Framework:** pytest
- **Security:** pytest-mock, requests
- **Scanning:** bandit (static analysis)

### Test Structure

```python
# tests/security/test_authentication.py
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

class TestAuthentication:
    def test_access_without_token(self):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/search/web?q=test")
        assert response.status_code == 401
    
    def test_access_with_invalid_token(self):
        """Test accessing with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/search/web?q=test", headers=headers)
        assert response.status_code == 401
    
    def test_access_with_expired_token(self):
        """Test accessing with expired token."""
        # Create expired token
        expired_token = create_expired_token()
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/search/web?q=test", headers=headers)
        assert response.status_code == 401
```

### Security Test Examples

#### SQL Injection
```python
# tests/security/test_injection.py
class TestSQLInjection:
    def test_search_sql_injection(self):
        """Test SQL injection in search query."""
        headers = self.get_auth_headers()
        malicious_query = "'; DROP TABLE users; --"
        response = client.get(
            f"/api/v1/search/web?q={malicious_query}",
            headers=headers
        )
        # Should not crash, should return 200 or 400
        assert response.status_code in [200, 400]
        
        # Verify users table still exists
        from app.database import get_db
        db = get_db()
        result = db.execute("SELECT COUNT(*) FROM users")
        assert result[0][0] >= 0
```

#### XSS (Cross-Site Scripting)
```python
# tests/security/test_xss.py
class TestXSS:
    def test_search_xss(self):
        """Test XSS in search query."""
        headers = self.get_auth_headers()
        xss_payload = "<script>alert('XSS')</script>"
        response = client.get(
            f"/api/v1/search/web?q={xss_payload}",
            headers=headers
        )
        assert response.status_code in [200, 400]
        # Ensure script tags are escaped in response
        if response.status_code == 200:
            assert "<script>" not in response.text
```

#### Rate Limiting
```python
# tests/security/test_rate_limiting.py
class TestRateLimiting:
    def test_login_rate_limit(self):
        """Test login rate limiting."""
        # Make 5 requests (limit is 5/min)
        for _ in range(5):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "WrongPassword"
            })
            assert response.status_code in [401, 429]
        
        # 6th request should be rate limited
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 429
        assert "Retry-After" in response.headers
```

#### Authorization
```python
# tests/security/test_authorization.py
class TestAuthorization:
    def test_admin_endpoint_requires_admin(self):
        """Test admin endpoint requires admin role."""
        # Regular user
        user_headers = self.get_user_headers()
        response = client.get("/api/v1/admin/users", headers=user_headers)
        assert response.status_code == 403
        
        # Admin user
        admin_headers = self.get_admin_headers()
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
```

### Security Test Checklist
- [ ] Authentication required for protected endpoints
- [ ] Invalid tokens rejected
- [ ] Expired tokens rejected
- [ ] SQL injection prevented
- [ ] XSS prevented
- [ ] CSRF protection enabled
- [ ] Rate limiting works
- [ ] Authorization checks work (admin vs user)
- [ ] Sensitive data not exposed in responses
- [ ] Passwords hashed (not plaintext)
- [ ] HTTPS enforced in production

---

## Performance Testing

### Scope
Test API performance under load, identify bottlenecks, ensure SLAs are met.

### Tools
- **Load Testing:** locust, k6, or Artillery
- **Profiling:** py-spy, cProfile
- **Monitoring:** Prometheus, Grafana

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Search latency (p50) | < 200ms | 95th percentile |
| Search latency (p95) | < 500ms | 99th percentile |
| Autocomplete latency | < 100ms | Average |
| API availability | 99.9% | Uptime |
| Concurrent users | 1000 | No degradation |
| Cache hit ratio | > 80% | Redis cache |

### Load Test Example (Locust)

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class NebulaUser(HttpUser):
    """Simulate user behavior."""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login on start."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def search(self):
        """Search (most common task)."""
        self.client.get(
            "/api/v1/search/web?q=artificial+intelligence",
            headers=self.headers
        )
    
    @task(1)
    def upload_document(self):
        """Upload document (less common)."""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        self.client.post(
            "/api/v1/storage/documents",
            files=files,
            headers=self.headers
        )
    
    @task(2)
    def vector_search(self):
        """Vector search."""
        self.client.post(
            "/api/v1/vector/search",
            json={"query": "machine learning", "top_k": 10},
            headers=self.headers
        )
```

### Load Test Scenarios

#### Scenario 1: Normal Load
```yaml
# tests/load/scenarios/normal_load.py
config:
  target: "http://localhost:8000"
  phases:
    - duration: 300  # 5 minutes
      arrival_rate: 10  # 10 users/second
  defaults:
    headers:
      Content-Type: "application/json"

scenarios:
  - name: "Normal user flow"
    requests:
      - post:
          url: "/api/v1/auth/login"
          json:
            email: "test@example.com"
            password: "SecurePass123!"
          capture:
            - json: "$.access_token"
              as: "token"
      - get:
          url: "/api/v1/search/web"
          qs:
            q: "test query"
          headers:
            Authorization: "Bearer {{token}}"
```

#### Scenario 2: Spike Load
```yaml
# tests/load/scenarios/spike_load.py
config:
  target: "http://localhost:8000"
  phases:
    - duration: 60
      arrival_rate: 5
    - duration: 120
      arrival_rate: 100  # Spike to 100 users/second
    - duration: 60
      arrival_rate: 5
```

#### Scenario 3: Stress Test
```yaml
# tests/load/scenarios/stress_test.py
config:
  target: "http://localhost:8000"
  phases:
    - duration: 600  # 10 minutes
      arrival_rate: 50
      ramp_to: 200  # Ramp from 50 to 200 users/second
```

### Performance Test Checklist
- [ ] Search latency < 200ms (p50)
- [ ] Search latency < 500ms (p95)
- [ ] 1000 concurrent users supported
- [ ] No memory leaks
- [ ] Database connection pool not exhausted
- [ ] Cache hit ratio > 80%
- [ ] Error rate < 1%
- [ ] API availability 99.9%

---

## Test Automation

### Test Execution

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run API tests only
pytest tests/api/

# Run security tests only
pytest tests/security/

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_auth.py::TestPasswordHashing::test_hash_password_returns_string

# Run in parallel
pytest -n auto
```

### Test Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    security: Security tests
    slow: Slow tests
    asyncio: Async tests
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.engine import init_db, get_db

@pytest.fixture(scope="session")
def db():
    """Create test database."""
    # Setup
    init_db()
    yield
    # Teardown

@pytest.fixture
def client(db):
    """Create test client."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client):
    """Get admin authentication headers."""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "AdminPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db

  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit security scan
        run: |
          pip install bandit
          bandit -r app/ -f json -o bandit-report.json
      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: bandit-report.json

  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Start server
        run: |
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 5
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run API tests
        run: pytest tests/api/ -v
      - name: Run Postman tests
        run: |
          npm install -g newman
          newman run docs/postman/nebula-api-collection.json --environment test.postman_environment.json

  load-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run load tests
        run: |
          pip install locust
          locust -f tests/load/locustfile.py --headless -u 100 -r 10 --run-time 5m --host http://localhost:8000
```

---

## Test Coverage

### Coverage Targets

| Module | Target | Current | Gap |
|--------|--------|---------|-----|
| `app/services/auth.py` | 95% | TBD | - |
| `app/services/search.py` | 90% | TBD | - |
| `app/services/ai.py` | 90% | TBD | - |
| `app/routes/auth.py` | 95% | TBD | - |
| `app/routes/search.py` | 90% | TBD | - |
| `app/routes/vector.py` | 85% | TBD | - |
| `app/middleware/` | 90% | TBD | - |
| `app/database/repositories/` | 85% | TBD | - |
| **Overall** | **80%** | **TBD** | **-** |

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### Coverage Checklist
- [ ] All critical paths covered (auth, search, documents)
- [ ] Error handling covered
- [ ] Edge cases covered
- [ ] Security scenarios covered
- [ ] Performance scenarios covered

---

## Test Data Management

### Fixtures

```python
# tests/fixtures/users.py
@pytest.fixture
def test_user():
    """Create test user."""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def admin_user():
    """Create admin user."""
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "role": "admin"
    }
```

### Factories

```python
# tests/factories.py
import factory
from app.database.models import User, Document

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.LazyAttribute(lambda obj: hash_password("SecurePass123!"))
    role = "user"
    email_verified = True

class DocumentFactory(factory.Factory):
    class Meta:
        model = Document
    
    user_id = 1
    filename = factory.Sequence(lambda n: f"document_{n}.pdf")
    content_type = "application/pdf"
    status = "indexed"
```

---

## Test Monitoring

### Metrics to Track
- Test pass/fail rate
- Test execution time
- Code coverage percentage
- Flaky test count
- Test failure reasons

### Dashboard
```
Test Suite Dashboard:
├── Total Tests: 500
├── Passed: 495 (99%)
├── Failed: 3 (1%)
├── Skipped: 2
├── Coverage: 85%
├── Execution Time: 3m 45s
└── Flaky Tests: 1
```

---

## Appendix A: Test Checklist

### Pre-Commit Checklist
- [ ] All new code has tests
- [ ] All tests pass locally
- [ ] Code coverage >= 80%
- [ ] No security vulnerabilities (Bandit scan)
- [ ] No linting errors (flake8, black)

### Pre-Deployment Checklist
- [ ] All tests pass in CI/CD
- [ ] Load tests pass
- [ ] Security tests pass
- [ ] Performance benchmarks met
- [ ] No critical bugs open

### Post-Deployment Checklist
- [ ] Smoke tests pass in production
- [ ] Monitoring dashboards healthy
- [ ] Error rates < 1%
- [ ] Latency within SLA

---

## Appendix B: Test Commands

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test
pytest tests/unit/test_auth.py::TestPasswordHashing::test_hash_password_returns_string

# Run tests matching pattern
pytest -k "test_password"

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v

# Run with debug output
pytest --pdb

# Generate coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Run security scan
bandit -r app/

# Run linting
flake8 app/
black --check app/

# Run type checking
mypy app/
```

---

## Conclusion

This testing strategy ensures the Nebula Search Engine API is production-ready through comprehensive automated testing at multiple levels. The strategy covers:

- ✅ Unit tests (50% of test suite)
- ✅ Integration tests (30% of test suite)
- ✅ API tests (15% of test suite)
- ✅ Security tests (injection, XSS, CSRF, rate limiting)
- ✅ Performance tests (load, stress, spike)
- ✅ 80% code coverage target
- ✅ CI/CD integration
- ✅ Test automation

**Next Steps:**
1. Implement test suite following this strategy
2. Set up CI/CD pipeline
3. Monitor test metrics
4. Toggle to Act mode to begin implementation