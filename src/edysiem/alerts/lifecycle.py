"""Lifecycle Manager do Alert Framework.

Gerencia as transicoes de estado do ciclo de vida de um alerta
(OPEN -> TRIAGE -> INVESTIGATING -> RESOLVED / FALSE_POSITIVE),
validando as transicoes definidas no ``AlertLifecycle``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .._utils import utcnow as _utcnow
from .exceptions import AlertInvalidStateTransition
from .models import Alert, AlertLifecycle, AlertTimelineEntry


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """Resultado de uma transicao de estado.

    Attributes:
        alert: Alerta apos a transicao (novo estado).
        changed: Se o estado realmente mudou.
        previous: Estado anterior.
    """

    alert: Alert
    changed: bool
    previous: AlertLifecycle


class LifecycleManager:
    """Aplica transicoes validas no ciclo de vida de alertas.

    O manager e stateless: recebe um ``Alert`` e retorna uma copia
    atualizada. A persistencia do estado e responsabilidade do
    ``AlertContext``/storage.
    """

    def transition(
        self,
        alert: Alert,
        target: AlertLifecycle,
        *,
        actor: str = "system",
        detail: str = "",
        now: datetime | None = None,
    ) -> TransitionResult:
        """Aplica uma transicao de estado.

        Args:
            alert: Alerta atual.
            target: Estado de destino.
            actor: Ator da acao (ex.: "analyst-01").
            detail: Detalhe da transicao.
            now: Carimbo de referencia.

        Raises:
            AlertInvalidStateTransition: Se a transicao nao e valida.

        Returns:
            ``TransitionResult`` com o alerta atualizado.
        """
        current = alert.status
        if current is target:
            # Transicao para o mesmo estado e idempotente
            return TransitionResult(alert=alert, changed=False, previous=current)

        if not current.can_transition_to(target):
            raise AlertInvalidStateTransition(current.value, target.value)

        now = now or _utcnow()
        entry = AlertTimelineEntry(
            action="status_change",
            detail=detail or f"{current.value} -> {target.value}",
            created_at=now,
            actor=actor,
        )

        updated = Alert(
            title=alert.title,
            description=alert.description,
            severity=alert.severity,
            priority=alert.priority,
            risk_score=alert.risk_score,
            confidence=alert.confidence,
            first_seen=alert.first_seen,
            last_seen=alert.last_seen,
            occurrences=alert.occurrences,
            status=target,
            source=alert.source,
            rule_id=alert.rule_id,
            mitre=alert.mitre,
            asset_id=alert.asset_id,
            user=alert.user,
            ioc_ids=alert.ioc_ids,
            tags=alert.tags,
            timeline=(*alert.timeline, entry),
            fingerprint=alert.fingerprint,
            event_ids=alert.event_ids,
            id=alert.id,
            created_at=alert.created_at,
            updated_at=now,
        )
        return TransitionResult(alert=updated, changed=True, previous=current)

    def validate_transition(self, current: AlertLifecycle, target: AlertLifecycle) -> bool:
        """Verifica se a transicao e valida (sem aplicar)."""
        return current.can_transition_to(target)


__all__ = ["LifecycleManager", "TransitionResult"]
