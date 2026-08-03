"""Primitivas de eventos: prioridade, ``Event``, ``CancellationToken`` e handler."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, TypeVar

from .._utils import new_id as _new_id
from .._utils import utcnow as _utcnow

T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)


class EventPriority(Enum):
    """Níveis de prioridade ordenados de um evento."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

    def __lt__(self, other: EventPriority) -> bool:
        if isinstance(other, EventPriority):
            return self.value < other.value
        return NotImplemented


@dataclass(frozen=True, slots=True)
class Event[T]:
    """Um evento imutável que trafega pelo barramento.

    Campos obrigatórios (``type``, ``payload``) vêm primeiro para satisfazer
    a restrição de ordenação de ``@dataclass``; os demais possuem defaults.

    Attributes:
        type: Nome/tipo canônico do evento (ex.: ``"alert.created"``).
        payload: Carga útil tipada transportada pelo evento.
        event_id: Identificador único do evento.
        created_at: Carimbo de tempo (UTC) da criação.
        priority: Prioridade de processamento.
        tags: Conjunto imutável de tags de contextualização.
    """

    type: str
    payload: T
    event_id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_utcnow)
    priority: EventPriority = EventPriority.NORMAL
    tags: frozenset[str] = field(default_factory=frozenset)


class CancellationToken:
    """Token de cooperação para cancelar a publicação de eventos.

    Seguro para uso síncrono e assíncrono. Uma vez cancelado, os handlers
    ainda não executados de uma publicação deixam de ser chamados.
    """

    __slots__ = ("_cancelled",)

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        """Marca o token como cancelado (irreversível)."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """``True`` quando o token já foi cancelado."""
        return self._cancelled

    def __bool__(self) -> bool:
        return self._cancelled

    async def __aenter__(self) -> CancellationToken:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class ElementHandler(Protocol[T_contra]):
    """Protocolo para um handler assíncrono de eventos."""

    async def handle(self, event: Event[T_contra]) -> None: ...


Handler = ElementHandler[object]


__all__ = [
    "CancellationToken",
    "ElementHandler",
    "Event",
    "EventPriority",
    "Handler",
]
