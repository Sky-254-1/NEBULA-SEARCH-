"""User management endpoints: profile, preferences, activity, avatar."""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.database.repositories.user import UserRepository
from app.database.repositories.settings import SettingsRepository
from app.database.repositories.search import SearchRepository
from app.services.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/v1/users", tags=["Users"])
settings = get_settings()


# ============================================
# Models
# ============================================

class UserProfile(BaseModel):
    """User profile model."""
    id: int
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool
    two_factor_enabled: bool
    created_at: str
    last_login: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserPreferences(BaseModel):
    """User preferences model."""
    user_id: int
    preferences: Dict[str, Any]
    updated_at: str


class UpdatePreferencesRequest(BaseModel):
    """Update preferences request."""
    preferences: Dict[str, Any]


class ActivityItem(BaseModel):
    """Activity log item."""
    id: int
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: str


class ActivityResponse(BaseModel):
    """Activity response."""
    activities: List[ActivityItem]
    total: int


# ============================================
# Profile Endpoints
# ============================================

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current user's profile."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile(
        id=user["id"],
        email=user["email"],
        role=user["role"],
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        phone_number=user.get("phone_number"),
        avatar_url=user.get("avatar_url"),
        email_verified=user.get("email_verified", False),
        two_factor_enabled=user.get("two_factor_enabled", False),
        created_at=str(user.get("created_at", "")),
        last_login=str(user.get("last_login")) if user.get("last_login") else None
    )


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    body: UpdateProfileRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update user profile."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user
    await users.update_profile(
        user["id"],
        first_name=body.first_name,
        last_name=body.last_name,
        phone_number=body.phone_number
    )
    
    # Fetch updated user
    updated_user = await users.get_by_email(email)
    
    return UserProfile(
        id=updated_user["id"],
        email=updated_user["email"],
        role=updated_user["role"],
        first_name=updated_user.get("first_name"),
        last_name=updated_user.get("last_name"),
        phone_number=updated_user.get("phone_number"),
        avatar_url=updated_user.get("avatar_url"),
        email_verified=updated_user.get("email_verified", False),
        two_factor_enabled=updated_user.get("two_factor_enabled", False),
        created_at=str(updated_user.get("created_at", "")),
        last_login=str(updated_user.get("last_login")) if updated_user.get("last_login") else None
    )


# ============================================
# Preferences Endpoints
# ============================================

@router.get("/preferences", response_model=UserPreferences)
async def get_preferences(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get user preferences."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = SettingsRepository(db)
    prefs = await repo.get_for_user(user["id"])
    
    return UserPreferences(
        user_id=user["id"],
        preferences=prefs or {},
        updated_at=str(datetime.now())
    )


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(
    body: UpdatePreferencesRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update user preferences."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = SettingsRepository(db)
    merged = await repo.upsert(user["id"], body.preferences)
    
    return UserPreferences(
        user_id=user["id"],
        preferences=merged,
        updated_at=str(datetime.now())
    )


# ============================================
# Activity Endpoints
# ============================================

@router.get("/activity", response_model=ActivityResponse)
async def get_activity(
    limit: int = Query(20, ge=1, le=100, description="Number of activities"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get user activity log."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        return ActivityResponse(activities=[], total=0)
    
    # Get search history as activity
    search_repo = SearchRepository(db)
    search_history = await search_repo.recent_for_user(user["id"], limit)
    
    activities = []
    for item in search_history:
        activities.append(ActivityItem(
            id=item.get("id", 0),
            action="search",
            resource_type="query",
            resource_id=None,
            ip_address=None,
            created_at=str(item.get("created_at", ""))
        ))
    
    return ActivityResponse(
        activities=activities[:limit],
        total=len(activities)
    )


# ============================================
# Avatar Endpoints
# ============================================

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upload user avatar."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file
    content = await file.read()
    max_size = 5 * 1024 * 1024  # 5MB
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")
    
    # Save file
    avatar_dir = settings.storage_uploads / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{user['id']}_{datetime.now().timestamp()}.{ext}"
    dest = avatar_dir / filename
    dest.write_bytes(content)
    
    # Update user avatar_url
    avatar_url = f"/uploads/avatars/{filename}"
    await users.update_avatar(user["id"], avatar_url)
    
    return {
        "success": True,
        "data": {
            "avatar_url": avatar_url,
            "message": "Avatar uploaded successfully"
        }
    }


@router.delete("/avatar")
async def delete_avatar(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete user avatar."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove avatar URL from user
    await users.update_avatar(user["id"], None)
    
    return {
        "success": True,
        "data": {
            "message": "Avatar deleted successfully"
        }
    }


# ============================================
# Account Management
# ============================================

@router.delete("/account")
async def delete_account(
    password: str,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete user account."""
    from app.services.auth import verify_password
    from app.database.repositories.session import SessionRepository
    
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    # Soft delete user
    await users.delete(user["id"])
    
    # Delete all sessions
    sessions = SessionRepository(db)
    await sessions.delete_all_for_user(user["id"])
    
    return {
        "success": True,
        "data": {
            "message": "Account deleted successfully"
        }
    }