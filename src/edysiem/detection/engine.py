"""Detection Engine do EDY SIEM.

Orquestra o Rule Engine sobre eventos correlacionados:
- Recebe ``CorrelatedEvent``
- Executa o ``RuleEngine`` (todas as regras)
- Produz ``DetectionOutcome`` com decisoes/findings
- Gera ``DetectionDecision`` por regra

Nao gera ``Alert`` ainda (sprint futura) - apenas a camada de decisao.

Exemplo:
    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    outcome = await det_engine.process(correlated_event)
    for finding in outcome.findings:
        print(finding.rule_id, finding.severity)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..correlation import CorrelatedEvent
from .base import DetectionFinding
from .models import DetectionMetrics, DetectionOutcome, DetectionResult
from .rule_engine import RuleEngine


@dataclass(frozen=True, slots=True)
class DetectionSummary:
    """Resumo executivo de um processamento."""

    detected: bool
    detected_rule_ids: tuple[str, ...]
    finding_count: int
    max_severity: str


class DetectionEngine:
    """Motor de deteccao que orquestra o RuleEngine sobre CorrelatedEvents.

    Responsabilidades:
    - Executar o RuleEngine contra o evento correlacionado
    - Agregar decisoes e findings em um ``DetectionOutcome``
    - Produzir um resumo executivo
    - Rastrear metricas agregadas
    """

    def __init__(self, rule_engine: RuleEngine) -> None:
        self._rule_engine = rule_engine

    @property
    def rule_engine(self) -> RuleEngine:
        """RuleEngine subjacente."""
        return self._rule_engine

    async def process(self, event: CorrelatedEvent) -> DetectionOutcome:
        """Processa um evento correlacionado e produz o outcome.

        Args:
            event: Evento correlacionado (saida do Correlation Engine).

        Returns:
            ``DetectionOutcome`` com todas as decisoes e findings.
        """
        result = await self._rule_engine.evaluate(event)

        findings: tuple[DetectionFinding, ...] = ()
        detected_ids: tuple[str, ...] = ()
        if result.findings:
            findings = result.findings
            detected_ids = tuple(sorted({f.rule_id for f in result.findings}))
        decisions: tuple[DetectionResult, ...] = (result,)

        return DetectionOutcome(
            event_id=event.event_id,
            decisions=decisions,
            findings=findings,
            detected_rule_ids=detected_ids,
        )

    def summarize(self, outcome: DetectionOutcome) -> DetectionSummary:
        """Gera um resumo executivo do outcome."""
        detected = bool(outcome.detected_rule_ids)
        severities = [f.severity.value for f in outcome.findings]

        from ..domain import Severity

        rank = {
            Severity.INFO.value: 0,
            Severity.LOW.value: 1,
            Severity.MEDIUM.value: 2,
            Severity.HIGH.value: 3,
            Severity.CRITICAL.value: 4,
        }
        max_sev = max(severities, key=lambda s: rank.get(s, 0)) if severities else "info"

        return DetectionSummary(
            detected=detected,
            detected_rule_ids=outcome.detected_rule_ids,
            finding_count=len(outcome.findings),
            max_severity=max_sev,
        )

    @property
    def metrics(self) -> DetectionMetrics:
        """Metricas do RuleEngine subjacente."""
        return self._rule_engine.metrics

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Snapshot de metricas do RuleEngine."""
        return self._rule_engine.get_metrics_snapshot()


__all__ = ["DetectionEngine", "DetectionSummary"]
