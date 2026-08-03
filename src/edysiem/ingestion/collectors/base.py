"""Contrato Enterprise de coletores de eventos brutos.

Define o protocolo oficial ``CollectorPlugin`` (desacoplado de parsers e de
qualquer plugin de negócio) e os tipos de suporte ``CollectorMetadata`` e
``CollectorCapability``. Um collector produz apenas ``RawEvent`` — a
transformação para ``ParsedEvent``/``CanonicalEvent`` é responsabilidade de
etapas posteriores da pipeline.

Este contrato substitui o antigo ``CollectorPlugin`` (setup/shutdown/collect)
de ``edysiem.plugins.contracts``, que agora apenas re-exporta este protocolo.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from ...domain import RawEvent

if TYPE_CHECKING:
    from ..health import CollectorHealth


class CollectorCapability(Enum):
    """Capacidades declaradas por um collector.

    Attributes:
        STREAMING: Entrega contínua via ``read()``.
        BATCH: Entrega em lotes.
        RECONNECT: Suporta reconexão automática.
        BACKPRESSURE: Coopera com o controle de backpressure.
        RATE_LIMIT: Respeita o rate limiter.
    """

    STREAMING = "streaming"
    BATCH = "batch"
    RECONNECT = "reconnect"
    BACKPRESSURE = "backpressure"
    RATE_LIMIT = "rate_limit"


@dataclass(frozen=True, slots=True)
class CollectorMetadata:
    """Metadados estáticos de um collector.

    Attributes:
        name: Identificador estável do collector.
        version: Versão semântica do collector.
        source_type: Tipo da fonte (ex.: ``"syslog"``, ``"file"``, ``"custom"``).
        description: Descrição legível opcional.
        capabilities: Capacidades declaradas pelo collector.
    """

    name: str
    version: str
    source_type: str
    description: str = ""
    capabilities: frozenset[CollectorCapability] = frozenset()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("name não pode ser vazio")
        if not self.version or not self.version.strip():
            raise ValueError("version não pode ser vazio")
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type não pode ser vazio")


@runtime_checkable
class CollectorPlugin(Protocol):
    """Coletor Enterprise: produz ``RawEvent`` e coopera com a infraestrutura.

    Nenhum collector conhece parser: a saída é sempre o evento bruto
    (``RawEvent``). O ciclo de vida é ``start``/``stop`` e o stream é
    consumido via ``read``. ``health`` expõe o estado observável e
    ``capabilities`` declara o que o collector suporta.
    """

    @property
    def metadata(self) -> CollectorMetadata:
        """Metadados estáticos do collector."""

    async def start(self) -> None:
        """Inicia a coleta (conexões, timers, recursos)."""

    async def stop(self) -> None:
        """Para a coleta graciosamente (libera recursos)."""

    def read(self) -> AsyncIterator[RawEvent]:
        """Stream de eventos brutos produzidos pelo collector."""

    async def health(self) -> CollectorHealth:
        """Snapshot de saúde do collector."""

    def capabilities(self) -> frozenset[CollectorCapability]:
        """Capacidades suportadas pelo collector."""


__all__ = ["CollectorCapability", "CollectorMetadata", "CollectorPlugin"]
