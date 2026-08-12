"""Segurança da API v1 — API Key, RBAC e Rate Limit (Sprint Final).

- ``require_api_key``: autenticação por API key (**opt-in** via env
  ``EDYSIEM_API_KEY``; sem env = modo dev aberto, preserva os testes).
- ``require_permission``: RBAC por papel (header ``X-EDY-Role``; default admin).
- ``rate_limit``: limitador de janela deslizante em memória (429).

Nenhuma funcionalidade nova de negócio; apenas camadas de proteção.
"""

from __future__ import annotations

import os
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from ipaddress import ip_address

from fastapi import HTTPException, Request

SHIELD_INGEST_PATH = "/api/v1/ingestion/sources/edy-shield/events"

# --- Autenticação (API Key) -------------------------------------------------


def api_key_expected() -> str | None:
    """Chave esperada (env ``EDYSIEM_API_KEY``); ``None`` = auth desligada."""
    value = os.environ.get("EDYSIEM_API_KEY")
    return value if value else None


async def require_api_key(request: Request) -> None:
    """Exige ``X-API-Key`` quando ``EDYSIEM_API_KEY`` estiver definida."""
    # The Shield route has its own scoped M2M credential and must not depend on
    # the operator-facing API key used by the remaining API.
    if request.url.path == SHIELD_INGEST_PATH:
        return
    expected = api_key_expected()
    if expected is None:
        return
    provided = request.headers.get("x-api-key")
    if provided != expected:
        raise HTTPException(status_code=401, detail="API key inválida")


def _shield_tokens() -> tuple[str, ...]:
    current = os.environ.get("EDYSIEM_SHIELD_INGEST_TOKEN", "")
    previous = os.environ.get("EDYSIEM_SHIELD_INGEST_PREVIOUS_TOKEN", "")
    if not current:
        raise HTTPException(status_code=503, detail="Shield ingestion is not configured")
    configured = tuple(token for token in (current, previous) if token)
    if any(len(token.encode("utf-8")) < 32 for token in configured):
        raise HTTPException(status_code=503, detail="Shield ingestion configuration is invalid")
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


async def require_shield_ingest_token(request: Request) -> None:
    """Authenticate the Shield producer with a scoped, rotatable Bearer token."""

    if request.url.scheme != "https" and not _is_loopback(request.url.hostname):
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


# --- RBAC -------------------------------------------------------------------

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"

PERMISSIONS: dict[str, frozenset[str]] = {
    ROLE_ADMIN: frozenset({"*"}),
    ROLE_ANALYST: frozenset(
        {
            "alert:read",
            "incident:read",
            "incident:write",
            "case:read",
            "case:write",
            "rule:read",
            "rule:write",
            "intel:read",
            "intel:write",
            "detection:read",
        }
    ),
    ROLE_VIEWER: frozenset(
        {"alert:read", "incident:read", "case:read", "rule:read", "intel:read", "detection:read"}
    ),
}


def require_permission(permission: str) -> Callable[..., Awaitable[None]]:
    """Exige um papel com a permissão (header ``X-EDY-Role``; default admin)."""

    async def dependency(request: Request) -> None:
        role = request.headers.get("x-edy-role", ROLE_ADMIN)
        perms = PERMISSIONS.get(role, frozenset())
        if "*" not in perms and permission not in perms:
            raise HTTPException(status_code=403, detail=f"permissão insuficiente: {permission}")

    return dependency


# --- Rate Limit (janela deslizante, em memória) ------------------------------


@dataclass
class _Bucket:
    hits: deque[float] = field(default_factory=deque)


def rate_limit(max_requests: int = 300, window_seconds: int = 60) -> Callable[..., Awaitable[None]]:
    """Limita requisições por IP em uma janela deslizante (429 ao exceder)."""
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
                    detail="rate limit excedido",
                    headers={"Retry-After": str(window_seconds)},
                )
            bucket.hits.append(now)

    return dependency


__all__ = [
    "PERMISSIONS",
    "ROLE_ADMIN",
    "ROLE_ANALYST",
    "ROLE_VIEWER",
    "SHIELD_INGEST_PATH",
    "api_key_expected",
    "rate_limit",
    "require_api_key",
    "require_permission",
    "require_shield_ingest_token",
]
