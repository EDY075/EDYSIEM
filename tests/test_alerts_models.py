"""Testes dos modelos do Alert Framework."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.alerts import (
    Alert,
    AlertFingerprint,
    AlertLifecycle,
    AlertPriority,
    AlertReason,
    AlertSeverity,
)
from edysiem.domain import RiskScore


def test_alert_severity_rank() -> None:
    assert AlertSeverity.INFO.rank == 0
    assert AlertSeverity.LOW.rank == 1
    assert AlertSeverity.MEDIUM.rank == 2
    assert AlertSeverity.HIGH.rank == 3
    assert AlertSeverity.CRITICAL.rank == 4


def test_alert_priority_rank() -> None:
    assert AlertPriority.P1.rank == 0
    assert AlertPriority.P5.rank == 4


def test_alert_lifecycle_transitions() -> None:
    assert AlertLifecycle.OPEN.can_transition_to(AlertLifecycle.TRIAGE)
    assert AlertLifecycle.OPEN.can_transition_to(AlertLifecycle.FALSE_POSITIVE)
    assert not AlertLifecycle.OPEN.can_transition_to(AlertLifecycle.RESOLVED)

    assert AlertLifecycle.TRIAGE.can_transition_to(AlertLifecycle.INVESTIGATING)
    assert AlertLifecycle.TRIAGE.can_transition_to(AlertLifecycle.RESOLVED)
    assert not AlertLifecycle.TRIAGE.can_transition_to(AlertLifecycle.OPEN)

    assert AlertLifecycle.RESOLVED.can_transition_to(AlertLifecycle.OPEN)
    assert not AlertLifecycle.RESOLVED.can_transition_to(AlertLifecycle.TRIAGE)


def test_alert_lifecycle_next_states() -> None:
    nexts = AlertLifecycle.OPEN.next_states()
    assert AlertLifecycle.TRIAGE in nexts
    assert AlertLifecycle.FALSE_POSITIVE in nexts


def test_alert_fingerprint_requires_hash() -> None:
    with pytest.raises(ValueError, match="hash nao pode ser vazio"):
        AlertFingerprint(hash="", rule_id="r")


def test_alert_reason_requires_rule_id() -> None:
    with pytest.raises(ValueError, match="rule_id nao pode ser vazio"):
        AlertReason(rule_id="", condition="x")


def test_alert_creation() -> None:
    alert = Alert(
        title="Brute force detectado",
        severity=AlertSeverity.HIGH,
        priority=AlertPriority.P2,
        risk_score=RiskScore(70),
        rule_id="brute-force",
    )
    assert alert.title == "Brute force detectado"
    assert alert.severity == AlertSeverity.HIGH
    assert alert.priority == AlertPriority.P2
    assert alert.risk_score == RiskScore(70)
    assert alert.status == AlertLifecycle.OPEN
    assert alert.occurrences == 1
    assert alert.id  # auto-gerado
    assert alert.created_at is not None


def test_alert_requires_title() -> None:
    with pytest.raises(ValueError, match="title nao pode ser vazio"):
        Alert(title="")


def test_alert_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence deve estar entre"):
        Alert(title="x", confidence=1.5)


def test_alert_invalid_occurrences() -> None:
    with pytest.raises(ValueError, match="occurrences deve ser >= 1"):
        Alert(title="x", occurrences=0)


def test_alert_bump() -> None:
    alert = Alert(title="x", rule_id="r")
    bumped = alert.bump()
    assert bumped.occurrences == 2
    assert bumped.id == alert.id
    assert bumped.first_seen == alert.first_seen
    assert bumped.last_seen >= alert.last_seen


def test_alert_bump_with_timestamp() -> None:
    now = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    alert = Alert(title="x", first_seen=now, last_seen=now)
    bumped = alert.bump(at=datetime(2026, 8, 3, 12, 5, 0, tzinfo=UTC))
    assert bumped.occurrences == 2
    assert bumped.last_seen.hour == 12
    assert bumped.last_seen.minute == 5
