"""
Rate Limiting middleware for CloudGuard AI API.

Uses in-memory token bucket algorithm with per-IP tracking.
In production, swap to Redis-backed limiter for multi-instance deployments.
"""

import logging
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket rate limiter for a single client."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def retry_after(self) -> float:
        """Seconds until a token is available."""
        if self.tokens >= 1:
            return 0.0
        return (1 - self.tokens) / self.rate


class RateLimitStore:
    """In-memory store for rate limit buckets, keyed by client IP."""

    def __init__(self, rate: float = 10.0, capacity: int = 60):
        self._buckets: dict[str, TokenBucket] = defaultdict(lambda: TokenBucket(rate, capacity))
        self.rate = rate
        self.capacity = capacity

    def check(self, client_id: str) -> tuple[bool, float]:
        bucket = self._buckets[client_id]
        allowed = bucket.consume()
        return allowed, bucket.retry_after

    def cleanup(self, max_age: float = 3600):
        """Remove stale entries older than max_age seconds."""
        now = time.monotonic()
        stale = [k for k, v in self._buckets.items() if now - v.last_refill > max_age]
        for k in stale:
            del self._buckets[k]


# Global stores — different limits for different endpoint groups
_general_limiter = RateLimitStore(rate=10.0, capacity=60)  # 10 req/s, burst 60
_scan_limiter = RateLimitStore(rate=2.0, capacity=10)  # 2 scans/s, burst 10
_auth_limiter = RateLimitStore(rate=5.0, capacity=20)  # 5 auth/s, burst 20


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    - /scan endpoint: 2 requests/second (heavy operation)
    - /auth/* endpoints: 5 requests/second (prevent brute force)
    - Everything else: 10 requests/second
    """

    async def dispatch(self, request: Request, call_next):
        client_ip = _get_client_ip(request)
        path = request.url.path

        # Select appropriate limiter
        if path.startswith("/scan"):
            allowed, retry_after = _scan_limiter.check(client_ip)
        elif path.startswith("/auth"):
            allowed, retry_after = _auth_limiter.check(client_ip)
        else:
            allowed, retry_after = _general_limiter.check(client_ip)

        if not allowed:
            logger.warning("Rate limit exceeded for %s on %s", client_ip, path)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please slow down.",
                    "retry_after": round(retry_after, 2),
                },
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(_general_limiter.capacity)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, int(_general_limiter._buckets[client_ip].tokens))
        )

        return response
