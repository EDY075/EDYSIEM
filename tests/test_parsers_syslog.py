"""Testes do parser Syslog RFC3164."""

from __future__ import annotations

from datetime import UTC, datetime

from edysiem.domain import RawEvent
from edysiem.parsers.syslog import parse


def _raw_syslog(payload: str) -> RawEvent:
    return RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload=payload,
        event_id="raw-1",
        received_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
    )


def test_parse_syslog_success() -> None:
    result = parse(
        _raw_syslog("<13>Aug  3 12:00:00 wks-01 sshd[1234]: Accepted password for admin")
    )
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["facility"] == "user"
    assert fields["severity"] == "notice"
    assert fields["facility_code"] == 1
    assert fields["severity_code"] == 5
    assert fields["process"] == "sshd"
    assert fields["pid"] == "1234"
    assert fields["message"] == "Accepted password for admin"
    assert fields["event_category"] == "auth"
    assert fields["event_action"] == "accept"


def test_parse_syslog_reject() -> None:
    result = parse(
        _raw_syslog("<10>Aug  3 12:00:01 fw-01 sshd[5678]: Failed password for root from 10.0.0.1")
    )
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["event_category"] == "auth"
    assert fields["event_action"] == "reject"


def test_parse_syslog_invalid_format() -> None:
    raw = RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload="not a syslog message",
        event_id="raw-1",
        received_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
    )
    result = parse(raw)
    assert result.is_err()
    assert result.error.code.name == "PLUGIN_ERROR"


def test_parse_syslog_bytes_payload() -> None:
    raw = RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload=b"<13>Aug  3 12:00:00 wks-01 sshd[1234]: Accepted",
        event_id="raw-1",
        received_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
    )
    result = parse(raw)
    assert result.is_ok()


def test_parse_syslog_kernel() -> None:
    result = parse(_raw_syslog("<3>Aug  3 12:00:00 host kernel: [12345.678] Out of memory"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["facility"] == "kernel"
    assert fields["severity"] == "error"
    assert fields["event_category"] == "network"  # kernel -> network


def test_parse_syslog_cron() -> None:
    result = parse(
        _raw_syslog("<73>Aug  3 12:00:00 host CROND[1234]: (root) CMD (run-parts /etc/cron.hourly)")
    )
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["facility"] == "cron"
    assert fields["event_category"] == "process"  # CROND process -> process


def test_parse_syslog_no_pid() -> None:
    result = parse(_raw_syslog("<13>Aug  3 12:00:00 host sshd: Accepted password for admin"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["process"] == "sshd"
    assert fields["pid"] is None


def test_parse_syslog_error_severity() -> None:
    result = parse(_raw_syslog("<3>Aug  3 12:00:00 host kernel: ERROR: something bad"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["severity"] == "error"
    assert fields["severity_code"] == 3


def test_parse_syslog_emergency() -> None:
    result = parse(_raw_syslog("<0>Aug  3 12:00:00 host kernel: Panic: system halted"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["severity"] == "emergency"
    assert fields["severity_code"] == 0


def test_parse_syslog_local0() -> None:
    result = parse(_raw_syslog("<134>Aug  3 12:00:00 host myapp[1]: Local message"))
    assert result.is_ok()
    fields = result.unwrap()
    assert fields["facility"] == "local0"
    assert fields["facility_code"] == 16
