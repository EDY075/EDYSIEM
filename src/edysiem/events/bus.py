"""Barramento de eventos assíncrono do EDY SIEM."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, TypeVar, cast

from .base import CancellationToken, ElementHandler, Event, EventPriority
from .registry import EventRegistry

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class EventHandlerRef:
    """Referência ao handler que processou um evento."""

    handler_id: str
    event_type: str


@dataclass(frozen=True, slots=True)
class HandlerError:
    """Falha individual de um handler durante a publicação."""

    handler_id: str
    error: Exception


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Resultado da publicação de um único evento.

    Attributes:
        published: True se o evento foi encaminhado a pelo menos um handler
            executado com sucesso.
        handled: Referências dos handlers executados com sucesso.
        rejected: Lista de handlers que lançaram exceção.
        cancelled: True se a publicação foi interrompida por cancelamento.
        duration_ms: Duração da publicação em milissegundos.
    """

    published: bool
    handled: list[EventHandlerRef] = field(default_factory=list)
    rejected: list[HandlerError] = field(default_factory=list)
    cancelled: bool = False
    duration_ms: float = 0.0

    @property
    def has_errors(self) -> bool:
        return bool(self.rejected)


class EventBus:
    """Barramento de eventos não-singleton, instanciável via DI.

    Executa os handlers de um evento em ordem decrescente de prioridade,
    respeitando o ``CancellationToken``. Falhas individuais são coletadas e
    repassadas em ``PublishResult`` (nunca ``None``).
    """

    def __init__(self, registry: EventRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> EventRegistry:
        return self._registry

    def subscribe(
        self,
        handler: ElementHandler[Any],
        event_type: str,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> EventRegistry:
        self._registry.register(handler, event_type, priority)
        return self._registry

    async def publish(
        self,
        event: Event[T],
        cancel_token: CancellationToken | None = None,
    ) -> PublishResult:
        """Publica um evento e executa os handlers de forma assíncrona."""
        start = perf_counter()
        handled: list[EventHandlerRef] = []
        rejected: list[HandlerError] = []

        subscriptions = self._registry.handlers_for(event.type)
        for subscription in subscriptions:
            if cancel_token is not None and cancel_token.is_cancelled:
                return self._finish(start, handled, rejected, True)
            try:
                handler = cast(ElementHandler[Any], subscription.handler)
                await handler.handle(event)
                handled.append(EventHandlerRef(subscription.id, event.type))
            except Exception as exc:
                rejected.append(HandlerError(subscription.id, exc))

        duration = (perf_counter() - start) * 1000.0
        published = bool(handled)
        return PublishResult(
            published=published,
            handled=handled,
            rejected=rejected,
            cancelled=False,
            duration_ms=duration,
        )

    def publish_sync(
        self,
        event: Event[T],
        cancel_token: CancellationToken | None = None,
    ) -> PublishResult:
        """Executa ``publish`` em um loop de eventos próprio (uso síncrono)."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.publish(event, cancel_token))

        # Um loop já está rodando nesta thread; rodamos num thread isolado.
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(self.publish(event, cancel_token))).result()

    @staticmethod
    def _finish(
        start: float,
        handled: list[EventHandlerRef],
        rejected: list[HandlerError],
        cancelled: bool,
    ) -> PublishResult:
        """Monta o resultado de uma publicação interrompida por cancelamento.

        ``published`` reflete o mesmo contrato da publicação completa:
        ``True`` somente se pelo menos um handler executou com sucesso antes
        do cancelamento.
        """
        duration = (perf_counter() - start) * 1000.0
        return PublishResult(
            published=bool(handled),
            handled=handled,
            rejected=rejected,
            cancelled=cancelled,
            duration_ms=duration,
        )


__all__ = ["EventBus", "EventHandlerRef", "HandlerError", "PublishResult"]
