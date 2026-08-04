"""Correlation Engine do EDY SIEM.

Framework Enterprise para correlacao de eventos enriquecidos.
Totalmente desacoplado e preparado para centenas de regras declarativas.

Pipeline:
    EnrichedEvent -> Correlation Engine -> CorrelatedEvent -> Detection

Arquitetura:
- ``CorrelationRule`` (Protocol): contrato de regra de correlacao
- ``CorrelationMetadata``: metadados declarativos da regra (id, prioridade, janela, etc.)
- ``CorrelationRegistry``: descoberta, registro e ordenacao por prioridade
- ``CorrelationContext``: estado de janela temporal (buffers por regra + chave)
- ``CorrelationEngine``: execucao com isolamento de falhas, timeout e metricas
- ``CorrelatedEvent``: evento correlacionado produzido para a Detection

Exemplo:
    from edysiem.correlation import CorrelationEngine, CorrelationRegistry
    from edysiem.correlation.plugins import ThresholdByIpRule

    registry = CorrelationRegistry()
    registry.register(ThresholdByIpRule(threshold=5, window_seconds=300))

    engine = CorrelationEngine(registry)
    correlated = await engine.process(enriched_event)

Regras de correlacao reais (brute force, impossible travel, beaconing) sao
implementadas em sprints futuras sobre este framework.
"""

from .base import (
    CorrelationDecision,
    CorrelationMatch,
    CorrelationMetadata,
    CorrelationPriority,
    CorrelationReason,
    CorrelationRule,
)
from .context import CorrelationContext
from .engine import CorrelationEngine
from .exceptions import (
    CorrelationError,
    CorrelationRuleNotFoundError,
    CorrelationRuleTimeoutError,
)
from .models import CorrelatedEvent, CorrelationMetrics, CorrelationResult
from .registry import CorrelationRegistry

__all__ = [
    "CorrelatedEvent",
    "CorrelationContext",
    "CorrelationDecision",
    "CorrelationEngine",
    "CorrelationError",
    "CorrelationMatch",
    "CorrelationMetadata",
    "CorrelationMetrics",
    "CorrelationPriority",
    "CorrelationReason",
    "CorrelationRegistry",
    "CorrelationResult",
    "CorrelationRule",
    "CorrelationRuleNotFoundError",
    "CorrelationRuleTimeoutError",
]
