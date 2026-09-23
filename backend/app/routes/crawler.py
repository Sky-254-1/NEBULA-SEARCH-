"""Crawler management routes."""

from fastapi import APIRouter

router = APIRouter(tags=["Crawler"])


@router.get("/health")
async def crawler_health():
    return {"status": "ok", "crawler": "available"}
