"""Rota de criacao de alertas."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...container import ApplicationContainer
from ...detection import DetectionFinding, DetectionReason
from ...domain import RiskScore, Severity
from ..deps import get_container
from ..schemas import AlertCreateRequest, AlertCreateResponse

router = APIRouter(tags=["alerts"])


@router.post(
    "/alerts",
    response_model=AlertCreateResponse,
    summary="Cria (ou deduplica) um alerta a partir de um finding",
)
async def create_alert(
    body: AlertCreateRequest,
    container: ApplicationContainer = Depends(get_container),
) -> AlertCreateResponse:
    """Transforma um finding em um alerta operacional (risk/fingerprint/dedup)."""
    finding = DetectionFinding(
        rule_id=body.rule_id,
        event_ids=tuple(body.event_ids),
        reason=DetectionReason(
            rule_id=body.rule_id,
            condition="API: alerta manual",
            values={"title": body.title},
        ),
        severity=Severity(body.severity.lower()),
        confidence=body.confidence,
        risk_score=RiskScore(body.risk_score),
        tags=frozenset(body.tags),
    )

    result = await container.alerts.process_finding(finding)
    return AlertCreateResponse(
        alert_id=result.alert.id,
        rule_id=result.alert.rule_id,
        severity=result.alert.severity.value,
        occurrences=result.alert.occurrences,
        kind="deduplicated" if not result.was_new else "created",
    )


__all__ = ["router"]
