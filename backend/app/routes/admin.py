"""Admin-only routes for system management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.database.repositories.audit import AuditRepository
from app.database.repositories.document import DocumentRepository
from app.database.repositories.search import SearchRepository
from app.database.repositories.session import SessionRepository
from app.database.repositories.user import UserRepository
from app.config import get_settings
from app.models.schemas import PaginationMeta
from app.services.auth import require_admin
from app.services.cache import cache_service
from app.services.queue import job_queue
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# ============================================
# Models
# ============================================

class UserManagementResponse(BaseModel):
    """User management response."""
    id: int
    email: str
    role: str
    email_verified: bool
    created_at: str
    last_login: Optional[str] = None
    is_active: bool


class UserListResponse(BaseModel):
    """User list response."""
    users: List[UserManagementResponse]
    pagination: PaginationMeta


class SystemStatsResponse(BaseModel):
    """System statistics response."""
    total_users: int
    active_users: int
    total_documents: int
    total_searches: int
    cache_hit_ratio: float
    uptime_seconds: float
    queue_size: int
    database_size_mb: float


class QueueStatsResponse(BaseModel):
    """Queue statistics response."""
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    queue_type: str  # "redis" or "memory"


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    connected: bool
    hit_ratio: float
    memory_usage_mb: float
    keys_count: int


# ============================================
# User Management
# ============================================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by email"),
    _admin=Depends(require_admin),
    db=Depends(get_db),
):
    """List all users with pagination and filtering."""
    users_repo = UserRepository(db)
    
    # Get all users (in production, add filtering and pagination to repository)
    # For now, we'll get all and filter in memory
    all_users = await users_repo.list_all()
    
    # Apply filters
    filtered_users = all_users
    if role:
        filtered_users = [u for u in filtered_users if u.get("role") == role]
    if search:
        filtered_users = [u for u in filtered_users if search.lower() in u.get("email", "").lower()]
    
    # Apply pagination
    total = len(filtered_users)
    start_idx = pagination.offset
    end_idx = start_idx + pagination.limit
    paginated_users = filtered_users[start_idx:end_idx]
    
    # Create pagination metadata
    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        has_next=pagination.page < (total + pagination.page_size - 1) // pagination.page_size,
        has_previous=pagination.page > 1,
    )
    
    return UserListResponse(
        users=[
            UserManagementResponse(
                id=u["id"],
                email=u["email"],
                role=u.get("role", "user"),
                email_verified=u.get("email_verified", False),
                created_at=str(u.get("created_at", "")),
                last_login=str(u.get("last_login")) if u.get("last_login") else None,
                is_active=u.get("is_active", True),
            )
            for u in paginated_users
        ],
        pagination=pagination_meta,
    )


@router.get("/users/{user_id}", response_model=UserManagementResponse)
async def get_user(user_id: int, _admin=Depends(require_admin), db=Depends(get_db)):
    """Get detailed user information."""
    users_repo = UserRepository(db)
    user = await users_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserManagementResponse(
        id=user["id"],
        email=user["email"],
        role=user.get("role", "user"),
        email_verified=user.get("email_verified", False),
        created_at=str(user.get("created_at", "")),
        last_login=str(user.get("last_login")) if user.get("last_login") else None,
        is_active=user.get("is_active", True),
    )


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: int, role: str, _admin=Depends(require_admin), db=Depends(get_db)):
    """Update user role."""
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'admin'")
    
    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await users.update_role(user_id, role)
    return {"message": f"User {user_id} role updated to {role}"}


@router.post("/users/{user_id}/activate")
async def activate_user(user_id: int, _admin=Depends(require_admin), db=Depends(get_db)):
    """Activate a user account."""
    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await users.update_status(user_id, is_active=True)
    return {"message": f"User {user_id} activated"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: int, _admin=Depends(require_admin), db=Depends(get_db)):
    """Deactivate a user account."""
    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await users.update_status(user_id, is_active=False)
    return {"message": f"User {user_id} deactivated"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, _admin=Depends(require_admin), db=Depends(get_db)):
    """Delete a user account."""
    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await users.delete(user_id)
    return {"message": f"User {user_id} deleted"}


# ============================================
# System Statistics
# ============================================

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(_admin=Depends(require_admin), db=Depends(get_db)):
    """Get comprehensive system statistics."""
    users_repo = UserRepository(db)
    docs_repo = DocumentRepository(db)
    search_repo = SearchRepository(db)

    # Get user stats
    total_users = await users_repo.count_all()
    active_users = total_users  # Simplified; in production, query active count separately

    total_documents = await docs_repo.count_all()
    total_searches = await search_repo.count_all()
    
    # Get cache stats
    cache_stats = await cache_service.get_stats()
    
    # Get queue stats
    queue_size = job_queue._redis.qsize() if job_queue._redis else 0
    
    # Calculate uptime (simplified - in production, track actual start time)
    import time
    from app.main import app as main_app
    uptime_seconds = time.time() - main_app.state.start_time if hasattr(main_app.state, 'start_time') else 0
    
    return SystemStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_documents=total_documents,
        total_searches=total_searches,
        cache_hit_ratio=cache_stats.get("hit_ratio", 0.0),
        uptime_seconds=uptime_seconds,
        queue_size=queue_size,
        database_size_mb=_database_size_mb(),
    )


def _database_size_mb() -> float:
    """Estimate SQLite database size; returns 0 for PostgreSQL (use pg metrics)."""
    from pathlib import Path

    settings = get_settings()
    if settings.uses_postgres:
        return 0.0
    db_path = Path(settings.db_path)
    if db_path.exists():
        return round(db_path.stat().st_size / (1024 * 1024), 2)
    return 0.0


# ============================================
# Queue Management
# ============================================

@router.get("/queue", response_model=QueueStatsResponse)
async def get_queue_stats(_admin=Depends(require_admin)):
    """Get job queue statistics."""
    if job_queue._redis:
        # Redis queue stats
        pending = await job_queue._redis.llen("queue:pending")
        processing = await job_queue._redis.llen("queue:processing")
        completed = await job_queue._redis.llen("queue:completed")
        failed = await job_queue._redis.llen("queue:failed")
        queue_type = "redis"
    else:
        # In-memory queue stats
        pending = len(job_queue._queue)
        processing = 0
        completed = 0
        failed = 0
        queue_type = "memory"
    
    return QueueStatsResponse(
        pending_jobs=pending,
        processing_jobs=processing,
        completed_jobs=completed,
        failed_jobs=failed,
        queue_type=queue_type,
    )


@router.post("/queue/clear")
async def clear_queue(_admin=Depends(require_admin)):
    """Clear all jobs from the queue."""
    if job_queue._redis:
        await job_queue._redis.delete("queue:pending", "queue:processing", "queue:completed", "queue:failed")
    else:
        job_queue._queue.clear()
    
    return {"message": "Queue cleared"}


@router.post("/queue/pause")
async def pause_queue(_admin=Depends(require_admin)):
    """Pause job processing."""
    job_queue._paused = True
    return {"message": "Queue paused"}


@router.post("/queue/resume")
async def resume_queue(_admin=Depends(require_admin)):
    """Resume job processing."""
    job_queue._paused = False
    return {"message": "Queue resumed"}


# ============================================
# Cache Management
# ============================================

@router.get("/cache", response_model=CacheStatsResponse)
async def get_cache_stats(_admin=Depends(require_admin)):
    """Get cache statistics."""
    stats = await cache_service.get_stats()
    return CacheStatsResponse(
        connected=stats.get("connected", False),
        hit_ratio=stats.get("hit_ratio", 0.0),
        memory_usage_mb=stats.get("memory_usage_mb", 0.0),
        keys_count=stats.get("keys_count", 0),
    )


@router.post("/cache/clear")
async def clear_cache(_admin=Depends(require_admin)):
    """Clear all cache entries."""
    await cache_service.clear()
    return {"message": "Cache cleared"}


@router.post("/cache/invalidate/{key_pattern}")
async def invalidate_cache_pattern(key_pattern: str, _admin=Depends(require_admin)):
    """Invalidate cache entries matching a pattern."""
    await cache_service.invalidate_pattern(key_pattern)
    return {"message": f"Cache entries matching '{key_pattern}' invalidated"}


# ============================================
# Audit Logs
# ============================================

@router.get("/audit-logs")
async def get_audit_logs(
    pagination: PaginationParams = Depends(),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    limit: int = Query(100, ge=1, le=1000),
    _admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Get audit logs with pagination and filtering."""
    audit = AuditRepository(db)
    
    # Get logs (in production, add filtering and pagination to repository)
    logs = await audit.get_recent(limit=limit)
    
    # Apply filters
    if user_id:
        logs = [log for log in logs if log.get("user_id") == user_id]
    if action:
        logs = [log for log in logs if log.get("action") == action]
    
    # Apply pagination
    total = len(logs)
    start_idx = pagination.offset
    end_idx = start_idx + pagination.limit
    paginated_logs = logs[start_idx:end_idx]
    
    # Create pagination metadata
    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        has_next=pagination.page < (total + pagination.page_size - 1) // pagination.page_size,
        has_previous=pagination.page > 1,
    )
    
    return {
        "logs": paginated_logs,
        "pagination": pagination_meta,
    }


# ============================================
# Session Management
# ============================================

@router.get("/sessions")
async def list_active_sessions(
    pagination: PaginationParams = Depends(),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    _admin=Depends(require_admin),
    db=Depends(get_db),
):
    """List all active sessions."""
    SessionRepository(db)
    
    # Get all sessions (in production, add filtering and pagination)
    # For now, return placeholder
    sessions = []
    total = 0
    
    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=0,
        has_next=False,
        has_previous=False,
    )
    
    return {
        "sessions": sessions,
        "pagination": pagination_meta,
    }


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(session_id: str, reason: str = "Revoked by administrator", _admin=Depends(require_admin), db=Depends(get_db)):
    """Revoke a user session."""
    sessions = SessionRepository(db)
    await sessions.revoke_session_family(session_id, reason)
    return {"message": f"Session family {session_id} revoked"}
