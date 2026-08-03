"""Contratos (protocolos) da camada de plugins do EDY SIEM.

O contrato oficial de ``CollectorPlugin`` vive em
``edysiem.ingestion.collectors.base`` (Enterprise: ``start``/``stop``/
``read``/``health``/``capabilities``). Este módulo re-exporta o contrato para
preservar a API da camada de plugins — nenhum collector real implementa o
protocolo antigo (``setup``/``shutdown``/``collect``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

from ..domain import (
    Alert,
    CanonicalEvent,
    EnrichedEvent,
    Notification,
    ParsedEvent,
    RawEvent,
)
from ..ingestion.collectors.base import CollectorPlugin
from ..result import Result


class PluginType(Enum):
    """Classificação funcional de um plugin."""

    PARSER = "parser"
    COLLECTOR = "collector"
    ANALYZER = "analyzer"
    ENRICHMENT = "enrichment"
    EXPORTER = "exporter"
    NOTIFICATION = "notification"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class PluginMeta:
    """Metadados estáticos de um plugin."""

    name: str
    version: str
    plugin_type: PluginType
    description: str = ""
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ExportResult:
    """Resultado de um export."""

    exported: int
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class NotifyResult:
    """Resultado de uma notificação enviada."""

    delivered: bool
    message_id: str | None = None


@runtime_checkable
class Plugin(Protocol):
    """Contrato base de todo plugin: identificação + ciclo de vida."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...


class ParserPlugin(Protocol):
    """Converte um ``RawEvent`` em uma lista de ``ParsedEvent``.

    Recebe o evento bruto emitido pelo Collector e produz eventos com
    campos estruturados extraídos do payload.
    """

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def parse(self, event: RawEvent) -> Result[list[ParsedEvent]]: ...


class AnalyzerPlugin(Protocol):
    """Analisa eventos enriquecidos e produz alertas."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def analyze(self, event: EnrichedEvent) -> Result[list[Alert]]: ...


class EnrichmentPlugin(Protocol):
    """Enriquece um ``CanonicalEvent`` com contexto adicional.

    Recebe o evento normalizado e retorna um ``EnrichedEvent`` com os
    ``Enrichment`` anexados — nunca muta o evento de entrada.
    """

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def enrich(
        self, event: CanonicalEvent, context: dict[str, object]
    ) -> Result[EnrichedEvent]: ...


class ExporterPlugin(Protocol):
    """Exporta eventos normalizados para um destino externo."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def export(self, records: list[CanonicalEvent]) -> ExportResult: ...


class NotificationPlugin(Protocol):
    """Entrega notificações a um canal (email, webhook, ...)."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def notify(self, notification: Notification) -> NotifyResult: ...


__all__ = [
    "AnalyzerPlugin",
    "CollectorPlugin",
    "EnrichmentPlugin",
    "ExportResult",
    "ExporterPlugin",
    "NotificationPlugin",
    "NotifyResult",
    "ParserPlugin",
    "Plugin",
    "PluginMeta",
    "PluginType",
]
