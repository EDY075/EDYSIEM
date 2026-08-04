"""Testes dos modelos base do Correlation Engine."""

from __future__ import annotations

import pytest

from edysiem.correlation import (
    CorrelationDecision,
    CorrelationMatch,
    CorrelationMetadata,
    CorrelationPriority,
    CorrelationReason,
)


def test_correlation_metadata_creation() -> None:
    metadata = CorrelationMetadata(
        id="brute-force",
        name="Brute Force",
        version="1.0.0",
        description="Detecta brute force",
        priority=CorrelationPriority.HIGH,
        required_fields=frozenset({"ip_src", "user"}),
        window_seconds=300.0,
    )
    assert metadata.id == "brute-force"
    assert metadata.priority == CorrelationPriority.HIGH
    assert "ip_src" in metadata.required_fields
    assert metadata.window_seconds == 300.0
    assert metadata.enabled_by_default is True
    assert metadata.author == "edysiem"


def test_correlation_metadata_defaults() -> None:
    metadata = CorrelationMetadata(id="rule-1", name="Rule 1", version="1.0.0")
    assert metadata.priority == CorrelationPriority.NORMAL
    assert metadata.required_fields == frozenset()
    assert metadata.required_event_types == frozenset()
    assert metadata.window_seconds is None
    assert metadata.dependencies == frozenset()
    assert metadata.enabled_by_default is True
    assert metadata.timeout_seconds == 0.0
    assert metadata.tags == frozenset()


def test_correlation_metadata_requires_id() -> None:
    with pytest.raises(ValueError, match="id nao pode ser vazio"):
        CorrelationMetadata(id="", name="Rule", version="1.0.0")


def test_correlation_metadata_requires_name() -> None:
    with pytest.raises(ValueError, match="name nao pode ser vazio"):
        CorrelationMetadata(id="rule", name="", version="1.0.0")


def test_correlation_metadata_requires_version() -> None:
    with pytest.raises(ValueError, match="version nao pode ser vazio"):
        CorrelationMetadata(id="rule", name="Rule", version="")


def test_correlation_metadata_invalid_window() -> None:
    with pytest.raises(ValueError, match="window_seconds deve ser > 0"):
        CorrelationMetadata(id="rule", name="Rule", version="1.0.0", window_seconds=0)


def test_correlation_priority_values() -> None:
    assert CorrelationPriority.CRITICAL.value == 0
    assert CorrelationPriority.HIGH.value == 10
    assert CorrelationPriority.NORMAL.value == 50
    assert CorrelationPriority.LOW.value == 100
    assert CorrelationPriority.BACKGROUND.value == 200


def test_correlation_decision_values() -> None:
    assert CorrelationDecision.MATCH.value == "match"
    assert CorrelationDecision.NO_MATCH.value == "no_match"
    assert CorrelationDecision.DEFERRED.value == "deferred"


def test_correlation_reason_creation() -> None:
    reason = CorrelationReason(
        rule_id="brute-force",
        condition="5 falhas em 60s",
        values={"ip_src": "10.0.0.1", "count": 5},
    )
    assert reason.rule_id == "brute-force"
    assert reason.values["count"] == 5


def test_correlation_reason_requires_rule_id() -> None:
    with pytest.raises(ValueError, match="rule_id nao pode ser vazio"):
        CorrelationReason(rule_id="", condition="x")


def test_correlation_reason_requires_condition() -> None:
    with pytest.raises(ValueError, match="condition nao pode ser vazio"):
        CorrelationReason(rule_id="rule", condition="")


def test_correlation_match_creation() -> None:
    reason = CorrelationReason(rule_id="brute-force", condition="5 falhas em 60s")
    match = CorrelationMatch(
        rule_id="brute-force",
        matched_event_ids=("evt-1", "evt-2"),
        reason=reason,
        severity="high",
    )
    assert match.rule_id == "brute-force"
    assert match.matched_event_ids == ("evt-1", "evt-2")
    assert match.severity == "high"
    assert match.created_at is not None


def test_correlation_match_requires_rule_id() -> None:
    with pytest.raises(ValueError, match="rule_id nao pode ser vazio"):
        CorrelationMatch(rule_id="", matched_event_ids=(), reason=None)  # type: ignore[arg-type]
