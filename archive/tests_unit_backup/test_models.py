"""Testes das entidades de domínio."""

import pytest
from datetime import datetime, timezone

from app.core.models import (
    Alert,
    AlertStatus,
    Asset,
    CanonicalEvent,
    Case,
    CaseStatus,
    Health,
    HealthStatus,
    Ioc,
    IocType,
    MitreRef,
    Role,
    Severity,
    User,
)

TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_event_immutable() -> None:
    e = CanonicalEvent(event_id="evt_1", timestamp=TS, source_type="syslog", source_host="h")
    assert e.event_id == "evt_1"
    with pytest.raises(Exception):
        e.event_id = "outra"  # type: ignore[misc]


def test_event_defaults() -> None:
    e = CanonicalEvent(event_id="e", timestamp=TS, source_type="s", source_host="h")
    assert e.severity == Severity.INFO
    assert e.trace_id == ""


def test_alert_defaults() -> None:
    a = Alert(alert_id="alt_1", rule_id="r1", severity=Severity.HIGH)
    assert a.status == AlertStatus.OPEN
    assert a.mitre is None
    assert a.evidence_ids == []


def test_alert_with_mitre() -> None:
    a = Alert(alert_id="a", rule_id="r", severity=Severity.CRITICAL, mitre=MitreRef("cred", "T1110"))
    assert a.mitre.technique == "T1110"


def test_asset() -> None:
    a = Asset(asset_id="ast_1", hostname="web-01", ip="10.0.0.5", criticality=Severity.HIGH)
    assert a.ip == "10.0.0.5"
    assert a.tags == []


def test_case_defaults() -> None:
    c = Case(case_id="inc_1", title="Incidente")
    assert c.status == CaseStatus.OPEN
    assert c.alert_ids == []


def test_ioc() -> None:
    i = Ioc(ioc_id="ioc_1", type=IocType.IP, value="10.0.0.5")
    assert i.type == IocType.IP


def test_health() -> None:
    h = Health(component="persistence")
    assert h.status == HealthStatus.ONLINE


def test_user_role() -> None:
    u = User(user_id="u1", username="ana", role=Role.ANALYST)
    assert u.role == Role.ANALYST


def test_severity_values() -> None:
    assert Severity.CRITICAL.value == "critical"
    assert Severity.HIGH.value == "high"
