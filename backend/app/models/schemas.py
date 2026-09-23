"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


# Base response schemas
class APIResponse(BaseModel):
    """Standard API response envelope."""
    status: str = "success"
    message: str = "Success"
    data: Optional[Any] = None
    metadata: dict = {}
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class APIError(BaseModel):
    """Standard API error response."""
    status: str = "error"
    error_code: str
    message: str
    validation_errors: list = []
    request_id: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: list[Any]
    pagination: PaginationMeta


# Authentication schemas
class AuthRequest(BaseModel):
    """Authentication request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class AuthResponse(BaseModel):
    """Authentication response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: Optional[str] = None


class UserInfo(BaseModel):
    """User information."""
    email: str
    role: str
    email_verified: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


# Search schemas
class SearchResult(BaseModel):
    """Search result item — supports both web and vector results."""
    # Vector / document result fields
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    filename: Optional[str] = None
    content: Optional[str] = None
    # Web result fields
    title: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None
    # Shared ranking field
    score: float = 0.0
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    combined_score: Optional[float] = None
    semantic_score: Optional[float] = None


class OrchestratedSearchResponse(BaseModel):
    """Orchestrated search response."""
    query: str
    results: list[SearchResult]
    backends_used: list[str]
    total: int


# Vector schemas
class VectorSearchRequest(BaseModel):
    """Vector search request."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(10, ge=1, le=100)
    filters: Optional[dict] = None


class Citation(BaseModel):
    """Citation for RAG answer."""
    id: int
    document_id: int
    chunk_id: int
    query: str
    snippet: str
    score: float
    created_at: datetime


class VectorAskRequest(BaseModel):
    """Vector ask (RAG) request."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)


class VectorAskResponse(BaseModel):
    """Vector ask response."""
    query: str
    answer: str
    citations: list[Citation]
    sources: list[str]


# Storage schemas
class DocumentResponse(BaseModel):
    """Document response."""
    id: int
    filename: str
    content_type: Optional[str] = None
    created_at: str
    indexed_at: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Document upload response."""
    id: int
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime
    status: str


class DocumentListResponse(BaseModel):
    """Document list response."""
    documents: list[DocumentResponse]
    pagination: Optional[PaginationMeta] = None


class ExportCreateRequest(BaseModel):
    """Export creation request."""
    export_type: str
    data: Optional[dict] = None


class ExportResponse(BaseModel):
    """Export response."""
    id: int
    export_type: str
    storage_path: str
    created_at: str


class ExportListResponse(BaseModel):
    """Export list response."""
    exports: list[ExportResponse]
    pagination: Optional[PaginationMeta] = None


class SettingsResponse(BaseModel):
    """Settings response."""
    settings: dict


class SettingsUpdateRequest(BaseModel):
    """Settings update request."""
    settings: dict


# Webhook schemas
class WebhookCreate(BaseModel):
    """Webhook creation request."""
    url: str = Field(..., pattern=r'^https?://')
    events: list[str] = Field(..., min_length=1)
    secret: Optional[str] = None
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    """Webhook response."""
    id: int
    url: str
    events: list[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None


class WebhookDelivery(BaseModel):
    """Webhook delivery log."""
    id: int
    webhook_id: int
    event_type: str
    status: str
    response_code: Optional[int]
    attempts: int
    created_at: datetime


# Health schemas
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    database: str
    cache: str
    timestamp: datetime


# Admin schemas
class SystemStats(BaseModel):
    """System statistics."""
    total_users: int
    active_users: int
    total_documents: int
    total_searches: int
    cache_hit_ratio: float
    uptime_seconds: float


# AI schemas
class AIRequest(BaseModel):
    """AI request."""
    prompt: str = Field(..., min_length=1, max_length=10000)


class AIResponse(BaseModel):
    """AI response."""
    answer: str
    provider: str


class AICompletionRequest(BaseModel):
    """AI completion request."""
    prompt: str = Field(..., min_length=1, max_length=10000)
    max_tokens: int = Field(500, ge=1, le=4000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    model: Optional[str] = None


class AICompletionResponse(BaseModel):
    """AI completion response."""
    text: str
    model: str
    tokens_used: int
    finish_reason: str


class SynthesizeRequest(BaseModel):
    """Synthesize request."""
    query: str = Field(..., min_length=1, max_length=1000)
    snippets: list[str] = Field(..., min_length=1)


class SynthesizeResponse(BaseModel):
    """Synthesize response."""
    synthesis: str
    sources: list[str]


class ChatMessage(BaseModel):
    """Chat message."""
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    messages: list[ChatMessage]


# Audio schemas
class AudioTranscriptionRequest(BaseModel):
    """Audio transcription request."""
    language: Optional[str] = Field(None, pattern=r'^[a-z]{2}$')


class AudioTranscriptionResponse(BaseModel):
    """Audio transcription response."""
    text: str
    language: str
    duration: float
    segments: list[dict]


# Utility schemas
class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# Vector schemas (additional)
class VectorSearchResult(BaseModel):
    """Vector search result."""
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    filename: str = ""
    content: str = ""
    score: float = 0.0
    vector_score: Optional[float] = 0.0
    keyword_score: Optional[float] = 0.0


class VectorSearchResponse(BaseModel):
    """Vector search response."""
    query: str
    results: list[VectorSearchResult]
    total: int


class VectorCitationResponse(BaseModel):
    """Vector citation response."""
    id: int
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    query: str
    snippet: Optional[str] = None
    score: float = 0.0
    created_at: str


class VectorCitationListResponse(BaseModel):
    """Vector citation list response."""
    citations: list[VectorCitationResponse]
    pagination: Optional[PaginationMeta] = None


class VectorReindexRequest(BaseModel):
    """Vector reindex request."""
    limit: Optional[int] = 100


class DocumentIndexStatusResponse(BaseModel):
    """Document index status response."""
    id: int
    filename: str
    status: str
    indexed_at: Optional[str] = None
    error_message: Optional[str] = None


# Features schemas (collections, bookmarks, notifications)
class SavedSearchCreate(BaseModel):
    """Saved search creation request."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[dict] = None
    label: Optional[str] = None


class SavedSearchResponse(BaseModel):
    """Saved search response."""
    id: int
    user_id: int
    query: str
    filters: Optional[dict] = None
    label: Optional[str] = None
    created_at: str
    updated_at: str


class SavedSearchListResponse(BaseModel):
    """Saved search list response."""
    saved_searches: list[SavedSearchResponse]


class CollectionCreate(BaseModel):
    """Collection creation request."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_public: bool = False


class CollectionUpdate(BaseModel):
    """Collection update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class CollectionResponse(BaseModel):
    """Collection response."""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    is_public: bool
    created_at: str
    updated_at: str


class CollectionListResponse(BaseModel):
    """Collection list response."""
    collections: list[CollectionResponse]


class CollectionItemCreate(BaseModel):
    """Collection item creation request."""
    document_id: Optional[int] = None
    search_result_id: Optional[int] = None
    note: Optional[str] = None


class CollectionItemResponse(BaseModel):
    """Collection item response."""
    id: int
    collection_id: int
    document_id: Optional[int] = None
    search_result_id: Optional[int] = None
    note: Optional[str] = None
    created_at: str


class BookmarkCreate(BaseModel):
    """Bookmark creation request."""
    title: str = Field(..., min_length=1, max_length=500)
    url: str = Field(..., min_length=1, max_length=2000)
    snippet: Optional[str] = None
    tags: Optional[list[str]] = None


class BookmarkUpdate(BaseModel):
    """Bookmark update request."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    snippet: Optional[str] = None
    tags: Optional[list[str]] = None


class BookmarkResponse(BaseModel):
    """Bookmark response."""
    id: int
    user_id: int
    title: str
    url: str
    snippet: Optional[str] = None
    tags: Optional[list[str]] = None
    created_at: str
    updated_at: str


class BookmarkListResponse(BaseModel):
    """Bookmark list response."""
    bookmarks: list[BookmarkResponse]


class NotificationResponse(BaseModel):
    """Notification response."""
    id: int
    user_id: int
    type: str
    title: str
    message: str
    data: Optional[dict] = None
    is_read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    """Notification list response."""
    notifications: list[NotificationResponse]
    unread_count: int
