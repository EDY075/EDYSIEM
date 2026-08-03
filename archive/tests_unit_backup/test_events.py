"""Testes do Event Bus."""

import pytest

from app.core.events import DomainEvent, EventBus, EventRegistry, Priority, PriorityQueue, Subscription


def test_registry_register() -> None:
    reg = EventRegistry()
    reg.register("event.normalized", {"x": int})
    assert reg.has("event.normalized")
    assert reg.schema("event.normalized") == {"x": int}


def test_registry_duplicate() -> None:
    reg = EventRegistry()
    reg.register("a")
    with pytest.raises(ValueError):
        reg.register("a")


def test_publish_calls_handler() -> None:
    bus = EventBus()
    received: list[str] = []
    bus.register_type("event.normalized")
    bus.subscribe("event.normalized", lambda e: received.append(e.event_type))
    bus.publish(DomainEvent(event_type="event.normalized"))
    assert received == ["event.normalized"]


def test_subscription_cancel() -> None:
    bus = EventBus()
    received: list[str] = []
    bus.register_type("a")
    sub = bus.subscribe("a", lambda e: received.append("x"))
    sub.cancel()
    bus.publish(DomainEvent(event_type="a"))
    assert received == []
    assert sub.cancelled


def test_priority_order() -> None:
    bus = EventBus()
    order: list[str] = []
    bus.register_type("evt")
    bus.subscribe("evt", lambda e: order.append(str(e.priority)))
    bus.publish(DomainEvent(event_type="evt", priority=Priority.LOW))
    bus.publish(DomainEvent(event_type="evt", priority=Priority.HIGH))
    assert order == ["0", "20"]


def test_handler_count() -> None:
    bus = EventBus()
    bus.register_type("a")
    bus.subscribe("a", lambda e: None)
    bus.subscribe("a", lambda e: None)
    assert bus.handler_count("a") == 2


def test_priority_queue() -> None:
    q = PriorityQueue()
    q.push(DomainEvent(event_type="a", priority=Priority.LOW))
    q.push(DomainEvent(event_type="b", priority=Priority.HIGH))
    q.push(DomainEvent(event_type="c", priority=Priority.NORMAL))
    assert len(q) == 3
    assert q.pop().event_type == "b"
    assert q.pop().event_type == "c"
    assert q.pop().event_type == "a"
    assert q.pop() is None


def test_event_ids_unique() -> None:
    e1 = DomainEvent(event_type="a")
    e2 = DomainEvent(event_type="a")
    assert e1.event_id != e2.event_id


def test_domain_event_immutable() -> None:
    e = DomainEvent(event_type="a")
    with pytest.raises(Exception):
        e.payload["x"] = 1  # type: ignore[index]
