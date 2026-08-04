"""Testes do Risk, Fingerprint e Dedup Engines."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.alerts import (
    AlertContext,
    AlertSeverity,
    DedupDecision,
    DedupEngine,
    FingerprintEngine,
    RiskEngine,
    RiskFactor,
)
from edysiem.alerts.models import Alert
from edysiem.domain import EnrichedEvent, Severity

# --- RiskEngine -----------------------------------------------------------


def test_risk_engine_basic() -> None:
    engine = RiskEngine()
    score = engine.evaluate(severity=AlertSeverity.CRITICAL, confidence=1.0)
    assert 0 <= score.value <= 100
    assert score.value > 50  # critical + full confidence -> alto


def test_risk_engine_low() -> None:
    engine = RiskEngine()
    score = engine.evaluate(severity=AlertSeverity.INFO, confidence=0.2)
    assert score.value < 30


def test_risk_engine_with_factors() -> None:
    engine = RiskEngine()
    asset_factor = engine.factor_from_asset_criticality(100)
    score = engine.evaluate(
        severity=AlertSeverity.HIGH,
        confidence=0.9,
        additional_factors=(asset_factor,),
    )
    assert 0 <= score.value <= 100
    assert score.value > 50


def test_risk_engine_factor_validation() -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="criticality deve estar entre"):
        engine.factor_from_asset_criticality(150)
    with pytest.raises(ValueError, match="intel_score deve estar entre"):
        engine.factor_from_intel(1.5)


def test_risk_factor_validation() -> None:
    with pytest.raises(ValueError, match="score deve estar entre"):
        RiskFactor(name="x", score=1.5)
    with pytest.raises(ValueError, match="weight nao pode ser negativo"):
        RiskFactor(name="x", score=0.5, weight=-1)
    with pytest.raises(ValueError, match="name nao pode ser vazio"):
        RiskFactor(name="", score=0.5)


def test_risk_engine_base_score() -> None:
    engine = RiskEngine(base_score=0)
    score = engine.evaluate(severity=AlertSeverity.INFO, confidence=0.0)
    assert score.value >= 0


# --- FingerprintEngine ----------------------------------------------------


def _event(**kwargs) -> EnrichedEvent:
    defaults = {
        "event_id": "evt-1",
        "trace_id": "t",
        "timestamp": datetime.now(UTC),
        "received_at": datetime.now(UTC),
        "source_type": "syslog",
        "source_host": "host-1",
        "event_category": "auth",
        "event_action": "reject",
        "severity": Severity.LOW,
        "ip_src": "10.0.0.1",
        "user": "admin",
    }
    defaults.update(kwargs)
    return EnrichedEvent(**defaults)


def test_fingerprint_deterministic() -> None:
    engine = FingerprintEngine()
    fp1 = engine.compute("brute-force", _event())
    fp2 = engine.compute("brute-force", _event())
    assert fp1.hash == fp2.hash


def test_fingerprint_differs_on_rule() -> None:
    engine = FingerprintEngine()
    fp1 = engine.compute("brute-force", _event())
    fp2 = engine.compute("other-rule", _event())
    assert fp1.hash != fp2.hash


def test_fingerprint_differs_on_identity() -> None:
    engine = FingerprintEngine()
    fp1 = engine.compute("r", _event(ip_src="10.0.0.1"))
    fp2 = engine.compute("r", _event(ip_src="10.0.0.2"))
    assert fp1.hash != fp2.hash


def test_fingerprint_without_event() -> None:
    engine = FingerprintEngine()
    fp = engine.compute("brute-force", None)
    assert fp.hash
    assert fp.rule_id == "brute-force"


def test_fingerprint_with_identity_override() -> None:
    engine = FingerprintEngine()
    fp1 = engine.compute("r", None, identity={"user": "admin"})
    fp2 = engine.compute("r", None, identity={"user": "root"})
    assert fp1.hash != fp2.hash


# --- DedupEngine ----------------------------------------------------------


def test_dedup_new() -> None:
    context = AlertContext()
    engine = DedupEngine(context)
    fp = FingerprintEngine().compute("r", _event())

    outcome = engine.check(fp)
    assert outcome.decision is DedupDecision.NEW


def test_dedup_after_save() -> None:
    context = AlertContext()
    engine = DedupEngine(context)
    fp = FingerprintEngine().compute("brute-force", _event())

    alert = Alert(title="x", rule_id="brute-force", fingerprint=fp)
    context.save(alert)

    outcome = engine.check(fp)
    assert outcome.decision is DedupDecision.DEDUP
    assert outcome.existing is not None
    assert outcome.existing.id == alert.id


def test_alert_context_ops() -> None:
    context = AlertContext()
    fp = FingerprintEngine().compute("r", _event())
    alert = Alert(title="x", rule_id="r", fingerprint=fp)

    context.save(alert)
    assert context.get(alert.id) == alert
    assert context.has_fingerprint(fp)
    assert len(context) == 1
    assert context.snapshot()["alerts"] == 1

    context.clear()
    assert len(context) == 0
