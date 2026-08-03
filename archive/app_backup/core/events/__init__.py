"""Event Bus interno — publisher/subscriber, eventos tipados, prioridade, cancelamento.

Sem dependências externas. Síncrono na base, com API compatível com async futuro.
"""

from __future__ import annotations

import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Protocol

from app.core.models import utc_now


class Priority(IntEnum):
    HIGH = 0
    NORMAL = 10
    LOW = 20


@dataclass(frozen=True)
class DomainEvent:
    """Evento de domínio tipado."""

    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    occurred_at: datetime = field(default_factory=utc_now)
    event_id: str = field(default_factory=lambda: f"evd_{uuid.uuid4().hex[:12]}")
    priority: Priority = Priority.NORMAL


EventHandler = Callable[[DomainEvent], None]


class EventRegistry:
    """Registro de tipos de evento e seus schemas (sem execução)."""

    def __init__(self) -> None:
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(self, event_type: str, schema: dict[str, Any] | None = None) -> None:
        if event_type in self._schemas:
            raise ValueError(f"event_type já registrado: {event_type}")
        self._schemas[event_type] = schema or {}

    def has(self, event_type: str) -> bool:
        return event_type in self._schemas

    def schema(self, event_type: str) -> dict[str, Any] | None:
        return self._schemas.get(event_type)


class Subscription:
    """Assinatura com suporte a cancelamento."""

    def __init__(self, event_type: str, handler: EventHandler, bus: "EventBus") -> None:
        self.event_type = event_type
        self.handler = handler
        self._bus = bus
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        self._bus._remove(self)  # noqa: SLF001

    @property
    def cancelled(self) -> bool:
        return self._cancelled


class EventBus:
    """Bus síncrono com prioridade e cancelamento."""

    def __init__(self, registry: EventRegistry | None = None) -> None:
        self._registry = registry or EventRegistry()
        self._subscribers: dict[str, list[Subscription]] = {}
        self._counter = itertools.count()

    def register_type(self, event_type: str, schema: dict[str, Any] | None = None) -> None:
        self._registry.register(event_type, schema)

    def subscribe(self, event_type: str, handler: EventHandler) -> Subscription:
        self._subscribers.setdefault(event_type, [])
        sub = Subscription(event_type, handler, self)
        self._subscribers[event_type].append(sub)
        return sub

    def _remove(self, sub: Subscription) -> None:
        subs = self._subscribers.get(sub.event_type, [])
        if sub in subs:
            subs.remove(sub)

    def publish(self, event: DomainEvent) -> None:
        subs = list(self._subscribers.get(event.event_type, []))
        # Ordena por prioridade (menor = mais alta) mantendo ordem de inscrição
        ordered = sorted(subs, key=lambda s: (event.priority, next(self._counter)))
        for sub in ordered:
            if sub.cancelled:
                continue
            sub.handler(event)

    def handler_count(self, event_type: str) -> int:
        return len(self._subscribers.get(event_type, []))


@dataclass
class PendingEvent:
    """Evento agendado com prioridade (para fila de processamento futuro)."""

    event: DomainEvent
    scheduled_at: datetime = field(default_factory=utc_now)
    seq: int = field(default_factory=itertools.count().__next__)

    def __lt__(self, other: "PendingEvent") -> bool:
        return (self.event.priority, self.seq) < (other.event.priority, other.seq)


class PriorityQueue:
    """Fila de eventos por prioridade (min-heap)."""

    def __init__(self) -> None:
        self._heap: list[PendingEvent] = []

    def push(self, event: DomainEvent) -> None:
        heapq.heappush(self._heap, PendingEvent(event))

    def pop(self) -> DomainEvent | None:
        if not self._heap:
            return None
        return heapq.heappop(self._heap).event

    def __len__(self) -> int:
        return len(self._heap)
