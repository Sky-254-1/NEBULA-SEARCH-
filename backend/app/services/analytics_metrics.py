"""Analytics Prometheus metrics instrumentation."""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable

try:
    from prometheus_client import Counter, Gauge, Histogram, REGISTRY

    def _safe_counter(name: str, documentation: str, labelnames: list[str] | None = None) -> Counter:
        """Create or return existing Prometheus counter to avoid duplicate registration."""
        existing = REGISTRY._names_to_collectors.get(name)
        if existing is not None:
            return existing  # type: ignore
        return Counter(name, documentation, labelnames or [])

    def _safe_gauge(name: str, documentation: str, labelnames: list[str] | None = None) -> Gauge:
        """Create or return existing Prometheus gauge to avoid duplicate registration."""
        existing = REGISTRY._names_to_collectors.get(name)
        if existing is not None:
            return existing  # type: ignore
        return Gauge(name, documentation, labelnames or [])

    def _safe_histogram(name: str, documentation: str, labelnames: list[str] | None = None, buckets: tuple | None = None) -> Histogram:
        """Create or return existing Prometheus histogram to avoid duplicate registration."""
        existing = REGISTRY._names_to_collectors.get(name)
        if existing is not None:
            return existing  # type: ignore
        if buckets:
            return Histogram(name, documentation, labelnames or [], buckets=buckets)
        return Histogram(name, documentation, labelnames or [])

    # Analytics-specific Prometheus metrics
    _prom_search_queries_total = _safe_counter(
        "nebula_search_queries_total",
        "Total search queries",
        ["search_type", "backend"],
    )
    _prom_popular_queries_total = _safe_counter(
        "nebula_popular_queries_total",
        "Popular query counts",
        ["query"],
    )
    _prom_zero_result_queries_total = _safe_counter(
        "nebula_zero_result_queries_total",
        "Zero-result query counts",
        ["query"],
    )
    _prom_average_search_latency = _safe_gauge(
        "nebula_average_search_latency_seconds",
        "Average search latency in seconds",
    )
    _prom_dashboard_generation_time = _safe_histogram(
        "nebula_dashboard_generation_time_seconds",
        "Dashboard generation time in seconds",
        ["period"],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0),
    )
    _prom_analytics_cache_hits = _safe_counter(
        "nebula_analytics_cache_hits_total",
        "Analytics cache hit count",
    )
    _prom_analytics_cache_misses = _safe_counter(
        "nebula_analytics_cache_misses_total",
        "Analytics cache miss count",
    )
    _prom_click_events_total = _safe_counter(
        "nebula_click_events_total",
        "Total click events",
        ["query"],
    )
    _prom_ctr_percentage = _safe_gauge(
        "nebula_ctr_percentage",
        "Click-through rate percentage",
        ["period"],
    )

    _HAS_PROMETHEUS = True
except ImportError:
    _HAS_PROMETHEUS = False

logger = logging.getLogger("nebula.analytics.metrics")


def record_search_query(search_type: str, backend: str) -> None:
    """Record a search query event."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_search_queries_total.labels(search_type=search_type, backend=backend).inc()
    except Exception:
        logger.debug("Failed to record search query metric")


def record_popular_query(query: str, count: int) -> None:
    """Record a popular query."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_popular_queries_total.labels(query=query).inc(count)
    except Exception:
        logger.debug("Failed to record popular query metric")


def record_zero_result_query(query: str, count: int) -> None:
    """Record a zero-result query."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_zero_result_queries_total.labels(query=query).inc(count)
    except Exception:
        logger.debug("Failed to record zero-result query metric")


def record_search_latency(latency_seconds: float) -> None:
    """Record average search latency."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_average_search_latency.set(latency_seconds)
    except Exception:
        logger.debug("Failed to record search latency metric")


def time_dashboard_generation(period: str) -> Callable:
    """Decorator to time dashboard generation."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _HAS_PROMETHEUS:
                return await func(*args, **kwargs)
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                duration = time.monotonic() - start
                _prom_dashboard_generation_time.labels(period=period).observe(duration)
                return result
            except Exception:
                logger.exception("Dashboard generation failed")
                raise
        return wrapper
    return decorator


def record_analytics_cache_hit() -> None:
    """Record analytics cache hit."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_analytics_cache_hits.inc()
    except Exception:
        logger.debug("Failed to record cache hit metric")


def record_analytics_cache_miss() -> None:
    """Record analytics cache miss."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_analytics_cache_misses.inc()
    except Exception:
        logger.debug("Failed to record cache miss metric")


def record_click_event(query: str) -> None:
    """Record a click event."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_click_events_total.labels(query=query).inc()
    except Exception:
        logger.debug("Failed to record click event metric")


def record_ctr(period: str, ctr_value: float) -> None:
    """Record click-through rate."""
    if not _HAS_PROMETHEUS:
        return
    try:
        _prom_ctr_percentage.labels(period=period).set(ctr_value)
    except Exception:
        logger.debug("Failed to record CTR metric")


class AnalyticsMetricsRecorder:
    """Context manager for recording analytics metrics."""

    def __init__(self, operation: str):
        self.operation = operation
        self.start_time: float = 0.0

    async def __aenter__(self) -> "AnalyticsMetricsRecorder":
        self.start_time = time.monotonic()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration = time.monotonic() - self.start_time
        if exc_type is None:
            logger.debug("%s completed in %.3fs", self.operation, duration)
        else:
            logger.error("%s failed after %.3fs", self.operation, duration)