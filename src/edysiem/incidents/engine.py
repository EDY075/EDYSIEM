"""Incident Engine Enterprise.

Orquestra o fluxo de agrupamento de alertas em incidentes:
    Alertas -> Correlator (grouping) -> Builder -> Dedup -> Lifecycle -> Incident

Decisoes:
- NEW: incidente criado
- DEDUP: occurrences+1 / last_seen atualizado (sem novo incidente)
- NO_GROUP: alertas nao atingem a pontuacao minima
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .._utils import utcnow as _utcnow
from ..alerts import Alert
from .builder import IncidentBuilder
from .context import IncidentContext
from .correlator import CorrelationDecision, IncidentCorrelator
from .grouping import GroupingEngine, IncidentGroup
from .lifecycle import IncidentLifecycleManager
from .models import Incident, IncidentMetrics, IncidentStatus
from .registry import IncidentRegistry


class IncidentResultKind(Enum):
    """Tipo de resultado do Incident Engine."""

    CREATED = "created"
    DEDUPLICATED = "deduplicated"
    NO_GROUP = "no_group"


@dataclass(frozen=True, slots=True)
class IncidentResult:
    """Resultado do processamento de um grupo de alertas.

    Attributes:
        kind: CREATED / DEDUPLICATED / NO_GROUP.
        incident: Incidente resultante (None se NO_GROUP).
        was_new: Se foi criado.
    """

    kind: IncidentResultKind
    incident: Incident | None = None
    was_new: bool = False


class IncidentEngine:
    """Motor de agrupamento de alertas em incidentes.

    Args:
        correlator: Correlaciona alertas (grouping + dedup).
        builder: Construtor de incidentes.
        lifecycle: Gerenciador de transicoes de estado.
        registry: Hooks de ciclo de vida.
        context: Armazenamento in-memory.
    """

    def __init__(
        self,
        correlator: IncidentCorrelator | None = None,
        builder: IncidentBuilder | None = None,
        lifecycle: IncidentLifecycleManager | None = None,
        registry: IncidentRegistry | None = None,
        context: IncidentContext | None = None,
    ) -> None:
        self._context = context if context is not None else IncidentContext()
        self._registry = registry or IncidentRegistry()
        self._correlator = correlator or IncidentCorrelator(GroupingEngine(), self._context)
        self._builder = builder or IncidentBuilder()
        self._lifecycle = lifecycle or IncidentLifecycleManager()
        self._metrics = IncidentMetrics()

    @property
    def context(self) -> IncidentContext:
        """Armazenamento de incidentes."""
        return self._context

    @property
    def registry(self) -> IncidentRegistry:
        """Registry de hooks."""
        return self._registry

    @property
    def correlator(self) -> IncidentCorrelator:
        """Correlator de alertas."""
        return self._correlator

    @property
    def metrics(self) -> IncidentMetrics:
        """Metricas do engine."""
        return self._metrics

    async def process_alerts(
        self,
        alerts: list[Alert],
        *,
        title: str | None = None,
        now: datetime | None = None,
    ) -> IncidentResult:
        """Processa uma lista de alertas em um incidente.

        Args:
            alerts: Alertas candidatos ao incidente.
            title: Titulo customizado.
            now: Carimbo de referencia.

        Returns:
            ``IncidentResult`` com kind CREATED/DEDUPLICATED/NO_GROUP.
        """
        now = now or _utcnow()

        outcome = self._correlator.correlate(alerts)
        if outcome.decision is CorrelationDecision.NO_GROUP:
            return IncidentResult(kind=IncidentResultKind.NO_GROUP, was_new=False)

        if outcome.decision is CorrelationDecision.DEDUP and outcome.existing is not None:
            return self._finalize_dedup(outcome.existing, now)

        if outcome.group is None:
            return IncidentResult(kind=IncidentResultKind.NO_GROUP, was_new=False)

        return self._finalize_created(outcome.group, title=title, now=now)

    def _finalize_created(
        self, group: IncidentGroup, *, title: str | None, now: datetime
    ) -> IncidentResult:
        """Persiste um incidente novo e notifica hooks."""
        incident = self._builder.build(group, title=title, now=now)
        self._context.save(incident)
        self._metrics.record_created(len(group.alerts), incident.title)
        self._registry.on_created(incident)
        return IncidentResult(kind=IncidentResultKind.CREATED, incident=incident, was_new=True)

    def _finalize_dedup(self, existing: Incident, now: datetime) -> IncidentResult:
        """Incrementa occurrences do incidente existente (sem novo)."""
        updated = existing.bump(at=now)
        self._context.save(updated)
        self._metrics.record_deduplicated()
        self._registry.on_updated(updated)
        return IncidentResult(
            kind=IncidentResultKind.DEDUPLICATED,
            incident=updated,
            was_new=False,
        )

    def transition(
        self,
        incident: Incident,
        target: IncidentStatus,
        *,
        actor: str = "system",
        detail: str = "",
        now: datetime | None = None,
    ) -> Incident:
        """Aplica uma transicao de estado no ciclo de vida.

        Raises:
            IncidentInvalidStateTransition: Se a transicao e invalida.
        """
        result = self._lifecycle.transition(incident, target, actor=actor, detail=detail, now=now)
        if result.changed:
            self._context.save(result.incident)
            self._registry.on_status_changed(
                result.incident, result.previous, result.incident.status
            )
            if target is IncidentStatus.REOPENED:
                self._metrics.record_reopened()
                self._registry.on_reopened(result.incident)
        return result.incident

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Snapshot de metricas do engine."""
        m = self._metrics
        return {
            "total_created": m.total_created,
            "total_deduplicated": m.total_deduplicated,
            "total_reopened": m.total_reopened,
            "total_grouped_alerts": m.total_grouped_alerts,
            "avg_alerts_per_incident": m.avg_alerts_per_incident,
            "created_by_rule": dict(m.created_by_rule),
            "context": self._context.snapshot(),
            "registry": self._registry.get_stats(),
            "last_updated": m.last_updated.isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        """Verifica saude do engine."""
        return {
            "engine": "healthy",
            "context": self._context.snapshot(),
            "metrics": self.get_metrics_snapshot(),
        }


__all__ = ["IncidentEngine", "IncidentResult", "IncidentResultKind"]
