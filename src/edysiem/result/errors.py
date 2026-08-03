"""Códigos de erro e o tipo ``Error`` estruturado do núcleo."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class ErrorCode(Enum):
    """Categorias normalizadas de erro usadas em toda a plataforma."""

    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    INTERNAL_ERROR = "internal_error"
    TIMEOUT = "timeout"
    QUEUE_FULL = "queue_full"
    PLUGIN_ERROR = "plugin_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Error:
    """Um erro estruturado e serializável.

    Attributes:
        code: Categoria canônica do erro.
        message: Mensagem legível e estável.
        details: Mapa opcional de detalhes adicionais.
        cause: Exceção de origem (nunca serializada em profundidade).
    """

    code: ErrorCode
    message: str
    details: Mapping[str, object] = field(default_factory=dict)
    cause: Exception | None = None

    def to_dict(self) -> dict[str, object]:
        """Serializa o erro em um dicionário JSON-friendly."""
        data: dict[str, object] = {
            "code": self.code.value,
            "message": self.message,
            "details": dict(self.details),
        }
        if self.cause is not None:
            data["cause"] = f"{type(self.cause).__name__}: {self.cause}"
        return data

    def __str__(self) -> str:
        return f"<Error code={self.code.value!r} message={self.message!r}>"


__all__ = ["Error", "ErrorCode"]
