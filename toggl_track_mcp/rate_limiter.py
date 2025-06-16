"""Rate limiting utilities for Toggl Track API."""

import asyncio
import time


class TokenBucketRateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 1.0, burst_size: int = 3):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum sustained request rate
            burst_size: Maximum number of requests that can be made immediately
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = time.time()
            # Add tokens based on time passed
            time_passed = now - self.last_update
            self.tokens = min(
                self.burst_size, self.tokens + time_passed * self.requests_per_second
            )
            self.last_update = now

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return

            # Need to wait for tokens
            wait_time = (1.0 - self.tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)
            self.tokens = 0.0

    def get_available_tokens(self) -> float:
        """Get number of tokens currently available."""
        now = time.time()
        time_passed = now - self.last_update
        return min(
            self.burst_size, self.tokens + time_passed * self.requests_per_second
        )
