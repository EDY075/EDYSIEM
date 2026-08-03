"""Testes do logging estruturado, JSON, contexto e saneamento."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum

import pytest

from edysiem.logging import (
    ContextManager,
    CorrelationId,
    JsonFormatter,
    LogFilter,
    RequestId,
    SessionId,
    StructuredFormatter,
    StructuredLogger,
    configure_logging,
    dumps,
    sanitize_mapping,
    to_json,
)


class SampleEnum(Enum):
    A = "alpha"


@dataclass(frozen=True)
class SampleData:
    name: str = "x"


def test_to_json_supported_types() -> None:
    payload = {
        "dt": datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
        "d": date(2024, 1, 2),
        "enum": SampleEnum.A,
        "dataclass": SampleData(),
        "set": {3, 1, 2},
        "bytes": b"ab",
        "exc": ValueError("x"),
    }
    text = to_json(payload)
    assert '"dt"' in text
    assert '"alpha"' in text
    assert '"name"' in text
    assert "ValueError" in text


def test_dumps_kwargs() -> None:
    text = dumps({"a": 1}, sort_keys=True)
    assert text == '{"a": 1}'


def test_json_formatter() -> None:
    formatter = JsonFormatter()
    line = formatter.format({"level": "INFO"})
    assert '"level": "INFO"' in line


def test_sanitize_mapping_redacts() -> None:
    safe = sanitize_mapping(
        {
            "password": "segredo",
            "api_key": "abc",
            "token": "t",
            "authorization": "Bearer x",
            "nested": {"password": "x", "ok": 1},
            "list": [{"secret": "s"}, "ok"],
        }
    )
    assert safe["password"] == "***"
    assert safe["api_key"] == "***"
    assert safe["nested"]["password"] == "***"
    assert safe["list"][0]["secret"] == "***"
    assert safe["nested"]["ok"] == 1


def test_sanitize_long_string_truncated() -> None:
    safe = sanitize_mapping({"long": "x" * 1000})
    assert len(safe["long"]) == 512 + 3


def test_log_filter_sanitizes_record() -> None:
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg={"password": "x"},
        args=(),
        exc_info=None,
    )
    flt = LogFilter()
    assert flt.filter(record) is True
    assert record.msg == {"password": "***"}


def test_context_manager() -> None:
    cm = ContextManager()
    cm.initialize()
    assert cm.get("correlation_id")
    assert cm.get_id("request_id")
    sid = cm.new_session()
    assert cm.get("session_id") == sid
    assert set(cm.snapshot()) == {"correlation_id", "request_id", "session_id"}
    merged = cm.record({"extra": 1})
    assert merged["extra"] == 1
    with pytest.raises(KeyError):
        cm.get("unknown")
    with pytest.raises(KeyError):
        cm.set("unknown", "x")


def test_context_ids_str() -> None:
    assert str(CorrelationId())
    assert str(RequestId())
    assert str(SessionId())


def test_structured_logger_emits(caplog) -> None:  # type: ignore[no-untyped-def]
    logger = StructuredLogger(
        context={"app": "core"},
        correlation_id="corr-1",
        request_id="req-1",
        session_id="sess-1",
    )
    with caplog.at_level(logging.INFO):
        logger.info("mensagem", extra_field=2)
        logger.warning("aviso")
        logger.error("erro")
        logger.debug("detalhe")
        logger.critical("critico")
        logger.exception("com exceção")
    assert "mensagem" in caplog.text


def test_structured_logger_properties() -> None:
    logger = StructuredLogger(correlation_id="c", request_id="r", session_id="s")
    assert logger.correlation_id == "c"
    assert logger.request_id == "r"
    assert logger.session_id == "s"
    assert logger.level == logging.getLogger("edysiem").level
    assert logger.context == {}


def test_configure_logging_json() -> None:
    logger = configure_logging("edysiem.test.json", level=logging.DEBUG, use_json=True)
    assert logger.level == logging.DEBUG
    assert logger.handlers
    assert logger.handlers[0].formatter is not None


def test_structured_formatter_text() -> None:
    formatter = StructuredFormatter(use_json=False)
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname=__file__, lineno=1, msg="msg", args=(), exc_info=None
    )
    out = formatter.format(record)
    assert "msg" in out
