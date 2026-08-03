"""Contratos de plugins — Protocols para coletores, parsers, enrichers, etc."""

from __future__ import annotations

from typing import Any, Protocol

from app.core.models import CanonicalEvent, Ioc, Severity
from app.core.result import Result


class Plugin(Protocol):
    """Contrato base de um plugin."""

    name: str

    def metadata(self) -> dict[str, Any]:
        ...


class ParserPlugin(Protocol):
    """Extrai campos estruturados de um payload bruto."""

    name: str
    source_types: tuple[str, ...]

    def parse(self, source_type: str, payload: str) -> Result[dict[str, Any]]:
        ...


class CollectorPlugin(Protocol):
    """Conecta a uma fonte e produz eventos brutos."""

    name: str

    def collect(self) -> Result[list[dict[str, Any]]]:
        ...


class AnalyzerPlugin(Protocol):
    """Analisa um evento e devolve achados (ex.: entropia, string)."""

    name: str

    def analyze(self, event: CanonicalEvent) -> Result[dict[str, Any]]:
        ...


class EnrichmentPlugin(Protocol):
    """Adiciona contexto a um evento (derivado, imutável)."""

    name: str

    def enrich(self, event: CanonicalEvent) -> Result[dict[str, Any]]:
        ...


class ExporterPlugin(Protocol):
    """Exporta dados (JSON/MD)."""

    name: str
    formats: tuple[str, ...]

    def export(self, data: dict[str, Any], fmt: str) -> Result[str]:
        ...


class NotificationPlugin(Protocol):
    """Envia notificações (email/webhook)."""

    name: str

    def notify(self, target: str, subject: str, body: str) -> Result[None]:
        ...


class IocProvider(Protocol):
    """Fonte de IOCs (threat intel)."""

    name: str

    def provide(self) -> Result[list[Ioc]]:
        ...


class SeverityClassifier(Protocol):
    """Classifica severidade de eventos/alertas."""

    name: str

    def classify(self, event: CanonicalEvent) -> Severity:
        ...
