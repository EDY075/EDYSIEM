"""Testes do normalizador de eventos."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from edysiem.domain import CanonicalEvent, ParsedEvent, Severity
from edysiem.normalization import Registry, StrategyNormalizer, register_default_normalizers


def _now() -> datetime:
    return datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)


def _parsed(**overrides: object) -> ParsedEvent:
    values: dict[str, object] = {
        "event_id": "evt-1",
        "trace_id": "trace-1",
        "timestamp": _now(),
        "source_type": "syslog",
        "source_host": "wks-01",
        "event_category": "auth",
        "event_action": "logon",
        "fields": {"user": "admin"},
        "raw": "payload original",
        "confidence": 1.0,
    }
    values.update(overrides)
    return ParsedEvent(**values)  # type: ignore[arg-type]


def test_normalizer_success() -> None:
    from edysiem.normalization import Registry

    registry = Registry()
    register_default_normalizers(registry)
    normalizer = StrategyNormalizer()
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed())
    assert result.is_ok()
    canonical = result.unwrap()
    assert isinstance(canonical, CanonicalEvent)
    assert canonical.event_id == "evt-1"
    assert canonical.source_type == "syslog"
    assert canonical.source_host == "wks-01"
    assert canonical.event_category == "auth"
    assert canonical.event_action == "logon"
    assert canonical.severity == Severity.INFO
    assert canonical.user == "admin"
    assert canonical.event_original == "payload original"
    assert canonical.normalized_fields == frozenset({"user"})
    assert canonical.confidence == 1.0
    assert canonical.schema_version == "1.0.0"


def test_normalizer_reject_severity() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed(event_category="auth", event_action="reject"))
    assert result.is_ok()
    assert result.unwrap().severity == Severity.HIGH


def test_normalizer_critical_severity() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed(event_category="threat", event_action="info"))
    assert result.is_ok()
    assert result.unwrap().severity == Severity.CRITICAL


def test_normalizer_low_confidence() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed(confidence=0.3))
    assert result.is_ok()
    assert result.unwrap().severity == Severity.LOW


def test_normalizer_missing_fields() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(
        _parsed(
            event_category="system",
            event_action="info",
            fields={},
        )
    )
    assert result.is_ok()
    canonical = result.unwrap()
    assert canonical.user is None
    assert canonical.process is None
    assert canonical.ip_src is None


def test_normalizer_custom_strategy() -> None:
    from edysiem.result import ok

    def custom_strategy(parsed: ParsedEvent):
        from edysiem.domain import CanonicalEvent, Severity

        canonical = CanonicalEvent(
            event_id=parsed.event_id,
            trace_id=parsed.trace_id,
            timestamp=parsed.timestamp,
            received_at=parsed.timestamp,
            source_type=parsed.source_type,
            source_host=parsed.source_host,
            event_category=parsed.event_category,
            event_action=parsed.event_action,
            severity=Severity.CRITICAL,
            user=parsed.fields.get("user"),
            event_original=str(parsed.raw),
            normalized_fields=frozenset(parsed.fields.keys()),
            confidence=parsed.confidence,
            metadata=parsed.fields,
        )
        return ok(canonical)

    normalizer = StrategyNormalizer()
    normalizer.register("custom", custom_strategy)
    result = normalizer.normalize(_parsed(source_type="custom"))
    assert result.is_ok()
    assert result.unwrap().severity == Severity.CRITICAL


def test_normalizer_unknown_source_type() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed(source_type="unknown"))
    assert result.is_ok()
    assert result.unwrap().source_type == "unknown"


def test_normalizer_immutable_result() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed())
    assert result.is_ok()
    canonical = result.unwrap()
    with pytest.raises(FrozenInstanceError):
        canonical.severity = Severity.HIGH  # type: ignore[misc]


def test_normalizer_event_category_auth() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed(event_category="auth", event_action="logon"))
    assert result.is_ok()
    canonical = result.unwrap()
    assert canonical.event_category == "auth"
    assert canonical.event_action == "logon"


def test_normalizer_event_category_network() -> None:
    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)
    result = normalizer.normalize(_parsed(event_category="network", event_action="connect"))
    assert result.is_ok()
    canonical = result.unwrap()
    assert canonical.event_category == "network"
