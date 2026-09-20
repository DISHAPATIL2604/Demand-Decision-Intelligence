"""
FastAPI Application Middleware
Project: Demand-Decision-Intelligence
Location: backend/core/middleware.py

Features:
- Request correlation ID (X-Request-ID)
- Request execution timing (X-Process-Time)
- Structured access logging
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("ddi.middleware")
logging.basicConfig(level=logging.INFO)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"Unhandled Exception: path={request.url.path} method={request.method} "
                f"correlation_id={correlation_id} duration_ms={duration_ms:.2f} error={exc}",
                exc_info=True
            )
            raise exc

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Request-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        logger.info(
            f"HTTP {request.method} {request.url.path} -> {response.status_code} "
            f"({duration_ms:.2f}ms) [id={correlation_id}]"
        )
        return response
