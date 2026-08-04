"""Testes da regra DEMO ThresholdByIpRule."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.correlation import (
    CorrelationContext,
    CorrelationEngine,
    CorrelationRegistry,
)
from edysiem.correlation.plugins import ThresholdByIpRule
from edysiem.domain import EnrichedEvent, Severity


def _event(event_id: str, ip: str) -> EnrichedEvent:
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


def test_demo_rule_validation() -> None:
    with pytest.raises(ValueError, match="threshold deve ser >= 2"):
        ThresholdByIpRule(threshold=1)
    with pytest.raises(ValueError, match="window_seconds deve ser > 0"):
        ThresholdByIpRule(threshold=5, window_seconds=0)


def test_demo_rule_metadata() -> None:
    rule = ThresholdByIpRule(threshold=3, window_seconds=60)
    meta = rule.metadata
    assert meta.id == "demo-threshold-by-ip"
    assert "ip_src" in meta.required_fields
    assert meta.window_seconds == 60.0


@pytest.mark.asyncio
async def test_demo_rule_no_match_below_threshold() -> None:
    rule = ThresholdByIpRule(threshold=5, window_seconds=60)
    context = CorrelationContext()

    result = await rule.evaluate(_event("evt-1", "10.0.0.1"), context)
    assert result.decision.value == "deferred"
    assert result.matches == ()


@pytest.mark.asyncio
async def test_demo_rule_match_above_threshold() -> None:
    rule = ThresholdByIpRule(threshold=3, window_seconds=60)
    context = CorrelationContext()

    # Ate 2 eventos: deferred
    result = await rule.evaluate(_event("evt-1", "10.0.0.1"), context)
    assert result.decision.value == "deferred"
    result = await rule.evaluate(_event("evt-2", "10.0.0.1"), context)
    assert result.decision.value == "deferred"

    # 3o evento: match
    result = await rule.evaluate(_event("evt-3", "10.0.0.1"), context)
    assert result.decision.value == "match"
    assert len(result.matches) == 1
    match = result.matches[0]
    assert match.rule_id == "demo-threshold-by-ip"
    assert "10.0.0.1" in match.reason.values["ip_src"]
    assert match.reason.values["count"] == 3


@pytest.mark.asyncio
async def test_demo_rule_per_ip_isolation() -> None:
    rule = ThresholdByIpRule(threshold=3, window_seconds=60)
    context = CorrelationContext()

    # IP A tem 3 eventos (match), IP B tem 1 (deferred)
    result = await rule.evaluate(_event("a1", "10.0.0.1"), context)
    result = await rule.evaluate(_event("a2", "10.0.0.1"), context)
    result = await rule.evaluate(_event("b1", "10.0.0.2"), context)
    assert result.decision.value == "deferred"

    result = await rule.evaluate(_event("a3", "10.0.0.1"), context)
    assert result.decision.value == "match"
    assert set(result.matches[0].matched_event_ids) == {"a1", "a2", "a3"}


@pytest.mark.asyncio
async def test_demo_rule_missing_ip_deferred() -> None:
    rule = ThresholdByIpRule(threshold=3, window_seconds=60)
    context = CorrelationContext()

    event = _event("evt-1", "10.0.0.1")
    event = EnrichedEvent(
        event_id="evt-no-ip",
        trace_id="t",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="syslog",
        source_host="host",
        event_category="auth",
        event_action="logon",
        severity=Severity.INFO,
    )
    result = await rule.evaluate(event, context)
    assert result.decision.value == "deferred"


@pytest.mark.asyncio
async def test_demo_rule_through_engine() -> None:
    """Valida a regra DEMO no fluxo completo do engine."""
    registry = CorrelationRegistry()
    registry.register(ThresholdByIpRule(threshold=3, window_seconds=60))
    engine = CorrelationEngine(registry)

    correlated1 = await engine.process(_event("evt-1", "10.0.0.1"))
    assert correlated1.matches == ()

    correlated2 = await engine.process(_event("evt-2", "10.0.0.1"))
    assert correlated2.matches == ()

    correlated3 = await engine.process(_event("evt-3", "10.0.0.1"))
    assert len(correlated3.matches) == 1
    assert correlated3.matches[0].rule_id == "demo-threshold-by-ip"

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_matches"] == 1
    assert snapshot["total_events_processed"] == 3
