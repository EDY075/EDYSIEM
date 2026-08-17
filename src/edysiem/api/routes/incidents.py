"""Rota de criacao de incidentes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from ...alerts import Alert, AlertFingerprint, AlertSeverity
from ...container import ApplicationContainer
from ...domain import RiskScore
from ..deps import get_container
from ..schemas import AlertPayload, IncidentCreateRequest, IncidentCreateResponse
from ..security import require_permission

router = APIRouter(tags=["incidents"])


def _to_alert(payload: AlertPayload) -> Alert:
    """Converte um payload de alerta em um ``Alert`` (sem persistence lookup)."""
    now = datetime.now(UTC)
    return Alert(
        title=payload.title,
        severity=AlertSeverity(payload.severity.lower()),
        risk_score=RiskScore(payload.risk_score),
        confidence=payload.confidence,
        rule_id=payload.rule_id,
        asset_id=payload.asset_id,
        user=payload.user,
        ioc_ids=tuple(payload.ioc_ids),
        mitre=frozenset(payload.mitre),
        fingerprint=AlertFingerprint(
            hash=payload.fingerprint_hash or f"fp-{payload.alert_id}",
            rule_id=payload.rule_id,
        ),
        first_seen=now,
        last_seen=now,
        id=payload.alert_id,
    )


@router.post(
    "/incidents",
    response_model=IncidentCreateResponse,
    summary="Cria um incidente a partir de alertas",
    dependencies=[Depends(require_permission("incident:write"))],
)
async def create_incident(
    body: IncidentCreateRequest,
    container: ApplicationContainer = Depends(get_container),
) -> IncidentCreateResponse:
    """Agrupa alertas relacionados em um incidente (grouping configuravel)."""
    alerts = [_to_alert(a) for a in body.alerts]
    result = await container.incidents.process_alerts(alerts, title=body.title)

    if result.incident is None:
        return IncidentCreateResponse(incident_id="", alerts_count=len(alerts), kind="no_group")

    return IncidentCreateResponse(
        incident_id=result.incident.id,
        alerts_count=len(result.incident.alerts),
        kind=("deduplicated" if result.kind.value == "deduplicated" else "created"),
    )


__all__ = ["router"]
