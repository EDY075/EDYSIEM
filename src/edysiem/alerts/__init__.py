"""Alert Engine Enterprise do EDY SIEM.

Camada responsavel pelo ciclo de vida completo de um alerta SOC:
- Transformar ``DetectionFinding`` em ``Alert``
- Avaliar risco (Risk Engine)
- Calcular fingerprint deterministico (Fingerprint Engine)
- Deduplicar alertas (Dedup Engine)
- Gerir ciclo de vida (Lifecycle Manager)

Fluxo:
    DetectionFinding
        -> Risk Evaluation
        -> Fingerprint
        -> Alert Builder
        -> Deduplication
        -> Alert Lifecycle
        -> Alert

Arquitetura:
- ``AlertEngine``: orquestra risco -> builder -> dedup -> lifecycle
- ``RiskEngine``: calcula ``risk_score`` (simples, preparado para multiplos fatores)
- ``FingerprintEngine``: hash deterministico de campos-chave
- ``DedupEngine``: incrementa occurrences / atualiza last_seen em vez de novo alerta
- ``AlertBuilder``: monta o ``Alert`` operacional
- ``LifecycleManager``: transicoes de estado (OPEN -> TRIAGE -> INVESTIGATING -> ...)
- ``AlertRegistry``: hooks de ciclo de vida (on_created, on_updated)

Sem Cases ainda, sem Dashboard ainda - somente arquitetura.
"""

from .base import AlertProcessor
from .builder import AlertBuilder
from .context import AlertContext
from .dedupe import DedupDecision, DedupEngine
from .engine import AlertEngine, AlertResult, AlertResultKind
from .exceptions import (
    AlertError,
    AlertInvalidStateTransition,
    AlertNotFoundError,
)
from .fingerprint import FingerprintEngine
from .lifecycle import LifecycleManager
from .models import (
    Alert,
    AlertFingerprint,
    AlertLifecycle,
    AlertMetrics,
    AlertPriority,
    AlertReason,
    AlertSeverity,
)
from .registry import AlertRegistry
from .risk import RiskEngine, RiskFactor

__all__ = [
    "Alert",
    "AlertBuilder",
    "AlertContext",
    "AlertEngine",
    "AlertError",
    "AlertFingerprint",
    "AlertInvalidStateTransition",
    "AlertLifecycle",
    "AlertMetrics",
    "AlertNotFoundError",
    "AlertPriority",
    "AlertProcessor",
    "AlertReason",
    "AlertRegistry",
    "AlertResult",
    "AlertResultKind",
    "AlertSeverity",
    "DedupDecision",
    "DedupEngine",
    "FingerprintEngine",
    "LifecycleManager",
    "RiskEngine",
    "RiskFactor",
]
