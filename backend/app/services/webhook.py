"""Webhook service for event notifications."""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Optional

import httpx

from app.config import get_settings
from app.models.webhook import WebhookDB, WebhookDeliveryDB, DeliveryStatus

settings = get_settings()
logger = logging.getLogger("nebula.webhook")


class WebhookService:
    """Manage webhooks and deliver events."""
    
    def __init__(self, db=None):
        self._db = db
        self._webhooks: dict[int, WebhookDB] = {}
        self._delivery_queue: list[WebhookDeliveryDB] = []
    
    async def create_webhook(
        self,
        user_id: int,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
        description: Optional[str] = None,
    ) -> WebhookDB:
        """Create a new webhook."""
        webhook = WebhookDB(
            id=len(self._webhooks) + 1,
            user_id=user_id,
            url=url,
            events=events,
            secret=secret,
            description=description,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._webhooks[webhook.id] = webhook
        return webhook
    
    async def get_webhook(self, webhook_id: int, user_id: int) -> Optional[WebhookDB]:
        """Get webhook by ID (with user ownership check)."""
        webhook = self._webhooks.get(webhook_id)
        if webhook and webhook.user_id == user_id:
            return webhook
        return None
    
    async def list_webhooks(self, user_id: int) -> list[WebhookDB]:
        """List all webhooks for a user."""
        return [w for w in self._webhooks.values() if w.user_id == user_id]
    
    async def update_webhook(
        self,
        webhook_id: int,
        user_id: int,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        secret: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[WebhookDB]:
        """Update webhook."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return None
        
        if url is not None:
            webhook.url = url
        if events is not None:
            webhook.events = events
        if secret is not None:
            webhook.secret = secret
        if description is not None:
            webhook.description = description
        if is_active is not None:
            webhook.is_active = is_active
        
        webhook.updated_at = datetime.now()
        return webhook
    
    async def delete_webhook(self, webhook_id: int, user_id: int) -> bool:
        """Delete webhook."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if webhook:
            del self._webhooks[webhook_id]
            return True
        return False
    
    async def trigger_event(
        self,
        event_type: str,
        payload: dict,
        user_id: Optional[int] = None,
    ):
        """
        Trigger webhook event.
        
        Args:
            event_type: Event type (e.g., "user.created")
            payload: Event payload
            user_id: User ID (for filtering webhooks)
        """
        # Find matching webhooks
        matching_webhooks = []
        for webhook in self._webhooks.values():
            if not webhook.is_active:
                continue
            if event_type not in webhook.events:
                continue
            if user_id and webhook.user_id != user_id:
                continue
            matching_webhooks.append(webhook)
        
        if not matching_webhooks:
            return
        
        # Deliver to all matching webhooks
        for webhook in matching_webhooks:
            await self._deliver_webhook(webhook, event_type, payload)
    
    async def _deliver_webhook(
        self,
        webhook: WebhookDB,
        event_type: str,
        payload: dict,
        max_retries: int = 3,
    ):
        """Deliver webhook with retry logic."""
        delivery = WebhookDeliveryDB(
            id=len(self._delivery_queue) + 1,
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            status=DeliveryStatus.PENDING,
            response_code=None,
            response_body=None,
            attempts=0,
            next_retry=datetime.now(),
            created_at=datetime.now(),
        )
        
        for attempt in range(max_retries):
            delivery.attempts = attempt + 1
            
            try:
                # Prepare request
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Nebula-Webhook/1.0",
                    "X-Webhook-Event": event_type,
                    "X-Webhook-ID": str(webhook.id),
                    "X-Webhook-Delivery": str(delivery.id),
                }
                
                # Add signature if secret is configured
                if webhook.secret:
                    payload_bytes = json.dumps(payload).encode()
                    signature = hmac.new(
                        webhook.secret.encode(),
                        payload_bytes,
                        hashlib.sha256,
                    ).hexdigest()
                    headers["X-Webhook-Signature"] = f"sha256={signature}"
                
                # Send request
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                    )
                    
                    delivery.response_code = response.status_code
                    delivery.response_body = response.text[:1000]  # Limit response body
                    
                    if response.status_code in (200, 201, 202, 204):
                        delivery.status = DeliveryStatus.SUCCESS
                        delivery.delivered_at = datetime.now()
                        webhook.last_triggered = datetime.now()
                        logger.info(
                            f"Webhook delivered successfully: {webhook.url} ({event_type})"
                        )
                        return
                    else:
                        delivery.status = DeliveryStatus.FAILED
                        logger.warning(
                            f"Webhook delivery failed (attempt {attempt + 1}): "
                            f"{webhook.url} returned {response.status_code}"
                        )
            
            except Exception as e:
                delivery.status = DeliveryStatus.FAILED
                logger.error(
                    f"Webhook delivery error (attempt {attempt + 1}): {webhook.url} - {e}"
                )
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        delivery.status = DeliveryStatus.FAILED
        logger.error(f"Webhook delivery failed after {max_retries} attempts: {webhook.url}")
    
    async def test_webhook(
        self,
        webhook_id: int,
        user_id: int,
    ) -> dict:
        """Test webhook delivery."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return {"success": False, "error": "Webhook not found"}
        
        test_payload = {
            "event": "test.event",
            "timestamp": datetime.now().isoformat(),
            "message": "This is a test webhook event",
        }
        
        try:
            await self._deliver_webhook(webhook, "test.event", test_payload)
            return {"success": True, "message": "Test webhook delivered"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_delivery_logs(
        self,
        webhook_id: int,
        user_id: int,
        limit: int = 50,
    ) -> list[WebhookDeliveryDB]:
        """Get delivery logs for a webhook."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return []
        
        # Filter deliveries for this webhook
        deliveries = [d for d in self._delivery_queue if d.webhook_id == webhook_id]
        return deliveries[-limit:]  # Return most recent


# Global webhook service instance
webhook_service = WebhookService()


# Import asyncio for sleep
import asyncio