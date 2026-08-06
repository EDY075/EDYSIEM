"""Testes do token bucket rate limiter (thread-safe, 100% stdlib)."""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

from edysiem.ingestion.rate_limiter import RateLimitConfig, TokenBucketRateLimiter


def test_config_defaults() -> None:
    config = RateLimitConfig()
    assert config.rate == 100.0
    assert config.burst == 200


@pytest.mark.parametrize(("rate", "burst"), [(0.0, 1), (-1.0, 5), (10.0, 0), (10.0, -1)])
def test_config_validation(rate: float, burst: int) -> None:
    with pytest.raises(ValueError, match="deve ser"):
        RateLimitConfig(rate=rate, burst=burst)


def test_burst_tokens_available_then_exhausted() -> None:
    limiter = TokenBucketRateLimiter(RateLimitConfig(rate=1.0, burst=3))
    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is False


def test_tokens_property_and_reset() -> None:
    limiter = TokenBucketRateLimiter(RateLimitConfig(rate=1.0, burst=5))
    assert limiter.tokens == 5.0
    assert limiter.try_acquire() is True
    assert limiter.tokens == pytest.approx(4.0)
    limiter.reset()
    assert limiter.tokens == 5.0


def test_acquire_consumes_token() -> None:
    limiter = TokenBucketRateLimiter(RateLimitConfig(rate=1.0, burst=1))

    async def scenario() -> bool:
        acquired = await limiter.acquire()
        return acquired

    assert asyncio.run(scenario()) is True
    assert limiter.tokens == pytest.approx(0.0)


def test_acquire_refills_after_wait() -> None:
    # rate = 100 tokens/s: após 30ms o bucket reabastece ~3 tokens.
    limiter = TokenBucketRateLimiter(RateLimitConfig(rate=100.0, burst=1))
    assert limiter.try_acquire() is True

    async def scenario() -> bool:
        await asyncio.sleep(0.03)
        return await limiter.acquire()

    assert asyncio.run(scenario()) is True


def test_acquire_timeout_returns_false() -> None:
    limiter = TokenBucketRateLimiter(RateLimitConfig(rate=0.5, burst=1))
    assert limiter.try_acquire() is True

    async def scenario() -> bool:
        return await limiter.acquire(timeout=0.02)

    assert asyncio.run(scenario()) is False


def test_try_acquire_after_real_time_refill() -> None:
    limiter = TokenBucketRateLimiter(RateLimitConfig(rate=50.0, burst=1))
    assert limiter.try_acquire() is True
    time.sleep(0.05)
    assert limiter.try_acquire() is True


def test_thread_safety_no_over_issue() -> None:
    # Taxa ~0 garante que o refill não reabastece durante a corrida; só o
    # burst inicial (50) está disponível para 100 threads.
    burst = 50
    limiter = TokenBucketRateLimiter(RateLimitConfig(rate=1e-9, burst=burst))
    acquired: list[bool] = []
    lock = threading.Lock()

    def worker() -> None:
        result = limiter.try_acquire()
        with lock:
            acquired.append(result)

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(acquired) <= burst
