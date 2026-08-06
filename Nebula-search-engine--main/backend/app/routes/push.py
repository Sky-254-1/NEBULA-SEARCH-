"""Push notification routes for FCM and APNs."""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.database.repositories.user import UserRepository
from app.services.auth import get_current_user

settings = get_settings()
router = APIRouter(prefix="/api/v1/notifications/push", tags=["Push Notifications"])


class PushTokenRegister(BaseModel):
    token: str
    platform: str  # "ios", "android", "web"
    device_id: Optional[str] = None


class PushNotificationSend(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    title: str
    body: str
    data: Optional[dict] = None


@router.post("/register")
async def register_push_token(body: PushTokenRegister, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Register push notification token for user."""
    if not settings.enable_push_notifications:
        raise HTTPException(status_code=404, detail="Push notifications are not enabled")
    
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store push token (in production, use proper storage)
    # For now, we'll store in a simple table or cache
    await users.update(user["id"], {
        "push_token": body.token,
        "push_platform": body.platform,
        "push_device_id": body.device_id,
        "push_token_updated_at": datetime.now(timezone.utc).isoformat(),
    })
    
    return {"message": "Push token registered"}


@router.delete("/unregister")
async def unregister_push_token(email: str = Depends(get_current_user), db=Depends(get_db)):
    """Unregister push notification token."""
    if not settings.enable_push_notifications:
        raise HTTPException(status_code=404, detail="Push notifications are not enabled")
    
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if user:
        await users.update(user["id"], {
            "push_token": None,
            "push_platform": None,
            "push_device_id": None,
        })
    
    return {"message": "Push token unregistered"}


@router.post("/send")
async def send_push_notification(body: PushNotificationSend, request: Request, db=Depends(get_db)):
    """Send push notification to user."""
    if not settings.enable_push_notifications:
        raise HTTPException(status_code=404, detail="Push notifications are not enabled")
    
    # Get current user from session
    current_user = request.state.user if hasattr(request.state, 'user') else None
    
    # Determine recipient
    target_user_id = body.user_id
    target_email = body.email
    
    if current_user:
        target_email = target_email or current_user.get("email")
    
    if not target_email:
        raise HTTPException(status_code=400, detail="No recipient specified")
    
    users = UserRepository(db)
    user = await users.get_by_email(target_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    push_token = user.get("push_token")
    platform = user.get("push_platform")
    
    if not push_token or not platform:
        raise HTTPException(status_code=404, detail="User has no push token registered")
    
    # Send notification based on platform
    try:
        if platform == "android" and settings.fcm_server_key:
            await _send_fcm_notification(push_token, body.title, body.body, body.data)
        elif platform == "ios" and settings.apns_key_id:
            await _send_apns_notification(push_token, body.title, body.body, body.data)
        elif platform == "web":
            await _send_web_push_notification(push_token, body.title, body.body, body.data)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")
    
    return {"message": "Notification sent"}


async def _send_fcm_notification(token: str, title: str, body: str, data: Optional[dict]):
    """Send notification via Firebase Cloud Messaging."""
    import httpx
    
    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Authorization": f"key={settings.fcm_server_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": token,
        "notification": {
            "title": title,
            "body": body,
        },
        "data": data or {},
        "priority": "high",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()


async def _send_apns_notification(token: str, title: str, body: str, data: Optional[dict]):
    """Send notification via Apple Push Notification Service."""
    # In production, use a proper APNs library like aioapns
    # For now, just log it
    print(f"[APNs] Would send to {token}: {title} - {body}")


async def _send_web_push_notification(token: str, title: str, body: str, data: Optional[dict]):
    """Send notification via Web Push."""
    # In production, use a proper Web Push library
    # For now, just log it
    print(f"[WebPush] Would send to {token}: {title} - {body}")


@router.get("/status")
async def get_push_status(email: str = Depends(get_current_user), db=Depends(get_db)):
    """Get push notification registration status."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "enabled": settings.enable_push_notifications,
        "registered": bool(user.get("push_token")),
        "platform": user.get("push_platform"),
        "updated_at": user.get("push_token_updated_at"),
    }