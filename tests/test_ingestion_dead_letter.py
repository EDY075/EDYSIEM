"""Testes da Dead Letter Queue (eventos mortos)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from edysiem.domain import RawEvent
from edysiem.ingestion.dead_letter import DeadLetterQueue, DeadLetterRecord
from edysiem.ingestion.metrics import METRIC_DEAD_LETTERS, MetricsRegistry


def _event() -> RawEvent:
    return RawEvent(source_type="syslog", source_host="host-1", raw_payload=b"x")


def test_submit_and_records_fields() -> None:
    dlq = DeadLetterQueue()
    event = _event()
    dlq.submit(event, "falha de parse", collector="syslog-collector", stacktrace="Trace...")
    records = dlq.records()
    assert len(records) == 1
    record = records[0]
    assert isinstance(record, DeadLetterRecord)
    assert record.payload is event
    assert record.error == "falha de parse"
    assert record.collector == "syslog-collector"
    assert record.stacktrace == "Trace..."
    assert isinstance(record.timestamp, datetime)
    assert record.timestamp.tzinfo is not None
    assert record.timestamp == record.timestamp.astimezone(UTC)


def test_len_and_order() -> None:
    dlq = DeadLetterQueue()
    dlq.submit("payload-1", "e1")
    dlq.submit("payload-2", "e2")
    assert len(dlq) == 2
    assert [r.error for r in dlq.records()] == ["e1", "e2"]


def test_records_is_immutable_copy() -> None:
    dlq = DeadLetterQueue()
    dlq.submit("p", "e")
    records = dlq.records()
    assert isinstance(records, tuple)
    with pytest.raises(AttributeError):
        records[0].payload = "mutado"  # type: ignore[misc]


def test_drain_empties_and_returns() -> None:
    dlq = DeadLetterQueue()
    dlq.submit("p1", "e1")
    dlq.submit("p2", "e2")
    drained = dlq.drain()
    assert len(drained) == 2
    assert len(dlq) == 0
    assert dlq.drain() == ()


def test_reset_clears() -> None:
    dlq = DeadLetterQueue()
    dlq.submit("p", "e")
    dlq.reset()
    assert len(dlq) == 0


def test_metric_increments_on_submit() -> None:
    metrics = MetricsRegistry()
    dlq = DeadLetterQueue(metrics=metrics)
    dlq.submit("p", "e")
    dlq.submit("p", "e")
    assert metrics.get(METRIC_DEAD_LETTERS) == 2.0


def test_max_records_bounds_and_drops_oldest() -> None:
    dlq = DeadLetterQueue(max_records=3)
    for i in range(5):
        dlq.submit(f"payload-{i}", f"error-{i}")
    assert len(dlq) == 3
    assert [r.error for r in dlq.records()] == ["error-2", "error-3", "error-4"]


def test_max_records_validation() -> None:
    with pytest.raises(ValueError, match="max_records"):
        DeadLetterQueue(max_records=0)
    with pytest.raises(ValueError, match="max_records"):
        DeadLetterQueue(max_records=-5)
