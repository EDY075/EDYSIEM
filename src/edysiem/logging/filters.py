"""Filtros de saneamento de dados sensíveis em logs."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, cast

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "cookie",
        "session_token",
        "private_key",
    }
)

REDACTED = "***"


def _redact_value(value: object) -> object:
    if isinstance(value, Mapping):
        return sanitize_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_redact_value(v) for v in value]
    if isinstance(value, str) and len(value) > 512:
        return value[:512] + "..."
    return value


def sanitize_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Retorna cópia do mapeamento com valores sensíveis mascarados."""
    safe: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            safe[key] = REDACTED
        else:
            safe[key] = _redact_value(value)
    return safe


class LogFilter(logging.Filter):
    """Filtro de logging que sanea registros antes da emissão."""

    def __init__(self) -> None:
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        # Sanea mensagens estruturadas (Mapping) já emitidas como `msg`.
        if isinstance(getattr(record, "msg", None), Mapping):
            record.msg = sanitize_mapping(cast(Mapping[str, Any], record.msg))
        return True


__all__ = ["REDACTED", "SENSITIVE_KEYS", "LogFilter", "sanitize_mapping"]
