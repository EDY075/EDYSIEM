"""Testes da fila FIFO thread-safe e async-ready (RawEventQueue)."""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

from edysiem.domain import RawEvent
from edysiem.ingestion.backpressure import BackpressureController
from edysiem.ingestion.dead_letter import DeadLetterQueue
from edysiem.ingestion.metrics import (
    METRIC_DEAD_LETTERS,
    METRIC_DROPS,
    METRIC_QUEUE_SIZE,
    MetricsRegistry,
)
from edysiem.ingestion.queue import DropPolicy, QueueConfig, RawEventQueue
from edysiem.result import ErrorCode


def _event(host: str = "host-1") -> RawEvent:
    return RawEvent(source_type="syslog", source_host=host, raw_payload=b"data")


def test_config_validation() -> None:
    with pytest.raises(ValueError, match="maxsize"):
        QueueConfig(maxsize=0)
    with pytest.raises(ValueError, match="maxsize"):
        QueueConfig(maxsize=-1)
    with pytest.raises(ValueError, match="put_timeout"):
        QueueConfig(put_timeout=-0.1)
    with pytest.raises(ValueError, match="get_timeout"):
        QueueConfig(get_timeout=-0.1)


def test_fifo_order_sync() -> None:
    queue = RawEventQueue()
    e1, e2, e3 = _event("a"), _event("b"), _event("c")
    assert queue.put_nowait(e1).is_ok()
    assert queue.put_nowait(e2).is_ok()
    assert queue.put_nowait(e3).is_ok()
    assert queue.get_nowait().event_id == e1.event_id
    assert queue.get_nowait().event_id == e2.event_id
    assert queue.get_nowait().event_id == e3.event_id


def test_fifo_order_async() -> None:
    e1, e2 = _event("a"), _event("b")

    async def scenario() -> tuple[str, str]:
        queue = RawEventQueue()
        assert (await queue.put(e1)).is_ok()
        assert (await queue.put(e2)).is_ok()
        first = await queue.get()
        second = await queue.get()
        return first.event_id, second.event_id

    first, second = asyncio.run(scenario())
    assert first == e1.event_id
    assert second == e2.event_id


def test_qsize_empty_full() -> None:
    queue = RawEventQueue(QueueConfig(maxsize=2))
    assert queue.empty()
    assert queue.qsize() == 0
    assert not queue.full()
    queue.put_nowait(_event())
    assert not queue.empty()
    assert queue.qsize() == 1
    queue.put_nowait(_event())
    assert queue.full()
    queue.get_nowait()
    assert not queue.full()


def test_get_nowait_empty_raises_queue_empty() -> None:
    queue = RawEventQueue()
    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()


def test_put_nowait_block_full_fails() -> None:
    queue = RawEventQueue(QueueConfig(maxsize=1, drop_policy=DropPolicy.BLOCK))
    assert queue.put_nowait(_event()).is_ok()
    result = queue.put_nowait(_event("b"))
    assert result.is_err()
    assert result.error.code is ErrorCode.QUEUE_FULL


def test_put_nowait_discard_policy() -> None:
    queue = RawEventQueue(QueueConfig(maxsize=1, drop_policy=DropPolicy.DISCARD))
    assert queue.put_nowait(_event()).is_ok()
    result = queue.put_nowait(_event("b"))
    assert result.is_ok()
    assert queue.qsize() == 1
    assert queue.metrics.get(METRIC_DROPS) == 1.0


def test_async_put_discard_policy() -> None:
    queue = RawEventQueue(QueueConfig(maxsize=1, drop_policy=DropPolicy.DISCARD))

    async def scenario() -> object:
        await queue.put(_event())
        return await queue.put(_event("b"))

    result = asyncio.run(scenario())
    assert result.is_ok()  # type: ignore[union-attr]
    assert queue.qsize() == 1
    assert queue.metrics.get(METRIC_DROPS) == 1.0


def test_put_nowait_dead_letter_policy() -> None:
    metrics = MetricsRegistry()
    dlq = DeadLetterQueue(metrics=metrics)
    queue = RawEventQueue(
        QueueConfig(maxsize=1, drop_policy=DropPolicy.DEAD_LETTER),
        dead_letter=dlq,
        metrics=metrics,
    )
    dropped = _event("b")
    assert queue.put_nowait(_event()).is_ok()
    result = queue.put_nowait(dropped)
    assert result.is_ok()
    assert queue.qsize() == 1
    assert len(dlq) == 1
    assert dlq.records()[0].payload.event_id == dropped.event_id  # type: ignore[union-attr]
    assert metrics.get(METRIC_DEAD_LETTERS) == 1.0


def test_dead_letter_policy_requires_dlq() -> None:
    with pytest.raises(ValueError, match="DEAD_LETTER"):
        RawEventQueue(QueueConfig(drop_policy=DropPolicy.DEAD_LETTER))


def test_async_put_dead_letter_policy() -> None:
    metrics = MetricsRegistry()
    dlq = DeadLetterQueue(metrics=metrics)
    queue = RawEventQueue(
        QueueConfig(maxsize=1, drop_policy=DropPolicy.DEAD_LETTER),
        dead_letter=dlq,
        metrics=metrics,
    )
    dropped = _event("b")

    async def scenario() -> object:
        await queue.put(_event())
        return await queue.put(dropped)

    result = asyncio.run(scenario())
    assert result.is_ok()  # type: ignore[union-attr]
    assert queue.qsize() == 1
    assert len(dlq) == 1
    assert dlq.records()[0].payload.event_id == dropped.event_id  # type: ignore[union-attr]
    assert metrics.get(METRIC_DEAD_LETTERS) == 1.0


def test_get_zero_timeout_raises_immediately() -> None:
    queue = RawEventQueue(QueueConfig(get_timeout=0))

    async def scenario() -> None:
        await queue.get()

    with pytest.raises(TimeoutError):
        asyncio.run(scenario())


def test_async_put_block_timeout_fails() -> None:
    queue = RawEventQueue(QueueConfig(maxsize=1, put_timeout=0.02))

    async def scenario() -> object:
        await queue.put(_event())
        return await queue.put(_event("b"))

    result = asyncio.run(scenario())
    assert result.is_err()  # type: ignore[union-attr]
    assert result.error.code is ErrorCode.QUEUE_FULL  # type: ignore[union-attr]


def test_get_timeout_raises() -> None:
    queue = RawEventQueue(QueueConfig(get_timeout=0.02))

    async def scenario() -> None:
        await queue.get()

    with pytest.raises(TimeoutError):
        asyncio.run(scenario())


def test_async_get_blocks_until_put() -> None:
    queue = RawEventQueue()
    event = _event()

    async def scenario() -> RawEvent:
        task = asyncio.create_task(queue.get())
        await asyncio.sleep(0.01)
        assert not task.done(), "get deveria bloquear até haver item"
        await queue.put(event)
        return await task

    got = asyncio.run(scenario())
    assert got.event_id == event.event_id


def test_async_put_blocks_until_space() -> None:
    queue = RawEventQueue(QueueConfig(maxsize=1))
    e1, e2 = _event("a"), _event("b")

    async def scenario() -> tuple[RawEvent, object]:
        await queue.put(e1)
        task = asyncio.create_task(queue.put(e2))
        await asyncio.sleep(0.01)
        assert not task.done(), "put BLOCK deveria aguardar espaço"
        got = await queue.get()
        result = await task
        return got, result

    got, result = asyncio.run(scenario())
    assert got.event_id == e1.event_id
    assert result.is_ok()  # type: ignore[union-attr]
    assert queue.qsize() == 1
    assert queue.get_nowait().event_id == e2.event_id


def test_sync_producer_wakes_async_consumer() -> None:
    queue = RawEventQueue()
    event = _event()

    def producer() -> None:
        time.sleep(0.1)
        queue.put_nowait(event)

    async def consume() -> RawEvent:
        return await queue.get()

    thread = threading.Thread(target=producer)
    thread.start()
    got = asyncio.run(consume())
    thread.join()
    assert got.event_id == event.event_id


def test_thread_safety_concurrent_put_nowait() -> None:
    queue = RawEventQueue()
    threads = 4
    per_thread = 100

    def worker(offset: int) -> None:
        for i in range(per_thread):
            queue.put_nowait(_event(f"h{offset + i}"))

    workers = [threading.Thread(target=worker, args=(i * per_thread,)) for i in range(threads)]
    for t in workers:
        t.start()
    for t in workers:
        t.join()
    assert queue.qsize() == threads * per_thread
    collected = {queue.get_nowait().source_host for _ in range(threads * per_thread)}
    assert len(collected) == threads * per_thread


def test_queue_size_gauge_metric() -> None:
    queue = RawEventQueue()
    queue.put_nowait(_event())
    queue.put_nowait(_event("b"))
    assert queue.metrics.get(METRIC_QUEUE_SIZE) == 2.0
    queue.get_nowait()
    assert queue.metrics.get(METRIC_QUEUE_SIZE) == 1.0


def test_reset_clears_queue() -> None:
    queue = RawEventQueue()
    queue.put_nowait(_event())
    queue.reset()
    assert queue.empty()
    assert queue.qsize() == 0
    assert queue.metrics.get(METRIC_QUEUE_SIZE) == 0.0


def test_put_backpressure_timeout_fails() -> None:
    backpressure = BackpressureController()
    backpressure.pause()
    queue = RawEventQueue(QueueConfig(put_timeout=0.02), backpressure=backpressure)

    result = asyncio.run(queue.put(_event()))
    assert result.is_err()
    assert result.error.code is ErrorCode.TIMEOUT


def test_put_waits_for_backpressure_resume() -> None:
    backpressure = BackpressureController()
    backpressure.pause()
    queue = RawEventQueue(backpressure=backpressure)
    event = _event()

    async def scenario() -> object:
        task = asyncio.create_task(queue.put(event))
        await asyncio.sleep(0.01)
        assert not task.done(), "put deveria aguardar o backpressure retomar"
        backpressure.resume()
        return await task

    result = asyncio.run(scenario())
    assert result.is_ok()  # type: ignore[union-attr]
    assert queue.qsize() == 1


def test_runtime_error_on_second_loop() -> None:
    queue = RawEventQueue()

    async def first() -> None:
        await queue.put(_event())

    asyncio.run(first())

    async def second() -> None:
        await queue.get()

    with pytest.raises(RuntimeError):
        asyncio.run(second())
