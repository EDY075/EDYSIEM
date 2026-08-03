"""Testes do Event Bus: primitivas, registro, prioridade, cancelamento e sync."""

from __future__ import annotations

import asyncio

import pytest

from edysiem.events import (
    CancellationToken,
    ElementHandler,
    Event,
    EventBus,
    EventPriority,
    EventRegistry,
    PublishResult,
)
from edysiem.exceptions import DomainException, PluginException


class RecordingHandler:
    """Handler de teste que registra os eventos recebidos."""

    def __init__(self, name: str = "rec") -> None:
        self.name = name
        self.received: list[str] = []

    async def handle(self, event: Event[str]) -> None:
        self.received.append(event.payload)


class FailingHandler:
    """Handler de teste que sempre lança exceção."""

    async def handle(self, event: Event[str]) -> None:
        raise RuntimeError("handler falhou")


def make_event(payload: str = "x", priority: EventPriority = EventPriority.NORMAL) -> Event[str]:
    return Event(type="test.event", payload=payload, priority=priority)


def test_event_defaults() -> None:
    event = make_event()
    assert event.event_id
    assert event.created_at is not None
    assert event.priority is EventPriority.NORMAL
    assert event.tags == frozenset()
    assert event.type == "test.event"
    assert event.payload == "x"


def test_event_priority_order() -> None:
    assert EventPriority.LOW < EventPriority.HIGH
    assert EventPriority.CRITICAL > EventPriority.NORMAL


def test_cancellation_token() -> None:
    token = CancellationToken()
    assert not token.is_cancelled
    assert not token
    token.cancel()
    assert token.is_cancelled
    assert token


def test_cancellation_token_async_context() -> None:
    async def inner() -> bool:
        async with CancellationToken() as token:
            return token.is_cancelled

    assert asyncio.run(inner()) is False


def test_registry_register_and_unsubscribe() -> None:
    registry = EventRegistry()
    handler = RecordingHandler()
    sub = registry.register(handler, "a.b", priority=EventPriority.HIGH)
    assert sub.enabled is True
    assert registry.handlers_for("a.b") == [sub]
    assert registry.subjects == frozenset({"a.b"})
    assert len(registry) == 1
    registry.unsubscribe(handler, "a.b")
    assert len(registry) == 0


def test_registry_duplicate_handler_raises() -> None:
    registry = EventRegistry()
    handler = RecordingHandler()
    registry.register(handler, "a.b")
    with pytest.raises(DomainException):
        registry.register(handler, "a.b")


def test_registry_empty_type_raises() -> None:
    registry = EventRegistry()
    with pytest.raises(PluginException):
        registry.register(RecordingHandler(), "  ")


def test_registry_unsubscribe_missing_raises() -> None:
    registry = EventRegistry()
    with pytest.raises(PluginException):
        registry.unsubscribe(RecordingHandler(), "a.b")


def test_registry_disable_enable() -> None:
    registry = EventRegistry()
    handler = RecordingHandler()
    registry.register(handler, "a.b")
    disabled = registry.disable(handler, "a.b")
    assert disabled.enabled is False
    assert registry.handlers_for("a.b") == []
    enabled = registry.unable("a.b", handler)
    assert enabled.enabled is True
    assert len(registry.handlers_for("a.b")) == 1


def test_registry_disable_missing_and_already_disabled() -> None:
    registry = EventRegistry()
    handler = RecordingHandler()
    with pytest.raises(PluginException):
        registry.disable(handler, "a.b")
    registry.register(handler, "a.b")
    registry.disable(handler, "a.b")
    with pytest.raises(DomainException):
        registry.disable(handler, "a.b")
    with pytest.raises(KeyError):
        registry.unable("nope", handler)


def test_bus_publish_orders_by_priority() -> None:
    async def inner() -> list[str]:
        bus = EventBus(EventRegistry())
        order: list[str] = []

        class PrioHandler:
            def __init__(self, tag: str) -> None:
                self.tag = tag

            async def handle(self, event: Event[str]) -> None:
                order.append(self.tag)

        bus.subscribe(PrioHandler("low"), "t", priority=EventPriority.LOW)
        bus.subscribe(PrioHandler("high"), "t", priority=EventPriority.HIGH)
        await bus.publish(Event(type="t", payload="x", priority=EventPriority.HIGH))
        return order

    # Prioridade decrescente: HIGH (2) antes de LOW (0).
    assert asyncio.run(inner()) == ["high", "low"]


def test_bus_publish_success_and_result() -> None:
    async def inner() -> PublishResult:
        bus = EventBus(EventRegistry())
        h1 = RecordingHandler("h1")
        bus.subscribe(h1, "test.event", priority=EventPriority.HIGH)
        return await bus.publish(make_event("hello"))

    result = asyncio.run(inner())
    assert isinstance(result, PublishResult)
    assert result.published
    assert len(result.handled) == 1
    assert not result.rejected
    assert not result.cancelled
    assert result.duration_ms >= 0
    assert result.has_errors is False


def test_bus_publish_captures_handler_errors() -> None:
    async def inner() -> PublishResult:
        bus = EventBus(EventRegistry())
        ok_handler = RecordingHandler("ok")
        failing = FailingHandler()
        bus.subscribe(ok_handler, "test.event", priority=EventPriority.HIGH)
        bus.subscribe(failing, "test.event", priority=EventPriority.LOW)
        return await bus.publish(make_event())

    result = asyncio.run(inner())
    assert len(result.rejected) == 1
    assert result.handled
    assert result.has_errors


def test_bus_publish_respects_cancel_token() -> None:
    async def inner() -> PublishResult:
        bus = EventBus(EventRegistry())
        first = RecordingHandler("first")
        second = RecordingHandler("second")
        bus.subscribe(first, "test.event", priority=EventPriority.HIGH)
        bus.subscribe(second, "test.event", priority=EventPriority.LOW)

        token = CancellationToken()

        class CancelAfterFirst(ElementHandler[str]):
            async def handle(self, event: Event[str]) -> None:
                token.cancel()

        bus.subscribe(CancelAfterFirst(), "test.event", priority=EventPriority.CRITICAL)
        return await bus.publish(make_event(), cancel_token=token)

    result = asyncio.run(inner())
    assert result.cancelled
    assert result.duration_ms >= 0


def test_bus_publish_no_subscribers() -> None:
    async def inner() -> PublishResult:
        bus = EventBus(EventRegistry())
        return await bus.publish(make_event())

    result = asyncio.run(inner())
    assert result.handled == []
    assert not result.rejected
    assert result.cancelled is False


def test_bus_publish_sync() -> None:
    bus = EventBus(EventRegistry())
    handler = RecordingHandler("sync")
    bus.subscribe(handler, "test.event")
    result = bus.publish_sync(make_event("sync"))
    assert result.published
    assert handler.received == ["sync"]


def test_bus_publish_sync_with_running_loop() -> None:
    bus = EventBus(EventRegistry())
    handler = RecordingHandler("loop")
    bus.subscribe(handler, "test.event")

    async def inner() -> PublishResult:
        # Loop já rodando nesta thread -> usa ThreadPoolExecutor.
        return bus.publish_sync(make_event("thread"))

    result = asyncio.run(inner())
    assert result.published
    assert handler.received == ["thread"]


def test_registry_iter() -> None:
    registry = EventRegistry()
    registry.register(RecordingHandler("i"), "x.y")
    assert any(event_type == "x.y" for event_type, _ in registry)
