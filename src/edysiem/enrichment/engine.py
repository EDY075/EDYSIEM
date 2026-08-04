"""Enrichment Engine do EDY SIEM.

Orquestra a execução do pipeline de enriquecimento:
- Descoberta e ordenação de plugins via Registry
- Execução assíncrona com isolamento de falhas
- Continuidade de processamento (falha de um plugin não para o pipeline)
- Métricas detalhadas por plugin e agregadas
- Timeout configurável por plugin
- Health checks integrados

Exemplo:
    registry = EnrichmentRegistry()
    registry.register(AssetEnricher())
    registry.register(GeoEnricher())

    engine = EnrichmentEngine(registry)
    enriched_event = await engine.enrich(canonical_event)

    # Métricas
    metrics = engine.get_metrics()
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .._utils import utcnow as _utcnow
from ..domain import CanonicalEvent, EnrichedEvent
from ..ingestion.metrics import MetricsRegistry
from ..result import Result, ok
from .base import EnrichmentPlugin
from .context import EnrichmentContext
from .models import EnrichmentResult
from .registry import EnrichmentRegistry


@dataclass(slots=True)
class EnrichmentMetrics:
    """Métricas agregadas do Enrichment Engine."""

    total_events_processed: int = 0
    total_enrichments_applied: int = 0
    total_plugin_executions: int = 0
    total_plugin_failures: int = 0
    total_duration_ms: float = 0.0
    plugins_executed: dict[str, int] = field(default_factory=dict)
    plugins_failed: dict[str, int] = field(default_factory=dict)
    avg_duration_ms: float = 0.0
    last_updated: datetime = field(default_factory=_utcnow)

    def record_execution(
        self, plugin_id: str, duration_ms: float, success: bool, enrichments_count: int
    ) -> None:
        """Registra uma execução de plugin."""
        self.total_plugin_executions += 1
        self.total_duration_ms += duration_ms
        self.plugins_executed[plugin_id] = self.plugins_executed.get(plugin_id, 0) + 1

        if success:
            self.total_enrichments_applied += enrichments_count
        else:
            self.total_plugin_failures += 1
            self.plugins_failed[plugin_id] = self.plugins_failed.get(plugin_id, 0) + 1

        self.avg_duration_ms = (
            self.total_duration_ms / self.total_plugin_executions
            if self.total_plugin_executions > 0
            else 0.0
        )
        self.last_updated = _utcnow()


class EnrichmentEngine:
    """Motor de enriquecimento Enterprise.

    Responsabilidades:
    - Executar plugins em ordem de prioridade + dependências
    - Isolar falhas (um plugin não derruba o pipeline)
    - Aplicar timeouts por plugin
    - Coletar métricas detalhadas
    - Gerar EnrichedEvent imutável
    """

    def __init__(
        self,
        registry: EnrichmentRegistry,
        context: EnrichmentContext,
        *,
        default_timeout_seconds: float = 30.0,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self._registry = registry
        self._context = context
        self._default_timeout = default_timeout_seconds
        self._metrics = metrics or MetricsRegistry()
        self._engine_metrics = EnrichmentMetrics()
        self._initialized = False
        self._setup_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Inicializa todos os plugins registrados (setup assíncrono)."""
        async with self._setup_lock:
            if self._initialized:
                return

            plugins = self._registry.get_ordered_plugins()
            for plugin in plugins:
                try:
                    await plugin.setup()
                except Exception:
                    # Log mas não falha a inicialização
                    self._metrics.increment("enrichment.engine.setup_failure")

            self._initialized = True

    async def enrich(self, event: CanonicalEvent) -> Result[EnrichedEvent]:
        """Enriquece um evento canônico executando todos os plugins aplicáveis.

        Args:
            event: Evento canônico a ser enriquecido.

        Returns:
            ``Success(EnrichedEvent)`` com enriquecimentos agregados;
            ``Failure`` se erro crítico (ex.: contexto inválido).
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()
        all_enrichments: list[Any] = []
        plugin_results: list[EnrichmentResult] = []

        # Obter plugins ordenados para a categoria do evento
        plugins = self._registry.get_ordered_plugins(event.event_category)

        for plugin in plugins:
            plugin_id = plugin.metadata.id
            timeout = plugin.metadata.timeout_seconds or self._default_timeout

            try:
                result = await self._execute_plugin_with_timeout(
                    plugin, event, all_enrichments, timeout
                )
                plugin_results.append(result)

                # Atualizar métricas
                self._engine_metrics.record_execution(
                    plugin_id,
                    result.duration_ms,
                    result.success,
                    len(result.enrichments),
                )

                if result.success:
                    all_enrichments.extend(result.enrichments)
                else:
                    # Log falha mas continua pipeline
                    # (record_execution já contabiliza failures acima)
                    self._metrics.increment("enrichment.plugin.failure")
                    self._metrics.increment(f"enrichment.plugin.{plugin_id}.failure")

            except TimeoutError:
                self._metrics.increment("enrichment.plugin.timeout")
                self._metrics.increment(f"enrichment.plugin.{plugin_id}.timeout")
                plugin_results.append(
                    EnrichmentResult.fail(
                        error=f"Timeout após {timeout}s",
                        duration_ms=timeout * 1000,
                        plugin_name=plugin_id,
                    )
                )
            except Exception as exc:
                self._metrics.increment("enrichment.plugin.error")
                self._metrics.increment(f"enrichment.plugin.{plugin_id}.error")
                plugin_results.append(
                    EnrichmentResult.fail(
                        error=f"Erro inesperado: {exc}",
                        duration_ms=0.0,
                        plugin_name=plugin_id,
                    )
                )

        # Construir EnrichedEvent final
        total_duration_ms = (time.perf_counter() - start_time) * 1000

        # Converter models.Enrichment para domain.Enrichment (usado pelo EnrichedEvent)
        from ..domain import Enrichment as DomainEnrichment

        domain_enrichments = tuple(
            DomainEnrichment(
                kind=enr.kind.value if hasattr(enr.kind, "value") else str(enr.kind),
                provider=enr.provider,
                data=enr.data,
                created_at=enr.created_at,
            )
            for enr in all_enrichments
        )

        enriched_event = EnrichedEvent(
            event_id=event.event_id,
            trace_id=event.trace_id,
            timestamp=event.timestamp,
            received_at=event.received_at,
            source_type=event.source_type,
            source_host=event.source_host,
            hostname=event.hostname,
            event_category=event.event_category,
            event_action=event.event_action,
            severity=event.severity,
            user=event.user,
            process=event.process,
            command_line=event.command_line,
            ip_src=event.ip_src,
            ip_dst=event.ip_dst,
            vendor=event.vendor,
            product=event.product,
            event_original=event.event_original,
            normalized_fields=event.normalized_fields,
            tags=event.tags,
            confidence=event.confidence,
            metadata=event.metadata,
            schema_version=event.schema_version,
            normalized_at=event.normalized_at,
            enrichments=domain_enrichments,
        )

        # Métricas globais
        self._metrics.increment("enrichment.events_processed")
        self._metrics.increment("enrichment.enrichments_applied", len(all_enrichments))
        self._metrics.observe("enrichment.duration_ms", total_duration_ms)

        return ok(enriched_event)

    async def _execute_plugin_with_timeout(
        self,
        plugin: EnrichmentPlugin,
        event: CanonicalEvent,
        current_enrichments: Sequence[object],
        timeout_seconds: float,
    ) -> EnrichmentResult:
        """Executa um plugin com timeout e isolamento de falhas."""
        plugin_id = plugin.metadata.id
        start = time.perf_counter()

        try:
            # Executar com timeout
            result = await asyncio.wait_for(
                plugin.enrich(event, self._context), timeout=timeout_seconds
            )
            duration_ms = (time.perf_counter() - start) * 1000

            if result.is_ok():
                enriched = result.unwrap()
                # Extrair enriquecimentos novos (não presentes no event original)
                new_enrichments = tuple(
                    e for e in enriched.enrichments if e not in current_enrichments
                )
                return EnrichmentResult.ok(
                    enrichments=new_enrichments,
                    duration_ms=duration_ms,
                    plugin_name=plugin_id,
                )
            else:
                # Result Failure - access error via .error
                failure = result
                error = getattr(failure, "error", None)
                error_msg = getattr(error, "message", str(error))
                return EnrichmentResult.fail(
                    error=str(error_msg),
                    duration_ms=(time.perf_counter() - start) * 1000,
                    plugin_name=plugin_id,
                )

        except TimeoutError:
            raise  # Re-raise para ser capturado pelo caller
        except Exception as exc:
            return EnrichmentResult.fail(
                error=f"Erro no plugin '{plugin_id}': {exc}",
                duration_ms=(time.perf_counter() - start) * 1000,
                plugin_name=plugin_id,
            )

    async def enrich_batch(self, events: list[CanonicalEvent]) -> list[Result[EnrichedEvent]]:
        """Enriquece múltiplos eventos em paralelo.

        Args:
            events: Lista de eventos canônicos.

        Returns:
            Lista de resultados na mesma ordem dos eventos de entrada.
        """
        if not self._initialized:
            await self.initialize()

        tasks = [self.enrich(event) for event in events]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def shutdown(self) -> None:
        """Finaliza todos os plugins graciosamente."""
        plugins = self._registry.get_ordered_plugins()
        for plugin in plugins:
            try:
                await plugin.shutdown()
            except Exception:
                self._metrics.increment("enrichment.engine.shutdown_failure")

    @property
    def metrics(self) -> EnrichmentMetrics:
        """Métricas do engine."""
        return self._engine_metrics

    @property
    def registry(self) -> EnrichmentRegistry:
        """Registry de plugins."""
        return self._registry

    @property
    def context(self) -> EnrichmentContext:
        """Contexto de enriquecimento."""
        return self._context

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Snapshot completo de métricas."""
        m = self._engine_metrics
        return {
            "total_events_processed": self._metrics.get("enrichment.events_processed"),
            "total_enrichments_applied": self._metrics.get("enrichment.enrichments_applied"),
            "total_plugin_executions": m.total_plugin_executions,
            "total_plugin_failures": m.total_plugin_failures,
            "avg_duration_ms": m.avg_duration_ms,
            "plugins_executed": dict(m.plugins_executed),
            "plugins_failed": dict(m.plugins_failed),
            "last_updated": m.last_updated.isoformat(),
            "context_cache": self._context.get_cache_stats(),
        }

    async def health_check(self) -> dict[str, Any]:
        """Verifica saúde do engine e componentes."""
        context_health = await self._context.health_check()
        registry_stats = self._registry.get_stats()

        return {
            "engine": "healthy" if self._initialized else "not_initialized",
            "initialized": self._initialized,
            "registry": registry_stats,
            "context": context_health,
            "metrics": self.get_metrics_snapshot(),
        }


__all__ = ["EnrichmentEngine", "EnrichmentMetrics"]
