"""Testes da regra DEMO LoginFailuresRule e cobertura do framework."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.correlation import CorrelatedEvent
from edysiem.detection import (
    DetectionContext,
    DetectionDecision,
    DetectionEngine,
    DetectionRegistry,
    RuleEngine,
)
from edysiem.detection.exceptions import (
    DetectionContextError,
    DetectionError,
    DetectionRuleDependencyError,
    DetectionRuleNotFoundError,
    DetectionRuleRegistrationError,
    DetectionRuleTimeoutError,
    RuleValidationError,
)
from edysiem.detection.plugins import LoginFailuresRule
from edysiem.domain import EnrichedEvent, Severity


def _failure_event(event_id: str, host: str = "host-1") -> CorrelatedEvent:
    source = EnrichedEvent(
        event_id=event_id,
        trace_id="trace-1",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="syslog",
        source_host=host,
        event_category="auth",
        event_action="reject",
        severity=Severity.LOW,
        ip_src="10.0.0.1",
    )
    return CorrelatedEvent(event_id=event_id, source_event=source)


def test_demo_rule_validation() -> None:
    with pytest.raises(ValueError, match="threshold deve ser >= 2"):
        LoginFailuresRule(threshold=1)
    with pytest.raises(ValueError, match="window_seconds deve ser > 0"):
        LoginFailuresRule(threshold=5, window_seconds=0)


def test_demo_rule_metadata() -> None:
    rule = LoginFailuresRule(threshold=3, window_seconds=60)
    meta = rule.metadata
    assert meta.id == "demo-login-failures"
    assert "source_host" in meta.required_fields
    assert meta.severity == Severity.MEDIUM
    assert meta.risk_score.value == 60


def test_demo_rule_below_threshold() -> None:
    rule = LoginFailuresRule(threshold=3, window_seconds=60)
    context = DetectionContext()
    result = asyncio_run(rule.evaluate(_failure_event("evt-1"), context))
    assert result.decision is DetectionDecision.DEFERRED


def test_demo_rule_above_threshold() -> None:
    rule = LoginFailuresRule(threshold=3, window_seconds=60)
    context = DetectionContext()

    asyncio_run(rule.evaluate(_failure_event("evt-1"), context))
    asyncio_run(rule.evaluate(_failure_event("evt-2"), context))
    asyncio_run(rule.evaluate(_failure_event("evt-3"), context))
    result = asyncio_run(rule.evaluate(_failure_event("evt-4"), context))

    assert result.decision is DetectionDecision.DETECTED
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.rule_id == "demo-login-failures"
    assert finding.reason.values["count"] == 4


def test_demo_rule_non_login_event() -> None:
    rule = LoginFailuresRule(threshold=3, window_seconds=60)
    context = DetectionContext()
    source = EnrichedEvent(
        event_id="evt-net",
        trace_id="t",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="syslog",
        source_host="host-1",
        event_category="network",
        event_action="connect",
        severity=Severity.INFO,
        ip_src="10.0.0.1",
    )
    event = CorrelatedEvent(event_id="evt-net", source_event=source)
    result = asyncio_run(rule.evaluate(event, context))
    assert result.decision is DetectionDecision.NO_DETECTION


def test_demo_rule_through_engine() -> None:
    registry = DetectionRegistry()
    registry.register(LoginFailuresRule(threshold=3, window_seconds=60))
    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    asyncio_run(det_engine.process(_failure_event("evt-1")))
    asyncio_run(det_engine.process(_failure_event("evt-2")))
    asyncio_run(det_engine.process(_failure_event("evt-3")))
    outcome = asyncio_run(det_engine.process(_failure_event("evt-4")))

    assert outcome.detected_rule_ids == ("demo-login-failures",)
    assert len(outcome.findings) == 1

    snapshot = rule_engine.get_metrics_snapshot()
    assert snapshot["total_detections"] == 1
    assert snapshot["total_events_processed"] == 4


# --- Exceptions e context (cobertura) -------------------------------------


def test_detection_exceptions_hierarchy() -> None:
    assert issubclass(DetectionError, Exception)
    assert issubclass(DetectionRuleNotFoundError, DetectionError)
    assert issubclass(DetectionRuleTimeoutError, DetectionError)
    assert issubclass(DetectionRuleRegistrationError, DetectionError)
    assert issubclass(DetectionRuleDependencyError, DetectionError)
    assert issubclass(DetectionContextError, DetectionError)
    assert issubclass(RuleValidationError, DetectionError)


def test_detection_not_found_error() -> None:
    err = DetectionRuleNotFoundError("missing")
    assert err.rule_id == "missing"
    assert "missing" in str(err)


def test_detection_timeout_error() -> None:
    err = DetectionRuleTimeoutError("slow", 5.0)
    assert err.rule_id == "slow"
    assert err.timeout_seconds == 5.0


def test_detection_registration_error() -> None:
    err = DetectionRuleRegistrationError("dup")
    assert "dup" in str(err)


def test_detection_dependency_error() -> None:
    err = DetectionRuleDependencyError("a", "b")
    assert err.rule_id == "a"
    assert err.missing_dependency == "b"


def test_rule_validation_error() -> None:
    err = RuleValidationError("rule-1", "campo invalido")
    assert err.rule_id == "rule-1"
    assert "campo invalido" in str(err)


def test_detection_context_add_validates() -> None:
    context = DetectionContext()
    with pytest.raises(ValueError, match="rule_id nao pode ser vazio"):
        context.add_event("", "host-1", "evt-1")
    with pytest.raises(ValueError, match="identity_key nao pode ser vazio"):
        context.add_event("rule-1", "", "evt-1")


def test_detection_context_window_validation() -> None:
    context = DetectionContext()
    with pytest.raises(ValueError, match="window_seconds deve ser > 0"):
        context.get_window("rule-1", "host-1", 0)


def test_detection_context_cache() -> None:
    context = DetectionContext()
    context.set_cache("key", "value")
    assert context.get_cache("key") == "value"
    assert context.get_cache("missing", "default") == "default"
    context.clear_cache()
    assert context.get_cache("key") is None


def test_detection_context_clear() -> None:
    context = DetectionContext()
    context.add_event("rule-1", "host-1", "evt-1")
    context.add_event("rule-2", "host-2", "evt-2")
    assert context.state_size == 2

    context.clear(rule_id="rule-1")
    assert context.state_size == 1

    context.clear()
    assert context.state_size == 0


def test_detection_context_snapshot() -> None:
    context = DetectionContext()
    context.add_event("rule-1", "host-1", "evt-1")
    snap = context.snapshot()
    assert snap["buffers_active"] == 1
    assert snap["total_entries"] == 1


def asyncio_run(coro):
    import asyncio

    return asyncio.run(coro)
