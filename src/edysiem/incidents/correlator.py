"""Incident Correlator.

Decide se um conjunto de alertas forma um incidente e se o incidente
ja existe (deduplicacao por fingerprint). Usa o ``GroupingEngine`` com
a ``GroupingConfig``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..alerts import Alert
from .context import IncidentContext
from .grouping import GroupingConfig, GroupingEngine, IncidentGroup


class CorrelationDecision(Enum):
    """Decisao do correlator.

    Attributes:
        NEW: Alertas formam um incidente novo.
        DEDUP: Incidente equivalente ja existe.
        NO_GROUP: Alertas nao atingem a pontuacao minima.
    """

    NEW = "new"
    DEDUP = "dedup"
    NO_GROUP = "no_group"


@dataclass(frozen=True, slots=True)
class CorrelationOutcome:
    """Resultado da correlacao.

    Attributes:
        decision: NEW / DEDUP / NO_GROUP.
        group: Grupo de alertas (se atingiu pontuacao).
        existing: Incidente existente (se DEDUP).
    """

    decision: CorrelationDecision
    group: IncidentGroup | None = None
    existing: Any = None


class IncidentCorrelator:
    """Correlaciona alertas em incidentes.

    Args:
        grouping: Engine de agrupamento.
        context: Contexto que guarda ``fingerprint_hash -> incident_id``.
    """

    def __init__(
        self,
        grouping: GroupingEngine | None = None,
        context: IncidentContext | None = None,
    ) -> None:
        self._grouping = grouping or GroupingEngine()
        self._context = context if context is not None else IncidentContext()

    @property
    def config(self) -> GroupingConfig:
        """Configuracao de agrupamento."""
        return self._grouping.config

    def correlate(self, alerts: list[Alert]) -> CorrelationOutcome:
        """Correlaciona a lista de alertas.

        Returns:
            ``CorrelationOutcome`` com a decisao.
        """
        group = self._grouping.group(alerts)
        if group is None:
            return CorrelationOutcome(decision=CorrelationDecision.NO_GROUP)

        existing = self._context.get_incident_by_fingerprint(group.fingerprint.hash)
        if existing is not None:
            return CorrelationOutcome(
                decision=CorrelationDecision.DEDUP,
                group=group,
                existing=existing,
            )

        return CorrelationOutcome(decision=CorrelationDecision.NEW, group=group)


__all__ = ["CorrelationDecision", "CorrelationOutcome", "IncidentCorrelator"]
