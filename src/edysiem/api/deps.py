"""Dependency injection da API v1 (FastAPI Depends).

O container unico e exposto em ``request.app.state.container`` no lifespan.
"""

from __future__ import annotations

from typing import cast

from fastapi import Request

from ..container import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    """Retorna o container unico da aplicacao (via request.state)."""
    return cast(ApplicationContainer, request.app.state.container)


__all__ = ["get_container"]
