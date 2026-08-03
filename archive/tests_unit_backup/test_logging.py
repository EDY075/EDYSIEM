"""Testes do logging base."""

import json
import logging

from app.core.logging import ContextualLogger, JsonFormatter, LogContext, get_logger


def test_log_context_new() -> None:
    ctx = LogContext.new()
    assert ctx.trace_id.startswith("tr_")


def test_log_context_with_trace() -> None:
    ctx = LogContext.new("tr_custom")
    assert ctx.trace_id == "tr_custom"


def test_get_logger_returns_contextual() -> None:
    logger = get_logger("test_logger", json_output=True, level=logging.DEBUG)
    assert isinstance(logger, ContextualLogger)


def test_json_formatter_output() -> None:
    record = logging.LogRecord(
        name="x", level=logging.INFO, pathname="", lineno=1, msg="msg", args=(), exc_info=None
    )
    record.trace_id = "tr_1"  # type: ignore[attr-defined]
    out = JsonFormatter().format(record)
    data = json.loads(out)
    assert data["level"] == "INFO"
    assert data["message"] == "msg"
    assert data["trace_id"] == "tr_1"


def test_json_formatter_context() -> None:
    record = logging.LogRecord("x", logging.INFO, "", 1, "m", (), None)
    record.context = {"a": 1}  # type: ignore[attr-defined]
    data = json.loads(JsonFormatter().format(record))
    assert data["context"] == {"a": 1}


def test_logger_info_with_context() -> None:
    logger = get_logger("test_ctx")
    # não deve lançar
    logger.info("teste", context=LogContext.new("tr_x"), context_data={"k": 1})
