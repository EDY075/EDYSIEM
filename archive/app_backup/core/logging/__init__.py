"""Logger central — structured logging, JSON-ready, correlation/request/session ID.

Sem dependências externas (formatter JSON próprio). Base para o Logging Design.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formatter que emite logs em JSON com campos padronizados."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("trace_id", "request_id", "session_id", "category"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        extra = getattr(record, "context", None)
        if isinstance(extra, dict):
            entry["context"] = extra
        return json.dumps(entry, ensure_ascii=False, default=str)


@dataclass(frozen=True)
class LogContext:
    """Contexto de correlação propagado nos logs."""

    trace_id: str
    request_id: str | None = None
    session_id: str | None = None

    @staticmethod
    def new(trace_id: str | None = None) -> "LogContext":
        return LogContext(
            trace_id=trace_id or f"tr_{uuid.uuid4().hex[:12]}",
            request_id=None,
            session_id=None,
        )


class ContextualLogger:
    """Wrapper de logging.Logger com contexto estruturado opcional."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    @property
    def underlying(self) -> logging.Logger:
        return self._logger

    def _log(self, level: int, message: str, context: LogContext | None, **kwargs: Any) -> None:
        extra: dict[str, Any] = {}
        if context:
            extra["trace_id"] = context.trace_id
            if context.request_id:
                extra["request_id"] = context.request_id
            if context.session_id:
                extra["session_id"] = context.session_id
        if "context" in kwargs:
            extra["context"] = kwargs.pop("context")
        extra.update(kwargs)
        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, context, **kwargs)

    def info(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        self._log(logging.INFO, message, context, **kwargs)

    def warning(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, context, **kwargs)

    def error(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, context, **kwargs)

    def critical(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, message, context, **kwargs)


def get_logger(name: str, *, json_output: bool = True, level: int = logging.INFO) -> ContextualLogger:
    """Obter logger contextual configurado."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter() if json_output else logging.Formatter("%(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return ContextualLogger(logger)


# Logger padrão da aplicação
app_logger = get_logger("edy_siem")
