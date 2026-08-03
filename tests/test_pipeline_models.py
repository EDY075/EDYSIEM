"""Testes dos modelos da pipeline oficial (RawEvent → EnrichedEvent)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict
from datetime import UTC, datetime

import pytest

from edysiem.domain import (
    CanonicalEvent,
    EnrichedEvent,
    Enrichment,
    ParsedEvent,
    RawEvent,
    RiskScore,
    Severity,
)


def _now() -> datetime:
    return datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)


def _raw(**overrides: object) -> RawEvent:
    values: dict[str, object] = {
        "source_type": "windows",
        "source_host": "wks-01",
        "raw_payload": b"4624",
    }
    values.update(overrides)
    return RawEvent(**values)  # type: ignore[arg-type]


def _parsed(**overrides: object) -> ParsedEvent:
    values: dict[str, object] = {
        "event_id": "evt-1",
        "timestamp": _now(),
        "source_type": "windows",
        "source_host": "wks-01",
        "event_type": "logon",
        "fields": {"user": "admin"},
        "raw": "payload original",
        "trace_id": "trace-1",
    }
    values.update(overrides)
    return ParsedEvent(**values)  # type: ignore[arg-type]


def _canonical(**overrides: object) -> CanonicalEvent:
    values: dict[str, object] = {
        "event_id": "evt-1",
        "timestamp": _now(),
        "source_type": "windows",
        "source_host": "wks-01",
        "event_type": "logon",
        "severity": Severity.MEDIUM,
    }
    values.update(overrides)
    return CanonicalEvent(**values)  # type: ignore[arg-type]


def _enrichment(**overrides: object) -> Enrichment:
    values: dict[str, object] = {
        "kind": "asset",
        "provider": "asset-db",
        "data": {"owner": "sec"},
    }
    values.update(overrides)
    return Enrichment(**values)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# RawEvent
# ---------------------------------------------------------------------------


def test_raw_event_full_creation() -> None:
    event = RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload="<13>Aug  3 12:00:00 host sshd[1]: Accepted",
        event_id="raw-1",
        received_at=_now(),
        tags=frozenset({"network"}),
        risk_score=RiskScore(20),
    )
    assert event.source_type == "syslog"
    assert event.source_host == "fw-01"
    assert event.raw_payload == "<13>Aug  3 12:00:00 host sshd[1]: Accepted"
    assert event.event_id == "raw-1"
    assert event.received_at == _now()
    assert event.tags == frozenset({"network"})
    assert event.risk_score == RiskScore(20)


def test_raw_event_defaults() -> None:
    event = _raw()
    assert event.event_id
    assert event.received_at is not None
    assert event.received_at.tzinfo is UTC
    assert event.tags == frozenset()
    assert event.risk_score == RiskScore(0)


def test_raw_event_accepts_str_or_bytes_payload() -> None:
    assert _raw(raw_payload="texto").raw_payload == "texto"
    assert _raw(raw_payload=b"bytes").raw_payload == b"bytes"


def test_raw_event_immutable() -> None:
    event = _raw()
    with pytest.raises(FrozenInstanceError):
        event.source_host = "outro"  # type: ignore[misc]


def test_raw_event_requires_source_type() -> None:
    with pytest.raises(ValueError, match="source_type não pode ser vazio"):
        _raw(source_type="")
    with pytest.raises(ValueError, match="source_type não pode ser vazio"):
        _raw(source_type="   ")


def test_raw_event_requires_source_host() -> None:
    with pytest.raises(ValueError, match="source_host não pode ser vazio"):
        _raw(source_host="")
    with pytest.raises(ValueError, match="source_host não pode ser vazio"):
        _raw(source_host="  ")


def test_raw_event_accepts_trimmed_values() -> None:
    event = _raw(source_type=" windows ", source_host=" wks-01 ")
    assert event.source_type == " windows "
    assert event.source_host == " wks-01 "


# ---------------------------------------------------------------------------
# ParsedEvent
# ---------------------------------------------------------------------------


def test_parsed_event_full_creation() -> None:
    event = _parsed(
        fields={"user": "admin", "ip": "10.0.0.5"},
        raw=b"raw-bytes",
    )
    assert event.event_id == "evt-1"
    assert event.timestamp == _now()
    assert event.source_type == "windows"
    assert event.source_host == "wks-01"
    assert event.event_type == "logon"
    assert event.fields == {"user": "admin", "ip": "10.0.0.5"}
    assert event.raw == b"raw-bytes"
    assert event.trace_id == "trace-1"


def test_parsed_event_immutable() -> None:
    event = _parsed()
    with pytest.raises(FrozenInstanceError):
        event.event_type = "network"  # type: ignore[misc]


def test_parsed_event_requires_source_type() -> None:
    with pytest.raises(ValueError, match="source_type não pode ser vazio"):
        _parsed(source_type="")


def test_parsed_event_requires_event_type() -> None:
    with pytest.raises(ValueError, match="event_type não pode ser vazio"):
        _parsed(event_type="")
    with pytest.raises(ValueError, match="event_type não pode ser vazio"):
        _parsed(event_type="   ")


def test_parsed_event_requires_trace_id() -> None:
    with pytest.raises(ValueError, match="trace_id não pode ser vazio"):
        _parsed(trace_id="")


# ---------------------------------------------------------------------------
# CanonicalEvent
# ---------------------------------------------------------------------------


def test_canonical_event_full_creation() -> None:
    event = CanonicalEvent(
        event_id="evt-1",
        timestamp=_now(),
        source_type="windows",
        source_host="wks-01",
        event_type="logon",
        severity=Severity.HIGH,
        user="admin",
        process="lsass.exe",
        ip_src="10.0.0.5",
        ip_dst="10.0.0.1",
        hostname="wks-01.corp",
        payload={"src_port": 4624},
        raw="payload original",
        trace_id="trace-1",
        normalized_at=_now(),
    )
    assert event.user == "admin"
    assert event.process == "lsass.exe"
    assert event.ip_src == "10.0.0.5"
    assert event.ip_dst == "10.0.0.1"
    assert event.hostname == "wks-01.corp"
    assert event.payload == {"src_port": 4624}
    assert event.raw == "payload original"
    assert event.trace_id == "trace-1"
    assert event.normalized_at == _now()


def test_canonical_event_defaults() -> None:
    event = _canonical()
    assert event.user is None
    assert event.process is None
    assert event.ip_src is None
    assert event.ip_dst is None
    assert event.hostname is None
    assert event.payload == {}
    assert event.raw == ""
    # trace_id vazio é permitido por default; a pipeline preenche em produção.
    assert event.trace_id == ""
    assert event.normalized_at is not None
    assert event.normalized_at.tzinfo is UTC


def test_canonical_event_immutable() -> None:
    event = _canonical()
    with pytest.raises(FrozenInstanceError):
        event.user = "root"  # type: ignore[misc]


@pytest.mark.parametrize(
    "field_name",
    ["event_id", "source_type", "source_host", "event_type"],
)
def test_canonical_event_requires_required_fields(field_name: str) -> None:
    with pytest.raises(ValueError, match="não pode ser vazio"):
        _canonical(**{field_name: ""})
    with pytest.raises(ValueError, match="não pode ser vazio"):
        _canonical(**{field_name: "   "})


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


def test_enrichment_full_creation() -> None:
    enrichment = _enrichment(
        kind="geo", provider="maxmind", data={"country": "BR"}, created_at=_now()
    )
    assert enrichment.kind == "geo"
    assert enrichment.provider == "maxmind"
    assert enrichment.data == {"country": "BR"}
    assert enrichment.created_at == _now()


def test_enrichment_default_created_at() -> None:
    enrichment = _enrichment()
    assert enrichment.created_at is not None
    assert enrichment.created_at.tzinfo is UTC


def test_enrichment_immutable() -> None:
    enrichment = _enrichment()
    with pytest.raises(FrozenInstanceError):
        enrichment.kind = "intel"  # type: ignore[misc]


def test_enrichment_requires_kind() -> None:
    with pytest.raises(ValueError, match="kind não pode ser vazio"):
        _enrichment(kind="")


def test_enrichment_requires_provider() -> None:
    with pytest.raises(ValueError, match="provider não pode ser vazio"):
        _enrichment(provider="   ")


# ---------------------------------------------------------------------------
# EnrichedEvent (herança de CanonicalEvent)
# ---------------------------------------------------------------------------


def test_enriched_event_inheritance_creation() -> None:
    enrichment = _enrichment()
    event = EnrichedEvent(
        event_id="evt-1",
        timestamp=_now(),
        source_type="windows",
        source_host="wks-01",
        event_type="logon",
        severity=Severity.CRITICAL,
        user="admin",
        enrichments=(enrichment,),
    )
    assert isinstance(event, CanonicalEvent)
    # Acesso aos campos canônicos via herança.
    assert event.event_id == "evt-1"
    assert event.source_type == "windows"
    assert event.source_host == "wks-01"
    assert event.event_type == "logon"
    assert event.severity is Severity.CRITICAL
    assert event.user == "admin"
    assert event.enrichments == (enrichment,)


def test_enriched_event_empty_enrichments_default() -> None:
    event = EnrichedEvent(
        event_id="evt-1",
        timestamp=_now(),
        source_type="windows",
        source_host="wks-01",
        event_type="logon",
        severity=Severity.LOW,
    )
    assert event.enrichments == ()


def test_enriched_event_immutable() -> None:
    event = EnrichedEvent(
        event_id="evt-1",
        timestamp=_now(),
        source_type="windows",
        source_host="wks-01",
        event_type="logon",
        severity=Severity.LOW,
        enrichments=(_enrichment(),),
    )
    with pytest.raises(FrozenInstanceError):
        event.severity = Severity.HIGH  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        event.enrichments = ()  # type: ignore[misc]


def test_enriched_event_inherits_validation() -> None:
    with pytest.raises(ValueError, match="event_id não pode ser vazio"):
        EnrichedEvent(
            event_id="",
            timestamp=_now(),
            source_type="windows",
            source_host="wks-01",
            event_type="logon",
            severity=Severity.LOW,
        )
    with pytest.raises(ValueError, match="source_type não pode ser vazio"):
        EnrichedEvent(
            event_id="evt-1",
            timestamp=_now(),
            source_type="",
            source_host="wks-01",
            event_type="logon",
            severity=Severity.LOW,
        )


def test_pipeline_models_flow_from_collector_to_enrichment() -> None:
    """Exercita a jornada oficial da pipeline com os modelos reais."""
    raw = RawEvent(source_type="syslog", source_host="fw-01", raw_payload=b"accepted")
    parsed = ParsedEvent(
        event_id=raw.event_id,
        timestamp=raw.received_at,
        source_type=raw.source_type,
        source_host=raw.source_host,
        event_type="auth",
        fields={"user": "admin"},
        raw=raw.raw_payload,
        trace_id="trace-1",
    )
    canonical = CanonicalEvent(
        event_id=parsed.event_id,
        timestamp=parsed.timestamp,
        source_type=parsed.source_type,
        source_host=parsed.source_host,
        event_type=parsed.event_type,
        severity=Severity.MEDIUM,
        user=parsed.fields["user"],
        trace_id=parsed.trace_id,
    )
    enrichment = Enrichment(kind="intel", provider="feodo", data={"confidence": 0.9})
    enriched = EnrichedEvent(**asdict(canonical), enrichments=(enrichment,))
    assert enriched.event_id == raw.event_id
    assert enriched.enrichments[0].provider == "feodo"
    assert enriched.severity is Severity.MEDIUM
