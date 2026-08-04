"""Error handlers da API v1.

- Handler global: qualquer excecao nao tratada -> 500 estruturado com trace_id.
- Handler de validacao (pydantic.ValidationError) -> 422 com detalhes.
- Handler de regras de negocio do domínio -> 400/404/409 conforme hierarquia.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..exceptions import (
    ConfigurationException,
    DomainException,
    EdysiemException,
    InfrastructureException,
)

logger = logging.getLogger("edysiem.http")


def _error_payload(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
        }
    }
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        payload["trace_id"] = request_id
    if extra:
        payload["details"] = extra
    return payload


def register_error_handlers(app: FastAPI) -> None:
    """Registra os handlers de erro globais na aplicacao."""

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "loc": list(e.get("loc", [])),
                "msg": e.get("msg", ""),
                "type": e.get("type", ""),
            }
            for e in exc.errors()
        ]
        logger.warning("validation error trace=%s", getattr(request.state, "request_id", "-"))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload(
                request, "validation_error", "payload invalido", 422, {"errors": details}
            ),
        )

    @app.exception_handler(DomainException)
    async def domain_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_payload(request, "domain_error", str(exc), 400),
        )

    @app.exception_handler(ConfigurationException)
    async def config_handler(request: Request, exc: ConfigurationException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(request, "configuration_error", str(exc), 500),
        )

    @app.exception_handler(InfrastructureException)
    async def infra_handler(request: Request, exc: InfrastructureException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_payload(request, "infrastructure_error", str(exc), 503),
        )

    @app.exception_handler(EdysiemException)
    async def base_handler(request: Request, exc: EdysiemException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(request, "edysiem_error", str(exc), 500),
        )

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error trace=%s", getattr(request.state, "request_id", "-"))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(request, "internal_error", "erro interno", 500),
        )


__all__ = ["register_error_handlers"]
