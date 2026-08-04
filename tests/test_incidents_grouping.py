"""Testes do grouping, correlator e builder do Incident Framework."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.domain import RiskScore
from edysiem.incidents import (
    GroupingConfig,
    GroupingCriterion,
    GroupingEngine,
    IncidentBuilder,
    IncidentContext,
    IncidentCorrelator,
    IncidentPriority,
    IncidentSeverity,
)
from edysiem.incidents.correlator import CorrelationDecision


def _alert(
    alert_id: str,
    rule_id: str = "brute-force",
    asset: str | None = "asset-1",
    user: str | None = "admin",
    severity: AlertSeverity = AlertSeverity.HIGH,
    risk: int = 70,
    iocs: tuple[str, ...] = (),
    mitre: frozenset[str] = frozenset(),
    seen: datetime | None = None,
) -> Alert:
    now = seen or datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    fp = AlertFingerprint(hash=f"fp-{alert_id}", rule_id=rule_id)
    return Alert(
        title=f"Alert {alert_id}",
        severity=severity,
        risk_score=RiskScore(risk),
        rule_id=rule_id,
        asset_id=asset,
        user=user,
        ioc_ids=iocs,
        mitre=mitre,
        fingerprint=fp,
        first_seen=now,
        last_seen=now,
        created_at=now,
        id=alert_id,
    )


# --- GroupingConfig -------------------------------------------------------


def test_grouping_config_defaults() -> None:
    cfg = GroupingConfig()
    assert cfg.min_score == 40
    assert cfg.time_window_seconds == 3600.0
    assert cfg.group_by == "rule"


def test_grouping_config_validation() -> None:
    with pytest.raises(ValueError, match="time_window_seconds deve ser > 0"):
        GroupingConfig(time_window_seconds=0)
    with pytest.raises(ValueError, match="min_score deve estar entre"):
        GroupingConfig(min_score=150)


def test_grouping_config_active() -> None:
    cfg = GroupingConfig()  # vazio = todos ativos
    assert cfg.active(GroupingCriterion.RULE)
    cfg2 = GroupingConfig(enabled_criteria=frozenset({GroupingCriterion.RULE}))
    assert cfg2.active(GroupingCriterion.RULE)
    assert not cfg2.active(GroupingCriterion.USER)


# --- GroupingEngine -------------------------------------------------------


def test_grouping_requires_two_alerts() -> None:
    engine = GroupingEngine()
    group = engine.group([_alert("a1")])
    assert group is None


def test_grouping_same_rule_groups() -> None:
    engine = GroupingEngine()
    alerts = [_alert("a1", rule_id="brute-force"), _alert("a2", rule_id="brute-force")]
    group = engine.group(alerts)
    assert group is not None
    assert group.score >= 40
    assert GroupingCriterion.RULE in group.matched_criteria
    assert group.fingerprint.hash


def test_grouping_different_rules_no_group() -> None:
    engine = GroupingEngine()
    alerts = [
        _alert("a1", rule_id="brute-force"),
        _alert("a2", rule_id="malware"),
    ]
    group = engine.group(alerts)
    # apenas TIME_WINDOW coincide (10/140) -> score < 50
    assert group is None


def test_grouping_config_disables_criteria() -> None:
    cfg = GroupingConfig(
        enabled_criteria=frozenset({GroupingCriterion.USER}),
        min_score=10,
    )
    engine = GroupingEngine(cfg)
    alerts = [_alert("a1", user="admin"), _alert("a2", user="admin")]
    group = engine.group(alerts)
    assert group is not None
    assert GroupingCriterion.USER in group.matched_criteria
    assert GroupingCriterion.RULE not in group.matched_criteria


def test_grouping_fingerprint_deterministic() -> None:
    engine = GroupingEngine()
    g1 = engine.group([_alert("a1"), _alert("a2")])
    g2 = engine.group([_alert("a1"), _alert("a2")])
    assert g1 is not None
    assert g2 is not None
    assert g1.fingerprint.hash == g2.fingerprint.hash


def test_grouping_time_window() -> None:
    engine = GroupingEngine(GroupingConfig(time_window_seconds=60, min_score=10))
    t0 = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    alerts = [
        _alert("a1", seen=t0),
        _alert("a2", seen=t0 + timedelta(seconds=120)),  # fora da janela
    ]
    group = engine.group(alerts)
    assert group is not None
    assert GroupingCriterion.TIME_WINDOW not in group.matched_criteria


# --- IncidentCorrelator ---------------------------------------------------


def test_correlator_new() -> None:
    context = IncidentContext()
    correlator = IncidentCorrelator(GroupingEngine(), context)
    outcome = correlator.correlate([_alert("a1"), _alert("a2")])
    assert outcome.decision is CorrelationDecision.NEW
    assert outcome.group is not None


def test_correlator_no_group() -> None:
    context = IncidentContext()
    correlator = IncidentCorrelator(GroupingEngine(), context)
    outcome = correlator.correlate([_alert("a1")])
    assert outcome.decision is CorrelationDecision.NO_GROUP


# --- IncidentBuilder ------------------------------------------------------


def test_builder_creates_incident() -> None:
    engine = GroupingEngine()
    group = engine.group([_alert("a1"), _alert("a2")])
    assert group is not None

    builder = IncidentBuilder()
    incident = builder.build(group)

    assert incident.alerts == ("a1", "a2")
    assert incident.severity == IncidentSeverity.HIGH
    assert incident.assets == frozenset({"asset-1"})
    assert incident.users == frozenset({"admin"})
    assert incident.evidence
    assert incident.timeline
    assert incident.fingerprint is not None
    assert incident.reason is not None
    assert incident.reason.alerts_count == 2


def test_builder_priority_from_risk() -> None:
    engine = GroupingEngine()
    group = engine.group([_alert("a1", risk=90), _alert("a2", risk=90)])
    assert group is not None

    builder = IncidentBuilder()
    incident = builder.build(group)
    assert incident.priority == IncidentPriority.P1


def test_builder_max_severity() -> None:
    engine = GroupingEngine()
    group = engine.group(
        [
            _alert("a1", severity=AlertSeverity.LOW),
            _alert("a2", severity=AlertSeverity.CRITICAL),
        ]
    )
    assert group is not None
    incident = IncidentBuilder().build(group)
    assert incident.severity == IncidentSeverity.CRITICAL


def test_builder_requires_group() -> None:
    builder = IncidentBuilder()
    from edysiem.incidents.exceptions import IncidentBuilderError

    class EmptyGroup:
        alerts = ()

    with pytest.raises(IncidentBuilderError, match="vazio"):
        builder.build(EmptyGroup())  # type: ignore[arg-type]


def min_score_placeholder():  # pragma: no cover
    return None
