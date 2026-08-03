"""Result Pattern — sem nunca retornar None para resultados de operação."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Códigos de erro estáveis do domínio."""

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFIGURATION_ERROR = "configuration_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    PLUGIN_ERROR = "plugin_error"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class Failure:
    """Descrição de falha de uma operação."""

    code: ErrorCode
    message: str
    details: dict[str, object] | None = None

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


@dataclass(frozen=True)
class Result(Generic[T]):
    """Resultado de uma operação — sucesso ou falha, nunca None silencioso."""

    ok: bool
    value: T | None = None
    failure: Failure | None = None

    @staticmethod
    def success(value: T) -> "Result[T]":
        return Result(ok=True, value=value)

    @staticmethod
    def fail(code: ErrorCode, message: str, details: dict[str, object] | None = None) -> "Result[T]":
        return Result(ok=False, failure=Failure(code=code, message=message, details=details))

    @staticmethod
    def from_failure(failure: Failure) -> "Result[T]":
        return Result(ok=False, failure=failure)

    def unwrap(self) -> T:
        """Retorna o valor ou levanta AssertionError (uso em testes/contrato)."""
        if not self.ok or self.value is None:
            raise AssertionError(f"Result não é sucesso: {self.failure}")
        return self.value

    def expect(self, message: str) -> T:
        if not self.ok or self.value is None:
            raise AssertionError(f"{message}: {self.failure}")
        return self.value

    def map(self, fn) -> "Result":
        if not self.ok:
            return self
        return Result.success(fn(self.value))  # type: ignore[arg-type]

    @property
    def is_success(self) -> bool:
        return self.ok

    @property
    def is_failure(self) -> bool:
        return not self.ok


def success(value: T) -> Result[T]:
    return Result.success(value)


def fail(code: ErrorCode, message: str, details: dict[str, object] | None = None) -> Result[T]:
    return Result.fail(code, message, details)
