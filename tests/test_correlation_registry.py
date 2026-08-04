"""Testes do CorrelationRegistry."""

from __future__ import annotations

import pytest

from edysiem.correlation import (
    CorrelationContext,
    CorrelationMetadata,
    CorrelationPriority,
    CorrelationRegistry,
    CorrelationResult,
)
from edysiem.correlation.exceptions import (
    CorrelationRuleDependencyError,
    CorrelationRuleRegistrationError,
)


class MockRule:
    def __init__(
        self,
        rule_id: str,
        priority: CorrelationPriority = CorrelationPriority.NORMAL,
        dependencies: frozenset[str] = frozenset(),
        event_types: frozenset[str] = frozenset(),
        enabled_by_default: bool = True,
    ) -> None:
        self._id = rule_id
        self._priority = priority
        self._dependencies = dependencies
        self._event_types = event_types
        self._enabled = enabled_by_default

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(
            id=self._id,
            name=f"Rule {self._id}",
            version="1.0.0",
            priority=self._priority,
            dependencies=self._dependencies,
            required_event_types=self._event_types,
            enabled_by_default=self._enabled,
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
        return CorrelationResult.no_match(duration_ms=0.0, rule_id=self._id)


def test_registry_register() -> None:
    registry = CorrelationRegistry()
    rule = MockRule("rule-1")
    registry.register(rule)
    assert "rule-1" in registry
    assert registry.get("rule-1") is rule
    assert registry.is_enabled("rule-1")


def test_registry_register_duplicate_fails() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("dup"))
    with pytest.raises(CorrelationRuleRegistrationError, match="ja registrada"):
        registry.register(MockRule("dup"))


def test_registry_unregister() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("rule-1"))
    assert registry.unregister("rule-1") is True
    assert "rule-1" not in registry
    assert registry.unregister("rule-1") is False


def test_registry_enable_disable() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("rule-1", enabled_by_default=False))
    assert not registry.is_enabled("rule-1")
    registry.enable("rule-1")
    assert registry.is_enabled("rule-1")
    registry.disable("rule-1")
    assert not registry.is_enabled("rule-1")


def test_registry_ordered_by_priority() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("low", priority=CorrelationPriority.LOW))
    registry.register(MockRule("high", priority=CorrelationPriority.HIGH))
    registry.register(MockRule("normal", priority=CorrelationPriority.NORMAL))

    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert ids == ["high", "normal", "low"]


def test_registry_priority_tiebreaker_registration() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("first"))
    registry.register(MockRule("second"))

    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert ids == ["first", "second"]


def test_registry_dependency_ordering() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("base"))
    registry.register(
        MockRule(
            "dependent",
            priority=CorrelationPriority.HIGH,
            dependencies=frozenset({"base"}),
        )
    )

    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert ids.index("base") < ids.index("dependent")


def test_registry_missing_dependency_fails() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("dependent", dependencies=frozenset({"missing"})))
    with pytest.raises(CorrelationRuleDependencyError, match="nao esta registrada"):
        registry.get_ordered_rules()


def test_registry_circular_dependency_fails() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("a", dependencies=frozenset({"b"})))
    registry.register(MockRule("b", dependencies=frozenset({"a"})))
    with pytest.raises(CorrelationRuleDependencyError, match="circular"):
        registry.get_ordered_rules()


def test_registry_event_type_filtering() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("auth-only", event_types=frozenset({"auth"})))
    registry.register(MockRule("net-only", event_types=frozenset({"network"})))
    registry.register(MockRule("all"))

    auth_rules = registry.get_ordered_rules("auth")
    auth_ids = [r.metadata.id for r in auth_rules]
    assert "auth-only" in auth_ids
    assert "all" in auth_ids
    assert "net-only" not in auth_ids


def test_registry_disabled_rule_not_executed() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("rule-1"))
    registry.register(MockRule("rule-2"), enabled=False)

    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert "rule-2" not in ids


def test_registry_stats() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("r1", priority=CorrelationPriority.HIGH))
    registry.register(MockRule("r2", priority=CorrelationPriority.NORMAL))
    registry.register(MockRule("r3", priority=CorrelationPriority.LOW))

    stats = registry.get_stats()
    assert stats["total_rules"] == 3
    assert stats["enabled_rules"] == 3
    assert stats["by_priority"]["HIGH"] == 1
    assert stats["by_priority"]["NORMAL"] == 1
    assert stats["by_priority"]["LOW"] == 1


def test_registry_cache_invalidation() -> None:
    registry = CorrelationRegistry()
    registry.register(MockRule("r1"))
    registry.get_ordered_rules()  # popula cache

    registry.register(MockRule("r2"))
    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert "r2" in ids
