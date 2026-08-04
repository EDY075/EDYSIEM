"""Testes dos contratos e especificações de plugins."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime

from edysiem.domain import (
    CanonicalEvent,
    EnrichedEvent,
    Enrichment,
    ParsedEvent,
    RawEvent,
    Severity,
)
from edysiem.plugins import (
    CollectorPlugin,
    ExportResult,
    NotifyResult,
    ParserPlugin,
    Plugin,
    PluginMeta,
    PluginSpec,
    PluginType,
    plugin_contracts,
)
from edysiem.result import ok


def _enriched_from_canonical(
    event: CanonicalEvent, enrichments: tuple[Enrichment, ...]
) -> EnrichedEvent:
    """Deriva um ``EnrichedEvent`` de um ``CanonicalEvent`` sem mutação.

    ``dataclasses.replace`` não funciona para subclasses com campos novos a
    partir da instância base; usamos ``asdict`` + construção explícita.
    """
    return EnrichedEvent(**asdict(event), enrichments=enrichments)


def _parsed_from_raw(event: RawEvent) -> ParsedEvent:
    """Constrói um ``ParsedEvent`` derivado de um ``RawEvent`` de teste."""
    return ParsedEvent(
        event_id=event.event_id,
        timestamp=datetime.now(UTC),
        source_type=event.source_type,
        source_host=event.source_host,
        event_category="auth",
        event_action="logon",
        fields={"user": "admin"},
        raw=event.raw_payload,
        trace_id="trace-test",
    )


def _canonical() -> CanonicalEvent:
    return CanonicalEvent(
        event_id="evt-1",
        trace_id="trace-test",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="windows",
        source_host="wks-01",
        event_category="auth",
        event_action="logon",
        severity=Severity.MEDIUM,
    )


class DummyParser:
    """Implementação de teste de um ``ParserPlugin`` (novo contrato)."""

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(name="dummy", version="1.0.0", plugin_type=PluginType.PARSER)

    async def setup(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def parse(self, event: RawEvent) -> object:
        return ok([_parsed_from_raw(event)])


class DummyEnricher:
    """Implementação de teste de um ``EnrichmentPlugin`` (novo contrato)."""

    @property
    def name(self) -> str:
        return "dummy-enricher"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(name="dummy-enricher", version="1.0.0", plugin_type=PluginType.ENRICHMENT)

    async def setup(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def enrich(self, event: CanonicalEvent, context: dict[str, object]) -> object:
        enrichment = Enrichment(
            kind="asset", provider="asset-db", data={"owner": context.get("owner", "")}
        )
        return ok(_enriched_from_canonical(event, (enrichment,)))


def test_plugin_type_values() -> None:
    assert PluginType.PARSER.value == "parser"
    assert PluginType.NOTIFICATION.value == "notification"
    assert PluginType.OTHER.value == "other"


def test_plugin_meta() -> None:
    meta = PluginMeta(name="p", version="2.0.0", plugin_type=PluginType.ANALYZER)
    assert meta.enabled is True
    assert meta.description == ""


def test_export_result() -> None:
    success = ExportResult(exported=3)
    assert success.success is True
    failed = ExportResult(exported=1, errors=["boom"])
    assert failed.success is False


def test_notify_result() -> None:
    result = NotifyResult(delivered=True, message_id="m-1")
    assert result.delivered is True
    assert result.message_id == "m-1"


def test_plugin_contracts_list() -> None:
    contracts = plugin_contracts()
    assert Plugin in contracts
    assert ParserPlugin in contracts
    assert len(contracts) == 7


def test_collector_plugin_is_enterprise_contract() -> None:
    """O ``CollectorPlugin`` re-exportado é o contrato Enterprise de ingestion.

    Sprint 2.2 removeu o protocolo antigo (setup/shutdown/collect) e passou a
    re-exportar ``edysiem.ingestion.collectors.base.CollectorPlugin``.
    """
    from edysiem.ingestion.collectors.base import CollectorPlugin as EnterpriseCollector

    assert CollectorPlugin is EnterpriseCollector
    assert hasattr(CollectorPlugin, "metadata")
    assert hasattr(CollectorPlugin, "start")
    assert hasattr(CollectorPlugin, "stop")
    assert hasattr(CollectorPlugin, "read")
    assert hasattr(CollectorPlugin, "health")
    assert hasattr(CollectorPlugin, "capabilities")


def test_runtime_checkable_protocol() -> None:
    parser = DummyParser()
    # Somente o protocolo base ``Plugin`` é @runtime_checkable.
    assert isinstance(parser, Plugin)
    # Os demais protocolos são verificáveis por atributos/assinatura.
    assert callable(parser.setup)
    assert callable(parser.shutdown)
    assert callable(parser.parse)


def test_parser_contract_accepts_raw_event() -> None:
    raw = RawEvent(source_type="windows", source_host="wks-01", raw_payload=b"4624")
    parsed = _parsed_from_raw(raw)
    assert parsed.event_id == raw.event_id
    assert parsed.source_type == raw.source_type
    assert parsed.event_category == "auth"
    assert parsed.raw == b"4624"


def test_enricher_contract_accepts_canonical_event() -> None:
    enricher = DummyEnricher()
    canonical = _canonical()
    result = asyncio.run(enricher.enrich(canonical, {"owner": "sec"}))
    enriched = result.unwrap()
    assert isinstance(enriched, EnrichedEvent)
    assert enriched.event_id == canonical.event_id
    assert len(enriched.enrichments) == 1
    assert enriched.enrichments[0].data == {"owner": "sec"}
    assert enricher.meta.plugin_type is PluginType.ENRICHMENT


def test_plugin_spec() -> None:
    spec = PluginSpec(
        name="windows-parser",
        plugin_type=PluginType.PARSER,
        required_capabilities=("windows_event",),
        version=">=1.0",
        description="Parser de logs do Windows",
    )
    assert spec.name == "windows-parser"
    assert spec.required_capabilities == ("windows_event",)
    assert spec.version == ">=1.0"
