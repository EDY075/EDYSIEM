"""Incident Lifecycle Manager.

Gerencia as transicoes de estado do ciclo de vida de um incidente
(OPEN -> TRIAGE -> INVESTIGATING -> CONTAINED -> RESOLVED -> CLOSED
-> REOPENED), validando as transicoes definidas no ``IncidentStatus``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .._utils import utcnow as _utcnow
from .exceptions import IncidentInvalidStateTransition
from .models import Incident, IncidentStatus, IncidentTimelineEntry


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """Resultado de uma transicao de estado.

    Attributes:
        incident: Incidente apos a transicao.
        changed: Se o estado realmente mudou.
        previous: Estado anterior.
    """

    incident: Incident
    changed: bool
    previous: IncidentStatus


class IncidentLifecycleManager:
    """Aplica transicoes validas no ciclo de vida de incidentes.

    O manager e stateless: recebe um ``Incident`` e retorna uma copia
    atualizada. Persistencia e responsabilidade do ``IncidentContext``.
    """

    def transition(
        self,
        incident: Incident,
        target: IncidentStatus,
        *,
        actor: str = "system",
        detail: str = "",
        now: datetime | None = None,
    ) -> TransitionResult:
        """Aplica uma transicao de estado.

        Raises:
            IncidentInvalidStateTransition: Se a transicao nao e valida.
        """
        current = incident.status
        if current is target:
            return TransitionResult(incident=incident, changed=False, previous=current)

        if not current.can_transition_to(target):
            raise IncidentInvalidStateTransition(current.value, target.value)

        now = now or _utcnow()
        entry = IncidentTimelineEntry(
            action="status_change",
            detail=detail or f"{current.value} -> {target.value}",
            created_at=now,
            actor=actor,
        )

        closed_at = None
        if target is IncidentStatus.CLOSED:
            closed_at = now

        updated = Incident(
            title=incident.title,
            description=incident.description,
            severity=incident.severity,
            priority=incident.priority,
            risk_score=incident.risk_score,
            confidence=incident.confidence,
            status=target,
            first_seen=incident.first_seen,
            last_seen=incident.last_seen,
            closed_at=closed_at,
            occurrences=incident.occurrences,
            alerts=incident.alerts,
            assets=incident.assets,
            users=incident.users,
            iocs=incident.iocs,
            mitre=incident.mitre,
            tactics=incident.tactics,
            techniques=incident.techniques,
            tags=incident.tags,
            timeline=(*incident.timeline, entry),
            owner=incident.owner,
            fingerprint=incident.fingerprint,
            reason=incident.reason,
            evidence=incident.evidence,
            id=incident.id,
            created_at=incident.created_at,
            updated_at=now,
        )
        return TransitionResult(incident=updated, changed=True, previous=current)

    def validate_transition(self, current: IncidentStatus, target: IncidentStatus) -> bool:
        """Verifica se a transicao e valida (sem aplicar)."""
        return current.can_transition_to(target)


__all__ = ["IncidentLifecycleManager", "TransitionResult"]
