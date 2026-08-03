"""Serialização JSON da estrutura de logs (stdlib)."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any, cast


def _json_default(value: object) -> object:
    """Fallback do serializador para tipos complexos."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(cast(Any, value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, Exception):
        return f"{type(value).__name__}: {value}"
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def to_json(data: object) -> str:
    """Serializa ``data`` para uma string JSON estável."""
    return json.dumps(data, default=_json_default, ensure_ascii=False)


def dumps(data: Any, **kwargs: Any) -> str:
    """Atalho tipado para ``json.dumps`` com suporte a tipos complexos."""
    return json.dumps(data, default=_json_default, ensure_ascii=False, **kwargs)


class JsonFormatter:
    """Converte qualquer mapeamento/log record em uma linha JSON."""

    def format(self, data: Mapping[str, Any]) -> str:
        return to_json(dict(data))

    def __call__(self, data: Mapping[str, Any]) -> str:
        return self.format(data)


__all__ = ["JsonFormatter", "dumps", "to_json"]
