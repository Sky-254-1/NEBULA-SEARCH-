"""
Circuit breaker middleware and utilities for external service calls.
Prevents cascading failures when dependencies are down.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """Circuit breaker for async operations."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit breaker %s entering HALF_OPEN state", self.name)
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as exc:
            await self._on_failure()
            raise exc

    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info("Circuit breaker %s closed (recovered)", self.name)
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                # Gradually reduce failure count on success
                self.failure_count = max(0, self.failure_count - 1)

    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()

            if self.failure_count >= self.failure_threshold:
                logger.error(
                    "Circuit breaker %s opened after %d failures", self.name, self.failure_count
                )
                self.state = CircuitState.OPEN

    def get_state(self) -> dict:
        """Get current circuit breaker state for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
        }


# Global circuit breakers for external services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    return _circuit_breakers[name]


# Pre-defined circuit breakers for common services
elasticsearch_breaker = get_circuit_breaker("elasticsearch")
redis_breaker = get_circuit_breaker("redis")
openai_breaker = get_circuit_breaker("openai")
rabbitmq_breaker = get_circuit_breaker("rabbitmq")
kafka_breaker = get_circuit_breaker("kafka")


# FastAPI middleware for circuit breaker monitoring
class CircuitBreakerMiddleware:
    """Middleware to track circuit breaker state in request context."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Add circuit breaker states to request state
        from starlette.requests import Request

        request = Request(scope, receive)
        request.state.circuit_breakers = {
            name: breaker.get_state() for name, breaker in _circuit_breakers.items()
        }

        await self.app(scope, receive, send)