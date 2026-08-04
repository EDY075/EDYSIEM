"""Testes suplementares do Correlation Engine (cobertura)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.correlation import (
    CorrelationContext,
    CorrelationEngine,
    CorrelationMetadata,
    CorrelationRegistry,
    CorrelationResult,
)
from edysiem.correlation.exceptions import (
    CorrelationContextError,
    CorrelationError,
    CorrelationRuleDependencyError,
    CorrelationRuleNotFoundError,
    CorrelationRuleRegistrationError,
    CorrelationRuleTimeoutError,
)
from edysiem.domain import EnrichedEvent, Severity


class AlwaysDeferredRule:
    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(id="deferred-rule", name="Deferred", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
        return CorrelationResult.deferred(duration_ms=1.0, rule_id="deferred-rule")


def _event() -> EnrichedEvent:
    return EnrichedEvent(
        event_id="evt-1",
        trace_id="trace-1",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="syslog",
        source_host="host-1",
        event_category="auth",
        event_action="logon",
        severity=Severity.INFO,
        ip_src="10.0.0.1",
    )


def test_exceptions_hierarchy() -> None:
    assert issubclass(CorrelationError, Exception)
    assert issubclass(CorrelationRuleNotFoundError, CorrelationError)
    assert issubclass(CorrelationRuleTimeoutError, CorrelationError)
    assert issubclass(CorrelationRuleRegistrationError, CorrelationError)
    assert issubclass(CorrelationRuleDependencyError, CorrelationError)
    assert issubclass(CorrelationContextError, CorrelationError)


def test_rule_not_found_error() -> None:
    err = CorrelationRuleNotFoundError("missing-rule")
    assert err.rule_id == "missing-rule"
    assert "missing-rule" in str(err)


def test_rule_timeout_error() -> None:
    err = CorrelationRuleTimeoutError("slow-rule", 5.0)
    assert err.rule_id == "slow-rule"
    assert err.timeout_seconds == 5.0
    assert "slow-rule" in str(err)


def test_rule_registration_error() -> None:
    err = CorrelationRuleRegistrationError("duplicate")
    assert "duplicate" in str(err)


def test_rule_dependency_error() -> None:
    err = CorrelationRuleDependencyError("rule-a", "rule-b")
    assert err.rule_id == "rule-a"
    assert err.missing_dependency == "rule-b"


def test_context_error() -> None:
    err = CorrelationContextError("estado invalido")
    assert "estado invalido" in str(err)


def test_correlation_result_fail() -> None:
    result = CorrelationResult.fail(error="boom", duration_ms=5.0, rule_id="r")
    assert result.decision.value == "no_match"
    assert result.error == "boom"
    assert result.duration_ms == 5.0


def test_correlation_result_deferred() -> None:
    result = CorrelationResult.deferred(duration_ms=2.0, rule_id="r")
    assert result.decision.value == "deferred"
    assert result.matches == ()


def test_registry_get_metadata() -> None:
    registry = CorrelationRegistry()
    registry.register(AlwaysDeferredRule())
    meta = registry.get_metadata("deferred-rule")
    assert meta is not None
    assert meta.id == "deferred-rule"
    assert registry.get_metadata("missing") is None


def test_registry_get_all_and_enabled() -> None:
    registry = CorrelationRegistry()
    registry.register(AlwaysDeferredRule(), enabled=False)

    assert "deferred-rule" in registry.get_all_rules()
    assert "deferred-rule" not in registry.get_enabled_rules()
    assert "deferred-rule" in registry.get_rule_ids()


def test_registry_iteration() -> None:
    registry = CorrelationRegistry()
    registry.register(AlwaysDeferredRule())
    assert len(list(registry)) == 1
    assert len(registry) == 1


@pytest.mark.asyncio
async def test_engine_deferred_rule() -> None:
    registry = CorrelationRegistry()
    registry.register(AlwaysDeferredRule())
    engine = CorrelationEngine(registry)

    correlated = await engine.process(_event())
    assert correlated.matches == ()


@pytest.mark.asyncio
async def test_engine_health_not_initialized() -> None:
    registry = CorrelationRegistry()
    engine = CorrelationEngine(registry)

    health = await engine.health_check()
    assert health["engine"] == "not_initialized"
    assert health["initialized"] is False


@pytest.mark.asyncio
async def test_engine_context_is_shared() -> None:
    """O contexto deve ser compartilhado entre process() calls."""
    from edysiem.correlation.plugins import ThresholdByIpRule

    registry = CorrelationRegistry()
    registry.register(ThresholdByIpRule(threshold=2, window_seconds=60))
    engine = CorrelationEngine(registry)

    await engine.process(_event())
    await engine.process(_event())
    # 1 chave (ip_src) acumulada no contexto
    assert engine.context.state_size == 1


def test_engine_default_timeout() -> None:
    registry = CorrelationRegistry()
    engine = CorrelationEngine(registry)
    assert engine._default_timeout == 5.0


def test_correlation_metadata_timeout_field() -> None:
    meta = CorrelationMetadata(
        id="r", name="R", version="1.0.0", timeout_seconds=2.5, tags=frozenset({"a"})
    )
    assert meta.timeout_seconds == 2.5
    assert "a" in meta.tags
