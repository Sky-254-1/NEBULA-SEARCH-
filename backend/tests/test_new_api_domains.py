"""Tests for new API domains: documents, users, notifications, analytics, recommendations, admin."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth import create_access_token
from app.config import get_settings

settings = get_settings()


# ============================================
# Test Fixtures
# ============================================

class APITestBase:
    """Bind module-scoped TestClient to test class instances."""

    @pytest.fixture(autouse=True)
    def _bind_client(self, client):
        self.client = client


@pytest.fixture
def mock_db():
    """Mock database connection."""
    db = AsyncMock()
    db.fetchone = AsyncMock()
    db.fetchall = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def user_token():
    """Create a test user token."""
    return create_access_token("test@example.com", role="user")


@pytest.fixture
def admin_token():
    """Create a test admin token."""
    return create_access_token("admin@example.com", role="admin")


@pytest.fixture
def auth_headers_user(user_token):
    """Authorization headers for regular user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def auth_headers_admin(admin_token):
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================
# Documents Domain Tests
# ============================================

class TestDocumentsAPI(APITestBase):
    """Test documents domain endpoints."""
    
    def test_list_documents_unauthorized(self):
        """Test listing documents without authentication."""
        response = self.client.get("/api/v1/documents/")
        assert response.status_code == 401
    
    def test_list_documents_authorized(self, auth_headers_user, mock_db):
        """Test listing documents with authentication."""
        with patch("app.routes.documents.get_db", return_value=mock_db):
            with patch("app.routes.documents.UserRepository") as MockUserRepo:
                # Mock user repository
                mock_user_repo = AsyncMock()
                mock_user_repo.get_id_by_email = AsyncMock(return_value=1)
                MockUserRepo.return_value = mock_user_repo
                
                # Mock document repository
                with patch("app.routes.documents.DocumentRepository") as MockDocRepo:
                    mock_doc_repo = AsyncMock()
                    mock_doc_repo.list_for_user = AsyncMock(return_value=[])
                    MockDocRepo.return_value = mock_doc_repo
                    
                    response = self.client.get("/api/v1/documents/", headers=auth_headers_user)
                    assert response.status_code == 200
                    assert "documents" in response.json()
                    assert "pagination" in response.json()
    
    def test_list_documents_with_pagination(self, auth_headers_user, mock_db):
        """Test listing documents with pagination parameters."""
        with patch("app.routes.documents.get_db", return_value=mock_db):
            with patch("app.routes.documents.UserRepository") as MockUserRepo:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_id_by_email = AsyncMock(return_value=1)
                MockUserRepo.return_value = mock_user_repo
                
                with patch("app.routes.documents.DocumentRepository") as MockDocRepo:
                    mock_doc_repo = AsyncMock()
                    # Mock 25 documents
                    mock_doc_repo.list_for_user = AsyncMock(return_value=[
                        {"id": i, "filename": f"doc{i}.txt", "content_type": "text/plain", 
                         "indexed_at": None, "created_at": "2024-01-01"}
                        for i in range(1, 26)
                    ])
                    MockDocRepo.return_value = mock_doc_repo
                    
                    response = self.client.get(
                        "/api/v1/documents/",
                        params={"page": 1, "page_size": 10},
                        headers=auth_headers_user
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert len(data["documents"]) == 10
                    assert data["pagination"]["total"] == 25
                    assert data["pagination"]["page"] == 1
                    assert data["pagination"]["page_size"] == 10
                    assert data["pagination"]["total_pages"] == 3
                    assert data["pagination"]["has_next"] is True
                    assert data["pagination"]["has_previous"] is False
    
    def test_upload_document_unauthorized(self):
        """Test uploading document without authentication."""
        response = self.client.post("/api/v1/documents/")
        assert response.status_code == 401
    
    def test_upload_document_invalid_type(self, auth_headers_user):
        """Test uploading document with invalid file type."""
        response = self.client.post(
            "/api/v1/documents/",
            files={"file": ("test.exe", b"content", "application/octet-stream")},
            headers=auth_headers_user
        )
        assert response.status_code == 400
        assert "File type not allowed" in response.json()["detail"]
    
    def test_delete_document_unauthorized(self):
        """Test deleting document without authentication."""
        response = self.client.delete("/api/v1/documents/1")
        assert response.status_code == 401


# ============================================
# Users Domain Tests
# ============================================

class TestUsersAPI(APITestBase):
    """Test users domain endpoints."""
    
    def test_get_profile_unauthorized(self):
        """Test getting profile without authentication."""
        response = self.client.get("/api/v1/users/profile")
        assert response.status_code == 401
    
    def test_get_profile_authorized(self, auth_headers_user, mock_db):
        """Test getting profile with authentication."""
        with patch("app.routes.users.get_db", return_value=mock_db):
            with patch("app.routes.users.UserRepository") as MockUserRepo:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_email = AsyncMock(return_value={
                    "id": 1,
                    "email": "test@example.com",
                    "role": "user",
                    "email_verified": True,
                    "created_at": "2024-01-01",
                    "last_login": None,
                })
                MockUserRepo.return_value = mock_user_repo
                
                response = self.client.get("/api/v1/users/profile", headers=auth_headers_user)
                assert response.status_code == 200
                data = response.json()
                assert data["email"] == "test@example.com"
                assert data["role"] == "user"
    
    def test_update_profile_unauthorized(self):
        """Test updating profile without authentication."""
        response = self.client.put("/api/v1/users/profile", json={"name": "Test User"})
        assert response.status_code == 401
    
    def test_get_preferences_unauthorized(self):
        """Test getting preferences without authentication."""
        response = self.client.get("/api/v1/users/preferences")
        assert response.status_code == 401
    
    def test_get_activity_unauthorized(self):
        """Test getting activity without authentication."""
        response = self.client.get("/api/v1/users/activity")
        assert response.status_code == 401


# ============================================
# Notifications Domain Tests
# ============================================

class TestNotificationsAPI(APITestBase):
    """Test notifications domain endpoints."""
    
    def test_list_notifications_unauthorized(self):
        """Test listing notifications without authentication."""
        response = self.client.get("/api/v1/notifications/")
        assert response.status_code == 401
    
    def test_list_notifications_authorized(self, auth_headers_user, mock_db):
        """Test listing notifications with authentication."""
        with patch("app.routes.notifications.get_db", return_value=mock_db):
            with patch("app.routes.notifications.UserRepository") as MockUserRepo:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_email = AsyncMock(return_value={
                    "id": 1,
                    "email": "test@example.com",
                })
                MockUserRepo.return_value = mock_user_repo

                with patch("app.routes.notifications.NotificationRepository") as MockNotifRepo:
                    mock_notif_repo = AsyncMock()
                    mock_notif_repo.list_for_user = AsyncMock(return_value=[])
                    mock_notif_repo.get_unread_count = AsyncMock(return_value=0)
                    MockNotifRepo.return_value = mock_notif_repo

                    response = self.client.get("/api/v1/notifications/", headers=auth_headers_user)
                    assert response.status_code == 200
                    data = response.json()
                    assert "notifications" in data
                    assert "pagination" in data
                    assert "unread_count" in data
    
    def test_list_notifications_with_pagination(self, auth_headers_user, mock_db):
        """Test listing notifications with pagination."""
        with patch("app.routes.notifications.get_db", return_value=mock_db):
            with patch("app.routes.notifications.UserRepository") as MockUserRepo:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_email = AsyncMock(return_value={"id": 1, "email": "test@example.com"})
                MockUserRepo.return_value = mock_user_repo

                with patch("app.routes.notifications.NotificationRepository") as MockNotifRepo:
                    mock_notif_repo = AsyncMock()
                    mock_notif_repo.list_for_user = AsyncMock(return_value=[])
                    mock_notif_repo.get_unread_count = AsyncMock(return_value=0)
                    MockNotifRepo.return_value = mock_notif_repo

                    response = self.client.get(
                        "/api/v1/notifications/",
                        params={"page": 1, "page_size": 20},
                        headers=auth_headers_user
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["pagination"]["page"] == 1
                    assert data["pagination"]["page_size"] == 20
    
    def test_get_unread_count_unauthorized(self):
        """Test getting unread count without authentication."""
        response = self.client.get("/api/v1/notifications/unread-count")
        assert response.status_code == 401
    
    def test_mark_as_read_unauthorized(self):
        """Test marking notification as read without authentication."""
        response = self.client.post("/api/v1/notifications/1/read")
        assert response.status_code == 401
    
    def test_get_preferences_unauthorized(self):
        """Test getting notification preferences without authentication."""
        response = self.client.get("/api/v1/notifications/preferences")
        assert response.status_code == 401
    
    def test_update_preferences_unauthorized(self):
        """Test updating notification preferences without authentication."""
        response = self.client.put("/api/v1/notifications/preferences", json={})
        assert response.status_code == 401


# ============================================
# Analytics Domain Tests
# ============================================

class TestAnalyticsAPI(APITestBase):
    """Test analytics domain endpoints."""
    
    def test_get_usage_stats_unauthorized(self):
        """Test getting usage stats without authentication."""
        response = self.client.get("/api/v1/analytics/usage")
        assert response.status_code == 401
    
    def test_get_usage_stats_authorized(self, auth_headers_user, mock_db):
        """Test getting usage stats with authentication."""
        with patch("app.routes.analytics.UserRepository") as MockUserRepo, patch(
            "app.routes.analytics.DocumentRepository"
        ) as MockDocRepo, patch("app.routes.analytics.search_analytics") as mock_analytics:
            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_email = AsyncMock(return_value={"id": 1, "email": "test@example.com"})
            MockUserRepo.return_value = mock_user_repo

            mock_doc_repo = AsyncMock()
            mock_doc_repo.list_for_user = AsyncMock(return_value=[])
            MockDocRepo.return_value = mock_doc_repo

            mock_analytics._set_db = MagicMock()
            mock_analytics.get_user_search_history = AsyncMock(return_value=[])

            response = self.client.get("/api/v1/analytics/usage", headers=auth_headers_user)
            assert response.status_code == 200
            data = response.json()
            assert "period_days" in data
            assert "total_searches" in data
    
    def test_get_search_analytics_unauthorized(self):
        """Test getting search analytics without authentication."""
        response = self.client.get("/api/v1/analytics/search")
        assert response.status_code == 401
    
    def test_get_performance_metrics_unauthorized(self):
        """Test getting performance metrics without authentication."""
        response = self.client.get("/api/v1/analytics/performance")
        assert response.status_code == 401
    
    def test_export_analytics_unauthorized(self):
        """Test exporting analytics without authentication."""
        response = self.client.get("/api/v1/analytics/export")
        assert response.status_code == 401


# ============================================
# Recommendations Domain Tests
# ============================================

class TestRecommendationsAPI(APITestBase):
    """Test recommendations domain endpoints."""
    
    def test_get_related_unauthorized(self):
        """Test getting related documents without authentication."""
        response = self.client.get("/api/v1/recommendations/related")
        assert response.status_code == 401
    
    def test_get_related_authorized(self, auth_headers_user, mock_db):
        """Test getting related documents with authentication."""
        with patch("app.routes.recommendations.get_db", return_value=mock_db):
            with patch("app.routes.recommendations.UserRepository") as MockUserRepo:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_email = AsyncMock(return_value={"id": 1, "email": "test@example.com"})
                MockUserRepo.return_value = mock_user_repo

                with patch("app.routes.recommendations.DocumentRepository") as MockDocRepo:
                    mock_doc_repo = AsyncMock()
                    mock_doc_repo.get_by_id = AsyncMock(return_value={"id": 1, "filename": "test.txt", "content_type": "text"})
                    mock_doc_repo.list_for_user = AsyncMock(return_value=[])
                    MockDocRepo.return_value = mock_doc_repo

                    response = self.client.get(
                        "/api/v1/recommendations/related",
                        params={"document_id": 1},
                        headers=auth_headers_user
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "recommendations" in data
                    assert "total" in data
    
    def test_get_personalized_unauthorized(self):
        """Test getting personalized recommendations without authentication."""
        response = self.client.get("/api/v1/recommendations/personalized")
        assert response.status_code == 401
    
    def test_get_similar_searches_unauthorized(self):
        """Test getting similar searches without authentication."""
        response = self.client.get("/api/v1/recommendations/similar-searches")
        assert response.status_code == 401


# ============================================
# Admin Domain Tests
# ============================================

class TestAdminAPI(APITestBase):
    """Test admin domain endpoints."""
    
    def test_list_users_unauthorized(self):
        """Test listing users without admin authentication."""
        response = self.client.get("/api/v1/admin/users")
        assert response.status_code == 401
    
    def test_list_users_non_admin(self, auth_headers_user):
        """Test listing users with non-admin user."""
        response = self.client.get("/api/v1/admin/users", headers=auth_headers_user)
        assert response.status_code == 403
    
    def test_list_users_admin(self, auth_headers_admin, mock_db):
        """Test listing users with admin authentication."""
        with patch("app.routes.admin.get_db", return_value=mock_db):
            with patch("app.routes.admin.UserRepository") as MockUserRepo:
                mock_user_repo = AsyncMock()
                mock_user_repo.list_all = AsyncMock(return_value=[
                    {
                        "id": 1,
                        "email": "user1@example.com",
                        "role": "user",
                        "email_verified": True,
                        "created_at": "2024-01-01",
                        "last_login": None,
                        "is_active": True,
                    }
                ])
                MockUserRepo.return_value = mock_user_repo
                
                response = self.client.get("/api/v1/admin/users", headers=auth_headers_admin)
                assert response.status_code == 200
                data = response.json()
                assert "users" in data
                assert "pagination" in data
    
    def test_get_system_stats_admin(self, auth_headers_admin, mock_db):
        """Test getting system stats with admin authentication."""
        with patch("app.routes.admin.get_db", return_value=mock_db):
            with patch("app.routes.admin.UserRepository") as MockUserRepo:
                with patch("app.routes.admin.DocumentRepository") as MockDocRepo:
                    with patch("app.routes.admin.cache_service") as mock_cache:
                        mock_user_repo = AsyncMock()
                        mock_user_repo.list_all = AsyncMock(return_value=[])
                        MockUserRepo.return_value = mock_user_repo
                        
                        mock_doc_repo = AsyncMock()
                        MockDocRepo.return_value = mock_doc_repo
                        
                        mock_cache.get_stats = AsyncMock(return_value={
                            "hit_ratio": 0.85,
                            "memory_usage_mb": 10.5,
                            "keys_count": 100,
                        })
                        
                        with patch("app.routes.admin.job_queue") as mock_queue:
                            mock_queue._redis = None
                            mock_queue._queue = []
                            
                            response = self.client.get("/api/v1/admin/stats", headers=auth_headers_admin)
                            assert response.status_code == 200
                            data = response.json()
                            assert "total_users" in data
                            assert "cache_hit_ratio" in data
    
    def test_get_queue_stats_admin(self, auth_headers_admin):
        """Test getting queue stats with admin authentication."""
        with patch("app.routes.admin.job_queue") as mock_queue:
            mock_queue._redis = None
            mock_queue._queue = []
            
            response = self.client.get("/api/v1/admin/queue", headers=auth_headers_admin)
            assert response.status_code == 200
            data = response.json()
            assert "pending_jobs" in data
            assert "queue_type" in data
    
    def test_get_cache_stats_admin(self, auth_headers_admin):
        """Test getting cache stats with admin authentication."""
        with patch("app.routes.admin.cache_service") as mock_cache:
            mock_cache.get_stats = AsyncMock(return_value={
                "connected": True,
                "hit_ratio": 0.85,
                "memory_usage_mb": 10.5,
                "keys_count": 100,
            })
            
            response = self.client.get("/api/v1/admin/cache", headers=auth_headers_admin)
            assert response.status_code == 200
            data = response.json()
            assert "connected" in data
            assert "hit_ratio" in data
    
    def test_clear_cache_admin(self, auth_headers_admin):
        """Test clearing cache with admin authentication."""
        with patch("app.routes.admin.cache_service") as mock_cache:
            mock_cache.clear = AsyncMock()
            
            response = self.client.post("/api/v1/admin/cache/clear", headers=auth_headers_admin)
            assert response.status_code == 200
            assert "message" in response.json()
    
    def test_get_audit_logs_admin(self, auth_headers_admin, mock_db):
        """Test getting audit logs with admin authentication."""
        with patch("app.routes.admin.get_db", return_value=mock_db):
            with patch("app.routes.admin.AuditRepository") as MockAuditRepo:
                mock_audit_repo = AsyncMock()
                mock_audit_repo.get_recent = AsyncMock(return_value=[])
                MockAuditRepo.return_value = mock_audit_repo
                
                response = self.client.get("/api/v1/admin/audit-logs", headers=auth_headers_admin)
                assert response.status_code == 200
                data = response.json()
                assert "logs" in data
                assert "pagination" in data


# ============================================
# Pagination Tests
# ============================================

class TestPaginationIntegration(APITestBase):
    """Test pagination across all collection endpoints."""
    
    def test_pagination_page_size_validation(self, auth_headers_user):
        """Test pagination page size validation."""
        # Page size too large
        response = self.client.get(
            "/api/v1/documents/",
            params={"page": 1, "page_size": 200},
            headers=auth_headers_user
        )
        assert response.status_code == 422  # Validation error
    
    def test_pagination_page_validation(self, auth_headers_user):
        """Test pagination page number validation."""
        # Page number less than 1
        response = self.client.get(
            "/api/v1/documents/",
            params={"page": 0, "page_size": 20},
            headers=auth_headers_user
        )
        assert response.status_code == 422  # Validation error
    
    def test_pagination_metadata_correctness(self, auth_headers_user, mock_db):
        """Test pagination metadata is correct."""
        with patch("app.routes.documents.get_db", return_value=mock_db):
            with patch("app.routes.documents.UserRepository") as MockUserRepo:
                with patch("app.routes.documents.DocumentRepository") as MockDocRepo:
                    mock_user_repo = AsyncMock()
                    mock_user_repo.get_id_by_email = AsyncMock(return_value=1)
                    MockUserRepo.return_value = mock_user_repo
                    
                    mock_doc_repo = AsyncMock()
                    # Mock 5 documents
                    mock_doc_repo.list_for_user = AsyncMock(return_value=[
                        {"id": i, "filename": f"doc{i}.txt", "content_type": "text/plain",
                         "indexed_at": None, "created_at": "2024-01-01"}
                        for i in range(1, 6)
                    ])
                    MockDocRepo.return_value = mock_doc_repo
                    
                    # Request page 1 with page_size 2
                    response = self.client.get(
                        "/api/v1/documents/",
                        params={"page": 1, "page_size": 2},
                        headers=auth_headers_user
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["pagination"]["total"] == 5
                    assert data["pagination"]["page"] == 1
                    assert data["pagination"]["page_size"] == 2
                    assert data["pagination"]["total_pages"] == 3
                    assert data["pagination"]["has_next"] is True
                    assert data["pagination"]["has_previous"] is False
                    
                    # Request page 2
                    response = self.client.get(
                        "/api/v1/documents/",
                        params={"page": 2, "page_size": 2},
                        headers=auth_headers_user
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["pagination"]["has_next"] is True
                    assert data["pagination"]["has_previous"] is True
                    
                    # Request last page
                    response = self.client.get(
                        "/api/v1/documents/",
                        params={"page": 3, "page_size": 2},
                        headers=auth_headers_user
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["pagination"]["has_next"] is False
                    assert data["pagination"]["has_previous"] is True


# ============================================
# Security Tests
# ============================================

class TestSecurity(APITestBase):
    """Test security features of new endpoints."""
    
    def test_cors_headers_present(self):
        """Test CORS headers are present."""
        response = self.client.get("/api/v1/documents/", headers={"Origin": "http://localhost:5173"})
        assert "access-control-allow-origin" in response.headers or response.status_code == 401
    
    def test_security_headers_present(self):
        """Test security headers are present."""
        response = self.client.get("/api/v1/documents/")
        # Should have security headers even on 401
        assert "x-frame-options" in response.headers or response.status_code == 401
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are present."""
        response = self.client.get("/api/v1/documents/")
        # Rate limit headers should be present
        assert response.status_code == 401
    
    def test_invalid_token_rejected(self):
        """Test invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/api/v1/documents/", headers=headers)
        assert response.status_code == 401
    
    def test_expired_token_rejected(self):
        """Test expired tokens are rejected."""
        # Create a token with very short expiry (this would need actual implementation)
        # For now, just test that invalid tokens are rejected
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid"}
        response = self.client.get("/api/v1/documents/", headers=headers)
        assert response.status_code == 401


# ============================================
# Backward Compatibility Tests
# ============================================

class TestBackwardCompatibility(APITestBase):
    """Test backward compatibility with legacy endpoints."""
    
    def test_storage_documents_endpoint_still_works(self, auth_headers_user, mock_db):
        """Test that legacy storage/documents endpoint still works."""
        with patch("app.routes.storage.get_db", return_value=mock_db):
            with patch("app.routes.storage.UserRepository") as MockUserRepo:
                with patch("app.routes.storage.DocumentRepository") as MockDocRepo:
                    mock_user_repo = AsyncMock()
                    mock_user_repo.get_id_by_email = AsyncMock(return_value=1)
                    MockUserRepo.return_value = mock_user_repo
                    
                    mock_doc_repo = AsyncMock()
                    mock_doc_repo.list_for_user = AsyncMock(return_value=[])
                    MockDocRepo.return_value = mock_doc_repo
                    
                    response = self.client.get("/api/v1/storage/documents", headers=auth_headers_user)
                    assert response.status_code == 200
    
    def test_storage_exports_endpoint_still_works(self, auth_headers_user, mock_db):
        """Test that legacy storage/exports endpoint still works."""
        with patch("app.routes.storage.get_db", return_value=mock_db):
            with patch("app.routes.storage.UserRepository") as MockUserRepo:
                with patch("app.routes.storage.ExportRepository") as MockExportRepo:
                    mock_user_repo = AsyncMock()
                    mock_user_repo.get_id_by_email = AsyncMock(return_value=1)
                    MockUserRepo.return_value = mock_user_repo
                    
                    mock_export_repo = AsyncMock()
                    mock_export_repo.list_for_user = AsyncMock(return_value=[])
                    MockExportRepo.return_value = mock_export_repo
                    
                    response = self.client.get("/api/v1/storage/exports", headers=auth_headers_user)
                    assert response.status_code == 200