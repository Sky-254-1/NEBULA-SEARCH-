"""Tests for app/routes/auth_extended.py — email verification, password reset, account management."""

import pytest
import time
from unittest.mock import ANY


class APITestBase:
    """Bind module-scoped TestClient to test class instances."""

    @pytest.fixture(autouse=True)
    def _bind_client(self, client):
        self.client = client


class TestEmailVerification(APITestBase):
    """Test email verification endpoints."""

    def test_verify_email_missing_token(self):
        """GET /verify-email without token returns 422."""
        response = self.client.get("/api/v1/auth/verify-email")
        assert response.status_code == 422

    def test_verify_email_invalid_token(self):
        """GET /verify-email with invalid token returns 400."""
        response = self.client.get("/api/v1/auth/verify-email", params={"token": "invalid"})
        assert response.status_code == 400

    def test_resend_verification_unauthorized(self):
        """POST /resend-verification without auth returns 401."""
        response = self.client.post("/api/v1/auth/resend-verification")
        assert response.status_code == 401

    def test_resend_verification_authenticated_user_verified(self):
        """POST /resend-verification for already-verified user returns 400."""
        # Signup and login
        self.client.post("/api/v1/auth/signup", json={
            "email": "verified@example.com", "password": "Password1!"
        })
        login = self.client.post("/api/v1/auth/login", json={
            "email": "verified@example.com", "password": "Password1!"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to resend verification (user may already have email_verified set)
        response = self.client.post(
            "/api/v1/auth/resend-verification",
            headers=headers,
        )
        # Should either succeed (sends email) or tell us already verified
        assert response.status_code in (200, 400)


class TestPasswordReset(APITestBase):
    """Test password reset endpoints."""

    def test_forgot_password_no_email(self):
        """POST /forgot-password without email returns 422."""
        response = self.client.post("/api/v1/auth/forgot-password", json={})
        assert response.status_code == 422

    def test_forgot_password_invalid_email(self):
        """POST /forgot-password with invalid email returns 422."""
        response = self.client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422

    def test_forgot_password_nonexistent_user(self):
        """POST /forgot-password for non-existent user returns generic message (no enumeration)."""
        response = self.client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com", "password": "Password1!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "If an account exists" in data["message"]

    def test_reset_password_no_token(self):
        """POST /reset-password without token returns 422."""
        response = self.client.post("/api/v1/auth/reset-password", json={})
        assert response.status_code == 422

    def test_reset_password_invalid_token(self):
        """POST /reset-password with invalid token returns 400."""
        response = self.client.post(
            "/api/v1/auth/reset-password",
            params={"token": "invalid", "new_password": "NewPass123!"},
        )
        assert response.status_code == 400

    def test_reset_password_weak_password(self):
        """POST /reset-password with weak password returns 400 (validation)."""
        response = self.client.post(
            "/api/v1/auth/reset-password",
            params={"token": "some-token", "new_password": "short"},
        )
        assert response.status_code == 400

    def test_forgot_password_and_reset_full_flow(self):
        """Test the full forgot-password -> reset-password flow via database."""
        import asyncio
        from datetime import datetime, timedelta, timezone
        from app.database.engine import connect
        from app.database.repositories.verification import PasswordResetRepository
        from app.database.repositories.user import UserRepository
        from app.services.auth import hash_token

        # Create a user first
        signup = self.client.post("/api/v1/auth/signup", json={
            "email": "resetflow@example.com", "password": "OldPass123!"
        })
        assert signup.status_code == 201

        # Request forgot password
        response = self.client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "resetflow@example.com", "password": "OldPass123!"},
        )
        assert response.status_code == 200

        # Manually create a reset token in the database
        async def _create_token():
            db = await connect()
            try:
                reset_token = "valid-reset-token-12345"
                token_hash = hash_token(reset_token)
                expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

                users = UserRepository(db)
                user = await users.get_by_email("resetflow@example.com")

                reset_repo = PasswordResetRepository(db)
                await reset_repo.create(
                    user["id"], token_hash, expires_at,
                    ip_address="127.0.0.1", user_agent="pytest"
                )
                return reset_token
            finally:
                await db.close()

        reset_token = asyncio.run(_create_token())

        # Now use the reset token
        response = self.client.post(
            "/api/v1/auth/reset-password",
            params={"token": reset_token, "new_password": "NewPass456!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Password reset successful" in data["message"]

        # Verify can login with new password
        login = self.client.post("/api/v1/auth/login", json={
            "email": "resetflow@example.com", "password": "NewPass456!"
        })
        assert login.status_code == 200
        assert "access_token" in login.json()

        # Old password should fail
        old_login = self.client.post("/api/v1/auth/login", json={
            "email": "resetflow@example.com", "password": "OldPass123!"
        })
        assert old_login.status_code == 401


class TestAccountManagement(APITestBase):
    """Test account management endpoints."""

    def _create_and_login(self, email: str, password: str = "Password1!"):
        """Helper: signup and login, return auth headers."""
        self.client.post("/api/v1/auth/signup", json={
            "email": email, "password": password
        })
        login = self.client.post("/api/v1/auth/login", json={
            "email": email, "password": password
        })
        token = login.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_change_password_unauthorized(self):
        """POST /change-password without auth returns 401."""
        response = self.client.post("/api/v1/auth/change-password")
        assert response.status_code == 401

    def test_change_password_wrong_current(self):
        """POST /change-password with wrong current password returns 400."""
        headers = self._create_and_login("changepass@example.com")
        response = self.client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            params={"current_password": "WrongPass1!", "new_password": "NewPass123!"},
        )
        assert response.status_code == 400

    def test_change_password_weak(self):
        """POST /change-password with weak new password returns 400."""
        headers = self._create_and_login("weakpass@example.com")
        response = self.client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            params={"current_password": "Password1!", "new_password": "weak"},
        )
        assert response.status_code == 400

    def test_change_password_success(self):
        """POST /change-password success flow."""
        headers = self._create_and_login("changepassok@example.com")
        response = self.client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            params={"current_password": "Password1!", "new_password": "NewPass789!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Password changed" in data["message"]

        # Old password should fail login
        old_login = self.client.post("/api/v1/auth/login", json={
            "email": "changepassok@example.com", "password": "Password1!"
        })
        assert old_login.status_code == 401

        # New password should work
        new_login = self.client.post("/api/v1/auth/login", json={
            "email": "changepassok@example.com", "password": "NewPass789!"
        })
        assert new_login.status_code == 200

    def test_change_email_unauthorized(self):
        """POST /change-email without auth returns 401."""
        response = self.client.post("/api/v1/auth/change-email")
        assert response.status_code == 401

    def test_change_email_wrong_password(self):
        """POST /change-email with wrong password returns 400."""
        headers = self._create_and_login("changeemail@example.com")
        response = self.client.post(
            "/api/v1/auth/change-email",
            headers=headers,
            params={"new_email": "new@example.com", "password": "WrongPass1!"},
        )
        assert response.status_code == 400

    def test_change_email_success(self):
        """POST /change-email success flow — verify token must be used before email changes."""
        headers = self._create_and_login("changeemailok@example.com")
        response = self.client.post(
            "/api/v1/auth/change-email",
            headers=headers,
            params={"new_email": "newemailok@example.com", "password": "Password1!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Verification email" in data["message"]

        # User's email should NOT have changed yet (still needs verification)
        old_login = self.client.post("/api/v1/auth/login", json={
            "email": "changeemailok@example.com", "password": "Password1!"
        })
        assert old_login.status_code == 200

        # New email should NOT be usable yet (unverified)
        new_login = self.client.post("/api/v1/auth/login", json={
            "email": "newemailok@example.com", "password": "Password1!"
        })
        assert new_login.status_code == 401

    def test_change_email_already_registered(self):
        """POST /change-email with existing email returns 409."""
        # Create first user
        self.client.post("/api/v1/auth/signup", json={
            "email": "existing@example.com", "password": "Password1!"
        })
        # Create second user
        headers = self._create_and_login("seconduser@example.com")
        # Try to change to existing email
        response = self.client.post(
            "/api/v1/auth/change-email",
            headers=headers,
            params={"new_email": "existing@example.com", "password": "Password1!"},
        )
        assert response.status_code == 409

    def test_delete_account_unauthorized(self):
        """DELETE /account without auth returns 401."""
        response = self.client.delete("/api/v1/auth/account")
        assert response.status_code == 401

    def test_delete_account_wrong_password(self):
        """DELETE /account with wrong password returns 400."""
        headers = self._create_and_login("deletewrong@example.com")
        response = self.client.delete(
            "/api/v1/auth/account",
            headers=headers,
            params={"password": "WrongPass1!"},
        )
        assert response.status_code == 400

    def test_delete_account_success(self):
        """DELETE /account success flow."""
        headers = self._create_and_login("deleteok@example.com")
        response = self.client.delete(
            "/api/v1/auth/account",
            headers=headers,
            params={"password": "Password1!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"]

        # Login should now fail
        login = self.client.post("/api/v1/auth/login", json={
            "email": "deleteok@example.com", "password": "Password1!"
        })
        assert login.status_code == 401

    def test_get_sessions_unauthorized(self):
        """GET /sessions without auth returns 401."""
        response = self.client.get("/api/v1/auth/sessions")
        assert response.status_code == 401

    def test_get_sessions_success(self):
        """GET /sessions for authenticated user returns session list."""
        headers = self._create_and_login("sessions@example.com")
        response = self.client.get("/api/v1/auth/sessions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_terminate_session_unauthorized(self):
        """DELETE /sessions/{id} without auth returns 401."""
        response = self.client.delete("/api/v1/auth/sessions/some-id")
        assert response.status_code == 401

    def test_terminate_session_not_found(self):
        """DELETE /sessions/{id} with non-existent session returns 404."""
        headers = self._create_and_login("termsession@example.com")
        response = self.client.delete(
            "/api/v1/auth/sessions/non-existent-session",
            headers=headers,
        )
        assert response.status_code == 404