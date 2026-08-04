"""Testes do DetectionRegistry."""

from __future__ import annotations

import pytest

from edysiem.detection import (
    DetectionContext,
    DetectionPriority,
    DetectionRegistry,
    DetectionResult,
    RuleMetadata,
)
from edysiem.detection.exceptions import (
    DetectionRuleDependencyError,
    DetectionRuleRegistrationError,
)


class MockRule:
    def __init__(
        self,
        rule_id: str,
        priority: DetectionPriority = DetectionPriority.NORMAL,
        dependencies: frozenset[str] = frozenset(),
        enabled: bool = True,
    ) -> None:
        self._id = rule_id
        self._priority = priority
        self._dependencies = dependencies
        self._enabled = enabled

    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id=self._id,
            name=f"Rule {self._id}",
            version="1.0.0",
            priority=self._priority,
            dependencies=self._dependencies,
            enabled=self._enabled,
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        return DetectionResult.no_detection(duration_ms=0.0, rule_id=self._id)


def test_registry_register() -> None:
    registry = DetectionRegistry()
    rule = MockRule("rule-1")
    registry.register(rule)
    assert "rule-1" in registry
    assert registry.get("rule-1") is rule
    assert registry.is_enabled("rule-1")


def test_registry_register_duplicate_fails() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("dup"))
    with pytest.raises(DetectionRuleRegistrationError, match="ja registrada"):
        registry.register(MockRule("dup"))


def test_registry_unregister() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("rule-1"))
    assert registry.unregister("rule-1") is True
    assert "rule-1" not in registry


def test_registry_enable_disable() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("rule-1", enabled=False))
    assert not registry.is_enabled("rule-1")
    registry.enable("rule-1")
    assert registry.is_enabled("rule-1")
    registry.disable("rule-1")
    assert not registry.is_enabled("rule-1")


def test_registry_ordered_by_priority() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("low", priority=DetectionPriority.LOW))
    registry.register(MockRule("high", priority=DetectionPriority.HIGH))
    registry.register(MockRule("normal", priority=DetectionPriority.NORMAL))

    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert ids == ["high", "normal", "low"]


def test_registry_dependency_ordering() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("base"))
    registry.register(
        MockRule("dependent", priority=DetectionPriority.HIGH, dependencies=frozenset({"base"}))
    )
    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert ids.index("base") < ids.index("dependent")


def test_registry_missing_dependency_fails() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("dependent", dependencies=frozenset({"missing"})))
    with pytest.raises(DetectionRuleDependencyError, match="nao esta registrada"):
        registry.get_ordered_rules()


def test_registry_circular_dependency_fails() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("a", dependencies=frozenset({"b"})))
    registry.register(MockRule("b", dependencies=frozenset({"a"})))
    with pytest.raises(DetectionRuleDependencyError, match="circular"):
        registry.get_ordered_rules()


def test_registry_get_metadata() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("rule-1"))
    meta = registry.get_metadata("rule-1")
    assert meta is not None
    assert meta.id == "rule-1"
    assert registry.get_metadata("missing") is None


def test_registry_get_all_and_enabled() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("rule-1"))
    registry.register(MockRule("rule-2", enabled=False))
    assert "rule-1" in registry.get_all_rules()
    assert "rule-1" in registry.get_enabled_rules()
    assert "rule-2" not in registry.get_enabled_rules()


def test_registry_stats_and_len() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("r1", priority=DetectionPriority.HIGH))
    registry.register(MockRule("r2"))
    registry.register(MockRule("r3", priority=DetectionPriority.LOW))

    assert len(registry) == 3
    assert len(list(registry)) == 3
    stats = registry.get_stats()
    assert stats["total_rules"] == 3
    assert stats["enabled_rules"] == 3
    assert stats["by_priority"]["HIGH"] == 1
    assert stats["by_priority"]["LOW"] == 1


def test_registry_cache_invalidation() -> None:
    registry = DetectionRegistry()
    registry.register(MockRule("r1"))
    registry.get_ordered_rules()
    registry.register(MockRule("r2"))
    ordered = registry.get_ordered_rules()
    ids = [r.metadata.id for r in ordered]
    assert "r2" in ids
