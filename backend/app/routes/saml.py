"""SAML 2.0 SSO authentication routes."""

from typing import Optional
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from app.config import get_settings
from app.database import get_db
from app.database.repositories.user import UserRepository
from app.services.auth import get_current_user

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth/saml", tags=["SAML"])


def _get_saml_auth(request: Request) -> OneLogin_Saml2_Auth:
    """Initialize SAML auth from request."""
    # Extract host and protocol
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("host", request.url.netloc)
    
    # Build SAML request dict
    saml_request = {
        "https": "on" if forwarded_proto == "https" else "off",
        "http_host": host,
        "script_name": request.url.path,
        "get_data": dict(request.query_params),
        "post_data": {},
    }
    
    # SAML configuration
    saml_settings = {
        "strict": True,
        "debug": settings.is_production is False,
        "sp": {
            "entityId": settings.jwt_issuer,
            "assertionConsumerService": {
                "url": f"{settings.jwt_issuer}/api/v1/auth/saml/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": f"{settings.jwt_issuer}/api/v1/auth/saml/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
        },
        "idp": {
            "entityId": settings.saml_entity_id,
            "singleSignOnService": {
                "url": settings.saml_metadata_url.replace("/metadata", "/sso") if settings.saml_metadata_url else "",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": settings.saml_metadata_url.replace("/metadata", "/sls") if settings.saml_metadata_url else "",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": open(settings.saml_cert_path).read() if settings.saml_cert_path else "",
        },
    }
    
    auth = OneLogin_Saml2_Auth(saml_request, saml_settings)
    return auth


@router.get("/login")
async def saml_login(request: Request):
    """Redirect to SAML IdP for login."""
    if not settings.enable_saml:
        raise HTTPException(status_code=404, detail="SAML is not enabled")
    
    auth = _get_saml_auth(request)
    return {"authorization_url": auth.login()}


@router.post("/acs")
async def saml_acs(request: Request, db=Depends(get_db)):
    """Assertion Consumer Service - handle SAML response."""
    if not settings.enable_saml:
        raise HTTPException(status_code=404, detail="SAML is not enabled")
    
    auth = _get_saml_auth(request)
    
    # Process SAML response
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        raise HTTPException(status_code=400, detail=f"SAML errors: {errors}")
    
    # Get user attributes
    attributes = auth.get_attributes()
    email = attributes.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress", [None])[0]
    name = attributes.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name", [None])[0]
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by SAML")
    
    # Find or create user
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        # Create new user from SAML
        from app.services.auth import hash_password
        random_password = secrets.token_urlsafe(32)
        hashed_password = hash_password(random_password)
        await users.create(email, hashed_password, role="user")
        user = await users.get_by_email(email)
    
    # Create tokens
    from app.database.repositories.session import SessionRepository
    from app.services.auth import create_access_token, create_refresh_token, hash_token
    from datetime import datetime, timezone, timedelta
    
    access_token = create_access_token(email, role=user["role"])
    refresh_token = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    
    session_id = str(uuid.uuid4())
    sessions = SessionRepository(db)
    await sessions.create(
        user["id"],
        hash_token(refresh_token),
        expires_at,
        session_id=session_id,
        device_name=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
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


@router.get("/metadata")
async def saml_metadata(request: Request):
    """Serve SAML SP metadata."""
    if not settings.enable_saml:
        raise HTTPException(status_code=404, detail="SAML is not enabled")
    
    auth = _get_saml_auth(request)
    metadata = auth.get_sp_metadata()
    return Response(content=metadata, media_type="application/xml")


@router.post("/logout")
async def saml_logout(request: Request, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Initiate SAML logout."""
    if not settings.enable_saml:
        raise HTTPException(status_code=404, detail="SAML is not enabled")
    
    auth = _get_saml_auth(request)
    return {"logout_url": auth.logout()}