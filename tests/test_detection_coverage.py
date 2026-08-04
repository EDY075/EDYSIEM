"""Testes suplementares do Detection Framework (cobertura)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from edysiem.correlation import CorrelatedEvent
from edysiem.detection import (
    DetectionContext,
    DetectionDecision,
    DetectionEngine,
    DetectionFinding,
    DetectionReason,
    DetectionRegistry,
    DetectionResult,
    RuleEngine,
    RuleMetadata,
)
from edysiem.detection.exceptions import RuleValidationError
from edysiem.domain import EnrichedEvent, RiskScore, Severity


class DetectRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="detect", name="Detect", version="1.0.0", severity=Severity.HIGH)

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        finding = DetectionFinding(
            rule_id="detect",
            event_ids=(event.event_id,),
            reason=DetectionReason(rule_id="detect", condition="x"),
            severity=Severity.HIGH,
            risk_score=RiskScore(90),
        )
        return DetectionResult.detected(findings=(finding,), duration_ms=1.0, rule_id="detect")


class FailingSetupRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="fail-setup", name="FailSetup", version="1.0.0")

    async def setup(self) -> None:
        raise RuntimeError("setup falhou")

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        return DetectionResult.no_detection(duration_ms=0.0, rule_id="fail-setup")


class EmptyNameRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="empty-name", name="", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        return DetectionResult.no_detection(duration_ms=0.0, rule_id="empty-name")


class NoEvaluateRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="no-eval", name="NoEval", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass


def _correlated() -> CorrelatedEvent:
    source = EnrichedEvent(
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
    )
    return CorrelatedEvent(event_id="evt-1", source_event=source)


def test_rule_engine_initialize_with_failing_setup() -> None:
    """Setup que falha nao impede o engine de inicializar."""
    registry = DetectionRegistry()
    registry.register(FailingSetupRule())
    registry.register(DetectRule())
    engine = RuleEngine(registry)

    asyncio.run(engine.initialize())
    assert engine._initialized is True


def test_rule_engine_validate_all_catches_invalid() -> None:
    registry = DetectionRegistry()
    registry.register(NoEvaluateRule())
    engine = RuleEngine(registry)

    with pytest.raises(RuleValidationError, match="nao implementa evaluate"):
        engine.validate_all()


def test_rule_engine_validate_missing_evaluate() -> None:
    engine = RuleEngine(DetectionRegistry())
    with pytest.raises(RuleValidationError, match="nao implementa evaluate"):
        engine.validate_rule(NoEvaluateRule())


def test_rule_engine_detect_high_severity() -> None:
    registry = DetectionRegistry()
    registry.register(DetectRule())
    engine = RuleEngine(registry)

    result = asyncio.run(engine.evaluate(_correlated()))
    assert result.decision is DetectionDecision.DETECTED
    assert result.rule_id == "detect"
    assert result.findings[0].severity == Severity.HIGH


def test_detection_engine_metrics() -> None:
    registry = DetectionRegistry()
    registry.register(DetectRule())
    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    asyncio.run(det_engine.process(_correlated()))

    snapshot = det_engine.get_metrics_snapshot()
    assert snapshot["total_events_processed"] == 1
    assert snapshot["total_detections"] == 1
    assert snapshot["detections_by_rule"]["detect"] == 1


def test_detection_engine_summary_max_severity() -> None:
    registry = DetectionRegistry()
    registry.register(DetectRule())
    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    outcome = asyncio.run(det_engine.process(_correlated()))
    summary = det_engine.summarize(outcome)
    assert summary.max_severity == "high"


def test_detection_result_fail() -> None:
    result = DetectionResult.fail(error="boom", duration_ms=5.0, rule_id="r")
    assert result.decision is DetectionDecision.NO_DETECTION
    assert result.error == "boom"


def test_detection_metrics_record_failure() -> None:
    from edysiem.detection import DetectionMetrics

    metrics = DetectionMetrics()
    metrics.record_failure("r", timeout=True)
    assert metrics.total_failures == 1
    assert metrics.total_timeout == 1
    assert metrics.failures_by_rule["r"] == 1


def test_detection_metrics_avg() -> None:
    from edysiem.detection import DetectionMetrics

    metrics = DetectionMetrics()
    metrics.record_execution("r", 10.0, 0, DetectionDecision.NO_DETECTION)
    assert metrics.avg_duration_ms == 10.0
    assert metrics.total_executions == 1


def test_registry_register_enabled_override() -> None:
    registry = DetectionRegistry()
    registry.register(DetectRule(), enabled=False)
    assert not registry.is_enabled("detect")


def test_registry_metadata_defaults() -> None:
    meta = RuleMetadata(id="r", name="R", version="1.0.0")
    assert meta.author == "edysiem"
    assert meta.severity == Severity.MEDIUM
    assert meta.risk_score == RiskScore(50)


def test_detection_finding_default_created_at() -> None:
    finding = DetectionFinding(
        rule_id="r",
        event_ids=("evt-1",),
        reason=DetectionReason(rule_id="r", condition="x"),
    )
    assert finding.created_at is not None
    assert finding.tags == frozenset()
    assert finding.confidence == 1.0


class TimeoutRule2:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="timeout2", name="Timeout2", version="1.0.0", timeout_seconds=0.05)

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        await asyncio.sleep(1.0)
        return DetectionResult.no_detection(duration_ms=0.0, rule_id="timeout2")


class FailRule2:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="fail2", name="Fail2", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        raise RuntimeError("boom")


def test_rule_engine_timeout_metrics() -> None:
    registry = DetectionRegistry()
    registry.register(TimeoutRule2())
    engine = RuleEngine(registry)

    asyncio.run(engine.evaluate(_correlated()))

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_failures"] == 1
    assert snapshot["total_timeout"] == 1
    assert snapshot["failures_by_rule"]["timeout2"] == 1


def test_rule_engine_failure_metrics() -> None:
    registry = DetectionRegistry()
    registry.register(FailRule2())
    engine = RuleEngine(registry)

    asyncio.run(engine.evaluate(_correlated()))

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_failures"] == 1
    assert snapshot["failures_by_rule"]["fail2"] == 1


def test_rule_engine_initialize_idempotent() -> None:
    registry = DetectionRegistry()
    registry.register(DetectRule())
    engine = RuleEngine(registry)

    asyncio.run(engine.initialize())
    asyncio.run(engine.initialize())
    assert engine._initialized is True


def test_detection_context_window_expiry() -> None:
    import time as _time

    context = DetectionContext()
    now = _time.monotonic()
    context.add_event("r", "host-1", "evt-1", timestamp=now)
    context.add_event("r", "host-1", "evt-2", timestamp=now - 600)

    window = context.get_window("r", "host-1", 300.0, now=now)
    assert window == ("evt-1",)
