"""Modelos do Detection Framework.

Define os resultados e metricas do processo de deteccao.
Todos imutaveis (frozen=True, slots=True) seguindo o padrao do projeto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .._utils import utcnow as _utcnow
from .base import DetectionDecision, DetectionFinding


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Resultado da avaliacao de uma regra de deteccao.

    Attributes:
        decision: Decisao da regra para o evento.
        findings: Findings produzidos (vazia se nao detectou).
        error: Mensagem de erro se a avaliacao falhou.
        duration_ms: Tempo de execucao em milissegundos.
        rule_id: Regra que avaliou.
    """

    decision: DetectionDecision
    findings: tuple[DetectionFinding, ...] = ()
    error: str | None = None
    duration_ms: float = 0.0
    rule_id: str = ""

    @classmethod
    def detected(
        cls,
        findings: tuple[DetectionFinding, ...],
        duration_ms: float,
        rule_id: str,
    ) -> DetectionResult:
        """Cria um resultado de DETECTED."""
        return cls(
            decision=DetectionDecision.DETECTED,
            findings=findings,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )

    @classmethod
    def no_detection(cls, duration_ms: float, rule_id: str) -> DetectionResult:
        """Cria um resultado de NO_DETECTION."""
        return cls(
            decision=DetectionDecision.NO_DETECTION,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )

    @classmethod
    def deferred(cls, duration_ms: float, rule_id: str) -> DetectionResult:
        """Cria um resultado de DEFERRED (acumulando estado)."""
        return cls(
            decision=DetectionDecision.DEFERRED,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )

    @classmethod
    def fail(cls, error: str, duration_ms: float, rule_id: str) -> DetectionResult:
        """Cria um resultado de falha."""
        return cls(
            decision=DetectionDecision.NO_DETECTION,
            error=error,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )


@dataclass(frozen=True, slots=True)
class DetectionOutcome:
    """Resultado agregado do Detection Engine para um evento.

    Attributes:
        event_id: ID do evento correlacionado processado.
        decisions: Tupla de decisoes por regra.
        findings: Todos os findings produzidos.
        detected_rule_ids: Regras que detectaram.
        processed_at: Carimbo (UTC).
    """

    event_id: str
    decisions: tuple[DetectionResult, ...] = ()
    findings: tuple[DetectionFinding, ...] = ()
    detected_rule_ids: tuple[str, ...] = ()
    processed_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id nao pode ser vazio")


@dataclass(slots=True)
class DetectionMetrics:
    """Metricas agregadas do Detection Framework (mutavel, nao frozen).

    Attributes:
        total_events_processed: Eventos correlacionados processados.
        total_executions: Execucoes de regras.
        total_detections: Total de deteccoes.
        total_failures: Total de falhas de regras.
        total_timeout: Total de timeouts.
        total_duration_ms: Tempo acumulado.
        executions_by_rule: Execucoes por regra.
        detections_by_rule: Deteccoes por regra.
        failures_by_rule: Falhas por regra.
        last_updated: Carimbo da ultima atualizacao.
    """

    total_events_processed: int = 0
    total_executions: int = 0
    total_detections: int = 0
    total_failures: int = 0
    total_timeout: int = 0
    total_duration_ms: float = 0.0
    executions_by_rule: dict[str, int] = field(default_factory=dict)
    detections_by_rule: dict[str, int] = field(default_factory=dict)
    failures_by_rule: dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=_utcnow)

    @property
    def avg_duration_ms(self) -> float:
        """Duracao media por execucao."""
        return self.total_duration_ms / self.total_executions if self.total_executions else 0.0

    def record_execution(
        self, rule_id: str, duration_ms: float, findings_count: int, decision: DetectionDecision
    ) -> None:
        """Registra uma execucao de regra."""
        self.total_executions += 1
        self.total_duration_ms += duration_ms
        self.executions_by_rule[rule_id] = self.executions_by_rule.get(rule_id, 0) + 1
        self.last_updated = _utcnow()

        if decision is DetectionDecision.DETECTED:
            self.total_detections += findings_count
            self.detections_by_rule[rule_id] = (
                self.detections_by_rule.get(rule_id, 0) + findings_count
            )

    def record_failure(self, rule_id: str, *, timeout: bool = False) -> None:
        """Registra uma falha de regra."""
        self.total_failures += 1
        self.failures_by_rule[rule_id] = self.failures_by_rule.get(rule_id, 0) + 1
        if timeout:
            self.total_timeout += 1
        self.last_updated = _utcnow()


__all__ = [
    "DetectionMetrics",
    "DetectionOutcome",
    "DetectionResult",
]
