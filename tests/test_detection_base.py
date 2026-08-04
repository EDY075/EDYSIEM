"""Testes dos modelos base do Detection Framework."""

from __future__ import annotations

import pytest

from edysiem.detection import (
    DetectionDecision,
    DetectionFinding,
    DetectionPriority,
    DetectionReason,
    RuleMetadata,
)
from edysiem.domain import RiskScore, Severity


def test_rule_metadata_creation() -> None:
    metadata = RuleMetadata(
        id="brute-force",
        name="Brute Force",
        version="1.0.0",
        description="Detecta brute force",
        priority=DetectionPriority.HIGH,
        severity=Severity.HIGH,
        confidence=0.9,
        risk_score=RiskScore(80),
        required_fields=frozenset({"ip_src"}),
        tags=frozenset({"auth"}),
    )
    assert metadata.id == "brute-force"
    assert metadata.priority == DetectionPriority.HIGH
    assert metadata.severity == Severity.HIGH
    assert metadata.confidence == 0.9
    assert metadata.risk_score == RiskScore(80)
    assert "ip_src" in metadata.required_fields
    assert metadata.enabled is True
    assert metadata.author == "edysiem"


def test_rule_metadata_defaults() -> None:
    metadata = RuleMetadata(id="r", name="R", version="1.0.0")
    assert metadata.priority == DetectionPriority.NORMAL
    assert metadata.severity == Severity.MEDIUM
    assert metadata.confidence == 1.0
    assert metadata.risk_score == RiskScore(50)
    assert metadata.dependencies == frozenset()
    assert metadata.enabled is True
    assert metadata.tags == frozenset()
    assert metadata.timeout_seconds == 0.0


def test_rule_metadata_requires_id() -> None:
    with pytest.raises(ValueError, match="id nao pode ser vazio"):
        RuleMetadata(id="", name="R", version="1.0.0")


def test_rule_metadata_requires_name() -> None:
    with pytest.raises(ValueError, match="name nao pode ser vazio"):
        RuleMetadata(id="r", name="", version="1.0.0")


def test_rule_metadata_requires_version() -> None:
    with pytest.raises(ValueError, match="version nao pode ser vazio"):
        RuleMetadata(id="r", name="R", version="")


def test_rule_metadata_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence deve estar entre"):
        RuleMetadata(id="r", name="R", version="1.0.0", confidence=1.5)


def test_detection_priority_values() -> None:
    assert DetectionPriority.CRITICAL.value == 0
    assert DetectionPriority.HIGH.value == 10
    assert DetectionPriority.NORMAL.value == 50
    assert DetectionPriority.LOW.value == 100
    assert DetectionPriority.BACKGROUND.value == 200


def test_detection_decision_values() -> None:
    assert DetectionDecision.DETECTED.value == "detected"
    assert DetectionDecision.NO_DETECTION.value == "no_detection"
    assert DetectionDecision.DEFERRED.value == "deferred"


def test_detection_reason_creation() -> None:
    reason = DetectionReason(
        rule_id="brute-force",
        condition="5 falhas em 60s",
        values={"count": 5},
    )
    assert reason.rule_id == "brute-force"
    assert reason.values["count"] == 5


def test_detection_reason_requires_rule_id() -> None:
    with pytest.raises(ValueError, match="rule_id nao pode ser vazio"):
        DetectionReason(rule_id="", condition="x")


def test_detection_finding_creation() -> None:
    reason = DetectionReason(rule_id="r", condition="x")
    finding = DetectionFinding(
        rule_id="r",
        event_ids=("evt-1",),
        reason=reason,
        severity=Severity.HIGH,
        confidence=0.8,
        risk_score=RiskScore(75),
    )
    assert finding.rule_id == "r"
    assert finding.event_ids == ("evt-1",)
    assert finding.severity == Severity.HIGH
    assert finding.confidence == 0.8
    assert finding.created_at is not None


def test_detection_finding_requires_rule_id() -> None:
    with pytest.raises(ValueError, match="rule_id nao pode ser vazio"):
        DetectionFinding(rule_id="", event_ids=(), reason=None)  # type: ignore[arg-type]


def test_detection_finding_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence deve estar entre"):
        DetectionFinding(
            rule_id="r",
            event_ids=(),
            reason=DetectionReason(rule_id="r", condition="x"),
            confidence=2.0,
        )
