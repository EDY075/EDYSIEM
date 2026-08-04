"""Incident Builder.

Recebe multiplos ``Alert`` (um ``IncidentGroup``) e produz um unico
``Incident`` com campos agregados: severidade maxima, uniao de
assets/users/iocs/mitre, primeiro/ultimo alerta, evidencias.
"""

from __future__ import annotations

from datetime import datetime

from .._utils import utcnow as _utcnow
from ..alerts import Alert
from ..domain import RiskScore
from .exceptions import IncidentBuilderError
from .grouping import IncidentGroup
from .models import (
    Incident,
    IncidentEvidence,
    IncidentPriority,
    IncidentReason,
    IncidentSeverity,
    IncidentStatus,
    IncidentTimelineEntry,
)

_SEVERITY_RANK = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}
_SEVERITY_BY_RANK = {
    0: IncidentSeverity.INFO,
    1: IncidentSeverity.LOW,
    2: IncidentSeverity.MEDIUM,
    3: IncidentSeverity.HIGH,
    4: IncidentSeverity.CRITICAL,
}


class IncidentBuilder:
    """Constroi ``Incident`` a partir de um ``IncidentGroup``."""

    def build(
        self,
        group: IncidentGroup,
        *,
        title: str | None = None,
        now: datetime | None = None,
    ) -> Incident:
        """Monta um incidente a partir de um grupo de alertas.

        Args:
            group: Grupo de alertas correlacionados.
            title: Titulo customizado (default: nome da regra comum).
            now: Carimbo de referencia.

        Returns:
            ``Incident`` com campos agregados e timeline inicial.

        Raises:
            IncidentBuilderError: Se o grupo esta vazio.
        """
        if not group.alerts:
            raise IncidentBuilderError("grupo de alertas vazio")

        now = now or _utcnow()
        alerts = group.alerts

        severity = self._max_severity(alerts)
        first_seen = min(a.first_seen for a in alerts)
        last_seen = max(a.last_seen for a in alerts)
        assets = frozenset(a.asset_id for a in alerts if a.asset_id)
        users = frozenset(a.user for a in alerts if a.user)
        iocs = frozenset(i for a in alerts for i in a.ioc_ids)
        mitre = frozenset(m for a in alerts for m in a.mitre)
        tags = frozenset(t for a in alerts for t in a.tags)

        rules = {a.rule_id for a in alerts}
        default_title = (
            f"Incidente {next(iter(rules))}"
            if len(rules) == 1
            else f"Incidente com {len(alerts)} alertas"
        )

        evidence = tuple(
            IncidentEvidence(
                alert_id=a.id,
                title=a.title,
                rule_id=a.rule_id,
                severity=a.severity,
                created_at=a.created_at,
            )
            for a in alerts
        )

        risk = RiskScore(self._aggregate_risk(alerts))
        reason = IncidentReason(
            criteria=frozenset(c.value for c in group.matched_criteria),
            alerts_count=len(alerts),
            score=group.score,
        )

        timeline = (
            IncidentTimelineEntry(
                action="created",
                detail=f"Incidente criado com {len(alerts)} alertas",
                created_at=now,
            ),
        )

        return Incident(
            title=title or default_title,
            description=self._build_description(group),
            severity=severity,
            priority=self._priority_from_risk(risk),
            risk_score=risk,
            confidence=self._avg_confidence(alerts),
            status=IncidentStatus.OPEN,
            first_seen=first_seen,
            last_seen=last_seen,
            occurrences=1,
            alerts=tuple(a.id for a in alerts),
            assets=assets,
            users=users,
            iocs=iocs,
            mitre=mitre,
            tags=tags,
            timeline=timeline,
            fingerprint=group.fingerprint,
            reason=reason,
            evidence=evidence,
        )

    @staticmethod
    def _max_severity(alerts: tuple[Alert, ...]) -> IncidentSeverity:
        """Severidade maxima entre os alertas."""
        best = 0
        for a in alerts:
            rank = _SEVERITY_RANK.get(a.severity.value, 0)
            if rank > best:
                best = rank
        return _SEVERITY_BY_RANK[best]

    @staticmethod
    def _aggregate_risk(alerts: tuple[Alert, ...]) -> int:
        """Risco agregado: media dos risk_scores."""
        if not alerts:
            return 0
        total = sum(a.risk_score.value for a in alerts)
        return round(total / len(alerts))

    @staticmethod
    def _avg_confidence(alerts: tuple[Alert, ...]) -> float:
        """Confianca media dos alertas."""
        if not alerts:
            return 1.0
        return round(sum(a.confidence for a in alerts) / len(alerts), 3)

    @staticmethod
    def _priority_from_risk(risk: RiskScore) -> IncidentPriority:
        """Deriva prioridade a partir do risk_score."""
        value = risk.value
        if value >= 80:
            return IncidentPriority.P1
        if value >= 60:
            return IncidentPriority.P2
        if value >= 40:
            return IncidentPriority.P3
        if value >= 20:
            return IncidentPriority.P4
        return IncidentPriority.P5

    @staticmethod
    def _build_description(group: IncidentGroup) -> str:
        """Descricao legivel do agrupamento."""
        criteria = ", ".join(sorted(c.value for c in group.matched_criteria))
        return (
            f"Incidente agregando {len(group.alerts)} alertas "
            f"(score {group.score}); criterios: {criteria or 'nenhum'}"
        )


__all__ = ["IncidentBuilder"]
