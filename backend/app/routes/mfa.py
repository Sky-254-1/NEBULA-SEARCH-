"""Multi-Factor Authentication routes."""


from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_db
from app.database.repositories.audit import AuditRepository
from app.database.repositories.user import UserRepository
from app.config import get_settings
from app.services.auth import get_current_user
from app.services.mfa import MFAService, enroll_mfa, verify_mfa_token

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth/mfa", tags=["MFA"])


@router.post("/setup")
async def setup_mfa(request: Request, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Setup MFA for current user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if MFA is already enabled
    if user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA is already enabled")
    
    # Generate MFA enrollment
    enrollment = enroll_mfa(email)
    
    # Store temporary secret in cache (will be confirmed in verify step)
    from app.services.cache import cache_service
    cache_key = f"mfa_setup:{email}"
    await cache_service.set(cache_key, enrollment.secret, ttl=600)  # 10 minutes
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "mfa_setup_initiated",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    # Return QR code and backup codes
    import base64
    qr_code_base64 = base64.b64encode(enrollment.qr_code).decode()
    
    return {
        "secret": enrollment.secret,
        "qr_code": f"data:image/png;base64,{qr_code_base64}",
        "backup_codes": enrollment.backup_codes,
        "message": "Scan the QR code with your authenticator app and enter the code to verify"
    }


@router.post("/verify")
async def verify_mfa_setup(
    request: Request,
    token: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Verify MFA setup with token."""
    from app.services.cache import cache_service
    
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get temporary secret from cache
    cache_key = f"mfa_setup:{email}"
    secret = await cache_service.get(cache_key)
    
    if not secret:
        raise HTTPException(status_code=400, detail="MFA setup expired. Please try again.")
    
    # Verify token
    is_valid, error = verify_mfa_token(secret, token)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Generate backup codes
    enrollment = enroll_mfa(email)
    backup_codes_hashed = [MFAService.hash_backup_code(code) for code in enrollment.backup_codes]
    
    # Save MFA settings to user
    await users.update_mfa(
        user_id=user["id"],
        mfa_enabled=True,
        mfa_secret=secret,
        mfa_backup_codes=backup_codes_hashed,
    )
    
    # Clear temporary secret
    await cache_service.delete(cache_key)
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "mfa_enabled",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    # Send notification email
    from app.services.email import email_service
    if email_service.enabled:
        await email_service.send_mfa_enabled_email(email)
    
    return {
        "message": "MFA enabled successfully",
        "backup_codes": enrollment.backup_codes
    }


@router.post("/verify-token")
async def verify_mfa_token_endpoint(
    request: Request,
    token: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Verify MFA token during login."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user or not user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    
    mfa_secret = user.get("mfa_secret")
    if not mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not properly configured")
    
    # Try TOTP token first
    is_valid, error = verify_mfa_token(mfa_secret, token)
    if is_valid:
        # Mark MFA as verified in session
        from app.database.repositories.session import SessionRepository
        SessionRepository(db)
        # Get current session from request
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header[7:]
            from app.services.auth import decode_token
            payload = decode_token(access_token)
            jti = payload.get("jti")
            # Store MFA verification in cache
            from app.services.cache import cache_service
            await cache_service.set(f"mfa_verified:{jti}", True, ttl=settings.jwt_expiry_minutes * 60)
        
        return {"message": "MFA token verified"}
    
    # Try backup code
    backup_codes = user.get("mfa_backup_codes", [])
    for i, backup_hash in enumerate(backup_codes):
        if MFAService.verify_backup_code(token, backup_hash):
            # Remove used backup code
            backup_codes.pop(i)
            await users.update_mfa_backup_codes(user["id"], backup_codes)
            
            if settings.enable_audit_logs:
                audit = AuditRepository(db)
                await audit.create(
                    user["id"],
                    "mfa_backup_code_used",
                    ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
            
            return {"message": "Backup code verified"}
    
    raise HTTPException(status_code=400, detail="Invalid MFA token or backup code")


@router.post("/disable")
async def disable_mfa(
    request: Request,
    password: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Disable MFA for current user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    
    # Verify password
    from app.services.auth import verify_password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    
    # Disable MFA
    await users.disable_mfa(user["id"])
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "mfa_disabled",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "MFA disabled successfully"}


@router.post("/regenerate-backup-codes")
async def regenerate_backup_codes(
    request: Request,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Regenerate backup codes."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user or not user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    
    # Generate new backup codes
    backup_codes = MFAService.generate_backup_codes()
    backup_codes_hashed = [MFAService.hash_backup_code(code) for code in backup_codes]
    
    # Save to database
    await users.update_mfa_backup_codes(user["id"], backup_codes_hashed)
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "mfa_backup_codes_regenerated",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {
        "message": "Backup codes regenerated",
        "backup_codes": backup_codes
    }


@router.post("/verify-login")
async def verify_mfa_login(
    request: Request,
    mfa_pending_token: str,
    token: str,
    db=Depends(get_db)
):
    """Complete MFA verification during login and issue real auth tokens."""
    from app.services.cache import cache_service
    from app.services.auth import create_access_token, create_refresh_token, hash_token
    from app.database.repositories.session import SessionRepository

    # Get pending session
    pending_data = await cache_service.get(f"mfa_pending:{mfa_pending_token}")
    if not pending_data:
        raise HTTPException(status_code=400, detail="MFA session expired. Please log in again.")

    # Get user's MFA secret
    users = UserRepository(db)
    user = await users.get_by_email(pending_data["email"])
    if not user or not user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA is not enabled")

    mfa_secret = user.get("mfa_secret")
    if not mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not properly configured")

    # Verify TOTP token or backup code
    is_valid, error = verify_mfa_token(mfa_secret, token)

    # Try backup code if TOTP fails
    if not is_valid:
        backup_codes = user.get("mfa_backup_codes", [])
        for i, backup_hash in enumerate(backup_codes):
            if MFAService.verify_backup_code(token, backup_hash):
                backup_codes.pop(i)
                await users.update_mfa_backup_codes(user["id"], backup_codes)
                is_valid = True
                break

    if not is_valid:
        raise HTTPException(status_code=400, detail=error or "Invalid verification code")

    # Clear pending token
    await cache_service.delete(f"mfa_pending:{mfa_pending_token}")

    # Issue real tokens
    from datetime import datetime, timedelta, timezone
    import uuid

    ip = request.client.host if request.client else "unknown"
    access_token = create_access_token(pending_data["email"], role=pending_data["role"])
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
        ip_address=ip,
    )

    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "mfa_login_complete",
            metadata={"session_id": session_id},
            ip=ip,
            user_agent=request.headers.get("user-agent"),
        )

    from app.models.schemas import AuthResponse
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expiry_minutes * 60,
    )


@router.get("/status")
async def get_mfa_status(email: str = Depends(get_current_user), db=Depends(get_db)):
    """Get MFA status for current user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "mfa_enabled": user.get("mfa_enabled", False),
        "has_backup_codes": len(user.get("mfa_backup_codes", [])) > 0
    }