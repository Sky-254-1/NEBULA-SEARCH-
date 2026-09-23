"""Root endpoint only — all /health routes live in app.health_routes."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    return {"message": "Nebula Search API is running.", "docs": "/docs", "version": "1.0.0"}
