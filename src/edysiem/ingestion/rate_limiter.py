"""Rate limiter token bucket para a infraestrutura de ingestão.

``TokenBucketRateLimiter`` implementa o algoritmo clássico de *token bucket*:
o bucket acumula até ``burst`` tokens e reabastece à taxa ``rate`` tokens por
segundo; cada ``acquire``/``try_acquire`` consome um token. Quando o bucket
está vazio, ``acquire`` aguarda até o próximo token (respeitando um timeout
opcional) e ``try_acquire`` retorna ``False`` imediatamente.

A implementação é thread-safe (``threading.Lock``) e 100% stdlib
(``time.monotonic`` para refill).
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Configuração do token bucket.

    Attributes:
        rate: Tokens adicionados por segundo (events/sec).
        burst: Capacidade máxima do bucket (rajada permitida).
    """

    rate: float = 100.0
    burst: int = 200

    def __post_init__(self) -> None:
        if self.rate <= 0:
            raise ValueError(f"rate deve ser > 0; recebido {self.rate}")
        if self.burst < 1:
            raise ValueError(f"burst deve ser >= 1; recebido {self.burst}")


class TokenBucketRateLimiter:
    """Token bucket thread-safe com aquisição síncrona e async.

    O bucket começa cheio (``burst`` tokens). ``try_acquire`` não bloqueia e
    ``acquire`` aguarda até o token disponível ou o ``timeout`` expirar
    (``None`` = aguarda indefinidamente).
    """

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self._config = config or RateLimitConfig()
        self._lock = threading.Lock()
        self._tokens = float(self._config.burst)
        self._last_refill = time.monotonic()

    def try_acquire(self) -> bool:
        """Tenta consumir um token sem bloquear.

        Returns:
            ``True`` se um token foi consumido; ``False`` se o bucket estava
            vazio (não há espera).
        """
        with self._lock:
            self._refill_locked()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    async def acquire(self, timeout: float | None = None) -> bool:
        """Aguarda (até ``timeout``) e consome um token.

        Args:
            timeout: Tempo máximo (segundos) de espera; ``None`` aguarda até
                o token estar disponível.

        Returns:
            ``True`` se um token foi consumido; ``False`` em timeout.
        """
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout
        while True:
            if self.try_acquire():
                return True
            if deadline is not None and loop.time() >= deadline:
                return False
            wait = self._wait_time()
            if wait <= 0.0:
                continue
            if deadline is not None:
                remaining = deadline - loop.time()
                if remaining <= 0.0:
                    return False
                wait = min(wait, remaining)
            await asyncio.sleep(wait)

    @property
    def tokens(self) -> float:
        """Número corrente de tokens no bucket (após refill)."""
        with self._lock:
            self._refill_locked()
            return self._tokens

    def reset(self) -> None:
        """Recarrega o bucket para a capacidade máxima."""
        with self._lock:
            self._tokens = float(self._config.burst)
            self._last_refill = time.monotonic()

    def _refill_locked(self) -> None:
        """Reabastece tokens proporcional ao tempo decorrido (deve segurar o lock)."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0.0:
            refilled = self._tokens + elapsed * self._config.rate
            self._tokens = min(float(self._config.burst), refilled)
            self._last_refill = now

    def _wait_time(self) -> float:
        """Segundos estimados até o próximo token (reabastecimento incluso)."""
        with self._lock:
            self._refill_locked()
            if self._tokens >= 1.0:
                return 0.0
            needed = 1.0 - self._tokens
            return needed / self._config.rate


__all__ = ["RateLimitConfig", "TokenBucketRateLimiter"]
