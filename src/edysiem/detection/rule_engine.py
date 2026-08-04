"""Rule Engine do Detection Framework.

Responsavel por carregar, registrar, validar e executar ``DetectionRule``:
- Carregar/registrar regras via Registry
- Validar regras (metadados, campos obrigatorios)
- Executar por prioridade + dependencias
- Isolar falhas (regra que falha nao derruba o pipeline)
- Timeout por regra
- Coletar metricas

Exemplo:
    registry = DetectionRegistry()
    registry.register(LoginFailuresRule())

    rule_engine = RuleEngine(registry)
    result = await rule_engine.evaluate(correlated_event)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..ingestion.metrics import MetricsRegistry
from .base import DetectionDecision, DetectionFinding
from .context import DetectionContext
from .exceptions import RuleValidationError
from .models import DetectionMetrics, DetectionResult
from .registry import DetectionRegistry

if TYPE_CHECKING:
    from ..correlation import CorrelatedEvent
    from .base import DetectionRule


@dataclass(frozen=True, slots=True)
class RuleExecution:
    """Resultado da execucao de uma regra para o RuleEngine."""

    rule_id: str
    result: DetectionResult
    decision: DetectionDecision
    duration_ms: float
    error: str | None = None


class RuleEngine:
    """Motor de execucao de regras de deteccao.

    Responsabilidades:
    - Executar regras em ordem de prioridade + dependencias
    - Validar regras antes de executar
    - Isolar falhas e timeouts
    - Coletar metricas por regra e agregadas
    """

    def __init__(
        self,
        registry: DetectionRegistry,
        context: DetectionContext | None = None,
        *,
        default_timeout_seconds: float = 5.0,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self._registry = registry
        self._context = context or DetectionContext()
        self._default_timeout = default_timeout_seconds
        self._metrics = metrics or MetricsRegistry()
        self._engine_metrics = DetectionMetrics()
        self._initialized = False
        self._setup_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Inicializa todas as regras registradas (setup async)."""
        async with self._setup_lock:
            if self._initialized:
                return
            for rule in self._registry.get_ordered_rules():
                try:
                    await rule.setup()
                except Exception:
                    self._metrics.increment("detection.rule_engine.setup_failure")
            self._initialized = True

    def validate_rule(self, rule: DetectionRule) -> None:
        """Valida uma regra (metadados e estrutura).

        Raises:
            RuleValidationError: Se a regra nao e valida.
        """
        metadata = rule.metadata
        if not metadata.id or not metadata.id.strip():
            raise RuleValidationError(rule_id=metadata.id, message="id nao pode ser vazio")
        if not metadata.name or not metadata.name.strip():
            raise RuleValidationError(rule_id=metadata.id, message="name nao pode ser vazio")
        if not metadata.version or not metadata.version.strip():
            raise RuleValidationError(rule_id=metadata.id, message="version nao pode ser vazio")

        evaluate = getattr(rule, "evaluate", None)
        if evaluate is None:
            raise RuleValidationError(
                rule_id=metadata.id, message="regra nao implementa evaluate()"
            )

    def validate_all(self) -> None:
        """Valida todas as regras registradas."""
        for rule in self._registry.get_all_rules().values():
            self.validate_rule(rule)

    async def evaluate(self, event: CorrelatedEvent) -> DetectionResult:
        """Executa todas as regras aplicaveis contra o evento correlacionado.

        Retorna o primeiro resultado DETECTED agregado; se nenhuma regra
        detectar, retorna NO_DETECTION com os findings acumulados.
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()
        all_findings: list[DetectionFinding] = []
        decisions: list[RuleExecution] = []
        present_fields = self._present_fields(event)

        for rule in self._registry.get_ordered_rules():
            rule_id = rule.metadata.id
            timeout = rule.metadata.timeout_seconds or self._default_timeout

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
                    rule_id, duration, len(result.findings), result.decision
                )
                self._metrics.increment("detection.rule.executions")
                self._metrics.increment(f"detection.rule.{rule_id}.executions")

                if result.decision is DetectionDecision.DETECTED:
                    all_findings.extend(result.findings)
                    self._metrics.increment("detection.detections", len(result.findings))

                decisions.append(
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
                self._metrics.increment("detection.rule.timeout")
                self._metrics.increment(f"detection.rule.{rule_id}.timeout")
                decisions.append(
                    RuleExecution(
                        rule_id=rule_id,
                        result=DetectionResult.fail(
                            error=f"Timeout apos {timeout}s",
                            duration_ms=duration,
                            rule_id=rule_id,
                        ),
                        decision=DetectionDecision.NO_DETECTION,
                        duration_ms=duration,
                        error="timeout",
                    )
                )

            except Exception as exc:
                duration = (time.perf_counter() - rule_start) * 1000
                self._engine_metrics.record_failure(rule_id)
                self._metrics.increment("detection.rule.failure")
                self._metrics.increment(f"detection.rule.{rule_id}.failure")
                decisions.append(
                    RuleExecution(
                        rule_id=rule_id,
                        result=DetectionResult.fail(
                            error=str(exc),
                            duration_ms=duration,
                            rule_id=rule_id,
                        ),
                        decision=DetectionDecision.NO_DETECTION,
                        duration_ms=duration,
                        error=str(exc),
                    )
                )

        total_duration = (time.perf_counter() - start_time) * 1000
        self._engine_metrics.total_events_processed += 1
        self._metrics.observe("detection.duration_ms", total_duration)

        if all_findings:
            return DetectionResult.detected(
                findings=tuple(all_findings),
                duration_ms=total_duration,
                rule_id=",".join(
                    d.rule_id for d in decisions if d.decision is DetectionDecision.DETECTED
                ),
            )

        return DetectionResult.no_detection(duration_ms=total_duration, rule_id="")

    def _present_fields(self, event: CorrelatedEvent) -> set[str]:
        """Retorna campos presentes no evento de origem (para filtro)."""
        present: set[str] = set()
        source = event.source_event
        if source is None:
            return present
        for field in (
            "ip_src",
            "ip_dst",
            "user",
            "hostname",
            "source_host",
            "event_category",
            "event_action",
            "process",
            "command_line",
        ):
            if getattr(source, field, None):
                present.add(field)
        return present

    @property
    def metrics(self) -> DetectionMetrics:
        """Metricas do RuleEngine."""
        return self._engine_metrics

    @property
    def context(self) -> DetectionContext:
        """Contexto de deteccao."""
        return self._context

    @property
    def registry(self) -> DetectionRegistry:
        """Registry de regras."""
        return self._registry

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Snapshot completo de metricas."""
        m = self._engine_metrics
        return {
            "total_events_processed": m.total_events_processed,
            "total_executions": m.total_executions,
            "total_detections": m.total_detections,
            "total_failures": m.total_failures,
            "total_timeout": m.total_timeout,
            "avg_duration_ms": m.avg_duration_ms,
            "executions_by_rule": dict(m.executions_by_rule),
            "detections_by_rule": dict(m.detections_by_rule),
            "failures_by_rule": dict(m.failures_by_rule),
            "context": self._context.snapshot(),
            "last_updated": m.last_updated.isoformat(),
        }

    async def health_check(self) -> dict[str, Any]:
        """Verifica saude do RuleEngine."""
        return {
            "engine": "healthy" if self._initialized else "not_initialized",
            "initialized": self._initialized,
            "registry": self._registry.get_stats(),
            "context": self._context.snapshot(),
            "metrics": self.get_metrics_snapshot(),
        }

    async def shutdown(self) -> None:
        """Finaliza todas as regras graciosamente."""
        for rule in self._registry.get_ordered_rules():
            try:
                await rule.shutdown()
            except Exception:
                self._metrics.increment("detection.rule_engine.shutdown_failure")


__all__ = ["RuleEngine", "RuleExecution"]
