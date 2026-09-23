"""Federated search across devices."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.database.repositories.search import SearchRepository
from app.services.auth import get_current_user

settings = get_settings()
router = APIRouter(prefix="/api/v1/search/federated", tags=["Federated Search"])


class FederatedSearchRequest(BaseModel):
    query: str
    devices: Optional[list[str]] = None  # List of device IDs to search
    include_history: bool = True
    include_documents: bool = True


class FederatedSearchResponse(BaseModel):
    query: str
    results: list[dict]
    devices_searched: list[str]
    total: int


@router.post("/search")
async def federated_search(body: FederatedSearchRequest, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Search across multiple devices/sessions."""
    if not settings.enable_federated_search:
        raise HTTPException(status_code=404, detail="Federated search is not enabled")
    
    # Get user's sessions/devices
    from app.database.repositories.session import SessionRepository
    sessions_repo = SessionRepository(db)
    sessions = await sessions_repo.get_user_sessions(email)
    
    # Filter devices if specified
    if body.devices:
        sessions = [s for s in sessions if s.get("session_id") in body.devices]
    
    devices_searched = [s.get("session_id") for s in sessions]
    
    # Search local index first
    search_repo = SearchRepository(db)
    local_results = await search_repo.search(body.query, limit=20)
    
    # TODO: In production, query remote devices via their APIs
    # For now, return local results with device info
    
    return {
        "query": body.query,
        "results": local_results,
        "devices_searched": devices_searched,
        "total": len(local_results),
    }


@router.get("/devices")
async def get_user_devices(email: str = Depends(get_current_user), db=Depends(get_db)):
    """Get list of user's registered devices."""
    if not settings.enable_federated_search:
        raise HTTPException(status_code=404, detail="Federated search is not enabled")
    
    from app.database.repositories.session import SessionRepository
    sessions_repo = SessionRepository(db)
    sessions = await sessions_repo.get_user_sessions(email)
    
    devices = []
    for session in sessions:
        devices.append({
            "session_id": session.get("session_id"),
            "device_name": session.get("device_name"),
            "ip_address": session.get("ip_address"),
            "created_at": session.get("created_at"),
            "last_used": session.get("last_used"),
            "is_active": session.get("is_active", True),
        })
    
    return {"devices": devices}


@router.delete("/devices/{session_id}")
async def remove_device(session_id: str, email: str = Depends(get_current_user), db=Depends(get_db)):
    """Remove a device from federated search."""
    if not settings.enable_federated_search:
        raise HTTPException(status_code=404, detail="Federated search is not enabled")
    
    from app.database.repositories.session import SessionRepository
    sessions_repo = SessionRepository(db)
    
    # Verify device belongs to user
    session = await sessions_repo.get_by_session_id(session_id)
    if not session or session.get("user_id") != email:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Deactivate session
    await sessions_repo.deactivate_session(session_id)
    
    return {"message": "Device removed"}