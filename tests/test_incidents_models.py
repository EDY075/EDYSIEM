"""Testes dos modelos do Incident Framework."""

from __future__ import annotations

import pytest

from edysiem.domain import RiskScore
from edysiem.incidents import (
    Incident,
    IncidentEvidence,
    IncidentFingerprint,
    IncidentPriority,
    IncidentReason,
    IncidentSeverity,
    IncidentStatus,
)


def test_incident_severity_rank() -> None:
    assert IncidentSeverity.INFO.rank == 0
    assert IncidentSeverity.CRITICAL.rank == 4


def test_incident_priority_rank() -> None:
    assert IncidentPriority.P1.rank == 0
    assert IncidentPriority.P5.rank == 4


def test_incident_status_transitions() -> None:
    assert IncidentStatus.OPEN.can_transition_to(IncidentStatus.TRIAGE)
    assert IncidentStatus.TRIAGE.can_transition_to(IncidentStatus.INVESTIGATING)
    assert IncidentStatus.INVESTIGATING.can_transition_to(IncidentStatus.CONTAINED)
    assert IncidentStatus.CONTAINED.can_transition_to(IncidentStatus.RESOLVED)
    assert IncidentStatus.RESOLVED.can_transition_to(IncidentStatus.CLOSED)
    assert IncidentStatus.CLOSED.can_transition_to(IncidentStatus.REOPENED)
    assert IncidentStatus.REOPENED.can_transition_to(IncidentStatus.INVESTIGATING)

    assert not IncidentStatus.OPEN.can_transition_to(IncidentStatus.CLOSED)
    assert not IncidentStatus.CONTAINED.can_transition_to(IncidentStatus.OPEN)


def test_incident_status_next_states() -> None:
    nexts = IncidentStatus.OPEN.next_states()
    assert IncidentStatus.TRIAGE in nexts


def test_incident_fingerprint_requires_hash() -> None:
    with pytest.raises(ValueError, match="hash nao pode ser vazio"):
        IncidentFingerprint(hash="", key="rule")


def test_incident_fingerprint_requires_key() -> None:
    with pytest.raises(ValueError, match="key nao pode ser vazio"):
        IncidentFingerprint(hash="abc", key="")


def test_incident_reason_validation() -> None:
    with pytest.raises(ValueError, match="alerts_count nao pode ser negativo"):
        IncidentReason(alerts_count=-1)


def test_incident_creation() -> None:
    incident = Incident(
        title="Brute force em massa",
        severity=IncidentSeverity.HIGH,
        priority=IncidentPriority.P2,
        risk_score=RiskScore(75),
        alerts=("alert-1", "alert-2"),
    )
    assert incident.title == "Brute force em massa"
    assert incident.severity == IncidentSeverity.HIGH
    assert incident.status == IncidentStatus.OPEN
    assert incident.occurrences == 1
    assert incident.alerts == ("alert-1", "alert-2")
    assert incident.id  # auto-gerado


def test_incident_requires_title() -> None:
    with pytest.raises(ValueError, match="title nao pode ser vazio"):
        Incident(title="")


def test_incident_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence deve estar entre"):
        Incident(title="x", confidence=1.5)


def test_incident_invalid_occurrences() -> None:
    with pytest.raises(ValueError, match="occurrences deve ser >= 1"):
        Incident(title="x", occurrences=0)


def test_incident_bump() -> None:
    incident = Incident(title="x")
    bumped = incident.bump()
    assert bumped.occurrences == 2
    assert bumped.id == incident.id


def test_incident_evidence() -> None:
    evidence = IncidentEvidence(alert_id="alert-1", title="A", rule_id="r")
    assert evidence.alert_id == "alert-1"
    assert evidence.rule_id == "r"


def test_incident_timeline_entry() -> None:
    from edysiem.incidents import IncidentTimelineEntry

    entry = IncidentTimelineEntry(action="created", actor="analyst-01")
    assert entry.action == "created"
    assert entry.actor == "analyst-01"
