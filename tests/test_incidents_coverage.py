"""Testes suplementares do Incident Framework (cobertura)."""

from __future__ import annotations

import asyncio

import pytest

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.domain import RiskScore
from edysiem.incidents import (
    GroupingConfig,
    GroupingCriterion,
    GroupingEngine,
    IncidentBuilder,
    IncidentContext,
    IncidentEngine,
    IncidentLifecycleManager,
    IncidentRegistry,
    IncidentResultKind,
    IncidentStatus,
)
from edysiem.incidents.exceptions import (
    IncidentError,
    IncidentInvalidStateTransition,
    IncidentNotFoundError,
    IncidentRegistrationError,
)


def _alert(alert_id: str, rule_id: str = "brute-force", iocs=(), mitre=frozenset()) -> Alert:
    fp = AlertFingerprint(hash=f"fp-{alert_id}", rule_id=rule_id)
    return Alert(
        title=f"Alert {alert_id}",
        severity=AlertSeverity.HIGH,
        risk_score=RiskScore(70),
        rule_id=rule_id,
        asset_id="asset-1",
        user="admin",
        ioc_ids=tuple(iocs),
        mitre=mitre,
        fingerprint=fp,
        id=alert_id,
    )


def _five_alerts() -> list[Alert]:
    return [_alert(f"bf-{i}") for i in range(5)]


def test_grouping_ioc_criterion() -> None:
    cfg = GroupingConfig(enabled_criteria=frozenset({GroupingCriterion.IOC}), min_score=10)
    engine = GroupingEngine(cfg)
    alerts = [_alert("a1", iocs=("ioc-1",)), _alert("a2", iocs=("ioc-1",))]
    group = engine.group(alerts)
    assert group is not None
    assert GroupingCriterion.IOC in group.matched_criteria


def test_grouping_mitre_criterion() -> None:
    cfg = GroupingConfig(enabled_criteria=frozenset({GroupingCriterion.MITRE}), min_score=10)
    engine = GroupingEngine(cfg)
    alerts = [
        _alert("a1", mitre=frozenset({"T1059"})),
        _alert("a2", mitre=frozenset({"T1059"})),
    ]
    group = engine.group(alerts)
    assert group is not None
    assert GroupingCriterion.MITRE in group.matched_criteria


def test_grouping_fingerprint_criterion() -> None:
    cfg = GroupingConfig(enabled_criteria=frozenset({GroupingCriterion.FINGERPRINT}), min_score=10)
    engine = GroupingEngine(cfg)
    alerts = [
        Alert(
            title="a1",
            severity=AlertSeverity.HIGH,
            rule_id="r",
            fingerprint=AlertFingerprint(hash="same", rule_id="r"),
            id="a1",
        ),
        Alert(
            title="a2",
            severity=AlertSeverity.HIGH,
            rule_id="r",
            fingerprint=AlertFingerprint(hash="same", rule_id="r"),
            id="a2",
        ),
    ]
    group = engine.group(alerts)
    assert group is not None
    assert GroupingCriterion.FINGERPRINT in group.matched_criteria


def test_grouping_no_criteria_but_time_only() -> None:
    cfg = GroupingConfig(enabled_criteria=frozenset({GroupingCriterion.TIME_WINDOW}), min_score=5)
    engine = GroupingEngine(cfg)
    alerts = [_alert("a1"), _alert("a2")]
    group = engine.group(alerts)
    assert group is not None
    assert GroupingCriterion.TIME_WINDOW in group.matched_criteria


def test_incident_context_ops() -> None:
    context = IncidentContext()
    group = GroupingEngine().group(_five_alerts())
    assert group is not None
    incident = IncidentBuilder().build(group)

    context.save(incident)
    assert context.get(incident.id) == incident
    assert len(context) == 1
    assert len(context.all()) == 1
    assert context.snapshot()["incidents"] == 1

    context.clear()
    assert len(context) == 0


def test_incident_context_fingerprint_lookup() -> None:
    context = IncidentContext()
    group = GroupingEngine().group(_five_alerts())
    assert group is not None
    incident = IncidentBuilder().build(group)

    context.save(incident)
    assert context.get_incident_by_fingerprint(group.fingerprint.hash) == incident
    assert context.get_incident_by_fingerprint("nope") is None


def test_registry_hooks() -> None:
    calls = []

    class Hook:
        def on_created(self, incident) -> None:
            calls.append("created")

        def on_updated(self, incident) -> None:
            calls.append("updated")

        def on_status_changed(self, incident, previous, current) -> None:
            calls.append(f"status:{current.value}")

        def on_reopened(self, incident) -> None:
            calls.append("reopened")

    registry = IncidentRegistry()
    registry.register(Hook(), name="h1")
    registry.register(Hook(), name="h2")

    assert len(registry) == 2
    assert len(list(registry)) == 2
    assert registry.get("h1") is not None
    assert "h1" in registry.processor_names()

    group = GroupingEngine().group(_five_alerts())
    assert group is not None
    incident = IncidentBuilder().build(group)

    registry.on_created(incident)
    registry.on_updated(incident)
    registry.on_status_changed(incident, IncidentStatus.OPEN, IncidentStatus.TRIAGE)
    registry.on_reopened(incident)

    assert "created" in calls
    assert "updated" in calls
    assert "reopened" in calls

    assert registry.unregister("h1") is True
    assert registry.get("h1") is None
    assert registry.get_stats()["total_processors"] == 1


def test_registry_hook_failure_isolated() -> None:
    calls = []

    class BadHook:
        def on_created(self, incident) -> None:
            raise RuntimeError("hook quebrado")

        def on_updated(self, incident) -> None:
            raise RuntimeError("hook quebrado")

        def on_status_changed(self, incident, previous, current) -> None:
            raise RuntimeError("hook quebrado")

        def on_reopened(self, incident) -> None:
            raise RuntimeError("hook quebrado")

    class GoodHook:
        def on_created(self, incident) -> None:
            calls.append("created")

        def on_updated(self, incident) -> None:
            calls.append("updated")

        def on_status_changed(self, incident, previous, current) -> None:
            calls.append("status")

        def on_reopened(self, incident) -> None:
            calls.append("reopened")

    registry = IncidentRegistry()
    registry.register(BadHook(), name="bad")
    registry.register(GoodHook(), name="good")

    group = GroupingEngine().group(_five_alerts())
    assert group is not None
    incident = IncidentBuilder().build(group)

    registry.on_created(incident)
    registry.on_updated(incident)
    assert "created" in calls
    assert "updated" in calls


def test_incidents_exceptions() -> None:
    assert issubclass(IncidentError, Exception)
    assert issubclass(IncidentNotFoundError, IncidentError)
    assert issubclass(IncidentInvalidStateTransition, IncidentError)
    assert issubclass(IncidentRegistrationError, IncidentError)

    err = IncidentNotFoundError("inc-1")
    assert err.incident_id == "inc-1"
    assert "inc-1" in str(err)


def test_engine_no_group_different_rules() -> None:
    engine = IncidentEngine()
    alerts = [_alert("a1", rule_id="brute-force"), _alert("a2", rule_id="malware")]
    result = asyncio.run(engine.process_alerts(alerts))
    assert result.kind is IncidentResultKind.NO_GROUP
    assert result.was_new is False


def test_lifecycle_validate_transition() -> None:
    manager = IncidentLifecycleManager()
    assert manager.validate_transition(IncidentStatus.OPEN, IncidentStatus.TRIAGE)
    assert not manager.validate_transition(IncidentStatus.OPEN, IncidentStatus.CLOSED)


def test_incident_builder_empty_group() -> None:
    builder = IncidentBuilder()
    from edysiem.incidents.exceptions import IncidentBuilderError

    class Empty:
        alerts = ()

    with pytest.raises(IncidentBuilderError, match="vazio"):
        builder.build(Empty())  # type: ignore[arg-type]


def test_incident_metrics_avg() -> None:
    from edysiem.incidents import IncidentMetrics

    metrics = IncidentMetrics()
    assert metrics.avg_alerts_per_incident == 0.0
    metrics.record_created(5, "brute-force")
    metrics.record_deduplicated()
    assert metrics.avg_alerts_per_incident == 5.0
    assert metrics.total_deduplicated == 1
    assert metrics.created_by_rule["brute-force"] == 1
