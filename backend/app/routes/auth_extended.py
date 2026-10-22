"""Extended authentication routes: email verification, password reset, account management."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_db
from app.database.repositories.audit import AuditRepository
from app.database.repositories.session import SessionRepository
from app.database.repositories.user import UserRepository
from app.database.repositories.verification import EmailVerificationRepository, PasswordResetRepository
from app.models.schemas import AuthRequest
from app.config import get_settings
from app.services.auth import get_current_user, hash_password, hash_token, verify_password, validate_password
from app.services.email import email_service

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["Auth Extended"])


# ============================================
# Email Verification
# ============================================

@router.get("/verify-email")
async def verify_email(request: Request, token: str, db=Depends(get_db)):
    """Verify email address using token."""
    token_hash = hash_token(token)
    verification_repo = EmailVerificationRepository(db)
    verification = await verification_repo.get_by_token_hash(token_hash)
    
    if not verification:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(str(verification["expires_at"]).replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification token has expired")
    
    # Mark token as used
    await verification_repo.mark_as_used(verification["id"])
    
    users = UserRepository(db)
    
    # If this verification has a pending email change, apply it
    if verification.get("pending_email"):
        await users.update_email(verification["user_id"], verification["pending_email"])
    else:
        # Standard verification: update email_verified status
        await users.update_email_verified(verification["user_id"], True)
    
    # Invalidate any other unused tokens for this user
    await verification_repo.invalidate_user_tokens(verification["user_id"])
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            verification["user_id"],
            "email_verification",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(request: Request, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Resend email verification link."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("email_verified"):
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Create new verification token
    verification_token = secrets.token_urlsafe(32)
    token_hash = hash_token(verification_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_expiry_hours)
    
    verification_repo = EmailVerificationRepository(db)
    await verification_repo.create(user["id"], token_hash, expires_at)
    
    # Send verification email
    if email_service.enabled:
        verification_link = f"{settings.jwt_issuer}/verify-email?token={verification_token}"
        await email_service.send_verification_email(email, verification_link)
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "resend_verification",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "Verification email sent"}


# ============================================
# Password Reset
# ============================================

@router.post("/forgot-password")
async def forgot_password(request: Request, body: AuthRequest, db=Depends(get_db)):
    """Request password reset link."""
    users = UserRepository(db)
    user = await users.get_by_email(str(body.email))
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If an account exists, a reset link has been sent"}
    
    # Create password reset token
    reset_token = secrets.token_urlsafe(32)
    token_hash = hash_token(reset_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.password_reset_expiry_hours)
    
    reset_repo = PasswordResetRepository(db)
    await reset_repo.create(
        user["id"],
        token_hash,
        expires_at,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    # Send reset email
    if email_service.enabled:
        reset_link = f"{settings.jwt_issuer}/reset-password?token={reset_token}"
        await email_service.send_password_reset_email(str(body.email), reset_link)
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "forgot_password",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "If an account exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: Request, token: str, new_password: str, db=Depends(get_db)):
    """Reset password using token."""
    # Validate new password
    validate_password(new_password)
    
    token_hash = hash_token(token)
    reset_repo = PasswordResetRepository(db)
    reset_token = await reset_repo.get_by_token_hash(token_hash)
    
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(str(reset_token["expires_at"]).replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Mark token as used
    await reset_repo.mark_as_used(reset_token["id"])
    
    # Update password
    users = UserRepository(db)
    hashed_password = hash_password(new_password)
    await users.update_password(reset_token["user_id"], hashed_password)
    
    # Invalidate all user sessions (force re-login)
    sessions = SessionRepository(db)
    await sessions.delete_all_for_user(reset_token["user_id"])
    
    # Invalidate any other unused reset tokens
    await reset_repo.invalidate_user_tokens(reset_token["user_id"])
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            reset_token["user_id"],
            "password_reset",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "Password reset successful. Please log in with your new password."}


# ============================================
# Account Management
# ============================================

@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Change password for authenticated user."""
    # Validate new password
    validate_password(new_password, email)
    
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    hashed_password = hash_password(new_password)
    await users.update_password(user["id"], hashed_password)
    
    # Invalidate all sessions (force re-login)
    sessions = SessionRepository(db)
    await sessions.delete_all_for_user(user["id"])
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "change_password",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "Password changed successfully. Please log in again."}


@router.post("/change-email")
async def change_email(
    request: Request,
    new_email: str,
    password: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Change email address for authenticated user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    
    # Check if new email is already taken
    existing = await users.get_by_email(new_email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Create email verification token for new email
    verification_token = secrets.token_urlsafe(32)
    token_hash = hash_token(verification_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_expiry_hours)
    
    verification_repo = EmailVerificationRepository(db)
    await verification_repo.create(
        user["id"],
        token_hash,
        expires_at,
        pending_email=new_email,  # Store pending email
    )
    
    # Send verification email to new address
    if email_service.enabled:
        verification_link = f"{settings.jwt_issuer}/verify-email?token={verification_token}"
        await email_service.send_verification_email(new_email, verification_link)
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "change_email",
            metadata={"new_email": new_email},
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "Verification email sent to new address. Please verify to complete the change."}


@router.delete("/account")
async def delete_account(
    request: Request,
    password: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Delete user account."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    
    # Soft delete user
    await users.delete(user["id"])
    
    # Delete all sessions
    sessions = SessionRepository(db)
    await sessions.delete_all_for_user(user["id"])
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "account_deletion",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "Account deleted successfully"}


# ============================================
# Session Management
# ============================================

@router.get("/sessions")
async def get_sessions(email: str = Depends(get_current_user), db=Depends(get_db)):
    """Get all active sessions for current user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = SessionRepository(db)
    active_sessions = await sessions.get_active_for_user(user["id"])
    
    return {
        "sessions": [
            {
                "session_id": s["session_id"],
                "device_name": s.get("device_name"),
                "ip_address": s.get("ip_address"),
                "created_at": s.get("created_at"),
                "last_activity_at": s.get("last_activity_at"),
                "expires_at": s.get("expires_at"),
            }
            for s in active_sessions
        ]
    }


@router.delete("/sessions/{session_id}")
async def terminate_session(
    request: Request,
    session_id: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Terminate a specific session."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = SessionRepository(db)
    session = await sessions.get_by_session_id(session_id)
    
    if not session or session["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await sessions.delete_by_session_id(session_id)
    
    if settings.enable_audit_logs:
        audit = AuditRepository(db)
        await audit.create(
            user["id"],
            "session_termination",
            metadata={"session_id": session_id},
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    
    return {"message": "Session terminated"}