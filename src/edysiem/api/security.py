"""Security controls for the EDY SIEM API.

Operator authentication is fail-closed. A key is useful only together with an
explicit server-side identity and role; caller-controlled role headers are
never trusted. EDY Shield ingestion keeps its independent scoped credential.
"""

from __future__ import annotations

import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from ipaddress import ip_address

from fastapi import HTTPException, Request

from ..exceptions import ConfigurationException

SHIELD_INGEST_PATH = "/api/v1/ingestion/sources/edy-shield/events"
PUBLIC_OPERATOR_PATHS = frozenset({"/api/v1/health", "/api/v1/version"})
MIN_API_KEY_BYTES = 32
_IDENTITY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$")
_PLACEHOLDER_MARKERS = ("replace-with", "change-me", "changeme", "example")

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"

PERMISSIONS: dict[str, frozenset[str]] = {
    ROLE_ADMIN: frozenset({"*"}),
    ROLE_ANALYST: frozenset(
        {
            "alert:read",
            "alert:write",
            "incident:read",
            "incident:write",
            "case:read",
            "case:write",
            "rule:read",
            "rule:write",
            "intel:read",
            "intel:write",
            "asset:read",
            "asset:write",
            "detection:read",
            "pipeline:write",
        }
    ),
    ROLE_VIEWER: frozenset(
        {
            "alert:read",
            "incident:read",
            "case:read",
            "rule:read",
            "intel:read",
            "asset:read",
            "detection:read",
        }
    ),
}


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    """Identity established from server-side credential configuration."""

    identity_id: str
    role: str
    auth_type: str = "api_key"


@dataclass(frozen=True, slots=True)
class _OperatorCredential:
    api_key: str
    identity: AuthenticatedIdentity


def api_key_expected() -> str | None:
    """Return the configured operator key, without enabling open mode."""

    value = os.environ.get("EDYSIEM_API_KEY", "").strip()
    return value or None


def _operator_credential() -> _OperatorCredential | None:
    key = api_key_expected()
    identity_id = os.environ.get("EDYSIEM_API_IDENTITY", "").strip()
    role = os.environ.get("EDYSIEM_API_ROLE", "").strip().lower()
    configured = (key, identity_id, role)
    if not any(configured):
        return None
    if not all(configured):
        raise HTTPException(status_code=503, detail="operator authentication is misconfigured")
    if key is None:  # Defensive narrowing; the partial-config branch above rejects this.
        raise HTTPException(status_code=503, detail="operator authentication is misconfigured")
    lowered = key.lower()
    if len(key.encode("utf-8")) < MIN_API_KEY_BYTES or any(
        marker in lowered for marker in _PLACEHOLDER_MARKERS
    ):
        raise HTTPException(status_code=503, detail="operator authentication is misconfigured")
    if _IDENTITY_PATTERN.fullmatch(identity_id) is None or role not in PERMISSIONS:
        raise HTTPException(status_code=503, detail="operator authentication is misconfigured")
    _reject_credential_collision(key, _raw_shield_tokens())
    return _OperatorCredential(key, AuthenticatedIdentity(identity_id=identity_id, role=role))


def operator_auth_configured() -> bool:
    """Return whether a complete, valid operator credential is configured."""

    try:
        return _operator_credential() is not None
    except HTTPException:
        return False


async def authenticate_operator(request: Request) -> AuthenticatedIdentity:
    """Authenticate one operator and cache the bound identity on the request."""

    cached = getattr(request.state, "authenticated_identity", None)
    if isinstance(cached, AuthenticatedIdentity):
        return cached
    credential = _operator_credential()
    if credential is None:
        raise HTTPException(status_code=503, detail="operator authentication is not configured")
    provided = request.headers.get("x-api-key", "")
    if not provided or not secrets.compare_digest(provided, credential.api_key):
        raise HTTPException(
            status_code=401,
            detail="invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    request.state.authenticated_identity = credential.identity
    return credential.identity


async def require_api_key(request: Request) -> None:
    """Require operator auth globally, except public health and scoped ingestion."""

    if request.url.path == SHIELD_INGEST_PATH or request.url.path in PUBLIC_OPERATOR_PATHS:
        return
    await authenticate_operator(request)


async def get_authenticated_identity(request: Request) -> AuthenticatedIdentity:
    """FastAPI dependency returning the authenticated server-side identity."""

    return await authenticate_operator(request)


def require_permission(permission: str) -> Callable[..., Awaitable[None]]:
    """Require a permission derived from the authenticated identity's role."""

    async def dependency(request: Request) -> None:
        identity = await authenticate_operator(request)
        perms = PERMISSIONS.get(identity.role, frozenset())
        if "*" not in perms and permission not in perms:
            raise HTTPException(status_code=403, detail=f"insufficient permission: {permission}")

    return dependency


def _raw_shield_tokens() -> tuple[str, ...]:
    current = os.environ.get("EDYSIEM_SHIELD_INGEST_TOKEN", "")
    previous = os.environ.get("EDYSIEM_SHIELD_INGEST_PREVIOUS_TOKEN", "")
    return tuple(token for token in (current, previous) if token)


def _reject_credential_collision(operator_key: str | None, shield_tokens: tuple[str, ...]) -> None:
    """Fail closed when operator and producer credentials are not separated."""

    if operator_key is None:
        return
    collision = False
    for token in shield_tokens:
        collision = secrets.compare_digest(operator_key, token) or collision
    if collision:
        raise HTTPException(status_code=503, detail="credential configuration is invalid")


def validate_credential_separation() -> None:
    """Reject an application configuration that reuses a scoped credential."""

    try:
        _reject_credential_collision(api_key_expected(), _raw_shield_tokens())
    except HTTPException as exc:
        raise ConfigurationException("credential configuration is invalid") from exc


def _shield_tokens() -> tuple[str, ...]:
    configured = _raw_shield_tokens()
    current = os.environ.get("EDYSIEM_SHIELD_INGEST_TOKEN", "")
    if not current:
        raise HTTPException(status_code=503, detail="Shield ingestion is not configured")
    if any(len(token.encode("utf-8")) < MIN_API_KEY_BYTES for token in configured):
        raise HTTPException(status_code=503, detail="Shield ingestion configuration is invalid")
    _reject_credential_collision(api_key_expected(), configured)
    return configured


def _is_loopback(host: str | None) -> bool:
    if host is None:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def is_local_peer(host: str | None) -> bool:
    """Return whether an ASGI peer is local; ``testclient`` is test-only."""

    return host == "testclient" or _is_loopback(host)


async def require_shield_ingest_token(request: Request) -> None:
    """Authenticate the Shield producer with a scoped, rotatable Bearer token."""

    peer = request.client.host if request.client is not None else None
    if request.url.scheme != "https" and not is_local_peer(peer):
        raise HTTPException(status_code=400, detail="HTTPS is required for Shield ingestion")
    expected_tokens = _shield_tokens()
    authorization = request.headers.get("authorization", "")
    scheme, separator, provided = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not provided:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    authenticated = False
    for expected in expected_tokens:
        authenticated = secrets.compare_digest(provided, expected) or authenticated
    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Invalid Shield ingestion credential",
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.authenticated_identity = AuthenticatedIdentity(
        identity_id="edy-shield", role=ROLE_VIEWER, auth_type="shield_m2m"
    )


@dataclass
class _Bucket:
    hits: deque[float] = field(default_factory=deque)


def rate_limit(max_requests: int = 300, window_seconds: int = 60) -> Callable[..., Awaitable[None]]:
    """Limit requests per peer IP in an in-memory sliding window."""

    buckets: dict[str, _Bucket] = defaultdict(_Bucket)
    lock = threading.Lock()

    async def dependency(request: Request) -> None:
        client = request.client
        key = client.host if client is not None else "unknown"
        now = time.monotonic()
        with lock:
            bucket = buckets[key]
            while bucket.hits and now - bucket.hits[0] > window_seconds:
                bucket.hits.popleft()
            if len(bucket.hits) >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="rate limit exceeded",
                    headers={"Retry-After": str(window_seconds)},
                )
            bucket.hits.append(now)

    return dependency


__all__ = [
    "MIN_API_KEY_BYTES",
    "PERMISSIONS",
    "PUBLIC_OPERATOR_PATHS",
    "ROLE_ADMIN",
    "ROLE_ANALYST",
    "ROLE_VIEWER",
    "SHIELD_INGEST_PATH",
    "AuthenticatedIdentity",
    "api_key_expected",
    "authenticate_operator",
    "get_authenticated_identity",
    "is_local_peer",
    "operator_auth_configured",
    "rate_limit",
    "require_api_key",
    "require_permission",
    "require_shield_ingest_token",
    "validate_credential_separation",
]
