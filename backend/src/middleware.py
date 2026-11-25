"""
Middleware for the LatMatrix API.

Provides request/response logging with timing information.
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from logging_config import get_logger, get_file_debug_logger

logger = get_logger(__name__)
debug_logger = get_file_debug_logger("middleware_debug")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests with timing and response status.

    Logs include method, path, query parameters, status code, and duration.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process a request and log it with timing information.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            The response from the next handler
        """
        # Record start time
        start_time = time.time()

        # Extract request information
        method = request.method
        path = request.url.path

        # For POST requests, log Content-Type and Content-Length headers
        # instead of query params (main endpoints use form data, not query params).
        if method == "POST":
            content_type = request.headers.get("content-type", "")
            content_length = request.headers.get("content-length", "")
            request_details = {
                "content_type": content_type,
                "content_length": content_length,
            }
        else:
            request_details = dict(request.query_params) if request.query_params else {}

        debug_logger.debug(
            f"Request received: {method} {path}",
            extra={"method": method, "path": path, "request_details": request_details},
        )

        try:
            # Get the response
            response = await call_next(request)
        except Exception as exc:
            debug_logger.debug(
                f"Exception during request processing: {type(exc).__name__}: {exc}",
                exc_info=True,
            )
            raise

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        debug_logger.debug(
            f"Response: {method} {path} -> {response.status_code}",
            extra={
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        # Log request with timing
        logger.info(
            f"{method} {path} - {response.status_code}",
            extra={
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "request_details": request_details,
            },
        )

        return response
