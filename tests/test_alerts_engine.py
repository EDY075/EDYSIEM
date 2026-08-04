"""Testes do AlertBuilder, LifecycleManager e AlertEngine."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from edysiem.alerts import (
    AlertBuilder,
    AlertContext,
    AlertEngine,
    AlertLifecycle,
    AlertPriority,
    AlertRegistry,
    AlertResultKind,
    AlertSeverity,
    DedupEngine,
    FingerprintEngine,
    LifecycleManager,
    RiskEngine,
)
from edysiem.alerts.exceptions import AlertInvalidStateTransition
from edysiem.detection import DetectionFinding, DetectionReason
from edysiem.domain import EnrichedEvent, RiskScore, Severity


def _finding(rule_id: str = "brute-force") -> DetectionFinding:
    return DetectionFinding(
        rule_id=rule_id,
        event_ids=("evt-1",),
        reason=DetectionReason(rule_id=rule_id, condition="5 falhas em 60s"),
        severity=Severity.HIGH,
        confidence=0.9,
        risk_score=RiskScore(70),
    )


def _event() -> EnrichedEvent:
    return EnrichedEvent(
        event_id="evt-1",
        trace_id="t",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="syslog",
        source_host="host-1",
        event_category="auth",
        event_action="reject",
        severity=Severity.LOW,
        ip_src="10.0.0.1",
        user="admin",
    )


# --- AlertBuilder ---------------------------------------------------------


def test_builder_creates_alert() -> None:
    builder = AlertBuilder(FingerprintEngine(), RiskEngine())
    alert = builder.build(_finding(), _event())

    assert alert.rule_id == "brute-force"
    assert alert.severity == AlertSeverity.HIGH
    assert alert.status == AlertLifecycle.OPEN
    assert alert.occurrences == 1
    assert alert.fingerprint is not None
    assert alert.event_ids == ("evt-1",)
    assert alert.timeline  # timeline inicial


def test_builder_priority_from_risk() -> None:
    builder = AlertBuilder()
    alert = builder.build(_finding(), _event())
    assert alert.priority == AlertPriority.P2  # risk 70 -> P2


def test_builder_requires_rule_id() -> None:
    builder = AlertBuilder()

    class BadFinding:
        rule_id = None
        event_ids = ()
        reason = None

    with pytest.raises(Exception, match="rule_id"):
        builder.build(BadFinding(), _event())


# --- LifecycleManager -----------------------------------------------------


def test_lifecycle_valid_transition() -> None:
    builder = AlertBuilder()
    alert = builder.build(_finding(), _event())
    manager = LifecycleManager()

    result = manager.transition(alert, AlertLifecycle.TRIAGE)
    assert result.changed is True
    assert result.alert.status == AlertLifecycle.TRIAGE
    assert result.previous == AlertLifecycle.OPEN
    assert len(result.alert.timeline) == 2  # created + status_change


def test_lifecycle_invalid_transition() -> None:
    builder = AlertBuilder()
    alert = builder.build(_finding(), _event())
    manager = LifecycleManager()

    with pytest.raises(AlertInvalidStateTransition, match="invalida"):
        manager.transition(alert, AlertLifecycle.RESOLVED)  # OPEN -> RESOLVED invalido


def test_lifecycle_idempotent() -> None:
    builder = AlertBuilder()
    alert = builder.build(_finding(), _event())
    manager = LifecycleManager()

    result = manager.transition(alert, AlertLifecycle.OPEN)
    assert result.changed is False


def test_lifecycle_full_flow() -> None:
    builder = AlertBuilder()
    alert = builder.build(_finding(), _event())
    manager = LifecycleManager()

    alert = manager.transition(alert, AlertLifecycle.TRIAGE).alert
    alert = manager.transition(alert, AlertLifecycle.INVESTIGATING).alert
    alert = manager.transition(alert, AlertLifecycle.RESOLVED).alert
    assert alert.status == AlertLifecycle.RESOLVED


# --- AlertEngine ----------------------------------------------------------


def test_engine_creates_alert() -> None:
    engine = AlertEngine()
    result = asyncio.run(engine.process_finding(_finding(), _event()))

    assert result.kind is AlertResultKind.CREATED
    assert result.was_new is True
    assert result.alert.rule_id == "brute-force"
    assert result.alert.fingerprint is not None


def test_engine_deduplicates() -> None:
    engine = AlertEngine()

    first = asyncio.run(engine.process_finding(_finding(), _event()))
    assert first.was_new is True
    assert first.alert.occurrences == 1

    second = asyncio.run(engine.process_finding(_finding(), _event()))
    assert second.was_new is False
    assert second.kind is AlertResultKind.DEDUPLICATED
    assert second.alert.occurrences == 2
    assert second.alert.id == first.alert.id


def test_engine_metrics() -> None:
    engine = AlertEngine()

    asyncio.run(engine.process_finding(_finding(), _event()))
    asyncio.run(engine.process_finding(_finding(), _event()))

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_created"] == 1
    assert snapshot["total_deduplicated"] == 1
    assert snapshot["created_by_rule"]["brute-force"] == 1
    assert snapshot["deduplicated_by_rule"]["brute-force"] == 1


def test_engine_transition() -> None:
    engine = AlertEngine()
    result = asyncio.run(engine.process_finding(_finding(), _event()))

    updated = engine.transition(result.alert, AlertLifecycle.TRIAGE)
    assert updated.status == AlertLifecycle.TRIAGE
    assert engine.context.get(updated.id).status == AlertLifecycle.TRIAGE


def test_engine_transition_invalid() -> None:
    engine = AlertEngine()
    result = asyncio.run(engine.process_finding(_finding(), _event()))

    with pytest.raises(AlertInvalidStateTransition):
        engine.transition(result.alert, AlertLifecycle.RESOLVED)


def test_engine_health_check() -> None:
    engine = AlertEngine()
    health = engine.health_check()
    assert health["engine"] == "healthy"
    assert "context" in health


def test_engine_registry_hooks() -> None:
    calls = []

    class Hook:
        def on_created(self, alert) -> None:
            calls.append(("created", alert.rule_id))

        def on_updated(self, alert) -> None:
            calls.append(("updated", alert.rule_id))

        def on_status_changed(self, alert, previous, current) -> None:
            calls.append(("status", previous, current))

    registry = AlertRegistry()
    registry.register(Hook(), name="hook")

    context = AlertContext()
    engine = AlertEngine(
        registry=registry,
        context=context,
        dedupe=DedupEngine(context),
    )

    result = asyncio.run(engine.process_finding(_finding(), _event()))
    engine.transition(result.alert, AlertLifecycle.TRIAGE)

    kinds = [c[0] for c in calls]
    assert "created" in kinds
    assert "status" in kinds


def test_alert_registry_duplicate_fails() -> None:
    registry = AlertRegistry()

    class Hook:
        def on_created(self, alert) -> None:
            pass

        def on_updated(self, alert) -> None:
            pass

        def on_status_changed(self, alert, previous, current) -> None:
            pass

    registry.register(Hook(), name="h")
    from edysiem.alerts.exceptions import AlertRegistrationError

    with pytest.raises(AlertRegistrationError):
        registry.register(Hook(), name="h")
