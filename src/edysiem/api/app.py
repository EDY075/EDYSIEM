"""Factory da API v1 (FastAPI).

Cria a aplicacao FastAPI com:
- Lifespan (startup/shutdown): inicializa engines e finaliza graciosamente
- Middleware de RequestID + HTTP logging
- Error handlers globais + validation handler
- Rotas: /health, /version, /metrics, /pipeline/run, /alerts, /incidents, /cases
- OpenAPI + Swagger (/docs) e ReDoc (/redoc)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from ipaddress import ip_address

from fastapi import Depends, FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from ..bootstrap import version
from ..config import load
from ..container import ApplicationContainer
from .errors import register_error_handlers
from .middleware import (
    HTTPLoggingMiddleware,
    LocalPeerOnlyMiddleware,
    MutationAuditMiddleware,
    RequestBodyLimitMiddleware,
    RequestIDMiddleware,
)
from .routes import (
    alerts,
    auth,
    cases,
    health,
    incidents,
    pipeline,
    shield_ingestion,
    shield_investigation,
    soc,
)
from .security import require_api_key, validate_credential_separation

_LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]


def _dev_docs_enabled(environment: str, configured_host: str) -> bool:
    explicit = os.environ.get("EDYSIEM_ENABLE_DEV_DOCS", "").strip().lower()
    try:
        local_host = (
            configured_host.lower() == "localhost" or ip_address(configured_host).is_loopback
        )
    except ValueError:
        local_host = False
    return explicit in {"1", "true", "yes", "on"} and environment == "development" and local_host


def _build_lifespan(
    container: ApplicationContainer,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # startup
        await container.enrichment.initialize()
        await container.correlation.initialize()
        await container.detection.rule_engine.initialize()
        try:
            yield
        finally:
            # shutdown
            await container.enrichment.shutdown()
            await container.correlation.shutdown()
            await container.detection.rule_engine.shutdown()
            container.close_persistence()

    return lifespan


def create_app(container: ApplicationContainer | None = None) -> FastAPI:
    """Cria a aplicacao FastAPI.

    Args:
        container: Container unico (default: construido via bootstrap).
    """
    cfg = load().unwrap()
    validate_credential_separation()
    container = container or ApplicationContainer(cfg)
    docs_enabled = _dev_docs_enabled(cfg.environment.value, cfg.app.host)

    app = FastAPI(
        title=cfg.project_name,
        version=version(),
        description="EDY SIEM - API v1 (pipeline, alertas, incidentes, cases)",
        lifespan=_build_lifespan(container),
        openapi_url="/openapi.json" if docs_enabled else None,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        # Operator authentication is fail-closed; health and Shield ingestion
        # have explicit, narrowly scoped exceptions in require_api_key.
        dependencies=[Depends(require_api_key)],
    )

    # Container acessivel por request.state (independente do lifespan)
    app.state.container = container

    # add_middleware wraps in reverse registration order.
    app.add_middleware(HTTPLoggingMiddleware)
    app.add_middleware(RequestBodyLimitMiddleware)
    app.add_middleware(MutationAuditMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_LOCAL_HOSTS)
    app.add_middleware(LocalPeerOnlyMiddleware)

    # Error handlers globais
    register_error_handlers(app)

    # Rotas
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(pipeline.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(incidents.router, prefix="/api/v1")
    app.include_router(cases.router, prefix="/api/v1")
    app.include_router(soc.router, prefix="/api/v1")
    app.include_router(shield_ingestion.router, prefix="/api/v1")
    app.include_router(shield_investigation.router, prefix="/api/v1")

    return app


__all__ = ["create_app"]
