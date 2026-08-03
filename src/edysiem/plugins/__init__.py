"""Contratos e especificações da camada de plugins."""

from .contracts import (
    AnalyzerPlugin,
    CollectorPlugin,
    EnrichmentPlugin,
    ExporterPlugin,
    ExportResult,
    NotificationPlugin,
    NotifyResult,
    ParserPlugin,
    Plugin,
    PluginMeta,
    PluginType,
)
from .specs import PluginSpec, plugin_contracts

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
    "PluginSpec",
    "PluginType",
    "plugin_contracts",
]