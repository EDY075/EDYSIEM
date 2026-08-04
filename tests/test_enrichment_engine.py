"""Testes do EnrichmentEngine."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.domain import CanonicalEvent, EnrichedEvent, Severity
from edysiem.enrichment import (
    Enrichment,
    EnrichmentContext,
    EnrichmentEngine,
    EnrichmentKind,
    EnrichmentRegistry,
    PluginMetadata,
    PluginPriority,
)
from edysiem.result import Result, ok


class MockPlugin:
    """Plugin mock para testes do engine."""

    def __init__(
        self,
        plugin_id: str,
        priority: PluginPriority = PluginPriority.NORMAL,
        enrichments: tuple[Enrichment, ...] = (),
        should_fail: bool = False,
        delay_ms: float = 0.0,
    ) -> None:
        self._id = plugin_id
        self._priority = priority
        self._enrichments = enrichments
        self._should_fail = should_fail
        self._delay_ms = delay_ms
        self.setup_called = False
        self.shutdown_called = False
        self.enrich_called = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id=self._id,
            name=f"Mock {self._id}",
            version="1.0.0",
            author="Test",
            priority=self._priority,
        )

    async def setup(self) -> None:
        self.setup_called = True

    async def shutdown(self) -> None:
        self.shutdown_called = True

    async def enrich(
        self, event: CanonicalEvent, context: EnrichmentContext
    ) -> Result[EnrichedEvent]:
        self.enrich_called = True
        if self._delay_ms > 0:
            import asyncio

            await asyncio.sleep(self._delay_ms / 1000)

        if self._should_fail:
            from edysiem.result import Error, ErrorCode, Failure

            return Failure[EnrichedEvent](
                Error(ErrorCode.PLUGIN_ERROR, f"Plugin {self._id} failed")
            )

        # O plugin recebe CanonicalEvent (sem enrichments) e deve retornar
        # EnrichedEvent com seus enriquecimentos. O engine acumula.
        enriched = EnrichedEvent(
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
            enrichments=self._enrichments,
        )
        return ok(enriched)


def _make_event(category: str = "auth") -> CanonicalEvent:
    return CanonicalEvent(
        event_id="evt-1",
        trace_id="trace-1",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="syslog",
        source_host="host-1",
        event_category=category,
        event_action="logon",
        severity=Severity.INFO,
    )


@pytest.fixture
async def engine() -> EnrichmentEngine:
    registry = EnrichmentRegistry()
    context = EnrichmentContext()
    engine = EnrichmentEngine(registry, context)
    await engine.initialize()
    yield engine
    await engine.shutdown()


@pytest.mark.asyncio
async def test_engine_enrich_single_plugin(engine: EnrichmentEngine) -> None:
    enrichment = Enrichment(
        kind=EnrichmentKind.ASSET,
        provider="test-plugin",
        data={"owner": "sec"},
    )
    plugin = MockPlugin("test-plugin", enrichments=(enrichment,))
    engine._registry.register(plugin)

    result = await engine.enrich(_make_event())

    assert result.is_ok()
    enriched = result.unwrap()
    assert len(enriched.enrichments) == 1
    assert enriched.enrichments[0].provider == "test-plugin"


@pytest.mark.asyncio
async def test_engine_enrich_multiple_plugins(engine: EnrichmentEngine) -> None:
    enrichment1 = Enrichment(kind=EnrichmentKind.ASSET, provider="plugin1", data={})
    enrichment2 = Enrichment(kind=EnrichmentKind.GEO, provider="plugin2", data={})

    plugin1 = MockPlugin("plugin1", enrichments=(enrichment1,))
    plugin2 = MockPlugin("plugin2", enrichments=(enrichment2,))

    engine._registry.register(plugin1)
    engine._registry.register(plugin2)

    result = await engine.enrich(_make_event())

    assert result.is_ok()
    enriched = result.unwrap()
    assert len(enriched.enrichments) == 2
    providers = {e.provider for e in enriched.enrichments}
    assert providers == {"plugin1", "plugin2"}


@pytest.mark.asyncio
async def test_engine_plugin_failure_isolation(engine: EnrichmentEngine) -> None:
    """Falha de um plugin não deve parar o pipeline."""
    good_enrichment = Enrichment(kind=EnrichmentKind.ASSET, provider="good", data={})
    good_plugin = MockPlugin("good-plugin", enrichments=(good_enrichment,))
    bad_plugin = MockPlugin("bad-plugin", should_fail=True)

    engine._registry.register(good_plugin)
    engine._registry.register(bad_plugin)

    result = await engine.enrich(_make_event())

    assert result.is_ok()
    enriched = result.unwrap()
    # Apenas o plugin bom deve ter enriquecido
    assert len(enriched.enrichments) == 1
    assert enriched.enrichments[0].provider == "good"


@pytest.mark.asyncio
async def test_engine_plugin_ordering(engine: EnrichmentEngine) -> None:
    """Plugins devem executar em ordem de prioridade."""
    order: list[str] = []

    class OrderedPlugin(MockPlugin):
        async def enrich(self, event, context):
            order.append(self._id)
            return await super().enrich(event, context)

    p1 = OrderedPlugin("low", priority=PluginPriority.LOW)
    p2 = OrderedPlugin("high", priority=PluginPriority.HIGH)
    p3 = OrderedPlugin("normal", priority=PluginPriority.NORMAL)

    engine._registry.register(p1)
    engine._registry.register(p2)
    engine._registry.register(p3)

    await engine.enrich(_make_event())

    # high -> normal -> low
    assert order == ["high", "normal", "low"]


@pytest.mark.asyncio
async def test_engine_metrics(engine: EnrichmentEngine) -> None:
    enrichment = Enrichment(kind=EnrichmentKind.ASSET, provider="metrics", data={})
    plugin = MockPlugin("metrics-plugin", enrichments=(enrichment,))
    engine._registry.register(plugin)

    await engine.enrich(_make_event())

    metrics = engine.get_metrics_snapshot()
    assert metrics["total_plugin_executions"] == 1
    assert metrics["plugins_executed"]["metrics-plugin"] == 1
    assert metrics["plugins_failed"] == {}


@pytest.mark.asyncio
async def test_engine_plugin_failure_metrics(engine: EnrichmentEngine) -> None:
    bad_plugin = MockPlugin("failing", should_fail=True)
    engine._registry.register(bad_plugin)

    await engine.enrich(_make_event())

    metrics = engine.get_metrics_snapshot()
    assert metrics["total_plugin_failures"] == 1
    assert metrics["plugins_failed"]["failing"] == 1


@pytest.mark.asyncio
async def test_engine_batch_enrich(engine: EnrichmentEngine) -> None:
    enrichment = Enrichment(kind=EnrichmentKind.ASSET, provider="batch", data={})
    plugin = MockPlugin("batch-plugin", enrichments=(enrichment,))
    engine._registry.register(plugin)

    events = [_make_event() for _ in range(3)]
    results = await engine.enrich_batch(events)

    assert len(results) == 3
    for result in results:
        assert result.is_ok()
        assert len(result.unwrap().enrichments) == 1


@pytest.mark.asyncio
async def test_engine_shutdown_calls_plugin_shutdown(engine: EnrichmentEngine) -> None:
    plugin = MockPlugin("shutdown-test")
    engine._registry.register(plugin)

    await engine.shutdown()

    assert plugin.shutdown_called


@pytest.mark.asyncio
async def test_engine_health_check(engine: EnrichmentEngine) -> None:
    health = await engine.health_check()
    assert health["engine"] == "healthy"
    assert health["initialized"] is True
    assert "registry" in health
    assert "context" in health
    assert "metrics" in health
