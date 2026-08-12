"""Rotas de health, version e metrics."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...bootstrap import version
from ...config import load
from ...container import ApplicationContainer
from ..deps import get_container
from ..schemas import HealthComponent, HealthResponse, MetricsResponse, VersionResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(container: ApplicationContainer = Depends(get_container)) -> HealthResponse:
    """Estado agregado dos engines da plataforma."""
    components: dict[str, HealthComponent] = {}
    environment = load().unwrap().environment.value

    try:
        ingestion = container.shield_inbox.health_snapshot()
        components["ingestion"] = HealthComponent(
            status="online",
            details={
                "receiver": "edy-shield",
                "receiver_state": "ready",
                **ingestion,
            },
        )
    except Exception:
        components["ingestion"] = HealthComponent(status="error")

    try:
        container.shield_inbox.manager.connect().execute("SELECT 1").fetchone()
        components["storage"] = HealthComponent(status="online")
    except Exception:
        components["storage"] = HealthComponent(status="error")

    try:
        components["enrichment"] = HealthComponent(
            status=(await container.enrichment.health_check())["engine"]
        )
    except Exception:
        components["enrichment"] = HealthComponent(status="error")

    try:
        components["correlation"] = HealthComponent(
            status=(await container.correlation.health_check())["engine"]
        )
    except Exception:
        components["correlation"] = HealthComponent(status="error")

    try:
        components["detection"] = HealthComponent(
            status=(await container.detection.rule_engine.health_check())["engine"]
        )
    except Exception:
        components["detection"] = HealthComponent(status="error")

    components["alerts"] = HealthComponent(status="online")
    components["incidents"] = HealthComponent(status="online")
    components["cases"] = HealthComponent(status="online")
    components["api"] = HealthComponent(status="online")

    healthy_statuses = {"healthy", "online"}
    overall = (
        "healthy" if all(c.status in healthy_statuses for c in components.values()) else "degraded"
    )
    return HealthResponse(
        status=overall,
        version=version(),
        environment=environment,
        components=components,
    )


@router.get("/version", response_model=VersionResponse, summary="Versao da plataforma")
async def get_version() -> VersionResponse:
    """Nome, versao e ambiente da plataforma."""
    cfg = load().unwrap()
    return VersionResponse(
        name=cfg.project_name,
        version=version(),
        environment=cfg.environment.value,
    )


@router.get("/metrics", response_model=MetricsResponse, summary="Metricas da plataforma")
async def metrics(container: ApplicationContainer = Depends(get_container)) -> MetricsResponse:
    """Metricas agregadas e por engine."""
    m = container.metrics
    components = {
        "enrichment": container.enrichment.get_metrics_snapshot(),
        "correlation": container.correlation.get_metrics_snapshot(),
        "detection": container.detection.get_metrics_snapshot(),
        "alerts": container.alerts.get_metrics_snapshot(),
        "incidents": container.incidents.get_metrics_snapshot(),
        "cases": container.cases.get_metrics_snapshot(),
    }
    return MetricsResponse(metrics=m.snapshot(), components=components)


__all__ = ["router"]
