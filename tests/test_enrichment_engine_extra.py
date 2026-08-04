"""Testes adicionais do EnrichmentEngine e exceptions."""

from __future__ import annotations

import asyncio
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
from edysiem.enrichment.exceptions import (
    EnrichmentError,
    EnrichmentTimeoutError,
    PluginDependencyError,
    PluginNotFoundError,
    PluginRegistrationError,
)
from edysiem.result import ok


class TimeoutPlugin:
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="timeout-plugin",
            name="Timeout",
            version="1.0.0",
            author="Test",
            timeout_seconds=0.05,
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def enrich(self, event: CanonicalEvent, context: EnrichmentContext):
        await asyncio.sleep(1.0)
        return ok(event)


class SlowPlugin:
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="slow-plugin",
            name="Slow",
            version="1.0.0",
            author="Test",
            timeout_seconds=0.5,
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def enrich(self, event: CanonicalEvent, context: EnrichmentContext):
        await asyncio.sleep(0.01)
        enrichment = Enrichment(kind=EnrichmentKind.CUSTOM, provider="slow", data={})
        return ok(
            EnrichedEvent(
                event_id=event.event_id,
                trace_id=event.trace_id,
                timestamp=event.timestamp,
                received_at=event.received_at,
                source_type=event.source_type,
                source_host=event.source_host,
                event_category=event.event_category,
                event_action=event.event_action,
                severity=event.severity,
                enrichments=(enrichment,),
            )
        )


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


@pytest.mark.asyncio
async def test_engine_timeout_isolation() -> None:
    """Plugin com timeout não deve parar o pipeline."""
    registry = EnrichmentRegistry()
    context = EnrichmentContext()
    engine = EnrichmentEngine(registry, context)
    await engine.initialize()

    timeout_plugin = TimeoutPlugin()
    slow_plugin = SlowPlugin()
    registry.register(timeout_plugin)
    registry.register(slow_plugin)

    result = await engine.enrich(_make_event())

    assert result.is_ok()
    enriched = result.unwrap()
    # Apenas o slow_plugin deve ter enriquecido
    assert len(enriched.enrichments) == 1
    assert enriched.enrichments[0].provider == "slow"


@pytest.mark.asyncio
async def test_engine_enrich_batch_empty() -> None:
    registry = EnrichmentRegistry()
    context = EnrichmentContext()
    engine = EnrichmentEngine(registry, context)
    await engine.initialize()

    results = await engine.enrich_batch([])
    assert results == []


@pytest.mark.asyncio
async def test_engine_health_check_not_initialized() -> None:
    registry = EnrichmentRegistry()
    context = EnrichmentContext()
    engine = EnrichmentEngine(registry, context)

    health = await engine.health_check()
    assert health["engine"] == "not_initialized"
    assert health["initialized"] is False


@pytest.mark.asyncio
async def test_engine_shutdown_with_no_plugins() -> None:
    registry = EnrichmentRegistry()
    context = EnrichmentContext()
    engine = EnrichmentEngine(registry, context)

    await engine.shutdown()  # Should not raise


@pytest.mark.asyncio
async def test_engine_initialize_twice_is_idempotent() -> None:
    registry = EnrichmentRegistry()
    context = EnrichmentContext()
    engine = EnrichmentEngine(registry, context)

    await engine.initialize()
    await engine.initialize()  # Second call should not re-run
    assert engine._initialized is True


def test_enrichment_timeout_error() -> None:
    error = EnrichmentTimeoutError("plugin-1", 30.0)
    assert error.plugin_name == "plugin-1"
    assert error.timeout_seconds == 30.0
    assert "plugin-1" in str(error)


def test_plugin_not_found_error() -> None:
    error = PluginNotFoundError("missing-plugin")
    assert error.plugin_id == "missing-plugin"
    assert "missing-plugin" in str(error)


def test_plugin_registration_error() -> None:
    error = PluginRegistrationError("duplicate plugin")
    assert "duplicate plugin" in str(error)


def test_plugin_dependency_error() -> None:
    error = PluginDependencyError("plugin-a", "plugin-b")
    assert error.plugin_id == "plugin-a"
    assert error.missing_dependency == "plugin-b"


def test_enrichment_error_base() -> None:
    error = EnrichmentError("base error")
    assert "base error" in str(error)


def test_plugin_priority_values() -> None:
    assert PluginPriority.CRITICAL.value == 0
    assert PluginPriority.HIGH.value == 10
    assert PluginPriority.NORMAL.value == 50
    assert PluginPriority.LOW.value == 100
    assert PluginPriority.BACKGROUND.value == 200
