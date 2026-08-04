"""Incident Engine Enterprise do EDY SIEM.

Camada responsavel por agrupar Alertas relacionados em um Incidente de
seguranca. Sem Case Management ainda, sem Dashboard - somente arquitetura.

Fluxo:
    Detection -> Risk -> Alert -> Incident Engine -> Incident

Arquitetura:
- ``IncidentCorrelator``: decide se alertas formam um incidente (grouping)
- ``GroupingConfig``: criterios configuraveis (asset, user, ioc, rule, fingerprint,
  janela temporal, MITRE) + pontuacao minima - nada hardcoded
- ``IncidentBuilder``: recebe varios Alert e produz um unico Incident
- ``IncidentEngine``: orquestra correlacao -> builder -> dedup -> lifecycle
- ``IncidentLifecycleManager``: OPEN -> TRIAGE -> INVESTIGATING -> CONTAINED
  -> RESOLVED -> CLOSED -> REOPENED
- ``IncidentRegistry``: hooks de ciclo de vida
"""

from .base import IncidentProcessor
from .builder import IncidentBuilder
from .context import IncidentContext
from .correlator import CorrelationDecision, CorrelationOutcome, IncidentCorrelator
from .engine import IncidentEngine, IncidentResult, IncidentResultKind
from .exceptions import (
    IncidentError,
    IncidentInvalidStateTransition,
    IncidentNotFoundError,
)
from .grouping import (
    GroupingConfig,
    GroupingCriterion,
    GroupingEngine,
    IncidentGroup,
)
from .lifecycle import IncidentLifecycleManager
from .models import (
    Incident,
    IncidentEvidence,
    IncidentFingerprint,
    IncidentMetrics,
    IncidentPriority,
    IncidentReason,
    IncidentSeverity,
    IncidentStatus,
    IncidentTimelineEntry,
)
from .registry import IncidentRegistry

__all__ = [
    "CorrelationDecision",
    "CorrelationOutcome",
    "GroupingConfig",
    "GroupingCriterion",
    "GroupingEngine",
    "Incident",
    "IncidentBuilder",
    "IncidentContext",
    "IncidentCorrelator",
    "IncidentEngine",
    "IncidentError",
    "IncidentEvidence",
    "IncidentFingerprint",
    "IncidentGroup",
    "IncidentInvalidStateTransition",
    "IncidentLifecycleManager",
    "IncidentMetrics",
    "IncidentNotFoundError",
    "IncidentPriority",
    "IncidentProcessor",
    "IncidentReason",
    "IncidentRegistry",
    "IncidentResult",
    "IncidentResultKind",
    "IncidentSeverity",
    "IncidentStatus",
    "IncidentTimelineEntry",
]
