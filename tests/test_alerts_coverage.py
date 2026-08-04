"""Testes suplementares do Alert Framework (cobertura)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from edysiem.alerts import (
    Alert,
    AlertBuilder,
    AlertContext,
    AlertEngine,
    AlertLifecycle,
    AlertRegistry,
    AlertSeverity,
    DedupEngine,
    FingerprintEngine,
    LifecycleManager,
    RiskEngine,
)
from edysiem.alerts.exceptions import (
    AlertBuilderError,
    AlertError,
    AlertInvalidStateTransition,
    AlertNotFoundError,
    AlertRegistrationError,
)
from edysiem.detection import DetectionFinding, DetectionReason
from edysiem.domain import EnrichedEvent, RiskScore, Severity


class FullFinding:
    """Finding com campos extras (asset, user, mitre, ioc)."""

    rule_id = "malware"
    event_ids = ("evt-1",)
    reason = DetectionReason(rule_id="malware", condition="assinatura")
    severity = Severity.CRITICAL
    confidence = 0.95
    risk_score = RiskScore(90)
    tags = frozenset({"malware"})
    mitre = frozenset({"T1059"})
    asset_id = "asset-1"
    user = "admin"
    ioc_ids = ("ioc-1",)


def _finding() -> DetectionFinding:
    return DetectionFinding(
        rule_id="brute-force",
        event_ids=("evt-1",),
        reason=DetectionReason(rule_id="brute-force", condition="x"),
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


def test_builder_full_fields() -> None:
    builder = AlertBuilder()
    alert = builder.build(FullFinding(), _event(), title="Malware detectado")

    assert alert.title == "Malware detectado"
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.mitre == frozenset({"T1059"})
    assert alert.asset_id == "asset-1"
    assert alert.user == "admin"
    assert alert.ioc_ids == ("ioc-1",)
    assert "malware" in alert.tags
    assert alert.priority.value == "p1"  # risk 90


def test_builder_severity_mapping() -> None:
    builder = AlertBuilder()
    alert = builder.build(_finding(), _event())
    assert alert.severity == AlertSeverity.HIGH

    low = builder.build(
        DetectionFinding(
            rule_id="r",
            event_ids=(),
            reason=DetectionReason(rule_id="r", condition="x"),
            severity=Severity.LOW,
        ),
        _event(),
    )
    assert low.severity == AlertSeverity.LOW


def test_risk_factor_from_intel() -> None:
    engine = RiskEngine()
    factor = engine.factor_from_intel(0.8)
    assert factor.name == "threat_intel"
    assert factor.score == 0.8

    score = engine.evaluate(
        severity=AlertSeverity.MEDIUM,
        confidence=0.5,
        additional_factors=(factor,),
    )
    assert 0 <= score.value <= 100


def test_risk_engine_zero_weight() -> None:
    engine = RiskEngine()
    score = engine.evaluate(
        severity=AlertSeverity.MEDIUM,
        confidence=0.0,
        additional_factors=(),
    )
    assert 0 <= score.value <= 100


def test_alerts_exceptions() -> None:
    assert issubclass(AlertError, Exception)
    assert issubclass(AlertNotFoundError, AlertError)
    assert issubclass(AlertInvalidStateTransition, AlertError)
    assert issubclass(AlertRegistrationError, AlertError)
    assert issubclass(AlertBuilderError, AlertError)

    err = AlertNotFoundError("alert-1")
    assert err.alert_id == "alert-1"
    assert "alert-1" in str(err)

    err2 = AlertInvalidStateTransition("open", "resolved")
    assert err2.current == "open"
    assert err2.target == "resolved"


def test_registry_hooks_on_updated_and_status() -> None:
    calls = []

    class Hook:
        def on_created(self, alert) -> None:
            calls.append("created")

        def on_updated(self, alert) -> None:
            calls.append("updated")

        def on_status_changed(self, alert, previous, current) -> None:
            calls.append(f"status:{previous}:{current}")

    registry = AlertRegistry()
    registry.register(Hook())

    context = AlertContext()
    engine = AlertEngine(registry=registry, context=context, dedupe=DedupEngine(context))

    # 1 criacao + 1 dedup (updated) + 1 transicao
    asyncio.run(engine.process_finding(_finding(), _event()))
    r2 = asyncio.run(engine.process_finding(_finding(), _event()))
    engine.transition(r2.alert, AlertLifecycle.TRIAGE)

    assert "created" in calls
    assert "updated" in calls
    assert any(c.startswith("status:") for c in calls)


def test_registry_unregister_and_stats() -> None:
    class Hook:
        def on_created(self, alert) -> None:
            pass

        def on_updated(self, alert) -> None:
            pass

        def on_status_changed(self, alert, previous, current) -> None:
            pass

    registry = AlertRegistry()
    registry.register(Hook(), name="h1")
    registry.register(Hook(), name="h2")

    assert registry.get("h1") is not None
    assert registry.unregister("h1") is True
    assert registry.get("h1") is None
    assert len(registry) == 1
    assert registry.get_stats()["total_processors"] == 1


def test_registry_hook_failure_isolated() -> None:
    calls = []

    class BadHook:
        def on_created(self, alert) -> None:
            raise RuntimeError("hook quebrado")

        def on_updated(self, alert) -> None:
            raise RuntimeError("hook quebrado")

        def on_status_changed(self, alert, previous, current) -> None:
            raise RuntimeError("hook quebrado")

    class GoodHook:
        def on_created(self, alert) -> None:
            calls.append("created")

        def on_updated(self, alert) -> None:
            calls.append("updated")

        def on_status_changed(self, alert, previous, current) -> None:
            calls.append("status")

    registry = AlertRegistry()
    registry.register(BadHook(), name="bad")
    registry.register(GoodHook(), name="good")

    context = AlertContext()
    engine = AlertEngine(registry=registry, context=context, dedupe=DedupEngine(context))

    asyncio.run(engine.process_finding(_finding(), _event()))
    # BadHook falha mas GoodHook ainda roda
    assert "created" in calls


def test_engine_metrics_updates_field() -> None:
    engine = AlertEngine()
    asyncio.run(engine.process_finding(_finding(), _event()))
    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_updates"] == 0  # campo preservado


def test_alert_context_fingerprint_lookup() -> None:
    context = AlertContext()
    fp = FingerprintEngine().compute("brute-force", _event())
    alert = Alert(title="x", rule_id="brute-force", fingerprint=fp)
    context.save(alert)

    assert context.get_alert_by_fingerprint(fp.hash) == alert
    assert context.get_alert_by_fingerprint("nonexistent") is None


def test_lifecycle_validate_transition() -> None:
    manager = LifecycleManager()
    assert manager.validate_transition(AlertLifecycle.OPEN, AlertLifecycle.TRIAGE)
    assert not manager.validate_transition(AlertLifecycle.OPEN, AlertLifecycle.RESOLVED)
