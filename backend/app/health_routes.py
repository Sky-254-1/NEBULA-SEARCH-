"""
Standard health check endpoints for Kubernetes-style probes and monitoring.

Endpoints
---------
GET /health         — Liveness probe: always returns ``{status:"ok"}`` when the
                      HTTP server is up.
GET /health/ready   — Readiness probe: verifies DB + critical deps are ready
                      to serve traffic.
GET /health/db      — DB-specific deep health check (runs a simple query).
GET /health/metrics — Resource utilisation (CPU / memory / disk) via psutil
                      if available; falls back to a minimal payload.
"""

import time
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.database.engine import connect
from app.services.cache import cache_service

router = APIRouter(tags=["Health"])
settings = get_settings()

_start_time = time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    timestamp: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    timestamp: str
    checks: dict[str, bool]


class DbHealthResponse(BaseModel):
    status: Literal["up", "down"]
    latency_ms: float | None = None
    backend: str
    error: str | None = None
    query_ok: bool = False


class MetricsResponse(BaseModel):
    timestamp: str
    uptime_seconds: float
    cpu_percent: float | None = None
    memory: dict[str, Any] | None = None
    disk: dict[str, Any] | None = None
    python: dict[str, Any] | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Internal check helpers
# ---------------------------------------------------------------------------


async def _db_check() -> tuple[bool, float | None, str | None]:
    """Run a cheap SELECT 1 against the configured DB backend.

    Returns a tuple ``(ok, latency_ms, error_message)``.
    """
    start = time.monotonic()
    try:
        db = await connect()
        try:
            await db.execute("SELECT 1")
            latency_ms = (time.monotonic() - start) * 1000
            return True, latency_ms, None
        finally:
            await db.close()
    except Exception as exc:  # pragma: no cover - defensive
        return False, None, str(exc)


async def _cache_check() -> bool:
    """Return True if Redis is connected (or memory cache is in use)."""
    try:
        if cache_service._redis:
            await cache_service._redis.ping()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/health", response_model=LivenessResponse, status_code=200)
async def liveness_probe() -> LivenessResponse:
    """Overall liveness probe.

    Returns HTTP 200 ``{"status":"ok"}`` as long as the HTTP server is
    running.  Use this for Kubernetes ``livenessProbe`` — it must **not**
    depend on external services (those belong on /health/ready).
    """
    return LivenessResponse(timestamp=_now_iso())


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_probe() -> ReadinessResponse:
    """Readiness probe — checks critical dependencies before serving traffic.

    A Kubernetes ``readinessProbe`` hitting this endpoint will keep the pod
    out of the Service Endpoints list until DB + cache are reachable.
    """
    db_ok, _lat, _err = await _db_check()
    cache_ok = await _cache_check()

    checks = {
        "database": db_ok,
        "cache": cache_ok,
    }

    ready = all(checks.values())
    if not ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": _now_iso(),
                "checks": checks,
            },
        )

    return ReadinessResponse(
        status="ready",
        timestamp=_now_iso(),
        checks=checks,
    )


@router.get("/health/db", response_model=DbHealthResponse)
async def db_health_probe() -> DbHealthResponse:
    """Database-specific health check.

    Runs a simple ``SELECT 1`` query and reports latency / status.
    """
    db_ok, latency_ms, error = await _db_check()
    return DbHealthResponse(
        status="up" if db_ok else "down",
        latency_ms=latency_ms,
        backend="postgresql" if settings.uses_postgres else "sqlite",
        error=error,
        query_ok=db_ok,
    )


@router.get("/health/metrics", response_model=MetricsResponse)
async def resource_metrics_probe() -> MetricsResponse:
    """Resource utilisation: CPU / memory / disk via ``psutil`` (if available)."""
    uptime = time.time() - _start_time
    base = MetricsResponse(
        timestamp=_now_iso(),
        uptime_seconds=round(uptime, 2),
    )

    try:
        import psutil  # type: ignore
    except ImportError as exc:
        base.error = f"psutil not installed: {exc}"
        return base

    try:
        vm = psutil.virtual_memory()
        du = psutil.disk_usage("/")

        base.cpu_percent = round(psutil.cpu_percent(interval=0.2), 2)
        base.memory = {
            "total_mb": round(vm.total / (1024 * 1024), 2),
            "available_mb": round(vm.available / (1024 * 1024), 2),
            "used_mb": round(vm.used / (1024 * 1024), 2),
            "percent": round(vm.percent, 2),
        }
        base.disk = {
            "total_gb": round(du.total / (1024 * 1024 * 1024), 2),
            "used_gb": round(du.used / (1024 * 1024 * 1024), 2),
            "free_gb": round(du.free / (1024 * 1024 * 1024), 2),
            "percent": round(du.percent, 2),
        }
        import sys as _sys

        base.python = {
            "version": _sys.version,
            "pid": psutil.Process().pid,
            "rss_mb": round(psutil.Process().memory_info().rss / (1024 * 1024), 2),
        }
    except Exception as exc:  # pragma: no cover - best effort
        base.error = str(exc)

    return base
