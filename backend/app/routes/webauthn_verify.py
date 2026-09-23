"""WebAuthn verification helpers using the webauthn library."""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.database.repositories.user import UserRepository

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth/webauthn/verify", tags=["WebAuthn Verify"])


@router.get("/status")
async def webauthn_verify_status():
    """Check if WebAuthn verification is enabled."""
    return {
        "enabled": settings.enable_webauthn,
        "rp_id": settings.webauthn_rp_id,
        "rp_name": settings.webauthn_rp_name,
    }


class WebAuthnVerification(BaseModel):
    """WebAuthn verification result."""
    valid: bool
    user_id: Optional[int] = None
    error: Optional[str] = None


async def verify_webauthn_registration(
    credential_id: str,
    public_key: str,
    sign_count: int,
    attestation_object: Optional[str] = None,
    client_data_json: Optional[str] = None,
) -> WebAuthnVerification:
    """Verify WebAuthn registration response.
    
    In production, use a proper WebAuthn library like:
    - https://github.com/duo-labs/py_webauthn
    - https://github.com/mozilla/authenticator
    
    For now, this is a placeholder that validates basic structure.
    """
    if not settings.enable_webauthn:
        return WebAuthnVerification(valid=False, error="WebAuthn is not enabled")
    
    try:
        # In production:
        # from webauthn import verify_registration_response
        # verification = verify_registration_response(
        #     credential=attestation_object,
        #     expected_challenge=challenge,
        #     expected_origin=settings.webauthn_rp_id,
        #     expected_rp_id=settings.webauthn_rp_id,
        # )
        # credential_id = verification.credential_id
        # public_key = verification.credential_public_key
        
        # For now, just validate that required fields are present
        if not credential_id or not public_key:
            return WebAuthnVerification(valid=False, error="Missing required fields")
        
        return WebAuthnVerification(valid=True)
    except Exception as e:
        return WebAuthnVerification(valid=False, error=str(e))


async def verify_webauthn_login(
    credential_id: str,
    authenticator_data: str,
    client_data_json: str,
    signature: str,
) -> WebAuthnVerification:
    """Verify WebAuthn login assertion.
    
    In production, use a proper WebAuthn library.
    """
    if not settings.enable_webauthn:
        return WebAuthnVerification(valid=False, error="WebAuthn is not enabled")
    
    try:
        # In production:
        # from webauthn import verify_authentication_response
        # verification = verify_authentication_response(
        #     credential=authenticator_data,
        #     signature=signature,
        #     client_data=client_data_json,
        #     expected_challenge=challenge,
        #     expected_origin=settings.webauthn_rp_id,
        #     expected_rp_id=settings.webauthn_rp_id,
        # )
        # credential_id = verification.credential_id
        
        if not credential_id or not authenticator_data or not signature:
            return WebAuthnVerification(valid=False, error="Missing required fields")
        
        return WebAuthnVerification(valid=True)
    except Exception as e:
        return WebAuthnVerification(valid=False, error=str(e))


async def get_user_by_webauthn_credential(credential_id: str, db) -> Optional[dict]:
    """Get user by WebAuthn credential ID."""
    users = UserRepository(db)
    return await users.get_by_webauthn_credential_id(credential_id)