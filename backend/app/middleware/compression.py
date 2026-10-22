"""Gzip compression middleware for response optimization."""

import gzip
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Gzip compression middleware for reducing response size."""

    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if client accepts gzip encoding
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response

        # Check if response is already compressed
        if response.headers.get("content-encoding"):
            return response

        # Check if response body is large enough to compress
        content_type = response.headers.get("content-type", "")
        
        # Only compress text-based content types
        compressible_types = (
            "text/",
            "application/json",
            "application/javascript",
            "application/xml",
            "application/rss+xml",
            "application/atom+xml",
        )
        
        if not any(content_type.startswith(ct) for ct in compressible_types):
            return response

        # Compress response body
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            if len(body) >= self.minimum_size:
                compressed = gzip.compress(body, compresslevel=6)
                response.headers["content-encoding"] = "gzip"
                response.headers["content-length"] = str(len(compressed))
                response.headers["vary"] = "accept-encoding"
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            else:
                # Return uncompressed if too small
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
        except Exception:
            # If compression fails, return original response
            return response