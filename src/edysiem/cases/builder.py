"""Case Builder.

Cria um ``Case`` a partir de um ``Incident`` (do Incident Engine),
herdando contexto relevante (severidade, prioridade, alertas, assets,
users, iocs, mitre).
"""

from __future__ import annotations

from datetime import datetime

from .._utils import utcnow as _utcnow
from ..incidents import Incident
from .exceptions import CaseBuilderError
from .models import (
    Case,
    CasePriority,
    CaseSeverity,
    CaseStatus,
    CaseTimelineEntry,
)

_SEVERITY_MAP = {
    "info": CaseSeverity.INFO,
    "low": CaseSeverity.LOW,
    "medium": CaseSeverity.MEDIUM,
    "high": CaseSeverity.HIGH,
    "critical": CaseSeverity.CRITICAL,
}


class CaseBuilder:
    """Constroi um ``Case`` a partir de um ``Incident``.

    Args:
        default_owner: Responsavel padrao caso o incidente nao tenha.
    """

    def __init__(self, default_owner: str | None = None) -> None:
        self._default_owner = default_owner

    def build(
        self,
        incident: Incident,
        *,
        title: str | None = None,
        owner: str | None = None,
        now: datetime | None = None,
    ) -> Case:
        """Monta um case de investigacao a partir de um incidente.

        Args:
            incident: Incidente de origem.
            title: Titulo customizado (default: titulo do incidente).
            owner: Responsavel (default: incidente/owner padrao).
            now: Carimbo de referencia.

        Returns:
            ``Case`` com contexto herdado do incidente.

        Raises:
            CaseBuilderError: Se o incidente nao tem titulo.
        """
        if not incident.title:
            raise CaseBuilderError("incidente sem titulo")

        now = now or _utcnow()
        severity = self._map_severity(incident.severity.value)

        entry = CaseTimelineEntry(
            action="created",
            detail=f"Case criado a partir do incidente {incident.id}",
            created_at=now,
        )

        return Case(
            title=title or incident.title,
            description=incident.description,
            owner=owner or self._default_owner,
            status=CaseStatus.OPEN,
            severity=severity,
            priority=self._map_priority(incident.priority.value),
            risk_score=incident.risk_score,
            incident_id=incident.id,
            alerts=incident.alerts,
            assets=incident.assets,
            users=incident.users,
            iocs=incident.iocs,
            mitre=incident.mitre,
            timeline=(entry,),
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _map_severity(value: str) -> CaseSeverity:
        """Mapeia severidade (string) para ``CaseSeverity``."""
        return _SEVERITY_MAP.get(str(value).lower(), CaseSeverity.MEDIUM)

    @staticmethod
    def _map_priority(value: str) -> CasePriority:
        """Mapeia prioridade (string) para ``CasePriority``."""
        mapping = {
            "p1": CasePriority.P1,
            "p2": CasePriority.P2,
            "p3": CasePriority.P3,
            "p4": CasePriority.P4,
            "p5": CasePriority.P5,
        }
        return mapping.get(str(value).lower(), CasePriority.P3)


__all__ = ["CaseBuilder"]
