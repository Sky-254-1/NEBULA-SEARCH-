"""Auth service unit tests."""

import jwt
import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.services.auth import create_token, decode_token, verify_password, hash_password

settings = get_settings()


def test_password_hash_roundtrip():
    stored = hash_password("secure-pass-123")
    assert verify_password("secure-pass-123", stored)
    assert not verify_password("wrong", stored)


def test_create_and_decode_token():
    token = create_token("user@example.com")
    payload = decode_token(token)
    assert payload["sub"] == "user@example.com"


def test_decode_expired_token():
    import datetime
    from datetime import timezone

    payload = {
        "sub": "user@example.com",
        "iat": datetime.datetime.now(timezone.utc),
        "exp": datetime.datetime.now(timezone.utc) - datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(HTTPException) as exc:
        decode_token(token)
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_decode_invalid_token():
    with pytest.raises(HTTPException) as exc:
        decode_token("not.a.valid.token")
    assert exc.value.status_code == 401
