"""Retry logic with exponential backoff for indexing jobs."""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.indexing.config import get_indexing_config

logger = logging.getLogger("nebula.indexing.retry")


class RetryStrategy(str, Enum):
    """Retry strategies."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_retries: int
    base_delay: float  # seconds
    max_delay: float = 300.0  # 5 minutes
    backoff_multiplier: float = 3.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    
    # Errors that should NOT be retried
    non_retryable_errors: tuple = (
        "unsupported file",
        "corrupt document",
        "permission denied",
        "file not found",
        "invalid format",
    )
    
    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """
        Determine if error should be retried.
        
        Args:
            error: Exception that occurred
            retry_count: Current retry count
            
        Returns:
            True if should retry
        """
        if retry_count >= self.max_retries:
            return False
        
        error_message = str(error).lower()
        
        # Check for non-retryable errors
        for non_retryable in self.non_retryable_errors:
            if non_retryable in error_message:
                logger.info("Not retrying non-retryable error: %s", error_message)
                return False
        
        return True
    
    def get_delay(self, retry_count: int) -> float:
        """
        Calculate delay before next retry.
        
        Args:
            retry_count: Current retry count (0-based)
            
        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.backoff_multiplier ** retry_count)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (retry_count + 1)
        else:  # FIXED
            delay = self.base_delay
        
        # Apply max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter (±20%) to prevent thundering herd
        if self.jitter:
            jitter_amount = delay * 0.2
            delay = delay + random.uniform(-jitter_amount, jitter_amount)  # nosec B311: intentional non-cryptographic jitter for retry backoff
        
        return max(0.1, delay)


class RetryHandler:
    """Manages retry logic for indexing jobs."""
    
    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self._policy = policy or RetryPolicy(
            max_retries=get_indexing_config().max_retries,
            base_delay=get_indexing_config().retry_base_delay,
            backoff_multiplier=get_indexing_config().retry_backoff_multiplier,
        )
    
    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """Check if job should be retried."""
        return self._policy.should_retry(error, retry_count)
    
    def get_delay(self, retry_count: int) -> float:
        """Get delay before next retry."""
        return self._policy.get_delay(retry_count)
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """
        Execute function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of function
            
        Raises:
            Last exception if all retries fail
        """
        last_error = None
        
        for attempt in range(self._policy.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                
                if not self.should_retry(exc, attempt):
                    logger.error(
                        "Job failed after %d attempts: %s",
                        attempt + 1,
                        str(exc),
                    )
                    raise
                
                delay = self.get_delay(attempt)
                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.1f seconds",
                    attempt + 1,
                    self._policy.max_retries,
                    str(exc),
                    delay,
                )
                
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_error


import asyncio


# Global retry handler
retry_handler = RetryHandler()


def get_retry_handler() -> RetryHandler:
    """Get global retry handler."""
    return retry_handler