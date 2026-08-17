"""
Enhanced health check endpoints.
Provides detailed health status for monitoring and load balancers.
"""

import asyncio
import time
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.database.engine import connect
from app.services.cache import cache_service
from app.services.queue import job_queue

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: str
    uptime: float
    version: str
    checks: dict
    dependencies: dict


class DependencyHealth(BaseModel):
    """Individual dependency health status."""
    status: Literal["up", "down", "degraded"]
    latency_ms: float | None = None
    error: str | None = None
    details: dict | None = None


_start_time = time.time()


def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - _start_time


async def check_database() -> DependencyHealth:
    """Check database connectivity and performance."""
    start = time.monotonic()
    try:
        db = await connect()
        await db.execute("SELECT 1")
        await db.close()
        latency = (time.monotonic() - start) * 1000
        
        # Check connection pool
        pool_info = {}
        if hasattr(db, 'pool'):
            pool = db.pool
            pool_info = {
                "size": getattr(pool, 'size', None),
                "free": getattr(pool, 'free', None),
            }
        
        return DependencyHealth(
            status="up",
            latency_ms=latency,
            details={"pool": pool_info}
        )
    except Exception as exc:
        return DependencyHealth(
            status="down",
            error=str(exc)
        )


async def check_redis() -> DependencyHealth:
    """Check Redis connectivity."""
    start = time.monotonic()
    try:
        if cache_service._redis:
            await cache_service._redis.ping()
            latency = (time.monotonic() - start) * 1000
            info = await cache_service._redis.info()
            return DependencyHealth(
                status="up",
                latency_ms=latency,
                details={
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                }
            )
        else:
            return DependencyHealth(
                status="up",
                details={"mode": "in-memory"}
            )
    except Exception as exc:
        return DependencyHealth(status="down", error=str(exc))


async def check_elasticsearch() -> DependencyHealth:
    """Check Elasticsearch connectivity."""
    start = time.monotonic()
    try:
        from elasticsearch import AsyncElasticsearch
        
        if not hasattr(check_elasticsearch, 'client'):
            check_elasticsearch.client = AsyncElasticsearch(
                [settings.elasticsearch_url] if settings.elasticsearch_url else []
            )
        
        health = await check_elasticsearch.client.cluster.health()
        latency = (time.monotonic() - start) * 1000
        
        status = "up" if health["status"] in ["green", "yellow"] else "degraded"
        
        return DependencyHealth(
            status=status,
            latency_ms=latency,
            details={
                "cluster_status": health["status"],
                "number_of_nodes": health.get("number_of_nodes"),
            }
        )
    except Exception as exc:
        return DependencyHealth(status="down", error=str(exc))


async def check_storage() -> DependencyHealth:
    """Check storage directories and permissions."""
    try:
        import os
        from pathlib import Path
        
        dirs = {
            "uploads": settings.storage_uploads,
            "cache": settings.storage_cache,
            "vector": settings.storage_vector,
            "indexes": settings.storage_indexes,
        }
        
        missing = []
        for name, path in dirs.items():
            if not Path(path).exists():
                missing.append(name)
        
        if missing:
            return DependencyHealth(
                status="degraded",
                error=f"Missing directories: {', '.join(missing)}"
            )
        
        return DependencyHealth(status="up", details={"directories": list(dirs.keys())})
    except Exception as exc:
        return DependencyHealth(status="down", error=str(exc))


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns overall status and individual dependency checks.
    """
    # Run all dependency checks in parallel
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_storage(),
        return_exceptions=True
    )
    
    # Optional Elasticsearch check
    es_check = None
    if settings.elasticsearch_url:
        es_check = await check_elasticsearch()
        checks.append(es_check)
    
    # Aggregate results
    dependencies = {}
    dep_names = ["database", "redis", "storage"]
    if es_check:
        dep_names.append("elasticsearch")
    
    for name, check in zip(dep_names, checks):
        if isinstance(check, Exception):
            dependencies[name] = DependencyHealth(
                status="down",
                error=str(check)
            ).dict()
        else:
            dependencies[name] = check.dict()
    
    # Determine overall status
    statuses = [d["status"] for d in dependencies.values()]
    
    if all(s == "up" for s in statuses):
        overall_status = "healthy"
    elif any(s == "down" for s in statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        uptime=get_uptime(),
        version="1.2.1",
        checks={
            "database": dependencies.get("database", {}).get("status") == "up",
            "redis": dependencies.get("redis", {}).get("status") == "up",
            "storage": dependencies.get("storage", {}).get("status") == "up",
        },
        dependencies=dependencies
    )


@router.get("/health/live", tags=["Health"])
async def liveness_probe():
    """
    Kubernetes liveness probe.
    Returns 200 if the application is running.
    """
    return {"status": "ok"}


@router.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """
    Kubernetes readiness probe.
    Returns 200 if the application is ready to serve traffic.
    """
    # Check critical dependencies
    db_health = await check_database()
    
    if db_health.status == "down":
        raise HTTPException(status_code=503, detail="Database not ready")
    
    return {"status": "ready"}


@router.get("/health/detailed", tags=["Health"])
async def detailed_health():
    """
    Detailed health check with system information.
    """
    import psutil
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": get_uptime(),
        "version": "1.2.1",
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        },
        "python": {
            "version": __import__('sys').version,
        }
    }