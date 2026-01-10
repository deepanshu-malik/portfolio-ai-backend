"""Request timeout middleware to prevent hanging requests."""

import asyncio
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts.

    Prevents requests from hanging indefinitely, which is critical
    for free tier deployments with limited resources.
    """

    def __init__(self, app, timeout: int = None):
        super().__init__(app)
        self.timeout = timeout or settings.request_timeout

    async def dispatch(self, request: Request, call_next):
        """Process request with timeout."""
        try:
            # Wrap the request handling with a timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=float(self.timeout)
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout after {self.timeout}s: "
                f"{request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Request timeout",
                    "message": f"Request took longer than {self.timeout} seconds to complete",
                },
            )
        except Exception as e:
            logger.error(f"Error in timeout middleware: {e}", exc_info=True)
            raise
