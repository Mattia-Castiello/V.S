import asyncio
import time


class AsyncTokenBucket:
    """Async token bucket rate limiter."""

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: tokens added per second
            capacity: maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        """Wait until tokens are available, then consume them."""
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                # Calculate wait time for enough tokens
                needed = tokens - self._tokens
                wait = needed / self.rate
                await asyncio.sleep(wait)

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now


# Global rate limiter for Vinted API: 20 requests per minute
vinted_limiter = AsyncTokenBucket(rate=20 / 60, capacity=20)

# Global rate limiter for SerpAPI: more conservative
serpapi_limiter = AsyncTokenBucket(rate=1 / 3, capacity=5)
