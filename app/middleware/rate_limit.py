"""In-memory rate limiting middleware."""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding window rate limiter.
    Limits requests per session_id or IP address.
    """

    def __init__(self, app, requests: int = None, window: int = None):
        super().__init__(app)
        self.requests = requests or settings.rate_limit_requests
        self.window = window or settings.rate_limit_window
        self.clients: Dict[str, list] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try session_id from body (for POST) or use IP
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        """Check if client is rate limited. Returns (is_limited, retry_after)."""
        now = time.time()
        window_start = now - self.window

        # Clean old requests
        self.clients[client_id] = [
            ts for ts in self.clients[client_id] if ts > window_start
        ]

        if len(self.clients[client_id]) >= self.requests:
            oldest = min(self.clients[client_id])
            retry_after = int(oldest + self.window - now) + 1
            return True, retry_after

        self.clients[client_id].append(now)
        return False, 0

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path == "/api/health" or request.url.path == "/":
            return await call_next(request)

        client_id = self._get_client_id(request)
        is_limited, retry_after = self._is_rate_limited(client_id)

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        return response
