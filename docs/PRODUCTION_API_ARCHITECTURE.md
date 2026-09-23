# IOIS (Nebula) — Production-Ready API Architecture

## Executive Summary

This document defines the complete production-ready API architecture for IOIS (Nebula), expanding on the existing FastAPI backend while maintaining backward compatibility. The architecture follows OWASP best practices, implements JWT rotation with refresh tokens, and provides a scalable foundation for growth.

**Existing Architecture Preserved:**
- FastAPI backend with async/await patterns
- SQLite (dev) / PostgreSQL (prod) dual-database support
- JWT authentication with refresh token rotation
- Rate limiting, security headers, CORS
- Audit logging and brute-force protection
- Vector search with RAG capabilities
- File upload and document management

**New Additions:**
- API Gateway layer (Kong/AWS API Gateway)
- Service modularization with clear boundaries
- Redis caching layer
- Notification service
- Analytics service
- Comprehensive RBAC permissions
- OpenAPI 3.0 specification
- Postman collection with automation
- CI/CD integration guidelines

---

## 1. Complete API Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                           │
│                   (Kong / AWS API Gateway)                   │
│  • Rate limiting  • Authentication  • SSL termination        │
│  • Request routing  • Load balancing  • Monitoring           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (nginx)                     │
│              • Health checks  • Circuit breaker              │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ Instance│         │ Instance│         │ Instance│
   │    1    │         │    2    │         │    3    │
   └─────────┘         └─────────┘         └─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer (FastAPI)                   │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Auth Service │ User Service │Search Service│            │
│  └──────────────┴──────────────┴──────────────┘            │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │Vector Service│Admin Service │Analytics Svc │            │
│  └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │PostgreSQL│         │  Redis  │         │  S3 /   │
   │  (Primary│         │ (Cache) │         │  MinIO  │
   │   DB)    │         │         │         │(Storage)│
   └─────────┘         └─────────┘         └─────────┘
                            │
                            ▼
                   ┌───────────────┐
                   │  Message Queue │
                   │    (Redis /   │
                   │   RabbitMQ)   │
                   └───────────────┘
```

### 1.2 Service Modules

#### Core Services (Existing)
1. **Auth Service** (`app/services/auth.py`)
   - JWT creation/validation
   - Password hashing (PBKDF2-SHA256)
   - Refresh token rotation
   - Brute-force protection
   - Session management

2. **Search Service** (`app/services/search.py`)
   - Web search orchestration
   - Backend management (Wikipedia, Brave, SerpAPI)
   - Result caching
   - Query expansion

3. **AI Service** (`app/services/ai.py`)
   - Multi-provider support (OpenAI, Ollama, GGUF)
   - Response synthesis
   - Chat history management

4. **Vector Service** (`vector/`)
   - Document indexing
   - Hybrid search (vector + keyword)
   - RAG (Retrieval-Augmented Generation)
   - Citation tracking

#### New Services (To Be Implemented)

5. **User Service** (`app/services/user.py`)
   - Profile management
   - Preferences
   - Account settings
   - Activity tracking

6. **Notification Service** (`app/services/notifications.py`)
   - In-app notifications
   - Email notifications (async)
   - Push notifications (mobile)
   - Notification preferences

7. **Analytics Service** (`app/services/analytics.py`)
   - Usage metrics
   - Search analytics
   - Performance monitoring
   - User behavior tracking

8. **File Service** (`app/services/files.py`)
   - Upload validation
   - Virus scanning (ClamAV)
   - Thumbnail generation
   - Format conversion

### 1.3 Database Layer

#### PostgreSQL Schema (Production)

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table (enhanced)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    phone_number VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_uuid ON users(uuid);
CREATE INDEX idx_users_role ON users(role);

-- Sessions table (enhanced)
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID DEFAULT uuid_generate_v4() NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    device_name TEXT,
    device_type VARCHAR(50), -- 'mobile', 'desktop', 'tablet'
    ip_address INET,
    user_agent TEXT,
    location_country VARCHAR(2),
    location_city VARCHAR(100),
    expires_at TIMESTAMP NOT NULL,
    rotated_at TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,
    parent_refresh_id INTEGER REFERENCES sessions(id),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_token_hash ON sessions(refresh_token_hash);

-- Audit logs table (enhanced)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_metadata ON audit_logs USING GIN(metadata);

-- Documents table (enhanced)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size_bytes BIGINT,
    storage_path TEXT NOT NULL,
    file_hash VARCHAR(64), -- SHA256
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    -- pending, indexing, indexed, error, duplicate
    indexed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_documents_user_id ON documents(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);

-- Search history table
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    backend VARCHAR(50) NOT NULL,
    result_count INTEGER,
    filters JSONB DEFAULT '{}',
    response_time_ms INTEGER,
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_created_at ON search_history(created_at DESC);
CREATE INDEX idx_search_history_query ON search_history USING GIN(to_tsquery('english', query));

-- Notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    -- 'info', 'warning', 'error', 'success'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

-- User preferences table
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, preference_key)
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Analytics events table (time-series)
CREATE TABLE analytics_events (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    properties JSONB DEFAULT '{}',
    session_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions (example for 2026)
CREATE TABLE analytics_events_2026_01 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE analytics_events_2026_02 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- Continue for future months...

CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at);
CREATE INDEX idx_analytics_events_properties ON analytics_events USING GIN(properties);

-- Exports table (enhanced)
CREATE TABLE exports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    status VARCHAR(50) DEFAULT 'pending',
    -- pending, processing, completed, failed
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP
);

CREATE INDEX idx_exports_user_id ON exports(user_id);
CREATE INDEX idx_exports_status ON exports(status);

-- Vector documents table (enhanced)
CREATE TABLE vector_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    indexed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(document_id)
);

CREATE INDEX idx_vector_documents_user_id ON vector_documents(user_id);
CREATE INDEX idx_vector_documents_status ON vector_documents(status);

-- Vector chunks table
CREATE TABLE vector_chunks (
    id SERIAL PRIMARY KEY,
    vector_document_id INTEGER NOT NULL REFERENCES vector_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_vector_chunks_vector_document_id ON vector_chunks(vector_document_id);
CREATE INDEX idx_vector_chunks_embedding ON vector_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Vector citations table
CREATE TABLE vector_citations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    chunk_id INTEGER REFERENCES vector_chunks(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    snippet TEXT,
    score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_vector_citations_user_id ON vector_citations(user_id);
CREATE INDEX idx_vector_citations_created_at ON vector_citations(created_at DESC);

-- Roles and permissions (for RBAC)
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
('admin', 'Full system access', '["*"]'),
('user', 'Standard user access', '["search:read", "documents:read", "documents:write", "profile:read", "profile:write", "notifications:read"]'),
('guest', 'Limited access', '["search:read"]');

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vector_documents_updated_at BEFORE UPDATE ON vector_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 1.4 File Storage

#### Storage Structure
```
storage/
├── uploads/
│   └── {user_id}/
│       └── {uuid}{ext}
├── cache/
│   ├── search/
│   └── api/
├── vector/
│   ├── indexes/
│   └── embeddings/
├── exports/
│   └── {user_id}/
│       └── {timestamp}_{type}.json
├── temp/
│   └── {uuid}
└── thumbnails/
    └── {user_id}/
```

#### S3/MinIO Configuration
```python
# app/services/storage.py
from minio import Minio
from minio.error import S3Error

class StorageService:
    def __init__(self):
        self.client = Minio(
            "storage.example.com",
            access_key=os.getenv("STORAGE_ACCESS_KEY"),
            secret_key=os.getenv("STORAGE_SECRET_KEY"),
            secure=True
        )
        self.bucket_name = "nebula-uploads"

    async def upload_file(self, user_id: int, file_path: Path) -> str:
        object_name = f"{user_id}/{file_path.name}"
        self.client.fput_object(
            self.bucket_name,
            object_name,
            str(file_path),
            content_type=detect_mime_type(file_path)
        )
        return f"s3://{self.bucket_name}/{object_name}"
```

### 1.5 Caching Strategy

#### Redis Cache Layers

```python
# app/services/cache.py
class CacheService:
    # L1: In-memory (per instance)
    # L2: Redis (shared)
    # L3: Database (persistent)

    CACHE_KEYS = {
        "user_profile": "user:{user_id}:profile",
        "search_results": "search:{query_hash}:{backend}",
        "ai_response": "ai:{prompt_hash}:{provider}",
        "api_response": "api:{endpoint}:{params_hash}",
    }

    CACHE_TTL = {
        "user_profile": 3600,  # 1 hour
        "search_results": 300,  # 5 minutes
        "ai_response": 1800,  # 30 minutes
        "api_response": 60,  # 1 minute
    }
```

### 1.6 Notification Service

```python
# app/services/notifications.py
class NotificationService:
    async def send_in_app(self, user_id: int, notification: dict):
        # Store in database
        await self.db.notifications.create(user_id, notification)

    async def send_email(self, user_id: int, template: str, data: dict):
        # Queue email job
        await self.queue.enqueue("send_email", {
            "user_id": user_id,
            "template": template,
            "data": data
        })

    async def send_push(self, user_id: int, message: str):
        # Send to mobile devices via FCM/APNS
        pass
```

### 1.7 Analytics Service

```python
# app/services/analytics.py
class AnalyticsService:
    async def track_event(self, user_id: int, event: dict):
        # Insert into partitioned table
        await self.db.execute(
            """
            INSERT INTO analytics_events (user_id, event_type, event_name, properties, session_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, event["type"], event["name"], event["properties"],
             event.get("session_id"), event.get("ip"), event.get("user_agent"))
        )

    async def get_metrics(self, metric: str, start: datetime, end: datetime):
        # Aggregate metrics
        pass
```

---

## 2. Endpoint Groups

### 2.1 Complete Endpoint Specification

#### AUTH Endpoints

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/v1/auth/signup` | Register new user | None | 5/min |
| POST | `/api/v1/auth/login` | Login with email/password | None | 5/min |
| POST | `/api/v1/auth/refresh` | Refresh access token | None | 10/min |
| POST | `/api/v1/auth/logout` | Logout current session | Optional | 10/min |
| POST | `/api/v1/auth/logout-all` | Logout all sessions | Required | 5/min |
| GET | `/api/v1/auth/me` | Get current user info | Required | 60/min |
| POST | `/api/v1/auth/forgot-password` | Request password reset | None | 3/min |
| POST | `/api/v1/auth/reset-password` | Reset password with token | None | 5/min |
| POST | `/api/v1/auth/verify-email` | Verify email address | None | 10/min |
| POST | `/api/v1/auth/2fa/enable` | Enable 2FA | Required | 5/min |
| POST | `/api/v1/auth/2fa/verify` | Verify 2FA code | Required | 5/min |
| POST | `/api/v1/auth/2fa/disable` | Disable 2FA | Required | 5/min |
| GET | `/api/v1/auth/sessions` | List active sessions | Required | 10/min |
| DELETE | `/api/v1/auth/sessions/{session_id}` | Revoke specific session | Required | 10/min |

#### USERS Endpoints

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/users/profile` | Get user profile | Required | 60/min |
| PUT | `/api/v1/users/profile` | Update user profile | Required | 30/min |
| DELETE | `/api/v1/users/account` | Delete user account | Required | 1/day |
| GET | `/api/v1/users/activity` | Get user activity log | Required | 10/min |
| PUT | `/api/v1/users/password` | Change password | Required | 5/min |
| GET | `/api/v1/users/preferences` | Get user preferences | Required | 60/min |
| PUT | `/api/v1/users/preferences` | Update preferences | Required | 30/min |
| POST | `/api/v1/users/avatar` | Upload avatar image | Required | 10/min |
| DELETE | `/api/v1/users/avatar` | Delete avatar | Required | 10/min |

#### SEARCH Endpoints

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/search/web` | Web search | Required | 30/min |
| GET | `/api/v1/search/orchestrate` | Multi-backend search | Required | 20/min |
| GET | `/api/v1/search/history` | Search history | Required | 10/min |
| DELETE | `/api/v1/search/history` | Clear search history | Required | 5/min |
| GET | `/api/v1/search/suggestions` | Get search suggestions | Optional | 60/min |
| POST | `/api/v1/search/save` | Save search query | Required | 30/min |
| GET | `/api/v1/search/saved` | List saved searches | Required | 10/min |

#### PROJECTS Endpoints (New)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/projects` | List user projects | Required | 60/min |
| POST | `/api/v1/projects` | Create new project | Required | 30/min |
| GET | `/api/v1/projects/{id}` | Get project details | Required | 60/min |
| PUT | `/api/v1/projects/{id}` | Update project | Required | 30/min |
| DELETE | `/api/v1/projects/{id}` | Delete project | Required | 10/min |
| POST | `/api/v1/projects/{id}/collaborators` | Add collaborator | Required | 20/min |
| DELETE | `/api/v1/projects/{id}/collaborators/{user_id}` | Remove collaborator | Required | 20/min |
| GET | `/api/v1/projects/{id}/documents` | List project documents | Required | 60/min |
| POST | `/api/v1/projects/{id}/documents` | Add document to project | Required | 30/min |

#### FILES Endpoints

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/files/documents` | List user documents | Required | 60/min |
| POST | `/api/v1/files/documents` | Upload document | Required | 20/min |
| GET | `/api/v1/files/documents/{id}` | Get document metadata | Required | 60/min |
| DELETE | `/api/v1/files/documents/{id}` | Delete document | Required | 20/min |
| GET | `/api/v1/files/documents/{id}/download` | Download document | Required | 30/min |
| POST | `/api/v1/files/documents/{id}/reindex` | Reindex document | Required | 10/min |
| GET | `/api/v1/files/documents/{id}/status` | Get indexing status | Required | 60/min |
| POST | `/api/v1/files/batch-upload` | Batch upload files | Required | 5/min |
| POST | `/api/v1/files/batch-delete` | Batch delete files | Required | 5/min |

#### VECTOR Endpoints

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/v1/vector/search` | Hybrid vector search | Required | 30/min |
| POST | `/api/v1/vector/ask` | RAG query with citations | Required | 20/min |
| GET | `/api/v1/vector/citations` | Recent citations | Required | 60/min |
| GET | `/api/v1/vector/stats` | Vector statistics | Required | 10/min |
| POST | `/api/v1/vector/export` | Export vector data | Required | 5/min |
| POST | `/api/v1/vector/documents/{id}/reindex` | Reindex document | Required | 10/min |
| POST | `/api/v1/vector/documents/reindex-all` | Reindex all documents | Required | 1/day |
| DELETE | `/api/v1/vector/cache` | Clear vector cache | Required | 5/min |

#### NOTIFICATIONS Endpoints (New)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/notifications` | List notifications | Required | 60/min |
| GET | `/api/v1/notifications/unread-count` | Get unread count | Required | 60/min |
| POST | `/api/v1/notifications/{id}/read` | Mark as read | Required | 60/min |
| POST | `/api/v1/notifications/read-all` | Mark all as read | Required | 10/min |
| DELETE | `/api/v1/notifications/{id}` | Delete notification | Required | 30/min |
| DELETE | `/api/v1/notifications` | Clear all notifications | Required | 5/min |
| PUT | `/api/v1/notifications/preferences` | Update notification preferences | Required | 10/min |
| GET | `/api/v1/notifications/preferences` | Get notification preferences | Required | 60/min |

#### ADMIN Endpoints

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/admin/audit-logs` | Get audit logs | Admin | 30/min |
| GET | `/api/v1/admin/users` | List all users | Admin | 30/min |
| GET | `/api/v1/admin/users/{id}` | Get user details | Admin | 60/min |
| PUT | `/api/v1/admin/users/{id}/role` | Update user role | Admin | 20/min |
| PUT | `/api/v1/admin/users/{id}/status` | Enable/disable user | Admin | 20/min |
| DELETE | `/api/v1/admin/users/{id}` | Delete user | Admin | 10/min |
| GET | `/api/v1/admin/sessions` | List all sessions | Admin | 30/min |
| POST | `/api/v1/admin/sessions/{id}/revoke` | Revoke session | Admin | 30/min |
| GET | `/api/v1/admin/stats` | System statistics | Admin | 10/min |
| GET | `/api/v1/admin/health` | Detailed health check | Admin | 10/min |
| POST | `/api/v1/admin/cache/clear` | Clear cache | Admin | 5/min |
| POST | `/api/v1/admin/queue/pause` | Pause job queue | Admin | 5/min |
| POST | `/api/v1/admin/queue/resume` | Resume job queue | Admin | 5/min |
| GET | `/api/v1/admin/queue/status` | Get queue status | Admin | 10/min |

#### ANALYTICS Endpoints (New)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/analytics/usage` | Get usage statistics | Required | 10/min |
| GET | `/api/v1/analytics/search` | Search analytics | Required | 10/min |
| GET | `/api/v1/analytics/performance` | Performance metrics | Required | 10/min |
| GET | `/api/v1/analytics/export` | Export analytics data | Required | 5/min |
| GET | `/api/v1/admin/analytics/overview` | System-wide analytics | Admin | 10/min |
| GET | `/api/v1/admin/analytics/users` | User analytics | Admin | 10/min |
| GET | `/api/v1/admin/analytics/errors` | Error rate analytics | Admin | 10/min |

#### HEALTH Endpoints

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/v1/health` | Basic health check | None | 100/min |
| GET | `/api/v1/health/detailed` | Detailed health check | None | 30/min |
| GET | `/api/v1/health/ready` | Readiness probe | None | 100/min |
| GET | `/api/v1/health/live` | Liveness probe | None | 100/min |

---

## 3. Detailed Endpoint Specifications

### 3.1 Authentication Endpoints

#### POST /api/v1/auth/signup

**Description:** Register a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Validation Rules:**
- `email`: Valid email format, max 255 characters
- `password`: Min 8 characters, max 128, must contain uppercase, lowercase, number, special char
- `first_name`: Optional, max 100 characters
- `last_name`: Optional, max 100 characters

**Response 201 Created:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "email_verified": false,
    "created_at": "2026-07-01T17:00:00Z"
  }
}
```

**Response 409 Conflict:**
```json
{
  "detail": "Email already registered"
}
```

**Response 422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must contain at least one uppercase letter",
      "type": "value_error"
    }
  ]
}
```

**Error Responses:**
- `400`: Invalid request data
- `409`: Email already exists
- `422`: Validation error
- `429`: Rate limit exceeded
- `500`: Internal server error

---

#### POST /api/v1/auth/login

**Description:** Authenticate user and receive JWT tokens

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Validation Rules:**
- `email`: Required, valid email format
- `password`: Required, min 6 characters

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Response 401 Unauthorized:**
```json
{
  "detail": "Invalid email or password"
}
```

**Response 429 Too Many Requests:**
```json
{
  "detail": "Too many login attempts. Please try again in 15 minutes.",
  "retry_after": 900
}
```

**Headers:**
- `Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Strict`
- `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict`

---

#### POST /api/v1/auth/refresh

**Description:** Refresh access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

**Response 401 Unauthorized:**
```json
{
  "detail": "Invalid refresh token"
}
```

**Security Notes:**
- Refresh token rotation on every use
- Old refresh token marked as rotated
- Reuse detection enabled
- Session family revoked on reuse

---

### 3.2 User Endpoints

#### GET /api/v1/users/profile

**Description:** Get current user's profile

**Authentication:** Required (JWT)

**Response 200 OK:**
```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "avatar_url": "https://cdn.example.com/avatars/1.jpg",
  "phone_number": "+1234567890",
  "email_verified": true,
  "two_factor_enabled": false,
  "role": "user",
  "last_login_at": "2026-07-01T16:00:00Z",
  "created_at": "2026-01-01T00:00:00Z"
}
```

#### PUT /api/v1/users/profile

**Description:** Update user profile

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

**Validation Rules:**
- `first_name`: Optional, max 100 chars, alphanumeric + spaces
- `last_name`: Optional, max 100 chars, alphanumeric + spaces
- `phone_number`: Optional, valid E.164 format

**Response 200 OK:**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "updated_at": "2026-07-01T17:05:00Z"
}
```

---

### 3.3 Search Endpoints

#### GET /api/v1/search/web

**Description:** Perform web search using specified backend

**Query Parameters:**
- `q` (required): Search query, 1-500 characters
- `backend` (optional): Search backend, default "wikipedia", enum: [wikipedia, brave, serpapi, duckduckgo]
- `page` (optional): Page number, default 1, min 1
- `page_size` (optional): Results per page, default 10, min 1, max 50

**Response 200 OK:**
```json
{
  "query": "artificial intelligence",
  "backend": "wikipedia",
  "page": 1,
  "page_size": 10,
  "total": 100,
  "results": [
    {
      "title": "Artificial Intelligence - Wikipedia",
      "snippet": "Artificial intelligence (AI) is intelligence demonstrated by machines...",
      "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
      "source": "wikipedia",
      "score": 0.95
    }
  ],
  "cached": false,
  "response_time_ms": 234
}
```

**Error Responses:**
- `400`: Invalid backend or query
- `401`: Unauthorized
- `402`: Search quota exceeded
- `502`: Backend service error
- `429`: Rate limit exceeded

---

### 3.4 Vector Endpoints

#### POST /api/v1/vector/search

**Description:** Hybrid vector + keyword search

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "top_k": 10,
  "filters": {
    "document_type": "pdf",
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-12-31"
    }
  },
  "hybrid_weight": 0.7
}
```

**Validation Rules:**
- `query`: Required, 1-500 characters
- `top_k`: Optional, default 10, min 1, max 50
- `filters`: Optional, JSON object
- `hybrid_weight`: Optional, 0-1, weight for vector vs keyword search

**Response 200 OK:**
```json
{
  "query": "machine learning algorithms",
  "total": 3,
  "results": [
    {
      "document_id": 1,
      "chunk_id": 5,
      "filename": "ml_guide.pdf",
      "content": "Machine learning algorithms can be categorized into...",
      "score": 0.92,
      "vector_score": 0.88,
      "keyword_score": 0.95,
      "highlights": [
        {
          "text": "machine learning algorithms",
          "start": 0,
          "end": 26
        }
      ]
    }
  ],
  "query_time_ms": 45
}
```

---

### 3.5 Notification Endpoints

#### GET /api/v1/notifications

**Description:** List user notifications with pagination

**Query Parameters:**
- `page` (optional): Page number, default 1
- `page_size` (optional): Results per page, default 20, max 100
- `unread_only` (optional): Filter unread only, default false
- `type` (optional): Filter by type, enum: [info, warning, error, success]

**Response 200 OK:**
```json
{
  "notifications": [
    {
      "id": 1,
      "type": "success",
      "title": "Document Indexed",
      "message": "Your document 'report.pdf' has been indexed successfully",
      "data": {
        "document_id": 123,
        "filename": "report.pdf"
      },
      "read": false,
      "created_at": "2026-07-01T17:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "unread_count": 1
}
```

---

## 4. Postman Collection Structure

### 4.1 Workspace: IOIS

**Workspace Settings:**
- Name: IOIS
- Type: Private
- Description: IOIS (Nebula) API Development & Testing

### 4.2 Collection: IOIS API v1

**Collection Variables:**
```json
{
  "base_url": {
    "value": "http://localhost:8000",
    "type": "default"
  },
  "api_version": {
    "value": "v1",
    "type": "default"
  },
  "access_token": {
    "value": "",
    "type": "default"
  },
  "refresh_token": {
    "value": "",
    "type": "default"
  },
  "user_id": {
    "value": "",
    "type": "default"
  },
  "email": {
    "value": "test@example.com",
    "type": "default"
  },
  "password": {
    "value": "TestPass123!",
    "type": "default"
  }
}
```

### 4.3 Folder Structure

```
IOIS API v1/
├── 📁 Auth
│   ├── Signup
│   ├── Login
│   ├── Refresh Token
│   ├── Logout
│   ├── Logout All
│   ├── Get Current User
│   ├── Forgot Password
│   ├── Reset Password
│   ├── Verify Email
│   ├── Enable 2FA
│   ├── Verify 2FA
│   ├── Disable 2FA
│   ├── List Sessions
│   └── Revoke Session
│
├── 📁 Users
│   ├── Get Profile
│   ├── Update Profile
│   ├── Delete Account
│   ├── Get Activity
│   ├── Change Password
│   ├── Get Preferences
│   ├── Update Preferences
│   ├── Upload Avatar
│   └── Delete Avatar
│
├── 📁 Search
│   ├── Web Search
│   ├── Orchestrated Search
│   ├── Search History
│   ├── Clear History
│   ├── Get Suggestions
│   ├── Save Search
│   └── List Saved Searches
│
├── 📁 Projects
│   ├── List Projects
│   ├── Create Project
│   ├── Get Project
│   ├── Update Project
│   ├── Delete Project
│   ├── Add Collaborator
│   ├── Remove Collaborator
│   ├── List Documents
│   └── Add Document
│
├── 📁 Files
│   ├── List Documents
│   ├── Upload Document
│   ├── Get Document
│   ├── Delete Document
│   ├── Download Document
│   ├── Reindex Document
│   ├── Get Index Status
│   ├── Batch Upload
│   └── Batch Delete
│
├── 📁 Vector
│   ├── Hybrid Search
│   ├── RAG Ask
│   ├── Recent Citations
│   ├── Vector Stats
│   ├── Export Vectors
│   ├── Reindex Document
│   ├── Reindex All
│   └── Clear Cache
│
├── 📁 Notifications
│   ├── List Notifications
│   ├── Unread Count
│   ├── Mark as Read
│   ├── Mark All as Read
│   ├── Delete Notification
│   ├── Clear All
│   ├── Get Preferences
│   └── Update Preferences
│
├── 📁 Admin
│   ├── Get Audit Logs
│   ├── List All Users
│   ├── Get User Details
│   ├── Update User Role
│   ├── Enable/Disable User
│   ├── Delete User
│   ├── List All Sessions
│   ├── Revoke Session
│   ├── System Stats
│   ├── Detailed Health
│   ├── Clear Cache
│   ├── Pause Queue
│   ├── Resume Queue
│   └── Queue Status
│
├── 📁 Analytics
│   ├── Get Usage Stats
│   ├── Search Analytics
│   ├── Performance Metrics
│   ├── Export Analytics
│   ├── System Overview
│   ├── User Analytics
│   └── Error Analytics
│
└── 📁 Health
    ├── Basic Health
    ├── Detailed Health
    ├── Readiness Probe
    └── Liveness Probe
```

### 4.4 Example Request: Login

```json
{
  "name": "Login",
  "event": [
    {
      "listen": "test",
      "script": {
        "exec": [
          "// Save tokens to environment",
          "const jsonData = pm.response.json();",
          "pm.environment.set('access_token', jsonData.access_token);",
          "pm.environment.set('refresh_token', jsonData.refresh_token);",
          "",
          "// Auto-refresh if token expires soon",
          "if (jsonData.expires_in < 300) {",
          "    pm.sendRequest({",
          "        url: pm.environment.get('base_url') + '/api/v1/auth/refresh',",
          "        method: 'POST',",
          "        header: { 'Content-Type': 'application/json' },",
          "        body: {",
          "            mode: 'raw',",
          "            raw: JSON.stringify({ refresh_token: pm.environment.get('refresh_token') })",
          "        }",
          "    }, function (err, res) {",
          "        if (!err) {",
          "            const data = res.json();",
          "            pm.environment.set('access_token', data.access_token);",
          "            pm.environment.set('refresh_token', data.refresh_token);",
          "        }",
          "    });",
          "}"
        ]
      }
    }
  ],
  "request": {
    "method": "POST",
    "header": [
      {
        "key": "Content-Type",
        "value": "application/json"
      }
    ],
    "body": {
      "mode": "raw",
      "raw": "{\n  \"email\": \"{{email}}\",\n  \"password\": \"{{password}}\"\n}"
    },
    "url": {
      "raw": "{{base_url}}/api/v1/auth/login",
      "host": ["{{base_url}}"],
      "path": ["api", "v1", "auth", "login"]
    }
  },
  "response": []
}
```

---

## 5. Environment Configurations

### 5.1 Local Environment

```json
{
  "id": "local",
  "name": "Local Development",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "enabled": true
    },
    {
      "key": "api_version",
      "value": "v1",
      "enabled": true
    },
    {
      "key": "timeout",
      "value": "30000",
      "enabled": true
    }
  ]
}
```

### 5.2 Staging Environment

```json
{
  "id": "staging",
  "name": "Staging",
  "values": [
    {
      "key": "base_url",
      "value": "https://staging-api.nebula-search.io",
      "enabled": true
    },
    {
      "key": "api_version",
      "value": "v1",
      "enabled": true
    },
    {
      "key": "timeout",
      "value": "30000",
      "enabled": true
    }
  ]
}
```

### 5.3 Production Environment

```json
{
  "id": "production",
  "name": "Production",
  "values": [
    {
      "key": "base_url",
      "value": "https://api.nebula-search.io",
      "enabled": true
    },
    {
      "key": "api_version",
      "value": "v1",
      "enabled": true
    },
    {
      "key": "timeout",
      "value": "30000",
      "enabled": true
    }
  ]
}
```

---

## 6. Postman Automation Scripts

### 6.1 Pre-request Script (Collection Level)

```javascript
// Auto-inject authentication token
if (pm.environment.get('access_token')) {
    pm.request.headers.upsert({
        key: 'Authorization',
        value: `Bearer ${pm.environment.get('access_token')}`
    });
}

// Add request ID for tracing
pm.request.headers.upsert({
    key: 'X-Request-ID',
    value: crypto.randomUUID()
});

// Log request for debugging
console.log(`${pm.request.method} ${pm.request.url.toString()}`);
```

### 6.2 Test Script (Collection Level)

```javascript
// Check for token expiration
const accessToken = pm.environment.get('access_token');
if (accessToken) {
    const payload = JSON.parse(atob(accessToken.split('.')[1]));
    const exp = payload.exp * 1000;
    const now = Date.now();

    // Refresh if token expires in next 5 minutes
    if (exp - now < 300000) {
        console.log('Token expiring soon, refreshing...');
        pm.sendRequest({
            url: pm.environment.get('base_url') + '/api/v1/auth/refresh',
            method: 'POST',
            header: { 'Content-Type': 'application/json' },
            body: {
                mode: 'raw',
                raw: JSON.stringify({
                    refresh_token: pm.environment.get('refresh_token')
                })
            }
        }, function (err, res) {
            if (!err && res.code === 200) {
                const data = res.json();
                pm.environment.set('access_token', data.access_token);
                pm.environment.set('refresh_token', data.refresh_token);
                console.log('Token refreshed successfully');
            }
        });
    }
}

// Validate response schema
if (pm.response.code === 200 || pm.response.code === 201) {
    try {
        const json = pm.response.json();
        pm.test('Response is valid JSON', () => {
            pm.expect(json).to.be.an('object');
        });
    } catch (e) {
        pm.test('Response parsing failed', () => {
            pm.expect.fail('Invalid JSON response');
        });
    }
}

// Log response time
pm.test('Response time is acceptable', () => {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});
```

### 6.3 Test Script: Login Request

```javascript
// Validate response structure
pm.test('Status code is 200', () => {
    pm.expect(pm.response.code).to.equal(200);
});

pm.test('Response has access_token', () => {
    const json = pm.response.json();
    pm.expect(json).to.have.property('access_token');
    pm.expect(json.access_token).to.be.a('string');
});

pm.test('Response has refresh_token', () => {
    const json = pm.response.json();
    pm.expect(json).to.have.property('refresh_token');
    pm.expect(json.refresh_token).to.be.a('string');
});

// Save tokens
pm.environment.set('access_token', pm.response.json().access_token);
pm.environment.set('refresh_token', pm.response.json().refresh_token);

// Save user info
if (pm.response.json().user) {
    pm.environment.set('user_id', pm.response.json().user.id);
    pm.environment.set('email', pm.response.json().user.email);
}
```

### 6.4 Test Script: Authenticated Request

```javascript
// Verify authentication
pm.test('Authentication successful', () => {
    pm.expect(pm.response.code).to.be.oneOf([200, 201, 204]);
});

// Check for rate limit headers
pm.test('Rate limit headers present', () => {
    pm.expect(pm.response.headers.has('X-RateLimit-Limit')).to.be.true;
    pm.expect(pm.response.headers.has('X-RateLimit-Remaining')).to.be.true;
});

// Validate response schema
const schema = {
    type: 'object',
    required: ['id', 'created_at'],
    properties: {
        id: { type: 'number' },
        created_at: { type: 'string', format: 'date-time' }
    }
};

pm.test('Response matches schema', () => {
    pm.expect(pm.response.json()).to.be.validJsonSchema(schema);
});
```

### 6.5 Collection Runner Configuration

```json
{
  "iteration": 1,
  "delay": 1000,
  "order": "sequential",
  "persist": true,
  "data": [
    {
      "email": "test@example.com",
      "password": "TestPass123!"
    }
  ]
}
```

### 6.6 Monitoring Configuration

```javascript
// Monitor: API Health Check
pm.test('API is healthy', function() {
    pm.expect(pm.response.code).to.equal(200);
    const json = pm.response.json();
    pm.expect(json.status).to.equal('healthy');
});

// Monitor: Response Time
pm.test('Response time < 500ms', function() {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

// Monitor: Error Rate
pm.test('No server errors', function() {
    pm.expect(pm.response.code).to.be.below(500);
});
```

---

## 7. Security Design

### 7.1 JWT Rotation Strategy

```python
# app/services/auth.py

class JWTManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.algorithm = settings.jwt_algorithm
        self.secret = settings.jwt_secret

    def create_access_token(self, email: str, role: str) -> str:
        """Create short-lived access token (15 min - 24 hours)"""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.jwt_expiry_minutes
        )
        payload = {
            "sub": email,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(32),  # Unique token ID
            "type": "access"
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self) -> str:
        """Create long-lived refresh token (7-30 days)"""
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.settings.refresh_token_days
        )
        payload = {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(32),
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def validate_token(self, token: str, token_type: str = "access") -> dict:
        """Validate and decode JWT"""
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            if payload.get("type") != token_type:
                raise HTTPException(401, "Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.JWTError:
            raise HTTPException(401, "Invalid token")
```

**Rotation Flow:**
1. Client uses refresh token to get new access token
2. Server marks old refresh token as rotated
3. Server creates new refresh token
4. Both tokens returned to client
5. If old refresh token reused → revoke entire session family

### 7.2 RBAC Permissions Matrix

```python
# app/middleware/rbac.py

PERMISSIONS = {
    # User permissions
    "user": {
        "search:read": "Perform web and vector searches",
        "documents:read": "View own documents",
        "documents:write": "Upload/delete own documents",
        "profile:read": "View own profile",
        "profile:write": "Update own profile",
        "notifications:read": "View own notifications",
        "notifications:write": "Manage own notifications",
        "projects:read": "View own projects",
        "projects:write": "Manage own projects",
        "analytics:read": "View own analytics",
    },
    # Admin permissions (includes all user permissions)
    "admin": {
        "*": "Full system access",
        "users:read": "View all users",
        "users:write": "Manage all users",
        "users:delete": "Delete users",
        "audit:read": "View audit logs",
        "sessions:read": "View all sessions",
        "sessions:write": "Revoke sessions",
        "system:read": "View system stats",
        "system:write": "Modify system settings",
        "cache:write": "Clear cache",
        "queue:write": "Manage job queue",
        "analytics:admin": "View system-wide analytics",
    }
}

def require_permission(permission: str):
    """Dependency to check user permission"""
    async def checker(email: str = Depends(get_current_user)):
        user = await get_user_by_email(email)
        role = user.get("role", "user")

        # Admin has all permissions
        if role == "admin" or "*" in PERMISSIONS.get(role, {}):
            return email

        # Check specific permission
        if permission not in PERMISSIONS.get(role, {}):
            raise HTTPException(403, f"Permission denied: {permission}")

        return email
    return checker
```

**Usage:**
```python
@router.get("/admin/users", dependencies=[Depends(require_permission("users:read"))])
async def list_users():
    pass
```

### 7.3 Input Validation

```python
# app/middleware/validation.py

from pydantic import BaseModel, validator, Field
import re

class SecureMixin:
    """Mixin for common security validations"""

    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            # Remove null bytes
            v = v.replace('\x00', '')
            # Normalize whitespace
            v = ' '.join(v.split())
        return v

class SearchRequest(SecureMixin, BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

    @validator('query')
    def validate_query(cls, v):
        # Prevent SQL injection patterns
        dangerous_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC)\b',
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*='
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Invalid query pattern')
        return v.strip()
```

### 7.4 SQL Injection Protection

```python
# All database queries use parameterized queries
# NEVER use string concatenation or f-strings for SQL

# GOOD ✅
await db.execute(
    "SELECT * FROM users WHERE email = ?",
    (email,)
)

# BAD ❌
await db.execute(
    f"SELECT * FROM users WHERE email = '{email}'"
)

# For PostgreSQL, use asyncpg parameterized queries
await conn.fetchrow(
    "SELECT * FROM users WHERE email = $1",
    email
)
```

### 7.5 XSS Protection

```python
# app/middleware/xss.py

from fastapi import Request
from fastapi.responses import JSONResponse

class XSSProtectionMiddleware:
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)

        # Add XSS protection headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

# Sanitize user input
def sanitize_html(text: str) -> str:
    """Remove HTML tags and escape special characters"""
    import html
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Escape HTML entities
    text = html.escape(text)
    return text
```

### 7.6 CSRF Strategy

```python
# app/middleware/csrf.py

from fastapi import Request
from fastapi.responses import JSONResponse

class CSRFProtectionMiddleware:
    async def __call__(self, request: Request, call_next):
        # Skip CSRF for API calls (using JWT)
        if request.headers.get("Content-Type") == "application/json":
            return await call_next(request)

        # Check CSRF token for form submissions
        csrf_token = request.headers.get("X-CSRF-Token")
        session_csrf = request.session.get("csrf_token")

        if not csrf_token or csrf_token != session_csrf:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid"}
            )

        return await call_next(request)

# Generate CSRF token
def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)
```

**Note:** For pure REST APIs using JWT in Authorization header, CSRF is not required. CSRF protection is only needed for cookie-based authentication.

### 7.7 Secure Headers

```python
# app/middleware/security.py

class SecurityHeadersMiddleware:
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS (only in production)
        if request.app.state.settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
```

### 7.8 Logging and Audit Trails

```python
# app/middleware/audit.py

class AuditMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )

        try:
            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                }
            )

            # Add request ID to response
            response.headers["X-Request-ID"] = request_id

            return response
        except Exception as exc:
            # Log error
            logger.exception(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(exc),
                }
            )
            raise
```

**Audit Log Entry:**
```python
# app/database/repositories/audit.py

async def create(self, user_id: int, action: str, **kwargs):
    await self._db.execute(
        """
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, metadata, ip_address, user_agent, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            action,
            kwargs.get("resource_type"),
            kwargs.get("resource_id"),
            json.dumps(kwargs.get("metadata", {})),
            kwargs.get("ip"),
            kwargs.get("user_agent"),
            kwargs.get("status", "success")
        )
    )
    await self._db.commit()
```

---

## 8. Database Mapping

### 8.1 Entity Relationship Diagram

```
users (1) ────< (N) sessions
  │
  ├───< (N) documents
  │     │
  │     └───< (N) vector_documents
  │           │
  │           └───< (N) vector_chunks
  │
  ├───< (N) search_history
  ├───< (N) notifications
  ├───< (N) user_preferences
  ├───< (N) exports
  ├───< (N) analytics_events
  │
  └───< (N) audit_logs

roles (1) ────< (N) user_roles (N) >──── (1) users
```

### 8.2 Index Strategy

```sql
-- Primary key indexes (automatic)
-- Unique indexes
CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_users_uuid ON users(uuid);
CREATE UNIQUE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE UNIQUE INDEX idx_sessions_token_hash ON sessions(refresh_token_hash);

-- Foreign key indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);

-- Composite indexes for common queries
CREATE INDEX idx_sessions_user_expires ON sessions(user_id, expires_at) WHERE revoked_at IS NULL;
CREATE INDEX idx_documents_user_status ON documents(user_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_notifications_user_read_created ON notifications(user_id, read, created_at DESC);

-- Full-text search indexes
CREATE INDEX idx_search_history_query_fts ON search_history USING GIN(to_tsvector('english', query));

-- JSONB indexes
CREATE INDEX idx_documents_metadata_gin ON documents USING GIN(metadata);
CREATE INDEX idx_analytics_events_properties_gin ON analytics_events USING GIN(properties);

-- Vector indexes (for similarity search)
CREATE INDEX idx_vector_chunks_embedding ON vector_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 8.3 Migration Order

```sql
-- Migration 001: Initial schema
-- Migration 002: Add user preferences
-- Migration 003: Add notifications
-- Migration 004: Add analytics events
-- Migration 005: Add vector support
-- Migration 006: Add RBAC tables
-- Migration 007: Add exports
-- Migration 008: Add soft deletes
-- Migration 009: Add audit log enhancements
-- Migration 010: Add vector partitioning
```

---

## 9. Developer Outputs

### 9.1 OpenAPI Specification Structure

```yaml
# openapi.yaml
openapi: 3.0.3
info:
  title: IOIS API
  description: Production-ready API for IOIS (Nebula) search platform
  version: 1.0.0
  contact:
    name: IOIS Team
    email: support@nebula-search.io

servers:
  - url: http://localhost:8000
    description: Local development
  - url: https://staging-api.nebula-search.io
    description: Staging environment
  - url: https://api.nebula-search.io
    description: Production environment

security:
  - BearerAuth: []

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT access token obtained from /auth/login

  schemas:
    User:
      type: object
      required: [id, email, role, created_at]
      properties:
        id:
          type: integer
        uuid:
          type: string
          format: uuid
        email:
          type: string
          format: email
        first_name:
          type: string
        last_name:
          type: string
        role:
          type: string
          enum: [user, admin]
        email_verified:
          type: boolean
        created_at:
          type: string
          format: date-time

    Error:
      type: object
      required: [detail]
      properties:
        detail:
          type: string

  responses:
    UnauthorizedError:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    ForbiddenError:
      description: Permission denied
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    NotFoundError:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    ValidationError:
      description: Validation error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

paths:
  /api/v1/auth/signup:
    post:
      tags: [Auth]
      summary: Register new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SignupRequest'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SignupResponse'
        '409':
          $ref: '#/components/responses/ConflictError'
        '422':
          $ref: '#/components/responses/ValidationError'

  /api/v1/auth/login:
    post:
      tags: [Auth]
      summary: Login user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedError'
        '429':
          description: Rate limit exceeded
```

### 9.2 Folder Structure

```
nebula-search-engine/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # App factory
│   │   ├── config.py                  # Settings
│   │   ├── database/
│   │   │   ├── __init__.py            # DB connection
│   │   │   ├── engine.py              # SQLite/PostgreSQL
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
├── docs/
│   ├── API_V1.md
│   ├── API_V1.1.md
│   ├── PRODUCTION_API_ARCHITECTURE.md
│   ├── POSTMAN_COLLECTION.json
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

### 9.3 API Versioning Plan

```python
# Versioning Strategy: URL Path Versioning

# Current: /api/v1/...
# Future:  /api/v2/...

# Version compatibility matrix:
# v1.0 - Initial release (current)
# v1.1 - Added vector search (current)
# v2.0 - Breaking changes (future)

# Backward compatibility:
# - Support v1 for 12 months after v2 release
# - Deprecation warnings in response headers
# - Migration guide for clients

# Implementation:
# app/main.py
from fastapi import FastAPI

app = FastAPI()

# v1 routes
v1_app = FastAPI()
v1_app.include_router(auth.router, prefix="/api/v1/auth")
v1_app.include_router(search.router, prefix="/api/v1/search")
# ... more v1 routes

app.mount("/v1", v1_app)

# v2 routes (future)
v2_app = FastAPI()
v2_app.include_router(auth_v2.router, prefix="/api/v2/auth")
# ... more v2 routes

app.mount("/v2", v2_app)
```

### 9.4 Deployment Checklist

```yaml
# Pre-Deployment Checklist

## Environment Setup
- [ ] Set JWT_SECRET (64+ character random string)
- [ ] Configure DATABASE_URL (PostgreSQL)
- [ ] Set REDIS_URL
- [ ] Configure CORS_ORIGINS
- [ ] Set OPENAI_API_KEY (if using OpenAI)
- [ ] Configure storage (S3/MinIO credentials)
- [ ] Set APP_ENV=production
- [ ] Enable HTTPS/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure logging (ELK/Splunk)
- [ ] Set up error tracking (Sentry)

## Database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Create indexes
- [ ] Set up read replicas (if needed)
- [ ] Configure connection pooling
- [ ] Enable pg_stat_statements
- [ ] Set up automated backups
- [ ] Configure point-in-time recovery

## Security
- [ ] Enable HTTPS only
- [ ] Configure HSTS
- [ ] Set up WAF (Cloudflare/AWS WAF)
- [ ] Enable rate limiting
- [ ] Configure DDoS protection
- [ ] Rotate all secrets
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Configure security headers
- [ ] Enable CORS with specific origins

## Performance
- [ ] Enable Redis caching
- [ ] Configure CDN for static assets
- [ ] Set up load balancer
- [ ] Configure auto-scaling
- [ ] Enable gzip compression
- [ ] Optimize database queries
- [ ] Set up connection pooling
- [ ] Configure worker processes

## Monitoring
- [ ] Set up health checks
- [ ] Configure alerts (PagerDuty/OpsGenie)
- [ ] Enable APM (New Relic/Datadog)
- [ ] Set up log aggregation
- [ ] Configure metrics (Prometheus)
- [ ] Set up dashboards (Grafana)
- [ ] Enable distributed tracing (Jaeger)

## Testing
- [ ] Run unit tests: `pytest`
- [ ] Run integration tests
- [ ] Run load tests: `locust`
- [ ] Run security scan: `bandit`
- [ ] Run dependency check: `safety`
- [ ] Verify Postman collection
- [ ] Test disaster recovery
- [ ] Perform penetration testing

## Documentation
- [ ] Update API documentation
- [ ] Generate OpenAPI spec
- [ ] Update README
- [ ] Create runbooks
- [ ] Document incident response
- [ ] Create deployment guide
```

### 9.5 CI/CD Integration

```yaml
# .github/workflows/ci-cd.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # Lint and format check
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install ruff mypy
      - run: ruff check backend/
      - run: mypy backend/

  # Run tests
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements-dev.txt
      - run: pytest backend/tests/ -v --cov=app

  # Security scan
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install bandit safety
      - run: bandit -r backend/app/
      - run: safety check -r backend/requirements.txt

  # Build Docker image
  build:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile
          push: false
          tags: nebula-api:${{ github.sha }}

  # Deploy to staging
  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          kubectl set image deployment/nebula-api \
            nebula-api=nebula-api:${{ github.sha }} \
            -n staging
          kubectl rollout status deployment/nebula-api -n staging

  # Deploy to production
  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          kubectl set image deployment/nebula-api \
            nebula-api=nebula-api:${{ github.sha }} \
            -n production
          kubectl rollout status deployment/nebula-api -n production
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up PostgreSQL database
- [ ] Run initial migrations
- [ ] Configure Redis cache
- [ ] Set up S3/MinIO storage
- [ ] Implement API Gateway (Kong)
- [ ] Configure load balancer (nginx)

### Phase 2: Core Services (Weeks 3-4)
- [ ] Implement User Service
- [ ] Implement Notification Service
- [ ] Implement Analytics Service
- [ ] Add RBAC middleware
- [ ] Enhance security headers
- [ ] Implement rate limiting per user

### Phase 3: New Endpoints (Weeks 5-6)
- [ ] Implement Users endpoints
- [ ] Implement Projects endpoints
- [ ] Implement Notifications endpoints
- [ ] Implement Analytics endpoints
- [ ] Add comprehensive validation
- [ ] Add request/response logging

### Phase 4: Testing & Documentation (Weeks 7-8)
- [ ] Write unit tests (80% coverage)
- [ ] Write integration tests
- [ ] Generate OpenAPI spec
- [ ] Create Postman collection
- [ ] Write API documentation
- [ ] Create deployment guides

### Phase 5: Production Readiness (Weeks 9-10)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure alerting
- [ ] Set up logging (ELK)
- [ ] Enable error tracking (Sentry)
- [ ] Perform load testing
- [ ] Security audit
- [ ] Penetration testing

### Phase 6: Deployment (Week 11)
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Monitor for 48 hours
- [ ] Document lessons learned

---

## 11. Missing Requirements Analysis

### 11.1 Critical Missing Features

1. **Email Service**
   - Password reset emails
   - Email verification
   - Notification emails
   - **Solution:** Integrate SendGrid/AWS SES/Mailgun

2. **File Virus Scanning**
   - Malware detection for uploads
   - **Solution:** Integrate ClamAV

3. **Image Processing**
   - Avatar resizing
   - Thumbnail generation
   - **Solution:** Use Pillow/Sharp

4. **Rate Limiting per User**
   - Current: IP-based only
   - **Solution:** Implement user_id-based rate limiting

5. **API Key Authentication**
   - For programmatic access
   - **Solution:** Add API key generation and validation

6. **Webhook Support**
   - Event notifications
   - **Solution:** Implement webhook system

7. **Bulk Operations**
   - Batch upload/delete
   - **Solution:** Implement async job queue

8. **Data Export (GDPR)**
   - User data export
   - Account deletion
   - **Solution:** Implement export service

### 11.2 Nice-to-Have Features

1. **GraphQL API**
   - Flexible queries
   - **Justification:** Not needed for current use case, REST is sufficient

2. **WebSocket Support**
   - Real-time notifications
   - **Justification:** Can use polling for now, WebSocket if needed later

3. **Multi-tenancy**
   - Organization support
   - **Justification:** Not required for single-user app

4. **API Versioning**
   - v1, v2 support
   - **Justification:** Plan for future, implement when needed

5. **GraphQL Subscriptions**
   - Real-time updates
   - **Justification:** Overkill for current requirements

---

## 12. Recommended Next Build Order

### Priority 1 (Critical - Week 1-2)
1. **PostgreSQL Migration**
   - Set up production database
   - Run migrations
   - Test data migration from SQLite

2. **Redis Cache**
   - Install and configure Redis
   - Implement caching layer
   - Cache search results and API responses

3. **User Service**
   - Profile management
   - Preferences
   - Avatar upload

### Priority 2 (High - Week 3-4)
4. **Notification Service**
   - In-app notifications
   - Email integration
   - Notification preferences

5. **Enhanced Security**
   - RBAC implementation
   - 2FA support
   - Email verification

6. **Analytics Service**
   - Event tracking
   - Usage metrics
   - Performance monitoring

### Priority 3 (Medium - Week 5-6)
7. **Projects Feature**
   - Project CRUD
   - Collaboration
   - Document organization

8. **File Service Enhancements**
   - Virus scanning
   - Thumbnail generation
   - Batch operations

9. **Admin Dashboard**
   - User management
   - System stats
   - Audit logs

### Priority 4 (Low - Week 7-8)
10. **Advanced Features**
    - API keys
    - Webhooks
    - Data export

11. **Performance Optimization**
    - Query optimization
    - Connection pooling
    - CDN integration

12. **Documentation**
    - OpenAPI spec
    - Postman collection
    - Deployment guides

---

## 13. API Blueprint Summary

### 13.1 Authentication Flow

```
1. User signs up → POST /api/v1/auth/signup
2. User logs in → POST /api/v1/auth/login
   - Returns access_token (15min) + refresh_token (30days)
3. User accesses protected resource
   - Header: Authorization: Bearer <access_token>
4. Access token expires → POST /api/v1/auth/refresh
   - Returns new access_token + refresh_token (rotation)
5. User logs out → POST /api/v1/auth/logout
   - Revokes refresh token
```

### 13.2 Request Flow

```
Client → API Gateway → Load Balancer → FastAPI Instance
                                                    │
                                                    ├→ Auth Middleware (JWT validation)
                                                    ├→ RBAC Middleware (permission check)
                                                    ├→ Rate Limit Middleware
                                                    ├→ Validation Middleware
                                                    ├→ Route Handler
                                                    ├→ Service Layer
                                                    ├→ Repository Layer
                                                    ├→ Database (PostgreSQL)
                                                    ├→ Cache (Redis)
                                                    └→ Response
```

### 13.3 Error Handling

```python
# Standard error response format
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-07-01T17:00:00Z"
}

# Error codes:
# VALIDATION_ERROR - 422
# UNAUTHORIZED - 401
# FORBIDDEN - 403
# NOT_FOUND - 404
# RATE_LIMIT_EXCEEDED - 429
# INTERNAL_ERROR - 500
# SERVICE_UNAVAILABLE - 503
```

---

## 14. Conclusion

This architecture provides a production-ready foundation for IOIS (Nebula) that:

✅ **Maintains backward compatibility** with existing code
✅ **Follows OWASP best practices** for security
✅ **Implements JWT rotation** with refresh tokens
✅ **Provides comprehensive RBAC** permissions
✅ **Scales horizontally** with stateless design
✅ **Includes monitoring** and observability
✅ **Supports CI/CD** with automated testing
✅ **Documents everything** with OpenAPI and Postman

**Next Steps:**
1. Review this document with the team
2. Prioritize features based on business needs
3. Set up development environment
4. Begin Phase 1 implementation
5. Create Postman collection from this spec
6. Run proof-of-concept for critical features

---

**Document Version:** 1.0
**Last Updated:** 2026-07-01
**Author:** Senior API Architect
**Status:** Ready for Review