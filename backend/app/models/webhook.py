"""Webhook models and database schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


# Database model (for reference)
class WebhookDB:
    """Webhook database model."""
    def __init__(
        self,
        id: int,
        user_id: int,
        url: str,
        events: list[str],
        secret: Optional[str],
        description: Optional[str],
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
        last_triggered: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.url = url
        self.events = events
        self.secret = secret
        self.description = description
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        self.last_triggered = last_triggered


class WebhookDeliveryDB:
    """Webhook delivery log database model."""
    def __init__(
        self,
        id: int,
        webhook_id: int,
        event_type: str,
        payload: dict,
        status: str,
        response_code: Optional[int],
        response_body: Optional[str],
        attempts: int,
        next_retry: Optional[datetime],
        created_at: datetime,
        delivered_at: Optional[datetime] = None,
    ):
        self.id = id
        self.webhook_id = webhook_id
        self.event_type = event_type
        self.payload = payload
        self.status = status
        self.response_code = response_code
        self.response_body = response_body
        self.attempts = attempts
        self.next_retry = next_retry
        self.created_at = created_at
        self.delivered_at = delivered_at


# Pydantic schemas for API
class WebhookCreate(BaseModel):
    """Webhook creation request."""
    url: HttpUrl
    events: list[str]  # e.g., ["user.created", "document.indexed", "search.completed"]
    secret: Optional[str] = None
    description: Optional[str] = None


class WebhookUpdate(BaseModel):
    """Webhook update request."""
    url: Optional[HttpUrl] = None
    events: Optional[list[str]] = None
    secret: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Webhook response."""
    id: int
    url: str
    events: list[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_triggered: Optional[datetime] = None


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery log response."""
    id: int
    webhook_id: int
    event_type: str
    status: str
    response_code: Optional[int]
    attempts: int
    created_at: datetime
    delivered_at: Optional[datetime] = None


class WebhookTestRequest(BaseModel):
    """Webhook test request."""
    event_type: str = "test.event"
    payload: Optional[dict] = None


class WebhookTestResponse(BaseModel):
    """Webhook test response."""
    success: bool
    status_code: Optional[int]
    response_body: Optional[str]
    error: Optional[str] = None


# Event types
class WebhookEvent:
    """Standard webhook event types."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_INDEXED = "document.indexed"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    
    SEARCH_COMPLETED = "search.completed"
    VECTOR_SEARCH_COMPLETED = "vector.search.completed"
    
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGED = "auth.password_changed"  # nosec B105: webhook event name, not a secret
    AUTH_MFA_ENABLED = "auth.mfa_enabled"
    AUTH_MFA_DISABLED = "auth.mfa_disabled"
    
    AI_TASK_COMPLETED = "ai.task_completed"
    AUDIO_TRANSCRIPTION_COMPLETED = "audio.transcription_completed"
    
    SYSTEM_ALERT = "system.alert"
    RATE_LIMIT_EXCEEDED = "system.rate_limit_exceeded"
    
    TEST_EVENT = "test.event"


# Delivery status
class DeliveryStatus:
    """Webhook delivery status."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"