"""Testes do EnrichmentRegistry."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.domain import CanonicalEvent, EnrichedEvent, Severity
from edysiem.enrichment import (
    Enrichment,
    EnrichmentKind,
    EnrichmentRegistry,
    PluginMetadata,
    PluginPriority,
)
from edysiem.enrichment.exceptions import (
    PluginDependencyError,
    PluginRegistrationError,
)
from edysiem.result import Result, ok


class MockPlugin:
    """Plugin mock para testes."""

    def __init__(
        self,
        plugin_id: str,
        name: str = "Mock",
        priority: PluginPriority = PluginPriority.NORMAL,
        dependencies: frozenset[str] = frozenset(),
        categories: frozenset[str] = frozenset(),
        should_fail: bool = False,
    ) -> None:
        self._id = plugin_id
        self._name = name
        self._priority = priority
        self._dependencies = dependencies
        self._categories = categories
        self._should_fail = should_fail
        self.setup_called = False
        self.shutdown_called = False
        self.enrich_called = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id=self._id,
            name=self._name,
            version="1.0.0",
            author="Test",
            description="Mock plugin",
            priority=self._priority,
            dependencies=self._dependencies,
            supported_event_categories=self._categories,
        )

    async def setup(self) -> None:
        self.setup_called = True

    async def shutdown(self) -> None:
        self.shutdown_called = True

    async def enrich(self, event: CanonicalEvent, context) -> Result[EnrichedEvent]:
        self.enrich_called = True
        if self._should_fail:
            from edysiem.result import Error, ErrorCode, Failure

            return Failure[EnrichedEvent](Error(ErrorCode.PLUGIN_ERROR, "mock failure"))

        enrichment = Enrichment(
            kind=EnrichmentKind.CUSTOM,
            provider=self._id,
            data={"mock": True},
        )
        return ok(
            EnrichedEvent(
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


def test_registry_register_plugin() -> None:
    registry = EnrichmentRegistry()
    plugin = MockPlugin("test-plugin")

    registry.register(plugin)

    assert "test-plugin" in registry
    assert registry.get("test-plugin") is plugin
    assert registry.is_enabled("test-plugin")


def test_registry_register_duplicate_fails() -> None:
    registry = EnrichmentRegistry()
    plugin1 = MockPlugin("duplicate")
    plugin2 = MockPlugin("duplicate")

    registry.register(plugin1)
    with pytest.raises(PluginRegistrationError, match="já registrado"):
        registry.register(plugin2)


def test_registry_unregister() -> None:
    registry = EnrichmentRegistry()
    plugin = MockPlugin("to-remove")

    registry.register(plugin)
    assert registry.unregister("to-remove") is True
    assert "to-remove" not in registry
    assert registry.unregister("to-remove") is False


def test_registry_enable_disable() -> None:
    registry = EnrichmentRegistry()
    plugin = MockPlugin("toggle")

    registry.register(plugin, enabled=False)
    assert not registry.is_enabled("toggle")

    registry.enable("toggle")
    assert registry.is_enabled("toggle")

    registry.disable("toggle")
    assert not registry.is_enabled("toggle")


def test_registry_get_ordered_plugins() -> None:
    registry = EnrichmentRegistry()
    p1 = MockPlugin("low", priority=PluginPriority.LOW)
    p2 = MockPlugin("high", priority=PluginPriority.HIGH)
    p3 = MockPlugin("normal", priority=PluginPriority.NORMAL)

    registry.register(p1)
    registry.register(p2)
    registry.register(p3)

    ordered = registry.get_ordered_plugins()
    ids = [p.metadata.id for p in ordered]

    assert ids == ["high", "normal", "low"]


def test_registry_priority_tiebreaker_registration_order() -> None:
    registry = EnrichmentRegistry()
    p1 = MockPlugin("first", priority=PluginPriority.NORMAL)
    p2 = MockPlugin("second", priority=PluginPriority.NORMAL)

    registry.register(p1)
    registry.register(p2)

    ordered = registry.get_ordered_plugins()
    ids = [p.metadata.id for p in ordered]

    assert ids == ["first", "second"]


def test_registry_dependency_ordering() -> None:
    registry = EnrichmentRegistry()
    base = MockPlugin("base", priority=PluginPriority.NORMAL)
    dependent = MockPlugin(
        "dependent", priority=PluginPriority.HIGH, dependencies=frozenset(["base"])
    )

    registry.register(base)
    registry.register(dependent)

    ordered = registry.get_ordered_plugins()
    ids = [p.metadata.id for p in ordered]

    # base deve vir antes de dependent, mesmo com prioridade menor
    assert ids.index("base") < ids.index("dependent")


def test_registry_missing_dependency_fails() -> None:
    registry = EnrichmentRegistry()
    plugin = MockPlugin("dependent", dependencies=frozenset(["missing"]))

    registry.register(plugin)
    with pytest.raises(PluginDependencyError, match="não está registrada"):
        registry.get_ordered_plugins()


def test_registry_circular_dependency_fails() -> None:
    registry = EnrichmentRegistry()
    a = MockPlugin("a", dependencies=frozenset(["b"]))
    b = MockPlugin("b", dependencies=frozenset(["a"]))

    registry.register(a)
    registry.register(b)
    with pytest.raises(PluginDependencyError, match="circular"):
        registry.get_ordered_plugins()


def test_registry_category_filtering() -> None:
    registry = EnrichmentRegistry()
    auth_plugin = MockPlugin("auth-only", categories=frozenset(["auth"]))
    net_plugin = MockPlugin("network-only", categories=frozenset(["network"]))
    all_plugin = MockPlugin("all-categories")

    registry.register(auth_plugin)
    registry.register(net_plugin)
    registry.register(all_plugin)

    auth_ordered = registry.get_ordered_plugins("auth")
    auth_ids = [p.metadata.id for p in auth_ordered]
    assert "auth-only" in auth_ids
    assert "all-categories" in auth_ids
    assert "network-only" not in auth_ids

    network_ordered = registry.get_ordered_plugins("network")
    network_ids = [p.metadata.id for p in network_ordered]
    assert "network-only" in network_ids
    assert "all-categories" in network_ids
    assert "auth-only" not in network_ids


def test_registry_stats() -> None:
    registry = EnrichmentRegistry()
    p1 = MockPlugin("p1", priority=PluginPriority.HIGH)
    p2 = MockPlugin("p2", priority=PluginPriority.NORMAL)
    p3 = MockPlugin("p3", priority=PluginPriority.LOW)

    registry.register(p1, enabled=True)
    registry.register(p2, enabled=False)
    registry.register(p3, enabled=True)

    stats = registry.get_stats()
    assert stats["total_plugins"] == 3
    assert stats["enabled_plugins"] == 2
    assert stats["by_priority"]["HIGH"] == 1
    assert stats["by_priority"]["NORMAL"] == 1
    assert stats["by_priority"]["LOW"] == 1


def test_registry_cache_invalidation() -> None:
    registry = EnrichmentRegistry()
    p1 = MockPlugin("p1")
    p2 = MockPlugin("p2")

    registry.register(p1)
    registry.get_ordered_plugins()  # Popula cache

    registry.register(p2)  # Deve invalidar cache

    ordered = registry.get_ordered_plugins()
    ids = [p.metadata.id for p in ordered]
    assert "p2" in ids
