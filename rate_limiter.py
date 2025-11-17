#!/usr/bin/env python3
import asyncio
import time
from collections import deque
from typing import Protocol, runtime_checkable, Optional

# Python's Protocol is Duck Typing
@runtime_checkable
class RateLimiter(Protocol):
    """
    Protocol (interface) for rate limiters.
    All rate limiters must implement the acquire() method.
    """
    
    async def acquire(self) -> None:
        """
        Acquire permission to make a request.
        Blocks until permission is granted.
        """
        ...


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling request rates.
    Allows bursts up to max_tokens while maintaining average rate.
    """
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds (e.g., 1.0 for per second, 60.0 for per minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.tokens = max_requests
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Acquire permission to make a request.
        Blocks until a token is available.
        """
        async with self.lock:
            while True:
                now = time.monotonic()
                time_passed = now - self.last_update
                
                # Refill tokens based on time passed
                self.tokens = min(
                    self.max_requests,
                    self.tokens + (time_passed * self.max_requests / self.time_window)
                )
                self.last_update = now
                
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                
                # Wait until next token is available
                wait_time = (1.0 - self.tokens) * self.time_window / self.max_requests
                await asyncio.sleep(wait_time)


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter that tracks exact timestamps.
    More accurate but uses more memory.
    """
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Acquire permission to make a request.
        Blocks until rate limit allows.
        """
        async with self.lock:
            now = time.monotonic()
            
            # Remove old requests outside the time window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()
            
            # If at limit, wait until oldest request expires
            if len(self.requests) >= self.max_requests:
                wait_time = self.requests[0] + self.time_window - now
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Recursively call to handle the request after waiting
                    return await self.acquire()
            
            # Record this request
            self.requests.append(now)


class LeakyBucketRateLimiter:
    """
    Leaky bucket rate limiter that processes requests at a constant rate.
    Smooths out bursts to a steady flow.
    """
    
    def __init__(self, rate: float):
        """
        Initialize the rate limiter.
        
        Args:
            rate: Requests per second (e.g., 2.0 for 2 req/sec)
        """
        self.rate = rate
        self.last_request_time: Optional[float] = None
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Acquire permission to make a request.
        Enforces constant spacing between requests.
        """
        async with self.lock:
            now = time.monotonic()
            
            if self.last_request_time is not None:
                time_since_last = now - self.last_request_time
                required_spacing = 1.0 / self.rate
                
                if time_since_last < required_spacing:
                    wait_time = required_spacing - time_since_last
                    await asyncio.sleep(wait_time)
            
            self.last_request_time = time.monotonic()


# Example usage and comparison
async def test_rate_limiters():
    """Test different rate limiter implementations."""
    
    print("Testing Token Bucket Rate Limiter (10 req/sec):")
    print("=" * 50)
    limiter1 = TokenBucketRateLimiter(max_requests=10, time_window=1.0)
    
    start = time.monotonic()
    for i in range(15):
        await limiter1.acquire()
        elapsed = time.monotonic() - start
        print(f"Request {i+1:2d} at {elapsed:.3f}s")
    print()
    
    print("Testing Sliding Window Rate Limiter (5 req/sec):")
    print("=" * 50)
    limiter2 = SlidingWindowRateLimiter(max_requests=5, time_window=1.0)
    
    start = time.monotonic()
    for i in range(10):
        await limiter2.acquire()
        elapsed = time.monotonic() - start
        print(f"Request {i+1:2d} at {elapsed:.3f}s")
    print()
    
    print("Testing Leaky Bucket Rate Limiter (3 req/sec):")
    print("=" * 50)
    limiter3 = LeakyBucketRateLimiter(rate=3.0)
    
    start = time.monotonic()
    for i in range(9):
        await limiter3.acquire()
        elapsed = time.monotonic() - start
        print(f"Request {i+1:2d} at {elapsed:.3f}s")


if __name__ == "__main__":
    asyncio.run(test_rate_limiters())
