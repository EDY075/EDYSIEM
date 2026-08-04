"""Correlation Engine do EDY SIEM.

Orquestra a execucao das regras de correlacao:
- Descoberta e ordenacao de regras via Registry
- Execucao async com isolamento de falhas e timeout
- Continuidade de pipeline (falha de uma regra nao para as outras)
- Metricas detalhadas por regra e agregadas

Exemplo:
    registry = CorrelationRegistry()
    registry.register(ThresholdByIpRule(threshold=5, window_seconds=300))

    engine = CorrelationEngine(registry)
    correlated = await engine.process(enriched_event)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..domain import EnrichedEvent
from ..ingestion.metrics import MetricsRegistry
from .base import CorrelationDecision, CorrelationMatch
from .context import CorrelationContext
from .models import CorrelatedEvent, CorrelationMetrics, CorrelationResult
from .registry import CorrelationRegistry

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class RuleExecution:
    """Resultado da execucao de uma regra para o engine."""

    rule_id: str
    result: CorrelationResult
    decision: CorrelationDecision
    duration_ms: float
    error: str | None = None


class CorrelationEngine:
    """Motor de correlacao Enterprise.

    Responsabilidades:
    - Executar regras em ordem de prioridade + dependencias
    - Isolar falhas (uma regra nao derruba o pipeline)
    - Aplicar timeout por regra
    - Coletar metricas detalhadas
    - Gerar ``CorrelatedEvent`` imutavel
    """

    def __init__(
        self,
        registry: CorrelationRegistry,
        context: CorrelationContext | None = None,
        *,
        default_timeout_seconds: float = 5.0,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self._registry = registry
        self._context = context or CorrelationContext()
        self._default_timeout = default_timeout_seconds
        self._metrics = metrics or MetricsRegistry()
        self._engine_metrics = CorrelationMetrics()
        self._initialized = False
        self._setup_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Inicializa todas as regras registradas (setup async)."""
        async with self._setup_lock:
            if self._initialized:
                return
            rules = self._registry.get_ordered_rules()
            for rule in rules:
                try:
                    await rule.setup()
                except Exception:
                    self._metrics.increment("correlation.engine.setup_failure")
            self._initialized = True

    async def process(self, event: EnrichedEvent) -> CorrelatedEvent:
        """Processa um evento contra todas as regras aplicaveis.

        Args:
            event: Evento enriquecido a correlacionar.

        Returns:
            ``CorrelatedEvent`` com todos os matches produzidos.
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()
        all_matches: list[CorrelationMatch] = []
        executions: list[RuleExecution] = []

        rules = self._registry.get_ordered_rules(event.event_category)
        present_fields = self._present_fields(event)

        for rule in rules:
            rule_id = rule.metadata.id
            timeout = rule.metadata.timeout_seconds or self._default_timeout

            # Pula regras que exigem campos ausentes no evento
            required = rule.metadata.required_fields
            if required and not required.issubset(present_fields):
                continue

            rule_start = time.perf_counter()
            try:
                result = await asyncio.wait_for(
                    rule.evaluate(event, self._context), timeout=timeout
                )
                duration = (time.perf_counter() - rule_start) * 1000

                self._engine_metrics.record_execution(
                    rule_id, duration, len(result.matches), result.decision
                )
                self._metrics.increment("correlation.rule.executions")
                self._metrics.increment(f"correlation.rule.{rule_id}.executions")

                if result.decision is CorrelationDecision.MATCH:
                    all_matches.extend(result.matches)
                    self._metrics.increment("correlation.matches", len(result.matches))

                executions.append(
                    RuleExecution(
                        rule_id=rule_id,
                        result=result,
                        decision=result.decision,
                        duration_ms=duration,
                    )
                )

            except TimeoutError:
                duration = (time.perf_counter() - rule_start) * 1000
                self._engine_metrics.record_failure(rule_id, timeout=True)
                self._metrics.increment("correlation.rule.timeout")
                self._metrics.increment(f"correlation.rule.{rule_id}.timeout")
                executions.append(
                    RuleExecution(
                        rule_id=rule_id,
                        result=CorrelationResult.fail(
                            error=(f"Timeout apos {timeout}s"),
                            duration_ms=duration,
                            rule_id=rule_id,
                        ),
                        decision=CorrelationDecision.NO_MATCH,
                        duration_ms=duration,
                        error="timeout",
                    )
                )

            except Exception as exc:
                duration = (time.perf_counter() - rule_start) * 1000
                self._engine_metrics.record_failure(rule_id)
                self._metrics.increment("correlation.rule.failure")
                self._metrics.increment(f"correlation.rule.{rule_id}.failure")
                executions.append(
                    RuleExecution(
                        rule_id=rule_id,
                        result=CorrelationResult.fail(
                            error=str(exc),
                            duration_ms=duration,
                            rule_id=rule_id,
                        ),
                        decision=CorrelationDecision.NO_MATCH,
                        duration_ms=duration,
                        error=str(exc),
                    )
                )

        # Metricas globais
        self._engine_metrics.total_events_processed += 1
        self._engine_metrics.state_size = self._context.state_size
        total_duration = (time.perf_counter() - start_time) * 1000
        self._metrics.increment("correlation.events_processed")
        self._metrics.observe("correlation.duration_ms", total_duration)

        return CorrelatedEvent(
            event_id=event.event_id,
            source_event=event,
            matches=tuple(all_matches),
        )

    def _present_fields(self, event: EnrichedEvent) -> set[str]:
        """Retorna campos presentes no evento (para filtro de regras).

        Um campo e considerado presente se nao e ``None`` nem vazio.
        """
        present = set()
        if event.ip_src:
            present.add("ip_src")
        if event.ip_dst:
            present.add("ip_dst")
        if event.user:
            present.add("user")
        if event.hostname:
            present.add("hostname")
        if event.source_host:
            present.add("source_host")
        if event.event_category:
            present.add("event_category")
        if event.event_action:
            present.add("event_action")
        if event.process:
            present.add("process")
        if event.command_line:
            present.add("command_line")
        return present

    @property
    def metrics(self) -> CorrelationMetrics:
        """Metricas do engine."""
        return self._engine_metrics

    @property
    def context(self) -> CorrelationContext:
        """Contexto de correlacao (estado de janela)."""
        return self._context

    @property
    def registry(self) -> CorrelationRegistry:
        """Registry de regras."""
        return self._registry

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Snapshot completo de metricas."""
        m = self._engine_metrics
        return {
            "total_events_processed": m.total_events_processed,
            "total_executions": m.total_executions,
            "total_matches": m.total_matches,
            "total_failures": m.total_failures,
            "total_timeout": m.total_timeout,
            "avg_duration_ms": m.avg_duration_ms,
            "executions_by_rule": dict(m.executions_by_rule),
            "matches_by_rule": dict(m.matches_by_rule),
            "failures_by_rule": dict(m.failures_by_rule),
            "state_size": m.state_size,
            "context": self._context.snapshot(),
            "last_updated": m.last_updated.isoformat(),
        }

    async def health_check(self) -> dict[str, Any]:
        """Verifica saude do engine."""
        return {
            "engine": "healthy" if self._initialized else "not_initialized",
            "initialized": self._initialized,
            "registry": self._registry.get_stats(),
            "context": self._context.snapshot(),
            "metrics": self.get_metrics_snapshot(),
        }

    async def shutdown(self) -> None:
        """Finaliza todas as regras graciosamente."""
        rules = self._registry.get_ordered_rules()
        for rule in rules:
            try:
                await rule.shutdown()
            except Exception:
                self._metrics.increment("correlation.engine.shutdown_failure")


__all__ = ["CorrelationEngine", "RuleExecution"]
