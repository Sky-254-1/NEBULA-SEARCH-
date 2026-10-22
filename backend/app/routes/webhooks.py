"""Webhook management routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_db
from app.database.repositories.user import UserRepository
from app.middleware.rate_limit import rate_limit
from app.models.schemas import MessageResponse
from app.models.webhook import (
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookUpdate,
)
from app.services.auth import get_current_user
from app.services.webhook import webhook_service

logger = logging.getLogger("nebula.webhooks")
router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.post("", response_model=WebhookResponse, status_code=201, dependencies=[Depends(rate_limit)])
async def create_webhook(
    request: Request,
    body: WebhookCreate,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Create a new webhook."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    webhook = await webhook_service.create_webhook(
        user_id=user["id"],
        url=str(body.url),
        events=body.events,
        secret=body.secret,
        description=body.description,
    )
    
    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        last_triggered=webhook.last_triggered,
    )


@router.get("", response_model=list[WebhookResponse], dependencies=[Depends(rate_limit)])
async def list_webhooks(
    request: Request,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all webhooks for current user."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    webhooks = await webhook_service.list_webhooks(user["id"])
    return [
        WebhookResponse(
            id=w.id,
            url=w.url,
            events=w.events,
            description=w.description,
            is_active=w.is_active,
            created_at=w.created_at,
            updated_at=w.updated_at,
            last_triggered=w.last_triggered,
        )
        for w in webhooks
    ]


@router.get("/{webhook_id}", response_model=WebhookResponse, dependencies=[Depends(rate_limit)])
async def get_webhook(
    request: Request,
    webhook_id: int,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get webhook details."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    webhook = await webhook_service.get_webhook(webhook_id, user["id"])
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        last_triggered=webhook.last_triggered,
    )


@router.put("/{webhook_id}", response_model=WebhookResponse, dependencies=[Depends(rate_limit)])
async def update_webhook(
    request: Request,
    webhook_id: int,
    body: WebhookUpdate,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update webhook."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    webhook = await webhook_service.update_webhook(
        webhook_id=webhook_id,
        user_id=user["id"],
        url=str(body.url) if body.url else None,
        events=body.events,
        secret=body.secret,
        description=body.description,
        is_active=body.is_active,
    )
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        last_triggered=webhook.last_triggered,
    )


@router.delete("/{webhook_id}", response_model=MessageResponse, dependencies=[Depends(rate_limit)])
async def delete_webhook(
    request: Request,
    webhook_id: int,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete webhook."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted = await webhook_service.delete_webhook(webhook_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return MessageResponse(message="Webhook deleted successfully")


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse, dependencies=[Depends(rate_limit)])
async def test_webhook(
    request: Request,
    webhook_id: int,
    body: WebhookTestRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Test webhook delivery."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await webhook_service.test_webhook(webhook_id, user["id"])
    return WebhookTestResponse(**result)


@router.get(
    "/{webhook_id}/deliveries",
    response_model=list[WebhookDeliveryResponse],
    dependencies=[Depends(rate_limit)],
)
async def get_webhook_deliveries(
    request: Request,
    webhook_id: int,
    limit: int = 50,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get webhook delivery logs."""
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    deliveries = await webhook_service.get_delivery_logs(webhook_id, user["id"], limit)
    return [
        WebhookDeliveryResponse(
            id=d.id,
            webhook_id=d.webhook_id,
            event_type=d.event_type,
            status=d.status,
            response_code=d.response_code,
            attempts=d.attempts,
            created_at=d.created_at,
            delivered_at=d.delivered_at,
        )
        for d in deliveries
    ]