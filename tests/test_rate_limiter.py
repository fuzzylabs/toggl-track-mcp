"""Tests for rate limiter."""

import asyncio
import pytest
import time

from toggl_track_mcp.rate_limiter import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic rate limiter functionality."""
    limiter = TokenBucketRateLimiter(requests_per_second=2.0, burst_size=3)
    
    # Should allow burst requests immediately
    start = time.time()
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()
    elapsed = time.time() - start
    
    assert elapsed < 0.1  # Should be nearly instantaneous


@pytest.mark.asyncio
async def test_rate_limiter_delay():
    """Test that rate limiter delays requests when needed."""
    limiter = TokenBucketRateLimiter(requests_per_second=1.0, burst_size=1)
    
    # First request should be immediate
    start = time.time()
    await limiter.acquire()
    first_elapsed = time.time() - start
    assert first_elapsed < 0.1
    
    # Second request should be delayed
    start = time.time()
    await limiter.acquire()
    second_elapsed = time.time() - start
    assert second_elapsed >= 0.9  # Should wait ~1 second


@pytest.mark.asyncio
async def test_rate_limiter_token_refill():
    """Test that tokens are refilled over time."""
    limiter = TokenBucketRateLimiter(requests_per_second=2.0, burst_size=2)
    
    # Use all tokens
    await limiter.acquire()
    await limiter.acquire()
    
    # Wait for token refill
    await asyncio.sleep(0.6)  # Should refill ~1.2 tokens
    
    # Should have tokens available again
    start = time.time()
    await limiter.acquire()
    elapsed = time.time() - start
    assert elapsed < 0.1


def test_get_available_tokens():
    """Test getting available tokens."""
    limiter = TokenBucketRateLimiter(requests_per_second=1.0, burst_size=3)
    
    # Should start with full tokens
    assert limiter.get_available_tokens() == 3.0
    
    # Manually consume tokens (simulate)
    limiter.tokens = 1.5
    assert limiter.get_available_tokens() == 1.5