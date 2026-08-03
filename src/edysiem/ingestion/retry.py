"""Política de retry com backoff exponencial e jitter.

``RetryPolicy`` define quantas tentativas executar e o intervalo entre elas;
``run_with_retry`` executa uma operação async até o sucesso ou o esgotamento
das tentativas. O backoff exponencial usa ``min(max_delay, base_delay * 2 **
(attempt - 1))`` e o jitter opcional aplica variação uniforme de ±20% via
``random.uniform`` (stdlib).
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ..logging import StructuredLogger

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Política de retentativa de operações falhas.

    Attributes:
        max_attempts: Número máximo de tentativas (>= 1).
        base_delay: Atraso base (segundos) antes da segunda tentativa.
        max_delay: Teto do atraso exponencial (segundos).
        exponential_backoff: Se ``True``, o atraso dobra a cada tentativa;
            caso contrário permanece constante em ``base_delay``.
        jitter: Se ``True``, aplica variação uniforme de ±20% no atraso.
        retryable_exceptions: Tupla de exceções retryable; vazia significa
            que todas as exceções são retryable.
    """

    max_attempts: int = 3
    base_delay: float = 0.1
    max_delay: float = 5.0
    exponential_backoff: bool = True
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = ()

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts deve ser >= 1; recebido {self.max_attempts}")
        if self.base_delay < 0:
            raise ValueError(f"base_delay não pode ser negativo; recebido {self.base_delay}")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay deve ser >= base_delay")

    def should_retry(self, attempt: int, exc: Exception) -> bool:
        """Diz se a tentativa ``attempt`` (1-based, a que falhou) deve repetir.

        Retorna ``False`` quando as tentativas esgotaram ou quando ``exc`` não
        está entre ``retryable_exceptions`` (se a tupla não for vazia).
        """
        if attempt >= self.max_attempts:
            return False
        if self.retryable_exceptions:
            return any(isinstance(exc, exc_type) for exc_type in self.retryable_exceptions)
        return True

    def delay_for(self, attempt: int) -> float:
        """Atraso (segundos) antes da tentativa ``attempt + 1``.

        ``attempt`` é a tentativa que acabou de falhar (1-based). Sem
        ``exponential_backoff``, o atraso é constante; com jitter, varia
        uniformemente entre 80% e 120% do valor nominal.
        """
        if self.exponential_backoff:
            # Base float evita Any do `int ** int` no typeshed do mypy.
            nominal = min(self.max_delay, self.base_delay * (2.0 ** (attempt - 1)))
        else:
            nominal = self.base_delay
        if not self.jitter:
            return nominal

        return random.uniform(nominal * 0.8, nominal * 1.2)  # noqa: S311


async def run_with_retry(
    operation: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    *,
    logger: logging.Logger | StructuredLogger | None = None,
) -> T:
    """Executa ``operation`` com retry conforme ``policy``.

    Args:
        operation: Callable async sem argumentos (ex.: um coro factory).
        policy: Política de retentativa.
        logger: Logger opcional (stdlib ou ``StructuredLogger``) para registrar
            cada retry.

    Returns:
        O valor da operação no primeiro sucesso.

    Raises:
        A última exceção levantada pela operação quando as tentativas esgotam
        ou quando a exceção não é retryable.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return await operation()
        except Exception as exc:
            if not policy.should_retry(attempt, exc):
                raise
            delay = policy.delay_for(attempt)
            if logger is not None:
                logger.warning(
                    f"tentativa {attempt} falhou; retry em {delay:.3f}s: {type(exc).__name__}"
                )
            await asyncio.sleep(delay)


__all__ = ["RetryPolicy", "run_with_retry"]
