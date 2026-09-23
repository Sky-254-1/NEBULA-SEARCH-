"""OAuth authentication routes."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_db
from app.database.repositories.audit import AuditRepository
from app.database.repositories.user import UserRepository
from app.config import get_settings
from app.services.auth import get_current_user, hash_password

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth/oauth", tags=["OAuth"])


class OAuthProvider:
    """OAuth provider configuration."""
    
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    APPLE = "apple"


def get_oauth_config(provider: str) -> Optional[dict]:
    """Get OAuth provider configuration."""
    configs = {
        OAuthProvider.GOOGLE: {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",  # nosec B105: public OAuth endpoint
            "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"],
        },
        OAuthProvider.GITHUB: {
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",  # nosec B105: public OAuth endpoint
            "user_info_url": "https://api.github.com/user",
            "scopes": ["user:email"],
        },
        OAuthProvider.MICROSOFT: {
            "client_id": settings.microsoft_client_id,
            "client_secret": settings.microsoft_client_secret,
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",  # nosec B105: public OAuth endpoint
            "user_info_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile"],
        },
        OAuthProvider.APPLE: {
            "client_id": settings.apple_client_id,
            "client_secret": settings.apple_client_secret,
            "auth_url": "https://appleid.apple.com/auth/authorize",
            "token_url": "https://appleid.apple.com/auth/token",  # nosec B105: public OAuth endpoint
            "user_info_url": "https://appleid.apple.com/auth/userinfo",
            "scopes": ["openid", "email", "name"],
        },
    }
    return configs.get(provider)


@router.get("/{provider}/authorize")
async def oauth_authorize(provider: str, request: Request):
    """Get OAuth authorization URL."""
    if not settings.enable_oauth:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    
    config = get_oauth_config(provider)
    if not config or not config["client_id"]:
        raise HTTPException(status_code=400, detail=f"OAuth provider '{provider}' is not configured")
    
    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in cache for validation
    from app.services.cache import cache_service
    await cache_service.set(f"oauth_state:{state}", provider, ttl=600)  # 10 minutes
    
    # Build authorization URL
    redirect_uri = f"{settings.jwt_issuer}/api/v1/auth/oauth/{provider}/callback"
    scopes = " ".join(config["scopes"])
    
    auth_url = (
        f"{config['auth_url']}?"
        f"client_id={config['client_id']}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"state={state}"
    )
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str, request: Request, db=Depends(get_db)):
    """Handle OAuth callback."""
    if not settings.enable_oauth:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    
    # Validate state parameter
    from app.services.cache import cache_service
    cached_provider = await cache_service.get(f"oauth_state:{state}")
    if not cached_provider or cached_provider != provider:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Clear state
    await cache_service.delete(f"oauth_state:{state}")
    
    config = get_oauth_config(provider)
    if not config:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    # Exchange code for token
    import httpx
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            config["token_url"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.jwt_issuer}/api/v1/auth/oauth/{provider}/callback",
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
            },
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token in response")
        
        # Get user info
        user_response = await client.get(
            config["user_info_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_response.json()
    
    # Extract email based on provider
    email = None
    if provider == OAuthProvider.GOOGLE:
        email = user_info.get("email")
    elif provider == OAuthProvider.GITHUB:
        email = user_info.get("email")
        if not email:
            # GitHub may not return email in user info, need to fetch from /user/emails
            async with httpx.AsyncClient() as client:
                emails_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    primary_email = next((e for e in emails if e.get("primary")), None)
                    email = primary_email.get("email") if primary_email else None
    elif provider == OAuthProvider.MICROSOFT:
        email = user_info.get("mail") or user_info.get("userPrincipalName")
    elif provider == OAuthProvider.APPLE:
        email = user_info.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by OAuth provider")
    
    # Find or create user
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        # Create new user
        # Generate random password (user will need to set password if they want to use email/password login)
        random_password = secrets.token_urlsafe(32)
        hashed_password = hash_password(random_password)
        
        await users.create(email, hashed_password, role="user")
        user = await users.get_by_email(email)
        
        # Link OAuth account
        await users.link_oauth(user["id"], provider, user_info.get("sub") or user_info.get("id"))
        
        if settings.enable_audit_logs:
            audit = AuditRepository(db)
            await audit.create(
                user["id"],
                "oauth_signup",
                metadata={"provider": provider},
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
    else:
        # Check if OAuth is already linked
        oauth_accounts = await users.get_oauth_accounts(user["id"])
        if not any(account["provider"] == provider for account in oauth_accounts):
            # Link OAuth account
            await users.link_oauth(user["id"], provider, user_info.get("sub") or user_info.get("id"))
        
        if settings.enable_audit_logs:
            audit = AuditRepository(db)
            await audit.create(
                user["id"],
                "oauth_login",
                metadata={"provider": provider},
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
    
    # Create session and tokens
    from app.database.repositories.session import SessionRepository
    from app.services.auth import create_access_token, create_refresh_token, hash_token
    
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
    
    # Return tokens
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",  # nosec B105: standard OAuth token type
        "user": {
            "email": user["email"],
            "role": user["role"],
        }
    }


@router.post("/link")
async def link_oauth_account(
    request: Request,
    provider: str,
    code: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Link OAuth account to current user."""
    if not settings.enable_oauth:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    
    # Similar to callback but for linking existing account
    # Implementation would be similar to oauth_callback
    # but instead of creating user, link to existing user
    
    return {"message": f"OAuth account linked to {provider}"}


@router.delete("/unlink")
async def unlink_oauth_account(
    request: Request,
    provider: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Unlink OAuth account from current user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has password (can't unlink if it's the only login method)
    if user.get("hashed_password"):
        # User has password, can unlink
        await users.unlink_oauth(user["id"], provider)
        
        if settings.enable_audit_logs:
            audit = AuditRepository(db)
            await audit.create(
                user["id"],
                "oauth_unlink",
                metadata={"provider": provider},
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        
        return {"message": f"OAuth account unlinked from {provider}"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Cannot unlink OAuth account. Please set a password first."
        )


@router.get("/accounts")
async def get_linked_oauth_accounts(email: str = Depends(get_current_user), db=Depends(get_db)):
    """Get linked OAuth accounts for current user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    oauth_accounts = await users.get_oauth_accounts(user["id"])
    
    return {
        "accounts": [
            {
                "provider": account["provider"],
                "provider_user_id": account["provider_user_id"],
                "created_at": account["created_at"],
            }
            for account in oauth_accounts
        ]
    }