"""Testes do CorrelationEngine."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from edysiem.correlation import (
    CorrelationContext,
    CorrelationEngine,
    CorrelationMatch,
    CorrelationMetadata,
    CorrelationReason,
    CorrelationRegistry,
    CorrelationResult,
)
from edysiem.domain import EnrichedEvent, Severity


def _event(event_id: str = "evt-1", ip: str = "10.0.0.1") -> EnrichedEvent:
    return EnrichedEvent(
        event_id=event_id,
        trace_id="trace-1",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="syslog",
        source_host="host-1",
        event_category="auth",
        event_action="logon",
        severity=Severity.INFO,
        ip_src=ip,
    )


class MatchRule:
    """Regra que sempre retorna match."""

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(id="match-rule", name="Match", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
        match = CorrelationMatch(
            rule_id="match-rule",
            matched_event_ids=(event.event_id,),
            reason=CorrelationReason(rule_id="match-rule", condition="always"),
        )
        return CorrelationResult.match(matches=(match,), duration_ms=1.0, rule_id="match-rule")


class NoMatchRule:
    """Regra que nunca dispara."""

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(id="no-match-rule", name="NoMatch", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
        return CorrelationResult.no_match(duration_ms=1.0, rule_id="no-match-rule")


class FailingRule:
    """Regra que levanta excecao."""

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(id="failing-rule", name="Failing", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
        raise RuntimeError("regra quebrada")


class TimeoutRule:
    """Regra que excede o timeout."""

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(
            id="timeout-rule",
            name="Timeout",
            version="1.0.0",
            timeout_seconds=0.05,
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
        await asyncio.sleep(1.0)
        return CorrelationResult.no_match(duration_ms=0.0, rule_id="timeout-rule")


class RequiredFieldRule:
    """Regra que exige ip_dst (evento so tem ip_src)."""

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(
            id="req-field-rule",
            name="ReqField",
            version="1.0.0",
            required_fields=frozenset({"ip_dst"}),
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
        match = CorrelationMatch(
            rule_id="req-field-rule",
            matched_event_ids=(event.event_id,),
            reason=CorrelationReason(rule_id="req-field-rule", condition="tem ip_dst"),
        )
        return CorrelationResult.match(matches=(match,), duration_ms=1.0, rule_id="req-field-rule")


@pytest.mark.asyncio
async def test_engine_single_match() -> None:
    registry = CorrelationRegistry()
    registry.register(MatchRule())
    engine = CorrelationEngine(registry)

    correlated = await engine.process(_event())

    assert len(correlated.matches) == 1
    assert correlated.matches[0].rule_id == "match-rule"
    assert correlated.event_id == "evt-1"
    assert correlated.source_event is not None


@pytest.mark.asyncio
async def test_engine_no_match() -> None:
    registry = CorrelationRegistry()
    registry.register(NoMatchRule())
    engine = CorrelationEngine(registry)

    correlated = await engine.process(_event())

    assert correlated.matches == ()


@pytest.mark.asyncio
async def test_engine_multiple_rules() -> None:
    registry = CorrelationRegistry()
    registry.register(MatchRule())
    registry.register(NoMatchRule())
    engine = CorrelationEngine(registry)

    correlated = await engine.process(_event())

    # Apenas MatchRule dispara
    assert len(correlated.matches) == 1


@pytest.mark.asyncio
async def test_engine_failure_isolation() -> None:
    """Falha de uma regra nao para as outras."""
    registry = CorrelationRegistry()
    registry.register(FailingRule())
    registry.register(MatchRule())
    engine = CorrelationEngine(registry)

    correlated = await engine.process(_event())

    # MatchRule ainda dispara mesmo com FailingRule quebrada
    assert len(correlated.matches) == 1
    assert correlated.matches[0].rule_id == "match-rule"


@pytest.mark.asyncio
async def test_engine_timeout_isolation() -> None:
    """Timeout de uma regra nao para as outras."""
    registry = CorrelationRegistry()
    registry.register(TimeoutRule())
    registry.register(MatchRule())
    engine = CorrelationEngine(registry)

    correlated = await engine.process(_event())

    assert len(correlated.matches) == 1
    assert correlated.matches[0].rule_id == "match-rule"


@pytest.mark.asyncio
async def test_engine_required_fields_skip() -> None:
    """Regra que exige ip_dst e pulada quando o evento nao tem ip_dst."""
    registry = CorrelationRegistry()
    registry.register(RequiredFieldRule())
    engine = CorrelationEngine(registry)

    correlated = await engine.process(_event())  # so tem ip_src

    assert correlated.matches == ()


@pytest.mark.asyncio
async def test_engine_metrics() -> None:
    registry = CorrelationRegistry()
    registry.register(MatchRule())
    registry.register(NoMatchRule())
    engine = CorrelationEngine(registry)

    await engine.process(_event())

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_events_processed"] == 1
    assert snapshot["total_executions"] == 2
    assert snapshot["total_matches"] == 1
    assert snapshot["matches_by_rule"]["match-rule"] == 1
    assert snapshot["executions_by_rule"]["no-match-rule"] == 1


@pytest.mark.asyncio
async def test_engine_failure_metrics() -> None:
    registry = CorrelationRegistry()
    registry.register(FailingRule())
    engine = CorrelationEngine(registry)

    await engine.process(_event())

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_failures"] == 1
    assert snapshot["failures_by_rule"]["failing-rule"] == 1


@pytest.mark.asyncio
async def test_engine_timeout_metrics() -> None:
    registry = CorrelationRegistry()
    registry.register(TimeoutRule())
    engine = CorrelationEngine(registry)

    await engine.process(_event())

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_failures"] == 1
    assert snapshot["total_timeout"] == 1


@pytest.mark.asyncio
async def test_engine_priority_order() -> None:
    order: list[str] = []

    class OrderedRule(MatchRule):
        @property
        def metadata(self) -> CorrelationMetadata:
            return CorrelationMetadata(
                id=self._id,
                name=self._name,
                version="1.0.0",
                priority=self._priority,
            )

        def __init__(self, rule_id: str, priority) -> None:
            self._id = rule_id
            self._name = rule_id
            self._priority = priority

        async def evaluate(self, event, context: CorrelationContext) -> CorrelationResult:
            order.append(self._id)
            return await super().evaluate(event, context)

    from edysiem.correlation import CorrelationPriority

    registry = CorrelationRegistry()
    registry.register(OrderedRule("low", CorrelationPriority.LOW))
    registry.register(OrderedRule("high", CorrelationPriority.HIGH))
    registry.register(OrderedRule("normal", CorrelationPriority.NORMAL))

    engine = CorrelationEngine(registry)
    await engine.process(_event())

    assert order == ["high", "normal", "low"]


@pytest.mark.asyncio
async def test_engine_health_check() -> None:
    registry = CorrelationRegistry()
    registry.register(MatchRule())
    engine = CorrelationEngine(registry)
    await engine.initialize()

    health = await engine.health_check()
    assert health["engine"] == "healthy"
    assert health["initialized"] is True
    assert "registry" in health
    assert "context" in health


@pytest.mark.asyncio
async def test_engine_shutdown() -> None:
    registry = CorrelationRegistry()
    rule = MatchRule()
    registry.register(rule)
    engine = CorrelationEngine(registry)

    await engine.shutdown()  # nao deve falhar


@pytest.mark.asyncio
async def test_engine_initialize_idempotent() -> None:
    registry = CorrelationRegistry()
    registry.register(MatchRule())
    engine = CorrelationEngine(registry)

    await engine.initialize()
    await engine.initialize()
    assert engine._initialized is True
