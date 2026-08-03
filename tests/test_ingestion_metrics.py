"""Testes do ``MetricsRegistry`` (observabilidade sem dependência externa)."""

from __future__ import annotations

import threading

import pytest

from edysiem.ingestion.metrics import (
    METRIC_DEAD_LETTERS,
    METRIC_DROPS,
    METRIC_LATENCY_MS,
    METRIC_QUEUE_SIZE,
    METRIC_RETRIES,
    MetricsRegistry,
)


def test_increment_default_and_custom_value() -> None:
    registry = MetricsRegistry()
    registry.increment("events")
    registry.increment("events")
    registry.increment("events", 3)
    assert registry.get("events") == 5.0


def test_set_gauge() -> None:
    registry = MetricsRegistry()
    registry.set_gauge(METRIC_QUEUE_SIZE, 42)
    registry.set_gauge(METRIC_QUEUE_SIZE, 7)
    assert registry.get(METRIC_QUEUE_SIZE) == 7.0


def test_observe_computes_average() -> None:
    registry = MetricsRegistry()
    registry.observe(METRIC_LATENCY_MS, 10)
    registry.observe(METRIC_LATENCY_MS, 30)
    assert registry.get(METRIC_LATENCY_MS) == 20.0


def test_observe_no_samples_returns_zero() -> None:
    registry = MetricsRegistry()
    assert registry.get(METRIC_LATENCY_MS) == 0.0


def test_get_missing_returns_zero() -> None:
    registry = MetricsRegistry()
    assert registry.get("nao_existe") == 0.0


def test_snapshot_consolidates_categories() -> None:
    registry = MetricsRegistry()
    registry.increment(METRIC_DROPS)
    registry.set_gauge(METRIC_QUEUE_SIZE, 3)
    registry.observe(METRIC_RETRIES, 2)
    registry.observe(METRIC_RETRIES, 4)
    snapshot = registry.snapshot()
    assert snapshot[METRIC_DROPS] == 1.0
    assert snapshot[METRIC_QUEUE_SIZE] == 3.0
    assert snapshot[METRIC_RETRIES] == 3.0


def test_snapshot_is_a_copy() -> None:
    registry = MetricsRegistry()
    registry.increment("events")
    snapshot = registry.snapshot()
    snapshot["events"] = 999
    assert registry.get("events") == 1.0


def test_reset_clears_everything() -> None:
    registry = MetricsRegistry()
    registry.increment("events")
    registry.set_gauge(METRIC_QUEUE_SIZE, 5)
    registry.observe(METRIC_LATENCY_MS, 15)
    registry.reset()
    assert registry.snapshot() == {}
    assert registry.get("events") == 0.0


def test_metric_name_constants_are_stable() -> None:
    assert METRIC_DEAD_LETTERS == "dead_letters"
    assert METRIC_DROPS == "drops"
    assert METRIC_QUEUE_SIZE == "queue_size"


def test_thread_safety_concurrent_increments() -> None:
    registry = MetricsRegistry()
    threads = 8
    per_thread = 500

    def worker() -> None:
        for _ in range(per_thread):
            registry.increment("events")

    workers = [threading.Thread(target=worker) for _ in range(threads)]
    for t in workers:
        t.start()
    for t in workers:
        t.join()
    assert registry.get("events") == threads * per_thread


def test_timer_average_float_value() -> None:
    registry = MetricsRegistry()
    registry.observe(METRIC_LATENCY_MS, 2.5)
    assert registry.get(METRIC_LATENCY_MS) == pytest.approx(2.5)
