"""Standardized API response formatting."""

import logging
import time
import uuid
from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("nebula.response")


class ResponseStandardizationMiddleware(BaseHTTPMiddleware):
    """Standardize all API responses with consistent envelope."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Skip standardization for docs and health endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health", "/metrics"]:
            return await call_next(request)
        
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    metadata: Optional[dict] = None,
    pagination: Optional[dict] = None,
) -> JSONResponse:
    """Create standardized success response."""
    content = {
        "status": "success",
        "message": message,
        "data": data,
        "metadata": metadata or {},
        "timestamp": time.time(),
    }
    
    if pagination:
        content["pagination"] = pagination
    
    return JSONResponse(status_code=status_code, content=content)


def error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    validation_errors: Optional[list] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Create standardized error response."""
    content = {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "validation_errors": validation_errors or [],
        "request_id": request_id,
        "timestamp": time.time(),
    }
    
    logger.warning(
        "API error: %s [%s] (status=%d, request_id=%s)",
        message,
        error_code,
        status_code,
        request_id,
    )
    
    return JSONResponse(status_code=status_code, content=content)


def pagination_metadata(
    total: int,
    page: int,
    page_size: int,
    total_pages: Optional[int] = None,
) -> dict:
    """Create standardized pagination metadata."""
    total_pages = total_pages or (total + page_size - 1) // page_size
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def pagination_links(request: Request, page: int, page_size: int, total_pages: int) -> dict:
    """Generate pagination links."""
    base_url = str(request.base_url).rstrip("/")
    path = request.url.path
    
    links = {}
    
    if page > 1:
        links["previous"] = f"{base_url}{path}?page={page-1}&page_size={page_size}"
    
    if page < total_pages:
        links["next"] = f"{base_url}{path}?page={page+1}&page_size={page_size}"
    
    links["first"] = f"{base_url}{path}?page=1&page_size={page_size}"
    links["last"] = f"{base_url}{path}?page={total_pages}&page_size={page_size}"
    
    return links


