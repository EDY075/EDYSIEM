"""Dependency injection da API v1 (FastAPI Depends).

O container unico e exposto em ``request.app.state.container`` no lifespan.
"""

from __future__ import annotations

from typing import cast

from fastapi import HTTPException, Request

from ..container import ApplicationContainer
from ..persistence import PersistenceError, ShieldInboxRepository


def get_container(request: Request) -> ApplicationContainer:
    """Retorna o container unico da aplicacao (via request.state)."""
    return cast(ApplicationContainer, request.app.state.container)


def get_shield_inbox(request: Request) -> ShieldInboxRepository:
    """Return the durable inbox configured for the Shield ingestion route."""

    container = cast(ApplicationContainer, request.app.state.container)
    try:
        return container.shield_inbox
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="ingestion inbox unavailable") from exc


__all__ = ["get_container", "get_shield_inbox"]
