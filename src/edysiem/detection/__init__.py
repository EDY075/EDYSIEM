"""Detection Framework do EDY SIEM.

Camada responsavel por interpretar regras de deteccao sobre eventos
correlacionados. Composta por:

- ``RuleEngine``: carrega, registra, valida e executa ``DetectionRule``
- ``DetectionEngine``: recebe ``CorrelatedEvent``, executa o ``RuleEngine``
  e produz ``DetectionResult`` com ``DetectionDecision``
- ``DSL``: estruturas e parser minimo para condicoes declarativas
  (preparado para evolucao: Sigma, MITRE em sprints futuras)

Pipeline:
    Correlation Engine -> CorrelatedEvent
        -> RuleEngine (DetectionRule) -> DetectionEngine
        -> DetectionResult / DetectionDecision  (Alert em sprint futura)

Arquitetura:
- ``DetectionRule`` (Protocol): contrato de regra de deteccao
- ``RuleMetadata``: metadados declarativos (id, severidade, risco, etc.)
- ``RuleCondition`` / ``RuleExpression``: DSL de condicoes
- ``DetectionRegistry``: descoberta, registro e ordenacao por prioridade
- ``RuleEngine``: execucao com isolamento de falhas, timeout e metricas
- ``DetectionEngine``: orquestra RuleEngine sobre CorrelatedEvents

Exemplo:
    from edysiem.detection import DetectionEngine, RuleEngine, DetectionRegistry
    from edysiem.detection.plugins import LoginFailuresRule

    registry = DetectionRegistry()
    registry.register(LoginFailuresRule())

    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    result = await det_engine.process(correlated_event)

Regras de deteccao reais (brute force, malware, exfiltration) e MITRE serao
implementadas em sprints futuras sobre este framework.
"""

from .base import (
    DetectionDecision,
    DetectionFinding,
    DetectionPriority,
    DetectionReason,
    DetectionRule,
    RuleMetadata,
)
from .context import DetectionContext
from .dsl import (
    RuleCondition,
    RuleExpression,
    RuleLogicalOp,
    RuleOperator,
    evaluate_expression,
    parse_rule_text,
)
from .engine import DetectionEngine
from .exceptions import (
    DetectionError,
    DetectionRuleNotFoundError,
    DetectionRuleTimeoutError,
)
from .models import DetectionMetrics, DetectionResult
from .registry import DetectionRegistry
from .rule_engine import RuleEngine

__all__ = [
    "DetectionContext",
    "DetectionDecision",
    "DetectionEngine",
    "DetectionError",
    "DetectionFinding",
    "DetectionMetrics",
    "DetectionPriority",
    "DetectionReason",
    "DetectionRegistry",
    "DetectionResult",
    "DetectionRule",
    "DetectionRuleNotFoundError",
    "DetectionRuleTimeoutError",
    "RuleCondition",
    "RuleEngine",
    "RuleExpression",
    "RuleLogicalOp",
    "RuleMetadata",
    "RuleOperator",
    "evaluate_expression",
    "parse_rule_text",
]
