"""Testes do IncidentLifecycleManager e IncidentEngine (inclui DEMO)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.domain import RiskScore
from edysiem.incidents import (
    GroupingConfig,
    GroupingEngine,
    IncidentBuilder,
    IncidentContext,
    IncidentCorrelator,
    IncidentEngine,
    IncidentLifecycleManager,
    IncidentRegistry,
    IncidentResultKind,
    IncidentStatus,
)
from edysiem.incidents.exceptions import (
    IncidentInvalidStateTransition,
    IncidentRegistrationError,
)


def _alert(alert_id: str, rule_id: str = "brute-force", seen=None) -> Alert:
    now = seen or datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    fp = AlertFingerprint(hash=f"fp-{alert_id}", rule_id=rule_id)
    return Alert(
        title=f"Alert {alert_id}",
        severity=AlertSeverity.HIGH,
        risk_score=RiskScore(70),
        rule_id=rule_id,
        asset_id="asset-1",
        user="admin",
        fingerprint=fp,
        first_seen=now,
        last_seen=now,
        id=alert_id,
    )


def _brute_force_alerts(n: int = 5) -> list[Alert]:
    """Gera N alertas de brute force (demo)."""
    base = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    return [
        _alert(f"bf-{i}", rule_id="brute-force", seen=base + timedelta(seconds=i)) for i in range(n)
    ]


# --- LifecycleManager -----------------------------------------------------


def test_lifecycle_valid_transition() -> None:
    builder = IncidentBuilder()
    group = GroupingEngine().group(_brute_force_alerts(5))
    assert group is not None
    incident = builder.build(group)

    manager = IncidentLifecycleManager()
    result = manager.transition(incident, IncidentStatus.TRIAGE)
    assert result.changed is True
    assert result.incident.status == IncidentStatus.TRIAGE
    assert len(result.incident.timeline) == 2


def test_lifecycle_invalid_transition() -> None:
    builder = IncidentBuilder()
    group = GroupingEngine().group(_brute_force_alerts(5))
    assert group is not None
    incident = builder.build(group)

    manager = IncidentLifecycleManager()
    with pytest.raises(IncidentInvalidStateTransition):
        manager.transition(incident, IncidentStatus.CLOSED)  # OPEN -> CLOSED invalido


def test_lifecycle_full_flow() -> None:
    builder = IncidentBuilder()
    group = GroupingEngine().group(_brute_force_alerts(5))
    assert group is not None
    incident = builder.build(group)

    manager = IncidentLifecycleManager()
    incident = manager.transition(incident, IncidentStatus.TRIAGE).incident
    incident = manager.transition(incident, IncidentStatus.INVESTIGATING).incident
    incident = manager.transition(incident, IncidentStatus.CONTAINED).incident
    incident = manager.transition(incident, IncidentStatus.RESOLVED).incident
    incident = manager.transition(incident, IncidentStatus.CLOSED).incident
    assert incident.status == IncidentStatus.CLOSED
    assert incident.closed_at is not None


def test_lifecycle_reopen() -> None:
    builder = IncidentBuilder()
    group = GroupingEngine().group(_brute_force_alerts(5))
    assert group is not None
    incident = builder.build(group)

    manager = IncidentLifecycleManager()
    for target in (
        IncidentStatus.TRIAGE,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.CONTAINED,
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
    ):
        incident = manager.transition(incident, target).incident

    reopened = manager.transition(incident, IncidentStatus.REOPENED).incident
    assert reopened.status == IncidentStatus.REOPENED


# --- IncidentEngine (inclui DEMO) -----------------------------------------


def test_engine_creates_incident_from_five_alerts() -> None:
    """DEMO: 5 alertas de brute force -> 1 incidente."""
    engine = IncidentEngine()
    result = asyncio.run(engine.process_alerts(_brute_force_alerts(5)))

    assert result.kind is IncidentResultKind.CREATED
    assert result.was_new is True
    assert result.incident is not None
    assert len(result.incident.alerts) == 5
    assert "brute-force" in result.incident.title


def test_engine_no_group_single_alert() -> None:
    engine = IncidentEngine()
    result = asyncio.run(engine.process_alerts([_alert("a1")]))
    assert result.kind is IncidentResultKind.NO_GROUP
    assert result.was_new is False


def test_engine_deduplicates() -> None:
    engine = IncidentEngine()

    first = asyncio.run(engine.process_alerts(_brute_force_alerts(5)))
    assert first.was_new is True
    assert first.incident is not None
    assert first.incident.occurrences == 1

    second = asyncio.run(engine.process_alerts(_brute_force_alerts(5)))
    assert second.kind is IncidentResultKind.DEDUPLICATED
    assert second.incident is not None
    assert second.incident.occurrences == 2
    assert second.incident.id == first.incident.id


def test_engine_transition() -> None:
    engine = IncidentEngine()
    result = asyncio.run(engine.process_alerts(_brute_force_alerts(5)))
    assert result.incident is not None

    updated = engine.transition(result.incident, IncidentStatus.TRIAGE)
    assert updated.status == IncidentStatus.TRIAGE
    assert engine.context.get(updated.id).status == IncidentStatus.TRIAGE


def test_engine_reopen_metrics() -> None:
    engine = IncidentEngine()
    result = asyncio.run(engine.process_alerts(_brute_force_alerts(5)))
    assert result.incident is not None

    incident = result.incident
    for target in (
        IncidentStatus.TRIAGE,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.CONTAINED,
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
    ):
        incident = engine.transition(incident, target)
    engine.transition(incident, IncidentStatus.REOPENED)

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_reopened"] == 1


def test_engine_metrics() -> None:
    engine = IncidentEngine()
    asyncio.run(engine.process_alerts(_brute_force_alerts(5)))

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_created"] == 1
    assert snapshot["total_grouped_alerts"] == 5
    assert snapshot["avg_alerts_per_incident"] == 5


def test_engine_custom_config() -> None:
    """Configuracao customizada: janela curta e min_score alto."""
    from edysiem.incidents import GroupingCriterion

    cfg = GroupingConfig(
        time_window_seconds=60,
        min_score=70,
        enabled_criteria=frozenset(
            {GroupingCriterion.RULE, GroupingCriterion.ASSET, GroupingCriterion.USER}
        ),
    )
    context = IncidentContext()
    engine = IncidentEngine(
        correlator=IncidentCorrelator(GroupingEngine(cfg), context),
        context=context,
    )

    # 5 alertas mesmos rule+asset+user+janela -> score 48% < 70 -> NO_GROUP
    result = asyncio.run(engine.process_alerts(_brute_force_alerts(5)))
    assert result.kind is IncidentResultKind.NO_GROUP


def test_engine_registry_hooks() -> None:
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
    registry.register(Hook(), name="hook")

    context = IncidentContext()
    engine = IncidentEngine(registry=registry, context=context)

    result = asyncio.run(engine.process_alerts(_brute_force_alerts(5)))
    assert result.incident is not None
    engine.transition(result.incident, IncidentStatus.TRIAGE)

    assert "created" in calls
    assert any(c.startswith("status:") for c in calls)


def test_engine_health_check() -> None:
    engine = IncidentEngine()
    health = engine.health_check()
    assert health["engine"] == "healthy"


def test_registry_duplicate_fails() -> None:
    class Hook:
        def on_created(self, incident) -> None:
            pass

        def on_updated(self, incident) -> None:
            pass

        def on_status_changed(self, incident, previous, current) -> None:
            pass

        def on_reopened(self, incident) -> None:
            pass

    registry = IncidentRegistry()
    registry.register(Hook(), name="h")
    with pytest.raises(IncidentRegistrationError):
        registry.register(Hook(), name="h")
