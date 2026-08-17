"""Middleware da API v1.

- ``RequestIDMiddleware``: adiciona/propaga ``X-Request-ID`` (trace_id).
- ``HTTPLoggingMiddleware``: log estruturado de cada request (método, path,
  status, duração, trace_id).
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..persistence import AuditAction
from .security import AuthenticatedIdentity, is_local_peer

REQUEST_ID_HEADER = "x-request-id"

logger = logging.getLogger("edysiem.http")

Dispatch = Callable[[Request], Awaitable[Response]]
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
DEFAULT_MAX_REQUEST_BODY_BYTES = 1_048_576
MAX_REQUEST_ID_LENGTH = 128
MAX_REQUEST_PATH_LENGTH = 512


class PayloadTooLargeError(Exception):
    pass


class RequestBodyLimitMiddleware:
    """Reject oversized request bodies, including chunked bodies."""

    def __init__(self, app: ASGIApp, max_body_bytes: int | None = None) -> None:
        self.app = app
        if max_body_bytes is None:
            configured = int(
                os.environ.get("EDYSIEM_MAX_REQUEST_BODY_BYTES", DEFAULT_MAX_REQUEST_BODY_BYTES)
            )
            self.max_body_bytes = max(1024, min(configured, 16 * 1024 * 1024))
        else:
            self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                parsed_length = int(raw_length)
                if parsed_length < 0:
                    await self._reject(scope, receive, send, status_code=400)
                    return
                if parsed_length > self.max_body_bytes:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                await self._reject(scope, receive, send, status_code=400)
                return
        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    raise PayloadTooLargeError
            return message

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except PayloadTooLargeError:
            if response_started:
                raise
            await self._reject(scope, receive, send)

    @staticmethod
    async def _reject(
        scope: Scope, receive: Receive, send: Send, *, status_code: int = 413
    ) -> None:
        message = "request body too large" if status_code == 413 else "invalid content-length"
        response = JSONResponse({"detail": message}, status_code=status_code)
        await response(scope, receive, send)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Garante um ``X-Request-ID`` em toda request e o propaga no response."""

    async def dispatch(self, request: Request, call_next: Dispatch) -> Response:
        candidate = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = candidate if _valid_request_id(candidate) else uuid.uuid4().hex
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def _valid_request_id(value: str) -> bool:
    return (
        bool(value)
        and len(value) <= MAX_REQUEST_ID_LENGTH
        and all(char.isascii() and (char.isalnum() or char in "._-") for char in value)
    )


def _safe_request_id(value: object) -> str:
    return value if isinstance(value, str) and _valid_request_id(value) else "-"


def _safe_request_path(value: str) -> str:
    """Bound a path and neutralize characters that can forge log/audit lines."""

    return "".join(
        char if char.isprintable() and char not in "\r\n" else "?"
        for char in value[:MAX_REQUEST_PATH_LENGTH]
    )


class LocalPeerOnlyMiddleware:
    """Reject network peers because EDY SIEM 0.3.0 is localhost-only."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        peer = client[0] if client is not None else None
        if is_local_peer(peer):
            await self.app(scope, receive, send)
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        response = JSONResponse({"detail": "localhost access required"}, status_code=403)
        await response(scope, receive, send)


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Loga cada request com trace_id e duração."""

    async def dispatch(self, request: Request, call_next: Dispatch) -> Response:
        start = time.perf_counter()
        request_id = _safe_request_id(getattr(request.state, "request_id", "-"))
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.2fms) trace=%s",
            request.method,
            _safe_request_path(request.url.path),
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


class MutationAuditMiddleware(BaseHTTPMiddleware):
    """Persist the authenticated actor and result of every mutating API call."""

    async def dispatch(self, request: Request, call_next: Dispatch) -> Response:
        try:
            response = await call_next(request)
        except Exception:
            self._record(request, status_code=500, outcome="exception")
            raise
        if request.method not in MUTATING_METHODS or not _safe_request_path(
            request.url.path
        ).startswith("/api/"):
            return response
        self._record(
            request,
            status_code=response.status_code,
            outcome="success" if response.status_code < 400 else "failure",
        )
        return response

    @staticmethod
    def _record(request: Request, *, status_code: int, outcome: str) -> None:
        resource = _safe_request_path(request.url.path)
        if request.method not in MUTATING_METHODS or not resource.startswith("/api/"):
            return
        identity = getattr(request.state, "authenticated_identity", None)
        actor = (
            identity.identity_id
            if isinstance(identity, AuthenticatedIdentity)
            else "unauthenticated"
        )
        auth_type = identity.auth_type if isinstance(identity, AuthenticatedIdentity) else "none"
        try:
            container: Any = request.app.state.container
            container.audit_engine.record(
                actor=actor,
                action=AuditAction.API_REQUEST,
                entity_type="HTTP",
                entity_id=resource,
                current=outcome,
                details={
                    "method": request.method,
                    "resource": resource,
                    "result": status_code,
                    "request_id": _safe_request_id(getattr(request.state, "request_id", "-")),
                    "auth_type": auth_type,
                },
            )
        except Exception:
            logger.exception("failed to persist mutation audit entry")


__all__ = [
    "DEFAULT_MAX_REQUEST_BODY_BYTES",
    "MAX_REQUEST_ID_LENGTH",
    "MAX_REQUEST_PATH_LENGTH",
    "MUTATING_METHODS",
    "REQUEST_ID_HEADER",
    "HTTPLoggingMiddleware",
    "LocalPeerOnlyMiddleware",
    "MutationAuditMiddleware",
    "PayloadTooLargeError",
    "RequestBodyLimitMiddleware",
    "RequestIDMiddleware",
]
