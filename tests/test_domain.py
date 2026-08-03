"""Testes das entidades de domínio."""

from __future__ import annotations

import pytest

from edysiem.domain import (
    IOC,
    Alert,
    AlertStatus,
    Asset,
    AssetGroup,
    Case,
    CaseStatus,
    EventType,
    Investigation,
    InvestigationStatus,
    InvestigationStep,
    IOCKind,
    LifecycleStatus,
    Notification,
    NotificationStatus,
    RawEvent,
    RiskScore,
    Rule,
    RuleState,
    Severity,
    StepStatus,
    Team,
    TimelineEntry,
    User,
    UserRole,
)


def test_risk_score_valid_and_invalid() -> None:
    assert RiskScore(0).value == 0
    assert RiskScore(100).value == 100
    with pytest.raises(ValueError, match="entre 0 e 100"):
        RiskScore(-1)
    with pytest.raises(ValueError, match="entre 0 e 100"):
        RiskScore(101)


def test_asset_defaults() -> None:
    asset = Asset(label="firewall-01")
    assert asset.id
    assert asset.lifecycle is LifecycleStatus.ACTIVE
    assert asset.tags == frozenset()
    assert asset.risk_score == RiskScore(0)


def test_asset_group() -> None:
    group = AssetGroup(name="DMZ", asset_ids=("a1", "a2"))
    assert group.name == "DMZ"
    assert group.asset_ids == ("a1", "a2")


def test_ioc() -> None:
    ioc = IOC(kind=IOCKind.IP, value="10.0.0.1", source="threat-intel")
    assert ioc.kind is IOCKind.IP
    assert ioc.confidence.name == "LOW"


def test_alert() -> None:
    alert = Alert(
        title="Possível scan",
        severity=Severity.HIGH,
        status=AlertStatus.OPEN,
        source_type=EventType.NETWORK,
        risk_score=RiskScore(80),
    )
    assert alert.title == "Possível scan"
    assert alert.severity is Severity.HIGH
    assert alert.risk_score.value == 80
    assert alert.body == {}


def test_case() -> None:
    case = Case(title="Incidente 1", status=CaseStatus.IN_PROGRESS)
    assert case.status is CaseStatus.IN_PROGRESS
    assert case.alert_ids == ()


def test_timeline_entry() -> None:
    entry = TimelineEntry(title="Início")
    assert entry.entry_type == "note"
    assert entry.body is None


def test_investigation_steps_and_timeline() -> None:
    inv = Investigation(title="Investigação A", status=InvestigationStatus.IN_PROGRESS)
    step = InvestigationStep(order=1, kind="collect", title="Coletar evidência")
    inv.add_step(step)
    entry = TimelineEntry(title="Abertura")
    inv.add_timeline_entry(entry)
    assert len(inv.steps) == 1
    assert inv.steps[0].status is StepStatus.PENDING
    assert len(inv.timeline) == 1


def test_rule() -> None:
    rule = Rule(name="Regra de brute force", state=RuleState.ENABLED)
    assert rule.state is RuleState.ENABLED
    assert rule.expression == {}


def test_team_and_user() -> None:
    team = Team(name="SOC N1", member_ids=("u1",))
    assert team.member_ids == ("u1",)
    user = User(
        username="analista",
        email="analista@edysiem.dev",
        roles=frozenset({UserRole.ANALYST}),
        teams=frozenset({team.id}),
    )
    assert user.roles == frozenset({UserRole.ANALYST})
    assert user.active is True
    assert user.password_hash is None
    assert user.is_superuser is False


def test_notification() -> None:
    note = Notification(alert_id="alert-1", channel="email")
    assert note.status is NotificationStatus.PENDING
    assert note.sent_at is None


def test_raw_event() -> None:
    event = RawEvent(source_type="windows", source_host="wks-01", raw_payload=b"4624")
    assert event.event_id
    assert event.received_at is not None
    assert event.tags == frozenset()
    assert event.risk_score == RiskScore(0)


def test_enum_values() -> None:
    assert Severity.CRITICAL.value == "critical"
    assert AlertStatus.ACK.value == "acknowledged"
    assert UserRole.ADMIN.value == "admin"
    assert EventType.THREAT.value == "threat"
