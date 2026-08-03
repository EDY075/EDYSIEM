"""Testes da política de retry (backoff exponencial + jitter)."""

from __future__ import annotations

import asyncio

import pytest

from edysiem.ingestion.retry import RetryPolicy, run_with_retry


def test_policy_defaults() -> None:
    policy = RetryPolicy()
    assert policy.max_attempts == 3
    assert policy.base_delay == 0.1
    assert policy.max_delay == 5.0
    assert policy.exponential_backoff is True
    assert policy.jitter is True
    assert policy.retryable_exceptions == ()


@pytest.mark.parametrize(
    ("max_attempts", "base_delay", "max_delay"),
    [
        (0, 0.1, 5.0),
        (-1, 0.1, 5.0),
        (3, -0.1, 5.0),
        (3, 0.5, 0.1),
    ],
)
def test_policy_validation(max_attempts: int, base_delay: float, max_delay: float) -> None:
    with pytest.raises(ValueError, match=r"deve ser|não pode ser"):
        RetryPolicy(max_attempts=max_attempts, base_delay=base_delay, max_delay=max_delay)


def test_should_retry_respects_max_attempts() -> None:
    policy = RetryPolicy(max_attempts=3)
    assert policy.should_retry(1, ValueError("x")) is True
    assert policy.should_retry(2, ValueError("x")) is True
    assert policy.should_retry(3, ValueError("x")) is False


def test_should_retry_filters_retryable_exceptions() -> None:
    policy = RetryPolicy(max_attempts=3, retryable_exceptions=(ValueError,))
    assert policy.should_retry(1, ValueError("x")) is True
    assert policy.should_retry(1, KeyError("x")) is False


def test_delay_for_exponential_no_jitter() -> None:
    policy = RetryPolicy(max_attempts=5, base_delay=0.1, max_delay=10.0, jitter=False)
    assert policy.delay_for(1) == pytest.approx(0.1)
    assert policy.delay_for(2) == pytest.approx(0.2)
    assert policy.delay_for(3) == pytest.approx(0.4)


def test_delay_for_exponential_caps_at_max_delay() -> None:
    policy = RetryPolicy(max_attempts=10, base_delay=1.0, max_delay=3.0, jitter=False)
    assert policy.delay_for(1) == pytest.approx(1.0)
    assert policy.delay_for(2) == pytest.approx(2.0)
    assert policy.delay_for(3) == pytest.approx(3.0)
    assert policy.delay_for(5) == pytest.approx(3.0)


def test_delay_for_constant_without_exponential() -> None:
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=0.25,
        max_delay=5.0,
        exponential_backoff=False,
        jitter=False,
    )
    assert policy.delay_for(1) == pytest.approx(0.25)
    assert policy.delay_for(2) == pytest.approx(0.25)
    assert policy.delay_for(3) == pytest.approx(0.25)


def test_delay_for_jitter_stays_within_range() -> None:
    policy = RetryPolicy(base_delay=0.1, max_delay=5.0)
    for attempt in (1, 2, 3):
        nominal = min(5.0, 0.1 * (2.0 ** (attempt - 1)))
        delay = policy.delay_for(attempt)
        assert nominal * 0.8 <= delay <= nominal * 1.2


def test_run_with_retry_success_first_try() -> None:
    calls: list[str] = []

    async def op() -> str:
        calls.append("call")
        return "ok"

    policy = RetryPolicy(max_attempts=3, base_delay=0.001, max_delay=0.01, jitter=False)
    result = asyncio.run(run_with_retry(op, policy))
    assert result == "ok"
    assert len(calls) == 1


def test_run_with_retry_success_after_retries() -> None:
    calls: list[int] = []

    async def op() -> str:
        calls.append(len(calls) + 1)
        if len(calls) < 3:
            raise ValueError("boom")
        return "recuperado"

    policy = RetryPolicy(max_attempts=5, base_delay=0.001, max_delay=0.01, jitter=False)
    result = asyncio.run(run_with_retry(op, policy))
    assert result == "recuperado"
    assert len(calls) == 3


def test_run_with_retry_raises_after_exhausting_attempts() -> None:
    calls: list[int] = []

    async def op() -> None:
        calls.append(len(calls) + 1)
        raise ValueError("sempre falha")

    policy = RetryPolicy(max_attempts=3, base_delay=0.001, max_delay=0.01, jitter=False)
    with pytest.raises(ValueError, match="sempre falha"):
        asyncio.run(run_with_retry(op, policy))
    assert len(calls) == 3


def test_run_with_retry_non_retryable_raises_immediately() -> None:
    calls: list[int] = []

    async def op() -> None:
        calls.append(len(calls) + 1)
        raise KeyError("não retryable")

    policy = RetryPolicy(
        max_attempts=3,
        base_delay=0.001,
        max_delay=0.01,
        jitter=False,
        retryable_exceptions=(ValueError,),
    )
    with pytest.raises(KeyError):
        asyncio.run(run_with_retry(op, policy))
    assert len(calls) == 1


class RecordingLogger:
    """Logger fake que registra as mensagens de warning."""

    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def test_run_with_retry_logs_retries() -> None:
    calls: list[int] = []

    async def op() -> str:
        calls.append(len(calls) + 1)
        if len(calls) < 2:
            raise ValueError("boom")
        return "ok"

    logger = RecordingLogger()
    policy = RetryPolicy(max_attempts=3, base_delay=0.001, max_delay=0.01, jitter=False)
    assert asyncio.run(run_with_retry(op, policy, logger=logger)) == "ok"
    assert len(logger.warnings) == 1
    assert "tentativa 1" in logger.warnings[0]
