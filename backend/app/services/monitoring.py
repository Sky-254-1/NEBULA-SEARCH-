"""Monitoring and metrics collection for API observability."""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("nebula.monitoring")


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CounterMetric:
    """Counter metric (monotonically increasing)."""
    name: str
    value: int = 0
    labels: dict = field(default_factory=dict)
    
    def increment(self, amount: int = 1):
        """Increment counter."""
        self.value += amount


@dataclass
class HistogramMetric:
    """Histogram metric (distribution of values)."""
    name: str
    values: list[float] = field(default_factory=list)
    buckets: list[float] = field(default_factory=lambda: [
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
    ])
    
    def observe(self, value: float):
        """Add observation."""
        self.values.append(value)
    
    def get_bucket_counts(self) -> dict:
        """Get counts per bucket."""
        counts = {str(bucket): 0 for bucket in self.buckets}
        for value in self.values:
            for bucket in self.buckets:
                if value <= bucket:
                    counts[str(bucket)] += 1
                    break
        return counts


class MetricsCollector:
    """Collect and store API metrics."""
    
    def __init__(self):
        self.request_count = CounterMetric("api_requests_total")
        self.request_duration = HistogramMetric("api_request_duration_seconds")
        self.error_count = CounterMetric("api_errors_total")
        self.rate_limit_count = CounterMetric("api_rate_limits_total")
        self.cache_hits = CounterMetric("cache_hits_total")
        self.cache_misses = CounterMetric("cache_misses_total")
        self.webhook_deliveries = CounterMetric("webhook_deliveries_total")
        self.webhook_failures = CounterMetric("webhook_failures_total")
        
        self._recent_requests: list[RequestMetrics] = []
        self._max_recent_requests = 1000
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Record API request metrics."""
        self.request_count.increment()
        self.request_duration.observe(response_time_ms / 1000.0)
        
        if status_code >= 400:
            self.error_count.increment()
        
        # Store recent request
        metrics = RequestMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            ip_address=ip_address,
        )
        self._recent_requests.append(metrics)
        
        # Keep only recent requests
        if len(self._recent_requests) > self._max_recent_requests:
            self._recent_requests = self._recent_requests[-self._max_recent_requests:]
    
    def record_rate_limit(self, endpoint: str, identifier: str):
        """Record rate limit event."""
        self.rate_limit_count.increment()
        logger.warning(f"Rate limit hit: {endpoint} by {identifier}")
    
    def record_cache_hit(self):
        """Record cache hit."""
        self.cache_hits.increment()
    
    def record_cache_miss(self):
        """Record cache miss."""
        self.cache_misses.increment()
    
    def record_webhook_delivery(self, success: bool):
        """Record webhook delivery."""
        self.webhook_deliveries.increment()
        if not success:
            self.webhook_failures.increment()
    
    def get_error_rate(self, window_minutes: int = 5) -> float:
        """Calculate error rate over time window."""
        cutoff = datetime.now().timestamp() - (window_minutes * 60)
        recent = [r for r in self._recent_requests if r.timestamp.timestamp() > cutoff]
        
        if not recent:
            return 0.0
        
        errors = sum(1 for r in recent if r.status_code >= 400)
        return errors / len(recent)
    
    def get_avg_response_time(self, window_minutes: int = 5) -> float:
        """Calculate average response time over time window."""
        cutoff = datetime.now().timestamp() - (window_minutes * 60)
        recent = [r for r in self._recent_requests if r.timestamp.timestamp() > cutoff]
        
        if not recent:
            return 0.0
        
        return sum(r.response_time_ms for r in recent) / len(recent)
    
    def get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.cache_hits.value + self.cache_misses.value
        if total == 0:
            return 0.0
        return self.cache_hits.value / total
    
    def get_metrics_summary(self) -> dict:
        """Get summary of all metrics."""
        return {
            "requests": {
                "total": self.request_count.value,
                "errors": self.error_count.value,
                "error_rate": self.get_error_rate(),
                "avg_response_time_ms": self.get_avg_response_time(),
            },
            "rate_limits": {
                "total": self.rate_limit_count.value,
            },
            "cache": {
                "hits": self.cache_hits.value,
                "misses": self.cache_misses.value,
                "hit_ratio": self.get_cache_hit_ratio(),
            },
            "webhooks": {
                "deliveries": self.webhook_deliveries.value,
                "failures": self.webhook_failures.value,
            },
        }


# Global metrics collector
metrics = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics."""
    
    async def dispatch(self, request: Request, call_next):
        """Record metrics for each request."""
        start_time = time.time()
        
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Get user info
        user_id = getattr(request.state, "user", None)
        ip_address = request.client.host if request.client else None
        
        # Record metrics
        metrics.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            ip_address=ip_address,
        )
        
        return response


