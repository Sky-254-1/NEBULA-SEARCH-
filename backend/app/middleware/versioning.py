"""API versioning middleware and utilities."""

import logging
from enum import Enum

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("nebula.versioning")


class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    V2 = "v2"
    LATEST = "v2"  # Default to latest stable version


class VersioningMiddleware(BaseHTTPMiddleware):
    """Handle API versioning via URI path and headers."""
    
    # Endpoints that are version-agnostic
    VERSION_AGNOSTIC_PATHS = {
        "/",
        "/health",
        "/health/live",
        "/health/ready",
        "/health/detailed",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
        "/metrics",
    }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip versioning for version-agnostic paths
        if request.url.path in self.VERSION_AGNOSTIC_PATHS:
            return await call_next(request)
        
        # Extract version from URI path (e.g., /api/v1/...)
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 3 and path_parts[1] == "api":
            version = path_parts[2]
            if version in [v.value for v in APIVersion]:
                # Add version info to request state
                request.state.api_version = version
                response = await call_next(request)
                
                # Add deprecation headers if needed
                if version == APIVersion.V1:
                    response.headers["X-API-Deprecated"] = "true"
                    response.headers["X-API-Deprecation-Date"] = "2026-12-31"
                    response.headers["X-API-Sunset-Date"] = "2027-06-30"
                    response.headers["X-API-Migration-Guide"] = "/docs/api-migration-v1-to-v2"
                
                return response
        
        # If no version in path, return error
        raise HTTPException(
            status_code=400,
            detail="API version required. Use /api/v1/ or /api/v2/",
        )


def get_api_version(request: Request) -> str:
    """Extract API version from request."""
    return getattr(request.state, "api_version", APIVersion.LATEST)


def require_version(min_version: str):
    """Dependency to enforce minimum API version."""
    def version_checker(request: Request):
        current = getattr(request.state, "api_version", APIVersion.LATEST)
        if current < min_version:
            raise HTTPException(
                status_code=426,
                detail=f"API version {min_version} or higher required. Current: {current}",
                headers={"X-API-Minimum-Version": min_version},
            )
        return current
    return version_checker


def deprecate_endpoint(sunset_date: str, migration_guide: str = ""):
    """Decorator to mark endpoints as deprecated."""
    def decorator(func):
        func.deprecated = True
        func.sunset_date = sunset_date
        func.migration_guide = migration_guide
        return func
    return decorator