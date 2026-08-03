"""Logger estruturado que emite registros JSON (produção) ou texto (dev)."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from .filters import LogFilter, sanitize_mapping
from .json import to_json


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class StructuredFormatter(logging.Formatter):
    """Formatter que adiciona contexto estruturado a um ``LogRecord``."""

    def __init__(self, *, use_json: bool = True) -> None:
        super().__init__()
        self._use_json = use_json

    def format(self, record: logging.LogRecord) -> str:
        payload = self._base_dict(record)
        if self._use_json:
            return to_json(payload)
        parts: list[str] = []
        for key in ("time", "level", "logger", "message"):
            if key in payload:
                parts.append(f"{key}={payload[key]!r}")
        return " ".join(parts)

    @staticmethod
    def _base_dict(record: logging.LogRecord) -> dict[str, Any]:
        data: dict[str, Any] = {
            "time": _now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        kv = record.__dict__.get("kv")
        if isinstance(kv, Mapping):
            data.update(kv)
        return sanitize_mapping(data)


def configure_logging(
    name: str = "edysiem",
    *,
    level: int = logging.INFO,
    use_json: bool = True,
) -> logging.Logger:
    """Configura o logger raiz ``edysiem`` com formatter JSON/texto.

    Returns:
        O logger raiz configurado.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    # Remove handlers pré-existentes para evitar duplicação.
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter(use_json=use_json))
    handler.addFilter(LogFilter())
    logger.addHandler(handler)
    return logger


class StructuredLogger:
    """Wrapper que emite eventos estruturados via ``logging``."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        *,
        context: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger("edysiem")
        self._context: dict[str, Any] = dict(context or {})
        self._correlation_id = correlation_id
        self._request_id = request_id
        self._session_id = session_id
        self._level: int = self._logger.level

    @property
    def level(self) -> int:
        return self._level

    @property
    def context(self) -> Mapping[str, Any]:
        return self._context

    @property
    def correlation_id(self) -> str | None:
        return self._correlation_id

    @property
    def request_id(self) -> str | None:
        return self._request_id

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def _emit(self, level: int, message: str, exc_info: bool, **extras: Any) -> None:
        kv: dict[str, Any] = dict(self._context)
        if self._correlation_id:
            kv["correlation_id"] = self._correlation_id
        if self._request_id:
            kv["request_id"] = self._request_id
        if self._session_id:
            kv["session_id"] = self._session_id
        kv.update(extras)
        self._logger.log(level, message, extra={"kv": kv}, exc_info=exc_info)

    def info(self, message: str, **extras: Any) -> None:
        self._emit(logging.INFO, message, False, **extras)

    def warning(self, message: str, **extras: Any) -> None:
        self._emit(logging.WARNING, message, False, **extras)

    def error(self, message: str, **extras: Any) -> None:
        self._emit(logging.ERROR, message, False, **extras)

    def debug(self, message: str, **extras: Any) -> None:
        self._emit(logging.DEBUG, message, False, **extras)

    def critical(self, message: str, **extras: Any) -> None:
        self._emit(logging.CRITICAL, message, False, **extras)

    def exception(self, message: str, exc_info: bool = True, **extras: Any) -> None:
        self._emit(logging.ERROR, message, exc_info, **extras)


__all__ = ["StructuredFormatter", "StructuredLogger", "configure_logging"]
