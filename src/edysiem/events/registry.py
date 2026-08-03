"""Registro de assinaturas de handlers por tipo de evento."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from ..exceptions import DomainException, PluginException
from .base import ElementHandler, EventPriority

# O registro associa um handler concreto (object) a uma assinatura.
HandlerKey = object


@dataclass(frozen=True, slots=True)
class EventSubscription:
    """Assinatura de um handler para um tipo de evento."""

    priority: EventPriority
    id: str
    enabled: bool
    handler: HandlerKey


Subject = str


class EventRegistry:
    """Data-class central que mapeia ``event_type -> {handler: assinatura}``."""

    def __init__(self) -> None:
        self._subscriptions: dict[Subject, dict[HandlerKey, EventSubscription]] = {}

    def register(
        self,
        handler: ElementHandler[Any],
        event_type: str,
        priority: EventPriority = EventPriority.NORMAL,
        enabled: bool = True,
    ) -> EventSubscription:
        """Registra um handler e retorna sua assinatura.

        Raises:
            PluginException: se o handler já estiver registrado para o tipo.
        """
        if not event_type or not event_type.strip():
            raise PluginException("event_type não pode ser vazio")
        subscription = EventSubscription(
            priority=priority,
            id=f"{type(handler).__name__}.{event_type}",
            enabled=enabled,
            handler=handler,
        )
        bucket = self._subscriptions.setdefault(event_type, {})
        if handler in bucket:
            raise DomainException(f"handler já registrado para o tipo {event_type!r}")
        bucket[handler] = subscription
        return subscription

    def unsubscribe(self, handler: ElementHandler[Any], event_type: str) -> EventSubscription:
        """Remove a assinatura de um handler.

        Raises:
            PluginException: se não houver assinatura para remover.
        """
        bucket = self._subscriptions.get(event_type)
        if bucket is None or handler not in bucket:
            raise PluginException(f"Nenhuma assinatura para o handler do tipo {event_type!r}")
        subscription = bucket.pop(handler)
        if not bucket:
            del self._subscriptions[event_type]
        return subscription

    def handlers_for(self, event_type: str) -> list[EventSubscription]:
        """Retorna assinaturas habilitadas ordenadas por prioridade decrescente."""
        bucket = self._subscriptions.get(event_type, {})
        subs = [s for s in bucket.values() if s.enabled]
        subs.sort(key=lambda s: s.priority.value, reverse=True)
        return subs

    def disable(self, handler: ElementHandler[Any], event_type: str) -> EventSubscription:
        """Desabilita a assinatura de um handler."""
        bucket = self._subscriptions.get(event_type)
        if bucket is None or handler not in bucket:
            raise PluginException(f"handler não encontrado para {event_type!r}")
        current = bucket[handler]
        if not current.enabled:
            raise DomainException("assinatura já está desabilitada")
        updated = EventSubscription(
            priority=current.priority,
            id=current.id,
            enabled=False,
            handler=handler,
        )
        bucket[handler] = updated
        return updated

    def unable(self, event_type: str, handler: ElementHandler[Any]) -> EventSubscription:
        """Reabilita uma assinatura desabilitada."""
        bucket = self._subscriptions.get(event_type)
        if bucket is None or handler not in bucket:
            raise KeyError(f"handler não encontrado para {event_type!r}")
        current = bucket[handler]
        updated = EventSubscription(
            priority=current.priority,
            id=current.id,
            enabled=True,
            handler=handler,
        )
        bucket[handler] = updated
        return updated

    @property
    def subjects(self) -> frozenset[str]:
        """Tipos (assuntos) de evento atualmente registrados."""
        return frozenset(self._subscriptions)

    def __len__(self) -> int:
        return sum(len(bucket) for bucket in self._subscriptions.values())

    def __iter__(self) -> Iterator[tuple[str, dict[HandlerKey, EventSubscription]]]:
        return iter(self._subscriptions.items())


__all__ = ["EventRegistry", "EventSubscription"]