"""Alert Builder do Alert Framework.

Transforma um ``DetectionFinding`` (saida do Detection Framework) em
um ``Alert`` operacional, aplicando risco e fingerprint.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .._utils import utcnow as _utcnow
from ..domain import EnrichedEvent, RiskScore
from .exceptions import AlertBuilderError
from .fingerprint import FingerprintEngine
from .models import (
    Alert,
    AlertLifecycle,
    AlertPriority,
    AlertSeverity,
    AlertTimelineEntry,
)
from .risk import RiskEngine

_SEVERITY_MAP = {
    "info": AlertSeverity.INFO,
    "low": AlertSeverity.LOW,
    "medium": AlertSeverity.MEDIUM,
    "high": AlertSeverity.HIGH,
    "critical": AlertSeverity.CRITICAL,
}


class AlertBuilder:
    """Constroi ``Alert`` a partir de um ``DetectionFinding``.

    Args:
        fingerprint_engine: Engine de fingerprint.
        risk_engine: Engine de risco.
    """

    def __init__(
        self,
        fingerprint_engine: FingerprintEngine | None = None,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self._fingerprints = fingerprint_engine or FingerprintEngine()
        self._risk = risk_engine or RiskEngine()

    def build(
        self,
        finding: Any,
        source_event: EnrichedEvent | None = None,
        *,
        title: str | None = None,
        identity: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> Alert:
        """Monta um alerta a partir de um ``DetectionFinding``.

        Args:
            finding: ``DetectionFinding`` com rule_id, reason, severity,
                confidence, risk_score, event_ids.
            source_event: Evento de origem (para campos de identidade).
            title: Titulo customizado (default: name da regra).
            identity: Campos adicionais de identidade.
            now: Carimbo de referencia (default: UTC agora).

        Returns:
            ``Alert`` com fingerprint, risco e timeline inicial.

        Raises:
            AlertBuilderError: Se o finding nao tem rule_id.
        """
        rule_id = getattr(finding, "rule_id", "") or ""
        if not rule_id:
            raise AlertBuilderError("finding nao possui rule_id")

        now = now or _utcnow()

        severity = self._map_severity(getattr(finding, "severity", None))
        confidence = float(getattr(finding, "confidence", 1.0))
        finding_risk = getattr(finding, "risk_score", None)

        # Risco avaliado pelo RiskEngine (preparado para multiplos fatores)
        risk = self._risk.evaluate(severity=severity, confidence=confidence)
        # Se o finding ja trouxe risco proprio, prioriza a agregacao
        if finding_risk is not None and isinstance(finding_risk, RiskScore):
            risk = finding_risk

        fingerprint = self._fingerprints.compute(rule_id, source_event, identity)

        alert_title = title or f"Alerta {rule_id}"
        description = str(getattr(finding, "reason", None) or "")

        timeline = (
            AlertTimelineEntry(
                action="created",
                detail=f"Alerta criado pela regra {rule_id}",
                created_at=now,
            ),
        )

        return Alert(
            title=alert_title,
            description=description,
            severity=severity,
            priority=self._priority_from_risk(risk),
            risk_score=risk,
            confidence=confidence,
            first_seen=now,
            last_seen=now,
            occurrences=1,
            status=AlertLifecycle.OPEN,
            source="detection",
            rule_id=rule_id,
            tags=frozenset(getattr(finding, "tags", frozenset())),
            timeline=timeline,
            fingerprint=fingerprint,
            event_ids=tuple(getattr(finding, "event_ids", ())),
            mitre=frozenset(getattr(finding, "mitre", frozenset())),
            asset_id=getattr(finding, "asset_id", None),
            user=getattr(finding, "user", None),
            ioc_ids=tuple(getattr(finding, "ioc_ids", ())),
        )

    @staticmethod
    def _map_severity(severity: Any) -> AlertSeverity:
        """Mapeia severidade (enum ou string) para ``AlertSeverity``."""
        if severity is None:
            return AlertSeverity.MEDIUM
        if isinstance(severity, AlertSeverity):
            return severity
        value = severity.value if hasattr(severity, "value") else str(severity)
        return _SEVERITY_MAP.get(str(value).lower(), AlertSeverity.MEDIUM)

    @staticmethod
    def _priority_from_risk(risk: RiskScore) -> AlertPriority:
        """Deriva prioridade a partir do risk_score."""
        value = risk.value
        if value >= 80:
            return AlertPriority.P1
        if value >= 60:
            return AlertPriority.P2
        if value >= 40:
            return AlertPriority.P3
        if value >= 20:
            return AlertPriority.P4
        return AlertPriority.P5


__all__ = ["_SEVERITY_MAP", "AlertBuilder"]
