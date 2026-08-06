"""WebAuthn biometric authentication routes."""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.database.repositories.user import UserRepository
from app.services.auth import get_current_user, hash_token

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth/webauthn", tags=["WebAuthn"])


# ---- Pydantic schemas ----
class WebAuthnRegistrationStart(BaseModel):
    username: str


class WebAuthnRegistrationComplete(BaseModel):
    credential_id: str
    public_key: str
    sign_count: int
    attestation_object: Optional[str] = None
    client_data_json: Optional[str] = None


class WebAuthnLoginStart(BaseModel):
    username: str


class WebAuthnLoginComplete(BaseModel):
    credential_id: str
    authenticator_data: str
    client_data_json: str
    signature: str


# ---- In-memory challenge store (use Redis in production) ----
_challenges: dict[str, dict] = {}


@router.post("/register/start")
async def webauthn_register_start(body: WebAuthnRegistrationStart, db=Depends(get_db)):
    """Start WebAuthn registration - returns challenge."""
    if not settings.enable_webauthn:
        raise HTTPException(status_code=404, detail="WebAuthn is not enabled")
    
    users = UserRepository(db)
    user = await users.get_by_email(body.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate challenge
    challenge = secrets.token_urlsafe(32)
    _challenges[body.username] = {
        "challenge": challenge,
        "type": "registration",
        "created_at": datetime.now(timezone.utc),
    }
    
    return {
        "challenge": challenge,
        "rp": {
            "name": settings.webauthn_rp_name,
            "id": settings.webauthn_rp_id,
        },
        "user": {
            "id": str(user["id"]),
            "name": body.username,
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},   # ES256
            {"type": "public-key", "alg": -257},  # RS256
        ],
    }


@router.post("/register/complete")
async def webauthn_register_complete(body: WebAuthnRegistrationComplete, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Complete WebAuthn registration."""
    if not settings.enable_webauthn:
        raise HTTPException(status_code=404, detail="WebAuthn is not enabled")
    
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    # In production, verify the attestation object and public key
    # For now, store the credential
    await users.update(user["id"], {
        "webauthn_credential_id": body.credential_id,
        "webauthn_public_key": body.public_key,
        "webauthn_sign_count": body.sign_count,
    })
    
    return {"message": "WebAuthn credential registered"}


@router.post("/login/start")
async def webauthn_login_start(body: WebAuthnLoginStart, db=Depends(get_db)):
    """Start WebAuthn login - returns challenge."""
    if not settings.enable_webauthn:
        raise HTTPException(status_code=404, detail="WebAuthn is not enabled")
    
    users = UserRepository(db)
    user = await users.get_by_email(body.username)
    if not user or not user.get("webauthn_credential_id"):
        raise HTTPException(status_code=404, detail="No WebAuthn credential found")
    
    # Generate challenge
    challenge = secrets.token_urlsafe(32)
    _challenges[body.username] = {
        "challenge": challenge,
        "type": "authentication",
        "created_at": datetime.now(timezone.utc),
    }
    
    return {
        "challenge": challenge,
        "rp_id": settings.webauthn_rp_id,
        "credential_id": user["webauthn_credential_id"],
    }


@router.post("/login/complete")
async def webauthn_login_complete(body: WebAuthnLoginComplete, db=Depends(get_db)):
    """Complete WebAuthn login and return JWT tokens."""
    if not settings.enable_webauthn:
        raise HTTPException(status_code=404, detail="WebAuthn is not enabled")
    
    # In production, verify the assertion using the public key
    # For now, find user by credential_id
    users = UserRepository(db)
    user = await users.get_by_webauthn_credential_id(body.credential_id)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credential")
    
    # Create tokens
    from app.database.repositories.session import SessionRepository
    from app.services.auth import create_access_token, create_refresh_token
    from datetime import timezone, timedelta
    
    access_token = create_access_token(user["email"], role=user["role"])
    refresh_token = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    
    session_id = secrets.token_urlsafe(16)
    sessions = SessionRepository(db)
    await sessions.create(
        user["id"],
        hash_token(refresh_token),
        expires_at,
        session_id=session_id,
        device_name="WebAuthn Biometric",
        ip_address=None,
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "role": user["role"],
        }
    }


@router.delete("/credential")
async def webauthn_remove_credential(email: str = Depends(get_current_user), db=Depends(get_db)):
    """Remove WebAuthn credential."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if user:
        await users.update(user["id"], {
            "webauthn_credential_id": None,
            "webauthn_public_key": None,
            "webauthn_sign_count": 0,
        })
    return {"message": "WebAuthn credential removed"}