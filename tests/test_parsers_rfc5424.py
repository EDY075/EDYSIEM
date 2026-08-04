"""Testes do parser Syslog RFC5424."""

from __future__ import annotations

from datetime import UTC, datetime

from edysiem.domain import RawEvent
from edysiem.parsers.rfc5424 import parse


def _raw_rfc5424(payload: str) -> RawEvent:
    return RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload=payload,
        event_id="raw-1",
        received_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
    )


def test_parse_rfc5424_success() -> None:
    result = parse(
        _raw_rfc5424(
            "<165>1 2026-08-03T12:00:00.000Z wks-01 sshd - -"
            ' [meta sequenceId="1"] User admin logged in'
        )
    )
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["version"] == 1
    assert fields["facility"] == "local4"
    assert fields["severity"] == "notice"
    assert fields["app_name"] == "sshd"
    assert fields["proc_id"] == "-"
    assert fields["msg_id"] == "-"
    assert fields["message"] == "User admin logged in"
    assert fields["event_category"] == "auth"
    assert fields["event_action"] == "info"


def test_parse_rfc5424_with_structured_data() -> None:
    result = parse(
        _raw_rfc5424(
            "<165>1 2026-08-03T12:00:00.000Z wks-01 sshd - -"
            ' [meta sequenceId="1" msgId="msg-1"] Login accepted'
        )
    )
    assert result.is_ok()
    fields = result.unwrap()
    sd = fields["structured_data"]
    assert "meta" in sd
    assert sd["meta"]["sequenceId"] == "1"
    assert sd["meta"]["msgId"] == "msg-1"


def test_parse_rfc5424_error() -> None:
    result = parse(_raw_rfc5424("<11>1 2026-08-03T12:00:00.000Z wks-01 kernel - - - Kernel panic"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["severity"] == "error"
    assert fields["event_category"] == "system"


def test_parse_rfc5424_invalid_format() -> None:
    raw = RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload="not an rfc5424 message",
        event_id="raw-1",
        received_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
    )
    result = parse(raw)
    assert result.is_err()
    assert result.error.code.name == "PLUGIN_ERROR"


def test_parse_rfc5424_bytes_payload() -> None:
    raw = RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload=b"<165>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - Test",
        event_id="raw-1",
        received_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
    )
    result = parse(raw)
    assert result.is_ok()


def test_parse_rfc5424_critical() -> None:
    result = parse(
        _raw_rfc5424("<2>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - Critical failure detected")
    )
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["severity"] == "critical"
    assert fields["severity_code"] == 2


def test_parse_rfc5424_emergency() -> None:
    result = parse(_raw_rfc5424("<0>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - System emergency"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["severity"] == "emergency"
    assert fields["severity_code"] == 0


def test_parse_rfc5424_denied_action() -> None:
    result = parse(
        _raw_rfc5424(
            "<10>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - Connection denied from 10.0.0.1"
        )
    )
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["event_action"] == "reject"


def test_parse_rfc5424_local0() -> None:
    result = parse(_raw_rfc5424("<134>1 2026-08-03T12:00:00.000Z wks-01 myapp - - - Local message"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["facility"] == "local0"
    assert fields["facility_code"] == 16
