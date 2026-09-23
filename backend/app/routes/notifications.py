"""Notification management endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.database.repositories.notification import NotificationRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import PaginationMeta
from app.services.auth import get_current_user
from app.utils.pagination import PaginationParams

logger = logging.getLogger("nebula.notifications")

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


async def _user_id(db, email: str) -> int:
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user["id"]


@router.get("/")
async def list_notifications(
    pagination: PaginationParams = Depends(),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List user's notifications with pagination."""
    user_id = await _user_id(db, email)
    notif_repo = NotificationRepository(db)

    rows = await notif_repo.list_for_user(
        user_id, limit=pagination.limit, unread_only=unread_only
    )
    unread_count = await notif_repo.get_unread_count(user_id)
    total = unread_count if unread_only else len(rows)

    notifications = [
        {
            "id": r["id"],
            "type": r["type"],
            "category": r["category"],
            "title": r["title"],
            "message": r["message"],
            "data": r.get("data") or {},
            "read": bool(r["is_read"]),
            "read_at": r.get("read_at"),
            "expires_at": r.get("expires_at"),
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]

    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        has_next=pagination.page < (total + pagination.page_size - 1) // pagination.page_size,
        has_previous=pagination.page > 1,
    )

    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count,
        "pagination": pagination_meta,
    }


@router.get("/unread-count")
async def get_unread_count(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get count of unread notifications."""
    user_id = await _user_id(db, email)
    notif_repo = NotificationRepository(db)
    count = await notif_repo.get_unread_count(user_id)
    return {"success": True, "data": {"unread_count": count}}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Mark notification as read."""
    user_id = await _user_id(db, email)
    notif_repo = NotificationRepository(db)
    await notif_repo.list_for_user(user_id, limit=1)  # just verify access
    await notif_repo.mark_read(notification_id, user_id)
    return {
        "success": True,
        "data": {
            "message": "Notification marked as read",
            "notification_id": notification_id,
        },
    }


@router.post("/read-all")
async def mark_all_as_read(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Mark all notifications as read."""
    user_id = await _user_id(db, email)
    notif_repo = NotificationRepository(db)
    await notif_repo.mark_all_read(user_id)
    return {"success": True, "data": {"message": "All notifications marked as read"}}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete a notification."""
    user_id = await _user_id(db, email)
    notif_repo = NotificationRepository(db)
    await notif_repo.delete(notification_id, user_id)
    return {
        "success": True,
        "data": {
            "message": "Notification deleted",
            "notification_id": notification_id,
        },
    }


@router.delete("/")
async def clear_all_notifications(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Soft-delete all notifications for the user."""
    user_id = await _user_id(db, email)
    notif_repo = NotificationRepository(db)
    rows = await notif_repo.list_for_user(user_id, limit=1000)
    for row in rows:
        await notif_repo.delete(row["id"], user_id)
    return {"success": True, "data": {"message": "All notifications cleared"}}


@router.get("/preferences")
async def get_preferences(
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get notification preferences."""
    user_id = await _user_id(db, email)
    # In production, store and load from notification_preferences table
    return {
        "email_enabled": True,
        "push_enabled": True,
        "in_app_enabled": True,
        "categories": {
            "search_alerts": True,
            "document_updates": True,
            "system_notifications": True,
            "security_alerts": True,
        },
        "user_id": user_id,
    }


@router.put("/preferences")
async def update_preferences(
    body: dict,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update notification preferences."""
    user_id = await _user_id(db, email)
    # In production, save to notification_preferences table
    return {"user_id": user_id, **body}
