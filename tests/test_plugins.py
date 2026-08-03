"""Testes dos contratos e especificações de plugins."""

from __future__ import annotations

from edysiem.domain import RawEvent
from edysiem.plugins import (
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


class DummyParser:
    """Implementação de teste de um ParserPlugin."""

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

    async def parse(self, raw: bytes | str) -> object:
        return ok([RawEvent(source="dummy", raw_payload=raw)])


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


def test_runtime_checkable_protocol() -> None:
    parser = DummyParser()
    # Somente o protocolo base ``Plugin`` é @runtime_checkable.
    assert isinstance(parser, Plugin)
    # Os demais protocolos são verificáveis por atributos/assinatura.
    assert callable(parser.setup)
    assert callable(parser.shutdown)
    assert callable(parser.parse)


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
