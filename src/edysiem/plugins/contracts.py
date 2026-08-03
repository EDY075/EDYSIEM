"""Contratos (protocolos) da camada de plugins do EDY SIEM."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

from ..domain import Alert, Notification, RawEvent
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


class PluginVersion(Protocol):
    """Versão semântica de um plugin."""


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
    """Converte bloco bruto em uma lista de ``RawEvent``."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def parse(self, raw: bytes | str) -> Result[list[RawEvent]]: ...


class CollectorPlugin(Protocol):
    """Coleta ``RawEvent`` de uma fonte externa."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    def collect(self) -> AsyncIterator[RawEvent]: ...


class AnalyzerPlugin(Protocol):
    """Analisa eventos e produz alertas."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def analyze(self, event: RawEvent) -> Result[list[Alert]]: ...


class EnrichmentPlugin(Protocol):
    """Enriquece um evento bruto com contexto adicional."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def enrich(self, event: RawEvent, context: dict[str, object]) -> RawEvent: ...


class ExporterPlugin(Protocol):
    """Exporta registros para um destino externo."""

    @property
    def name(self) -> str: ...

    @property
    def meta(self) -> PluginMeta: ...

    async def setup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def export(self, records: list[RawEvent]) -> ExportResult: ...


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
    "PluginVersion",
]