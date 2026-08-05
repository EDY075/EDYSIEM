"""Factory da API v1 (FastAPI).

Cria a aplicacao FastAPI com:
- Lifespan (startup/shutdown): inicializa engines e finaliza graciosamente
- Middleware de RequestID + HTTP logging
- Error handlers globais + validation handler
- Rotas: /health, /version, /metrics, /pipeline/run, /alerts, /incidents, /cases
- OpenAPI + Swagger (/docs) e ReDoc (/redoc)
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from ..bootstrap import version
from ..config import load
from ..container import ApplicationContainer
from .errors import register_error_handlers
from .middleware import HTTPLoggingMiddleware, RequestIDMiddleware
from .routes import alerts, cases, health, incidents, pipeline, soc


def _build_lifespan(
    container: ApplicationContainer,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # startup
        await container.enrichment.initialize()
        await container.correlation.initialize()
        await container.detection.rule_engine.initialize()
        yield
        # shutdown
        await container.enrichment.shutdown()
        await container.correlation.shutdown()
        await container.detection.rule_engine.shutdown()

    return lifespan


def create_app(container: ApplicationContainer | None = None) -> FastAPI:
    """Cria a aplicacao FastAPI.

    Args:
        container: Container unico (default: construido via bootstrap).
    """
    cfg = load().unwrap()
    container = container or ApplicationContainer(cfg)

    app = FastAPI(
        title=cfg.project_name,
        version=version(),
        description="EDY SIEM - API v1 (pipeline, alertas, incidentes, cases)",
        lifespan=_build_lifespan(container),
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Container acessivel por request.state (independente do lifespan)
    app.state.container = container

    # Middleware (ordem: RequestID antes do logging)
    app.add_middleware(HTTPLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Error handlers globais
    register_error_handlers(app)

    # Rotas
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(pipeline.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(incidents.router, prefix="/api/v1")
    app.include_router(cases.router, prefix="/api/v1")
    app.include_router(soc.router, prefix="/api/v1")

    return app


__all__ = ["create_app"]
