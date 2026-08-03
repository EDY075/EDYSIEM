"""Módulo central de validação — tipos, domínio e configuração."""

from __future__ import annotations

import re
from typing import Any, Callable, TypeVar

from app.core.errors import ValidationException
from app.core.result import ErrorCode, Result

T = TypeVar("T")

_IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


def validate_not_empty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValidationException(f"{field_name} não pode ser vazio")
    return value


def validate_type(value: Any, expected: type, field_name: str) -> Any:
    if not isinstance(value, expected):
        raise ValidationException(
            f"{field_name} deve ser {expected.__name__}, recebeu {type(value).__name__}"
        )
    return value


def validate_ipv4(value: str, field_name: str = "ip") -> str:
    if not _IPV4_RE.match(value):
        raise ValidationException(f"{field_name} inválido: {value!r}")
    parts = value.split(".")
    if any(int(p) > 255 for p in parts):
        raise ValidationException(f"{field_name} inválido (octeto > 255): {value!r}")
    return value


def validate_range(value: int, min_val: int, max_val: int, field_name: str) -> int:
    if value < min_val or value > max_val:
        raise ValidationException(f"{field_name} deve estar entre {min_val} e {max_val}")
    return value


def validate_dict_keys(data: dict[str, Any], required: list[str], field_name: str = "payload") -> dict[str, Any]:
    missing = [k for k in required if k not in data]
    if missing:
        raise ValidationException(f"{field_name} ausentes: {', '.join(missing)}")
    return data


def validate_enum(value: Any, enum_cls: type, field_name: str) -> Any:
    try:
        return enum_cls(value)  # type: ignore[arg-type,return-value]
    except (ValueError, TypeError):
        allowed = ", ".join(e.value for e in enum_cls)  # type: ignore[attr-defined]
        raise ValidationException(f"{field_name} inválido: {value!r} (esperado: {allowed})")


def try_validate(fn: Callable[[], T]) -> Result[T]:
    """Executar validação capturando ValidationException como Result.fail."""
    try:
        return Result.success(fn())
    except ValidationException as exc:
        return Result.fail(ErrorCode.VALIDATION_ERROR, exc.message, exc.details)


def safe_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    return data.get(key, default)
