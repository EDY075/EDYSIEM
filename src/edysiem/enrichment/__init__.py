"""Enrichment Engine do EDY SIEM.

Framework Enterprise para enriquecimento de eventos canônicos.
Desacoplado, extensível e preparado para dezenas de plugins.

Arquitetura:
- ``EnrichmentPlugin`` (Protocol): contrato do plugin de enriquecimento
- ``PluginMetadata``: metadados declarativos do plugin (id, versão, prioridade, etc.)
- ``EnrichmentRegistry``: descoberta, registro e ordenação por prioridade
- ``EnrichmentContext``: contexto compartilhado (asset DB, geo, intel, cache)
- ``EnrichmentEngine``: execução do pipeline com isolamento de falhas, métricas

Exemplo de uso:
    from edysiem.enrichment import EnrichmentEngine, EnrichmentRegistry
    from edysiem.enrichment.plugins import AssetEnricher, GeoEnricher

    registry = EnrichmentRegistry()
    registry.register(AssetEnricher())
    registry.register(GeoEnricher())

    engine = EnrichmentEngine(registry)
    enriched = await engine.enrich(canonical_event)

Plugins de enriquecimento reais (asset, geo, threat intel) são implementados
em sprints futuras sobre este framework.
"""

from .base import (
    EnrichmentPlugin,
    PluginMetadata,
    PluginPriority,
    PluginResult,
)
from .context import EnrichmentContext
from .engine import EnrichmentEngine, EnrichmentMetrics
from .exceptions import (
    EnrichmentError,
    EnrichmentTimeoutError,
    PluginNotFoundError,
)
from .models import (
    CachePolicy,
    Enrichment,
    EnrichmentKind,
    EnrichmentResult,
)
from .registry import EnrichmentRegistry

__all__ = [
    "CachePolicy",
    "Enrichment",
    "EnrichmentContext",
    "EnrichmentEngine",
    "EnrichmentError",
    "EnrichmentKind",
    "EnrichmentMetrics",
    "EnrichmentPlugin",
    "EnrichmentRegistry",
    "EnrichmentResult",
    "EnrichmentTimeoutError",
    "PluginMetadata",
    "PluginNotFoundError",
    "PluginPriority",
    "PluginResult",
]
