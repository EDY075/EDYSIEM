"""Modelos do Enrichment Engine.

Define os value objects e resultados do processo de enriquecimento.
Todos imutáveis (frozen=True, slots=True) seguindo o padrão do projeto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .._utils import utcnow as _utcnow


class EnrichmentKind(Enum):
    """Categoria do enriquecimento aplicado."""

    ASSET = "asset"
    GEO = "geo"
    THREAT_INTEL = "threat_intel"
    USER = "user"
    PROCESS = "process"
    NETWORK = "network"
    CUSTOM = "custom"


class CachePolicy(Enum):
    """Política de cache para o enriquecimento."""

    NONE = "none"
    TTL = "ttl"
    ETERNAL = "eternal"


@dataclass(frozen=True, slots=True)
class Enrichment:
    """Value object de contexto enriquecido anexado a um evento.

    Produzido por um ``EnrichmentPlugin`` e agregado em ``EnrichedEvent``.

    Attributes:
        kind: Categoria do enriquecimento.
        provider: Provedor da informação (ex.: ``"asset-db"``, ``"maxmind"``).
        data: Dados estruturados do enriquecimento.
        created_at: Carimbo de tempo (UTC) de criação.
        cache_policy: Política de cache aplicável.
        ttl_seconds: Tempo de vida do cache (se aplicável).
    """

    kind: EnrichmentKind
    provider: str
    data: dict[str, Any]
    created_at: datetime = field(default_factory=_utcnow)
    cache_policy: CachePolicy = CachePolicy.NONE
    ttl_seconds: int | None = None

    def __post_init__(self) -> None:
        if not self.kind:
            raise ValueError("kind não pode ser vazio")
        if not self.provider or not self.provider.strip():
            raise ValueError("provider não pode ser vazio")
        if self.cache_policy == CachePolicy.TTL and (
            self.ttl_seconds is None or self.ttl_seconds <= 0
        ):
            raise ValueError("TTL deve ser > 0 quando cache_policy=TLL")


@dataclass(frozen=True, slots=True)
class EnrichmentResult:
    """Resultado da execução de um plugin de enriquecimento.

    Attributes:
        success: Se o enriquecimento foi bem-sucedido.
        enrichments: Tupla de enriquecimentos aplicados (vazio se falhou).
        error: Mensagem de erro se ``success=False``.
        duration_ms: Tempo de execução em milissegundos.
        plugin_name: Nome do plugin que executou.
    """

    success: bool
    enrichments: tuple[object, ...] = ()
    error: str | None = None
    duration_ms: float = 0.0
    plugin_name: str = ""

    @classmethod
    def ok(
        cls,
        enrichments: tuple[object, ...],
        duration_ms: float,
        plugin_name: str,
    ) -> EnrichmentResult:
        """Cria um resultado de sucesso."""
        return cls(
            success=True,
            enrichments=enrichments,
            duration_ms=duration_ms,
            plugin_name=plugin_name,
        )

    @classmethod
    def fail(
        cls,
        error: str,
        duration_ms: float,
        plugin_name: str,
    ) -> EnrichmentResult:
        """Cria um resultado de falha."""
        return cls(
            success=False,
            error=error,
            duration_ms=duration_ms,
            plugin_name=plugin_name,
        )


__all__ = [
    "CachePolicy",
    "Enrichment",
    "EnrichmentKind",
    "EnrichmentResult",
]
