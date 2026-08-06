"""Segurança da API v1 — API Key, RBAC e Rate Limit (Sprint Final).

- ``require_api_key``: autenticação por API key (**opt-in** via env
  ``EDYSIEM_API_KEY``; sem env = modo dev aberto, preserva os testes).
- ``require_permission``: RBAC por papel (header ``X-EDY-Role``; default admin).
- ``rate_limit``: limitador de janela deslizante em memória (429).

Nenhuma funcionalidade nova de negócio; apenas camadas de proteção.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from fastapi import HTTPException, Request

# --- Autenticação (API Key) -------------------------------------------------


def api_key_expected() -> str | None:
    """Chave esperada (env ``EDYSIEM_API_KEY``); ``None`` = auth desligada."""
    value = os.environ.get("EDYSIEM_API_KEY")
    return value if value else None


async def require_api_key(request: Request) -> None:
    """Exige ``X-API-Key`` quando ``EDYSIEM_API_KEY`` estiver definida."""
    expected = api_key_expected()
    if expected is None:
        return
    provided = request.headers.get("x-api-key")
    if provided != expected:
        raise HTTPException(status_code=401, detail="API key inválida")


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
                raise HTTPException(status_code=429, detail="rate limit excedido")
            bucket.hits.append(now)

    return dependency


__all__ = [
    "PERMISSIONS",
    "ROLE_ADMIN",
    "ROLE_ANALYST",
    "ROLE_VIEWER",
    "api_key_expected",
    "rate_limit",
    "require_api_key",
    "require_permission",
]
