"""Middleware da API v1.

- ``RequestIDMiddleware``: adiciona/propaga ``X-Request-ID`` (trace_id).
- ``HTTPLoggingMiddleware``: log estruturado de cada request (método, path,
  status, duração, trace_id).
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "x-request-id"

logger = logging.getLogger("edysiem.http")

Dispatch = Callable[[Request], Awaitable[Response]]


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Garante um ``X-Request-ID`` em toda request e o propaga no response."""

    async def dispatch(self, request: Request, call_next: Dispatch) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Loga cada request com trace_id e duração."""

    async def dispatch(self, request: Request, call_next: Dispatch) -> Response:
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "-")
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.2fms) trace=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


__all__ = ["REQUEST_ID_HEADER", "HTTPLoggingMiddleware", "RequestIDMiddleware"]
