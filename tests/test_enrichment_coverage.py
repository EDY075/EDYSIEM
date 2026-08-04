"""Testes adicionais de normalizacao e parsers para cobertura."""

from __future__ import annotations

from datetime import UTC, datetime

from edysiem.domain import ParsedEvent
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
        "raw": "payload",
        "confidence": 1.0,
    }
    values.update(overrides)
    return ParsedEvent(**values)  # type: ignore[arg-type]


def test_normalizer_vendor_product_fields() -> None:
    from edysiem.normalization import Registry

    normalizer = StrategyNormalizer()
    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)

    result = normalizer.normalize(
        _parsed(vendor="cisco", product="ios", fields={"src_ip": "10.0.0.1"})
    )
    assert result.is_ok()
    canonical = result.unwrap()
    assert canonical.vendor == "cisco"
    assert canonical.product == "ios"
    assert canonical.ip_src == "10.0.0.1"


def test_normalizer_command_line_field() -> None:
    normalizer = StrategyNormalizer()
    from edysiem.normalization import Registry

    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)

    result = normalizer.normalize(_parsed(fields={"command_line": "powershell.exe -enc abc"}))
    assert result.is_ok()
    assert result.unwrap().command_line == "powershell.exe -enc abc"


def test_normalizer_windows_strategy() -> None:
    normalizer = StrategyNormalizer()
    from edysiem.normalization import Registry

    registry = Registry()
    register_default_normalizers(registry)
    for source_type, strategy in registry.strategies().items():
        normalizer.register(source_type, strategy)

    result = normalizer.normalize(
        _parsed(
            source_type="windows",
            fields={
                "user": "admin",
                "process_name": "lsass.exe",
                "source_ip": "10.0.0.5",
            },
        )
    )
    assert result.is_ok()
    canonical = result.unwrap()
    assert canonical.process == "lsass.exe"
    assert canonical.ip_src == "10.0.0.5"


def test_registry_unregister() -> None:
    registry = Registry()

    def strategy(p: ParsedEvent):
        from edysiem.result import ok

        return ok(None)

    registry.register("test", strategy)
    assert "test" in registry.source_types()

    registry.unregister("test")
    assert "test" not in registry.source_types()


def test_registry_get_none() -> None:
    registry = Registry()
    assert registry.get("missing") is None


def test_registry_source_types_empty() -> None:
    registry = Registry()
    assert registry.source_types() == frozenset()


def test_registry_strategies_dict() -> None:
    registry = Registry()

    def strategy(p: ParsedEvent):
        from edysiem.result import ok

        return ok(None)

    registry.register("a", strategy)
    strategies = registry.strategies()
    assert "a" in strategies


def test_normalizer_classify_severity() -> None:
    from edysiem.domain import Severity
    from edysiem.normalization.normalizer import _classify_severity

    assert _classify_severity("auth", "reject", 1.0) == Severity.HIGH
    assert _classify_severity("auth", "accept", 1.0) == Severity.LOW
    assert _classify_severity("network", "reject", 1.0) == Severity.HIGH
    assert _classify_severity("threat", "info", 1.0) == Severity.CRITICAL
    assert _classify_severity("system", "info", 0.3) == Severity.LOW
    assert _classify_severity("system", "info", 1.0) == Severity.INFO
