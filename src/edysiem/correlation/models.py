"""Modelos do Correlation Engine.

Define os resultados, o evento correlacionado e as metricas do framework.
Todos imutaveis (frozen=True, slots=True) seguindo o padrao do projeto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .._utils import utcnow as _utcnow
from ..domain import EnrichedEvent
from .base import CorrelationDecision, CorrelationMatch


@dataclass(frozen=True, slots=True)
class CorrelationResult:
    """Resultado da avaliacao de uma regra de correlacao.

    Attributes:
        decision: Decisao da regra para o evento corrente.
        matches: Tupla de matches produzidos (vazia se nao disparou).
        error: Mensagem de erro se a avaliacao falhou.
        duration_ms: Tempo de execucao em milissegundos.
        rule_id: Regra que avaliou.
    """

    decision: CorrelationDecision
    matches: tuple[CorrelationMatch, ...] = ()
    error: str | None = None
    duration_ms: float = 0.0
    rule_id: str = ""

    @classmethod
    def match(
        cls,
        matches: tuple[CorrelationMatch, ...],
        duration_ms: float,
        rule_id: str,
    ) -> CorrelationResult:
        """Cria um resultado de MATCH."""
        return cls(
            decision=CorrelationDecision.MATCH,
            matches=matches,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )

    @classmethod
    def no_match(cls, duration_ms: float, rule_id: str) -> CorrelationResult:
        """Cria um resultado de NO_MATCH."""
        return cls(
            decision=CorrelationDecision.NO_MATCH,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )

    @classmethod
    def deferred(cls, duration_ms: float, rule_id: str) -> CorrelationResult:
        """Cria um resultado de DEFERRED (acumulando estado)."""
        return cls(
            decision=CorrelationDecision.DEFERRED,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )

    @classmethod
    def fail(cls, error: str, duration_ms: float, rule_id: str) -> CorrelationResult:
        """Cria um resultado de falha (rule_id vazio quando nao executou)."""
        return cls(
            decision=CorrelationDecision.NO_MATCH,
            error=error,
            duration_ms=duration_ms,
            rule_id=rule_id,
        )


@dataclass(frozen=True, slots=True)
class CorrelatedEvent:
    """Evento correlacionado produzido pelo Correlation Engine.

    Agrega um evento de origem e todos os matches das regras que dispararam.

    Attributes:
        event_id: ID do evento de origem.
        source_event: Evento enriquecido de origem.
        matches: Todos os matches de correlacao para este evento.
        correlated_at: Carimbo de tempo (UTC) da correlacao.
    """

    event_id: str
    source_event: EnrichedEvent
    matches: tuple[CorrelationMatch, ...] = ()
    correlated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id nao pode ser vazio")


@dataclass(slots=True)
class CorrelationMetrics:
    """Metricas agregadas do Correlation Engine (mutavel, nao frozen).

    Attributes:
        total_events_processed: Eventos avaliados.
        total_executions: Total de execucoes de regras.
        total_matches: Total de matches produzidos.
        total_failures: Total de falhas de regras.
        total_timeout: Total de timeouts de regras.
        total_duration_ms: Tempo acumulado de execucao.
        executions_by_rule: Execucoes por regra.
        matches_by_rule: Matches por regra.
        failures_by_rule: Falhas por regra.
        state_size: Tamanho do estado (janelas/buffers) no contexto.
        last_updated: Carimbo da ultima atualizacao.
    """

    total_events_processed: int = 0
    total_executions: int = 0
    total_matches: int = 0
    total_failures: int = 0
    total_timeout: int = 0
    total_duration_ms: float = 0.0
    executions_by_rule: dict[str, int] = field(default_factory=dict)
    matches_by_rule: dict[str, int] = field(default_factory=dict)
    failures_by_rule: dict[str, int] = field(default_factory=dict)
    state_size: int = 0
    last_updated: datetime = field(default_factory=_utcnow)

    @property
    def avg_duration_ms(self) -> float:
        """Duracao media por execucao."""
        return self.total_duration_ms / self.total_executions if self.total_executions else 0.0

    def record_execution(
        self,
        rule_id: str,
        duration_ms: float,
        matches_count: int,
        decision: CorrelationDecision,
    ) -> None:
        """Registra uma execucao de regra."""
        self.total_executions += 1
        self.total_duration_ms += duration_ms
        self.executions_by_rule[rule_id] = self.executions_by_rule.get(rule_id, 0) + 1
        self.last_updated = _utcnow()

        if decision is CorrelationDecision.MATCH:
            self.total_matches += matches_count
            self.matches_by_rule[rule_id] = self.matches_by_rule.get(rule_id, 0) + matches_count

    def record_failure(self, rule_id: str, *, timeout: bool = False) -> None:
        """Registra uma falha de regra."""
        self.total_failures += 1
        self.failures_by_rule[rule_id] = self.failures_by_rule.get(rule_id, 0) + 1
        if timeout:
            self.total_timeout += 1
        self.last_updated = _utcnow()


__all__ = [
    "CorrelatedEvent",
    "CorrelationMetrics",
    "CorrelationResult",
]
