"""
Regression tests for MFA Login Response Validation.

Validates that:
1. Login for user without MFA returns valid AuthResponse with mfa_required=False and tokens.
2. Login for MFA-enabled user returns valid MFAChallengeResponse with mfa_required=True and pending token.
3. Both response types pass FastAPI response-model validation.
4. MFA challenge response does NOT contain access_token or refresh_token.
5. MFA pending token is rejected by protected endpoints as an access token or refresh token.
6. Successful MFA verification issues real auth tokens and clears the pending session.
7. Invalid or expired MFA challenges are rejected safely with status 400.
8. Pydantic schema discriminated union correctly distinguishes both response models.
"""

import asyncio
import pyotp
import pytest
from pydantic import TypeAdapter, ValidationError

from app.database import get_db
from app.database.repositories.user import UserRepository
from app.models.schemas import (
    AuthResponse,
    AuthSuccessResponse,
    LoginResponse,
    MFAChallengeResponse,
    MFALoginVerifyRequest,
    MFARequiredResponse,
)
from app.services.mfa import MFAService


class TestSchemaValidation:
    """Unit tests for Pydantic schema validation and discriminated union."""

    def test_auth_response_defaults(self):
        """AuthResponse defaults mfa_required to False."""
        resp = AuthResponse(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=1800,
        )
        assert resp.mfa_required is False
        assert resp.access_token == "test_access_token"
        assert resp.refresh_token == "test_refresh_token"
        assert resp.token_type == "bearer"
        assert resp.expires_in == 1800

    def test_mfa_challenge_response_defaults(self):
        """MFAChallengeResponse defaults mfa_required to True and has no tokens."""
        resp = MFAChallengeResponse(
            mfa_pending_token="sample_pending_token_32chars_long",
        )
        assert resp.mfa_required is True
        assert resp.mfa_pending_token == "sample_pending_token_32chars_long"
        assert resp.message == "MFA verification required"
        assert not hasattr(resp, "access_token")
        assert not hasattr(resp, "refresh_token")

    def test_login_response_discriminated_union_success(self):
        """TypeAdapter(LoginResponse) resolves AuthResponse when mfa_required=False."""
        adapter = TypeAdapter(LoginResponse)
        parsed = adapter.validate_python({
            "mfa_required": False,
            "access_token": "acc123",
            "refresh_token": "ref123",
            "token_type": "bearer",
            "expires_in": 1800,
        })
        assert isinstance(parsed, AuthResponse)
        assert parsed.mfa_required is False
        assert parsed.access_token == "acc123"

    def test_login_response_discriminated_union_mfa_required(self):
        """TypeAdapter(LoginResponse) resolves MFAChallengeResponse when mfa_required=True."""
        adapter = TypeAdapter(LoginResponse)
        parsed = adapter.validate_python({
            "mfa_required": True,
            "mfa_pending_token": "pending_xyz",
            "message": "MFA verification required",
        })
        assert isinstance(parsed, MFAChallengeResponse)
        assert parsed.mfa_required is True
        assert parsed.mfa_pending_token == "pending_xyz"

    def test_login_response_rejects_missing_mfa_pending_token(self):
        """When mfa_required=True, missing mfa_pending_token raises ValidationError."""
        adapter = TypeAdapter(LoginResponse)
        with pytest.raises(ValidationError):
            adapter.validate_python({
                "mfa_required": True,
                "message": "MFA verification required",
            })

    def test_login_response_rejects_missing_tokens_when_mfa_false(self):
        """When mfa_required=False, missing access_token raises ValidationError."""
        adapter = TypeAdapter(LoginResponse)
        with pytest.raises(ValidationError):
            adapter.validate_python({
                "mfa_required": False,
                "expires_in": 1800,
            })


class TestMFALoginEndpointFlow:
    """Integration tests for /api/v1/auth/login and MFA challenge validation."""

    @pytest.fixture(autouse=True)
    def _bind_client(self, client):
        self.client = client

    def test_login_user_without_mfa_success(self):
        """Login for user without MFA returns HTTP 200 with tokens and mfa_required=False."""
        email = "user_no_mfa@example.com"
        password = "Password123!"

        # Create user
        signup_res = self.client.post("/api/v1/auth/signup", json={"email": email, "password": password})
        assert signup_res.status_code in (201, 409)

        # Login
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_res.status_code == 200

        data = login_res.json()
        assert data.get("mfa_required") is False
        assert "access_token" in data and len(data["access_token"]) > 0
        assert "refresh_token" in data and len(data["refresh_token"]) > 0
        assert data.get("token_type") == "bearer"
        assert data.get("expires_in") == 1800

    def test_login_mfa_enabled_user_challenge(self):
        """Login for MFA-enabled user returns HTTP 200 with mfa_required=True and NO tokens."""
        email = "user_with_mfa@example.com"
        password = "Password123!"

        # Create user
        signup_res = self.client.post("/api/v1/auth/signup", json={"email": email, "password": password})
        assert signup_res.status_code in (201, 409)

        # Enable MFA on the user record in database
        async def _enable_mfa():
            from app.database.engine import connect
            db = await connect()
            try:
                users = UserRepository(db)
                user = await users.get_by_email(email)
                secret = MFAService.generate_secret()
                backup_codes = MFAService.generate_backup_codes()
                hashed_backups = [MFAService.hash_backup_code(c) for c in backup_codes]
                await users.update_mfa(
                    user_id=user["id"],
                    mfa_enabled=True,
                    mfa_secret=secret,
                    mfa_backup_codes=hashed_backups,
                )
                return secret, backup_codes
            finally:
                await db.close()

        secret, backup_codes = asyncio.run(_enable_mfa())

        # Attempt Login — must return MFA challenge, NOT 500 error!
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_res.status_code == 200, f"Expected 200 OK, got {login_res.status_code}: {login_res.text}"

        data = login_res.json()

        # Contract assertions
        assert data.get("mfa_required") is True
        assert "mfa_pending_token" in data
        assert len(data["mfa_pending_token"]) > 20
        assert data.get("message") == "MFA verification required"

        # Security assertion: NO authentication tokens issued yet
        assert "access_token" not in data or data["access_token"] is None
        assert "refresh_token" not in data or data["refresh_token"] is None

        # Verify mfa_pending_token is REJECTED by protected endpoints as Bearer token
        mfa_pending_token = data["mfa_pending_token"]
        auth_me_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {mfa_pending_token}"},
        )
        assert auth_me_res.status_code == 401

        # Verify mfa_pending_token is REJECTED as a refresh token
        refresh_res = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": mfa_pending_token},
        )
        assert refresh_res.status_code == 401

        # Complete MFA Login with valid TOTP code
        totp = pyotp.TOTP(secret)
        valid_totp = totp.now()

        # Verify via JSON body (MFALoginVerifyRequest)
        verify_res = self.client.post(
            "/api/v1/auth/mfa/verify-login",
            json={"mfa_pending_token": mfa_pending_token, "token": valid_totp},
        )
        assert verify_res.status_code == 200, f"Verification failed: {verify_res.text}"
        auth_data = verify_res.json()

        assert auth_data.get("mfa_required") is False
        assert "access_token" in auth_data and len(auth_data["access_token"]) > 0
        assert "refresh_token" in auth_data and len(auth_data["refresh_token"]) > 0

        # Verify the newly issued access_token now accesses protected endpoints
        me_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        assert me_res.status_code == 200
        assert me_res.json().get("email") == email

        # Verify pending token was invalidated and cannot be replayed
        replay_res = self.client.post(
            "/api/v1/auth/mfa/verify-login",
            json={"mfa_pending_token": mfa_pending_token, "token": valid_totp},
        )
        assert replay_res.status_code == 400

    def test_mfa_login_verify_invalid_code_rejected(self):
        """Submitting an invalid code returns 400 without issuing tokens."""
        email = "mfa_invalid_code@example.com"
        password = "Password123!"

        # Create user
        signup_res = self.client.post("/api/v1/auth/signup", json={"email": email, "password": password})
        assert signup_res.status_code in (201, 409)

        # Enable MFA
        async def _enable_mfa():
            from app.database.engine import connect
            db = await connect()
            try:
                users = UserRepository(db)
                user = await users.get_by_email(email)
                secret = MFAService.generate_secret()
                await users.update_mfa(user_id=user["id"], mfa_enabled=True, mfa_secret=secret)
            finally:
                await db.close()

        asyncio.run(_enable_mfa())

        # Trigger login to receive pending token
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_res.status_code == 200
        pending_token = login_res.json()["mfa_pending_token"]

        # Submit invalid 6-digit code
        verify_res = self.client.post(
            "/api/v1/auth/mfa/verify-login",
            json={"mfa_pending_token": pending_token, "token": "000000"},
        )
        assert verify_res.status_code == 400
        assert "Invalid verification code" in verify_res.json().get("detail", "")

    def test_mfa_login_verify_expired_or_unknown_pending_token(self):
        """Submitting a non-existent or expired pending token returns 400."""
        verify_res = self.client.post(
            "/api/v1/auth/mfa/verify-login",
            json={"mfa_pending_token": "non_existent_token_12345678", "token": "123456"},
        )
        assert verify_res.status_code == 400
        assert "MFA session expired" in verify_res.json().get("detail", "")
