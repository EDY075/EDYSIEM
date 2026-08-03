"""Tipos ``Result``/``Success``/``Failure`` do núcleo.

Implementa um tipo soma de sucesso/falha com API estilo Rust, sem dependências
externas. É a espinha dorsal de propagação de erros de todo o EDYI.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, NoReturn, TypeAlias, TypeVar

from .errors import Error, ErrorCode

T = TypeVar("T")
U = TypeVar("U")


class ResultUnwrapError(Exception):
    """Lançada quando ``unwrap``/``expect`` são chamados em uma ``Failure``."""


class Success(Generic[T]):
    """Contêiner de sucesso que carrega um valor."""

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self._value

    def unwrap_or(self, default: T) -> T:
        return self._value

    def expect(self, msg: str) -> T:
        return self._value

    def map(self, func: Callable[[T], U]) -> Result[U]:
        return ok(func(self._value))

    def map_err(self, func: Callable[[Error], Error]) -> Result[T]:
        return self

    def and_then(self, func: Callable[[T], Result[U]]) -> Result[U]:
        return func(self._value)

    def __repr__(self) -> str:
        return f"Success({self._value!r})"


class Failure(Generic[T]):
    """Contêiner de falha que carrega um ``Error``."""

    __slots__ = ("_error",)

    def __init__(self, error: Error) -> None:
        self._error = error

    @property
    def error(self) -> Error:
        return self._error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise ResultUnwrapError(self._error.message)

    def unwrap_or(self, default: T) -> T:
        return default

    def expect(self, msg: str) -> T:
        raise ResultUnwrapError(msg)

    def map(self, func: Callable[[T], U]) -> Result[T]:
        return self

    def map_err(self, func: Callable[[Error], Error]) -> Result[T]:
        return Failure(func(self._error))

    def and_then(self, func: Callable[[T], Result[U]]) -> Result[T]:
        return self

    def __repr__(self) -> str:
        return f"Failure({self._error!r})"


Result: TypeAlias = Success[T] | Failure[T]


def ok(value: T) -> Success[T]:
    """Cria uma ``Result`` de sucesso."""
    return Success(value)


def err(error: Error) -> Failure[object]:
    """Cria uma ``Result`` de falha."""
    return Failure(error)


def and_then(result: Result[T], func: Callable[[T], Result[U]]) -> Result[U]:
    """Aplica ``func`` em cadeia, propagando falhas."""
    if isinstance(result, Success):
        return func(result.value)
    return result  # type: ignore[return-value]


def from_exc(
    exception: BaseException,
    code: ErrorCode = ErrorCode.INTERNAL_ERROR,
    message: str | None = None,
) -> Result[NoReturn]:
    """Converte uma exceção em uma ``Failure``.

    Args:
        exception: Exceção de origem.
        code: Código de erro a utilizar para a falha.
        message: Mensagem opcional; usa a da exceção se não informada.
    """
    msg = message if message is not None else str(exception)
    cause: Exception | None
    if isinstance(exception, Exception):
        cause = getattr(exception, "cause", None)
    else:
        cause = None
    return Failure(Error(code=code, message=msg, details={}, cause=cause))


__all__ = [
    "Failure",
    "Result",
    "ResultUnwrapError",
    "Success",
    "and_then",
    "err",
    "from_exc",
    "ok",
]