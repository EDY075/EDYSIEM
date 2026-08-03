"""Sistema de eventos: primitivas, registro e barramento."""

from .base import CancellationToken, ElementHandler, Event, EventPriority, Handler
from .bus import EventBus, EventHandlerRef, HandlerError, PublishResult
from .registry import EventRegistry, EventSubscription

__all__ = [
    "CancellationToken",
    "ElementHandler",
    "Event",
    "EventBus",
    "EventHandlerRef",
    "EventPriority",
    "EventRegistry",
    "EventSubscription",
    "Handler",
    "HandlerError",
    "PublishResult",
]
