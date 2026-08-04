"""Testes do RuleEngine e DetectionEngine."""

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
    DetectionPriority,
    DetectionReason,
    DetectionRegistry,
    DetectionResult,
    RuleEngine,
    RuleMetadata,
)
from edysiem.detection.exceptions import RuleValidationError
from edysiem.domain import EnrichedEvent, RiskScore, Severity


def _correlated(event_id: str = "evt-1", **source_kwargs) -> CorrelatedEvent:
    defaults = {
        "event_id": event_id,
        "trace_id": "trace-1",
        "timestamp": datetime.now(UTC),
        "received_at": datetime.now(UTC),
        "source_type": "syslog",
        "source_host": "host-1",
        "event_category": "auth",
        "event_action": "logon",
        "severity": Severity.INFO,
        "ip_src": "10.0.0.1",
    }
    defaults.update(source_kwargs)
    source = EnrichedEvent(**defaults)
    return CorrelatedEvent(event_id=event_id, source_event=source)


class AlwaysDetectRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="always-detect",
            name="Always",
            version="1.0.0",
            severity=Severity.HIGH,
            risk_score=RiskScore(80),
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        finding = DetectionFinding(
            rule_id="always-detect",
            event_ids=(event.event_id,),
            reason=DetectionReason(rule_id="always-detect", condition="sempre"),
            severity=Severity.HIGH,
            risk_score=RiskScore(80),
        )
        return DetectionResult.detected(
            findings=(finding,), duration_ms=1.0, rule_id="always-detect"
        )


class NeverDetectRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="never", name="Never", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        return DetectionResult.no_detection(duration_ms=1.0, rule_id="never")


class FailingRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="failing", name="Failing", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        raise RuntimeError("regra quebrada")


class TimeoutRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="timeout", name="Timeout", version="1.0.0", timeout_seconds=0.05)

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        await asyncio.sleep(1.0)
        return DetectionResult.no_detection(duration_ms=0.0, rule_id="timeout")


class RequiredFieldRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="req-field",
            name="ReqField",
            version="1.0.0",
            required_fields=frozenset({"ip_dst"}),
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
        finding = DetectionFinding(
            rule_id="req-field",
            event_ids=(event.event_id,),
            reason=DetectionReason(rule_id="req-field", condition="tem ip_dst"),
        )
        return DetectionResult.detected(findings=(finding,), duration_ms=1.0, rule_id="req-field")


class NoEvaluateRule:
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(id="no-eval", name="NoEval", version="1.0.0")

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass


def test_rule_engine_detect() -> None:
    registry = DetectionRegistry()
    registry.register(AlwaysDetectRule())
    engine = RuleEngine(registry)

    result = asyncio.run(engine.evaluate(_correlated()))
    assert result.decision is DetectionDecision.DETECTED
    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "always-detect"


def test_rule_engine_no_detection() -> None:
    registry = DetectionRegistry()
    registry.register(NeverDetectRule())
    engine = RuleEngine(registry)

    result = asyncio.run(engine.evaluate(_correlated()))
    assert result.decision is DetectionDecision.NO_DETECTION
    assert result.findings == ()


def test_rule_engine_failure_isolation() -> None:
    registry = DetectionRegistry()
    registry.register(FailingRule())
    registry.register(AlwaysDetectRule())
    engine = RuleEngine(registry)

    result = asyncio.run(engine.evaluate(_correlated()))
    assert result.decision is DetectionDecision.DETECTED
    assert result.findings[0].rule_id == "always-detect"


def test_rule_engine_timeout_isolation() -> None:
    registry = DetectionRegistry()
    registry.register(TimeoutRule())
    registry.register(AlwaysDetectRule())
    engine = RuleEngine(registry)

    result = asyncio.run(engine.evaluate(_correlated()))
    assert result.decision is DetectionDecision.DETECTED


def test_rule_engine_required_fields_skip() -> None:
    registry = DetectionRegistry()
    registry.register(RequiredFieldRule())  # exige ip_dst; evento so tem ip_src
    engine = RuleEngine(registry)

    result = asyncio.run(engine.evaluate(_correlated()))
    assert result.decision is DetectionDecision.NO_DETECTION


def test_rule_engine_validation() -> None:
    registry = DetectionRegistry()
    registry.register(NoEvaluateRule())
    engine = RuleEngine(registry)

    with pytest.raises(RuleValidationError, match="nao implementa evaluate"):
        engine.validate_rule(NoEvaluateRule())


def test_rule_engine_validate_all() -> None:
    registry = DetectionRegistry()
    registry.register(AlwaysDetectRule())
    engine = RuleEngine(registry)
    engine.validate_all()  # nao deve falhar


def test_rule_engine_metrics() -> None:
    registry = DetectionRegistry()
    registry.register(AlwaysDetectRule())
    registry.register(NeverDetectRule())
    engine = RuleEngine(registry)

    asyncio.run(engine.evaluate(_correlated()))

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_events_processed"] == 1
    assert snapshot["total_executions"] == 2
    assert snapshot["total_detections"] == 1
    assert snapshot["detections_by_rule"]["always-detect"] == 1


def test_rule_engine_priority_order() -> None:
    order: list[str] = []

    class OrderedRule(AlwaysDetectRule):
        def __init__(self, rule_id: str, priority: DetectionPriority) -> None:
            self._id = rule_id
            self._priority = priority

        @property
        def metadata(self) -> RuleMetadata:
            return RuleMetadata(
                id=self._id, name=self._id, version="1.0.0", priority=self._priority
            )

        async def evaluate(self, event, context: DetectionContext) -> DetectionResult:
            order.append(self._id)
            return await super().evaluate(event, context)

    registry = DetectionRegistry()
    registry.register(OrderedRule("low", DetectionPriority.LOW))
    registry.register(OrderedRule("high", DetectionPriority.HIGH))
    engine = RuleEngine(registry)

    asyncio.run(engine.evaluate(_correlated()))
    assert order == ["high", "low"]


def test_detection_engine_process() -> None:
    registry = DetectionRegistry()
    registry.register(AlwaysDetectRule())
    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    outcome = asyncio.run(det_engine.process(_correlated()))
    assert outcome.event_id == "evt-1"
    assert outcome.detected_rule_ids == ("always-detect",)
    assert len(outcome.findings) == 1


def test_detection_engine_summarize() -> None:
    registry = DetectionRegistry()
    registry.register(AlwaysDetectRule())
    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    outcome = asyncio.run(det_engine.process(_correlated()))
    summary = det_engine.summarize(outcome)
    assert summary.detected is True
    assert summary.detected_rule_ids == ("always-detect",)
    assert summary.finding_count == 1
    assert summary.max_severity == "high"


def test_detection_engine_no_detection_summary() -> None:
    registry = DetectionRegistry()
    registry.register(NeverDetectRule())
    rule_engine = RuleEngine(registry)
    det_engine = DetectionEngine(rule_engine)

    outcome = asyncio.run(det_engine.process(_correlated()))
    summary = det_engine.summarize(outcome)
    assert summary.detected is False
    assert summary.finding_count == 0


def test_rule_engine_health_check() -> None:
    registry = DetectionRegistry()
    registry.register(AlwaysDetectRule())
    engine = RuleEngine(registry)
    asyncio.run(engine.initialize())

    health = asyncio.run(engine.health_check())
    assert health["engine"] == "healthy"
    assert health["initialized"] is True


def test_rule_engine_shutdown() -> None:
    registry = DetectionRegistry()
    registry.register(AlwaysDetectRule())
    engine = RuleEngine(registry)
    asyncio.run(engine.shutdown())  # nao deve falhar


def test_rule_engine_default_timeout() -> None:
    engine = RuleEngine(DetectionRegistry())
    assert engine._default_timeout == 5.0
