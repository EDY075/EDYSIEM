"""Especificações e cola de contratos da camada de plugins."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    AnalyzerPlugin,
    CollectorPlugin,
    EnrichmentPlugin,
    ExporterPlugin,
    NotificationPlugin,
    ParserPlugin,
    Plugin,
    PluginMeta,
    PluginType,
)


@dataclass(frozen=True, slots=True)
class PluginSpec:
    """Registro de especificação de um plugin contratado."""

    name: str
    plugin_type: PluginType
    required_capabilities: tuple[str, ...] = ()
    version: str = "*"
    description: str = ""


# Interface funcional exposta pela camada de plugins.
PluginContract = (
    Plugin
    | ParserPlugin
    | CollectorPlugin
    | AnalyzerPlugin
    | EnrichmentPlugin
    | ExporterPlugin
    | NotificationPlugin
)

__all__ = [
    "AnalyzerPlugin",
    "CollectorPlugin",
    "EnrichmentPlugin",
    "ExporterPlugin",
    "NotificationPlugin",
    "ParserPlugin",
    "Plugin",
    "PluginMeta",
    "PluginSpec",
    "PluginType",
    "plugin_contracts",
]


def plugin_contracts() -> tuple[type[object], ...]:
    """Retorna os protocolos contratados disponíveis na camada."""
    return (
        Plugin,
        ParserPlugin,
        CollectorPlugin,
        AnalyzerPlugin,
        EnrichmentPlugin,
        ExporterPlugin,
        NotificationPlugin,
    )