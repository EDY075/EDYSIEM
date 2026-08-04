"""Contratos base do Enrichment Engine.

Define o protocolo ``EnrichmentPlugin`` e os metadados declarativos
que todo plugin de enriquecimento deve implementar.

O design segue o padrão Plugin do projeto: Protocol + metadata declarativos
+ ciclo de vida assíncrono (setup/shutdown).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from ..domain import CanonicalEvent, EnrichedEvent
from ..result import Result

if TYPE_CHECKING:
    from .context import EnrichmentContext


class PluginPriority(Enum):
    """Prioridade de execução do plugin (menor = executa primeiro)."""

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 100
    BACKGROUND = 200


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """Metadados declarativos de um plugin de enriquecimento.

    Atributos:
        id: Identificador único e estável do plugin (ex.: ``"asset-enricher"``).
        name: Nome legível do plugin.
        version: Versão semântica do plugin.
        author: Autor/origem do plugin.
        description: Descrição legível do que o plugin faz.
        priority: Prioridade de execução (menor = primeiro).
        dependencies: IDs de plugins dos quais este depende.
        supported_event_categories: Categorias de evento suportadas
            (ex.: ``["auth", "network", "process"]``). Vazio = todas.
        cache_policy: Política de cache padrão do plugin.
        timeout_seconds: Timeout de execução (0 = sem timeout).
        tags: Tags para agrupamento/filtragem.
        enabled: Se o plugin está ativo por padrão.
        created_at: Carimbo de criação do metadata.
    """

    id: str
    name: str
    version: str
    author: str
    description: str = ""
    priority: PluginPriority = PluginPriority.NORMAL
    dependencies: frozenset[str] = frozenset()
    supported_event_categories: frozenset[str] = frozenset()
    cache_policy: str = "none"
    timeout_seconds: float = 0.0
    tags: frozenset[str] = frozenset()
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("id não pode ser vazio")
        if not self.name or not self.name.strip():
            raise ValueError("name não pode ser vazio")
        if not self.version or not self.version.strip():
            raise ValueError("version não pode ser vazio")
        if not self.author or not self.author.strip():
            raise ValueError("author não pode ser vazio")


@dataclass(frozen=True, slots=True)
class PluginResult:
    """Resultado da execução de um plugin de enriquecimento.

    Attributes:
        success: Se a execução foi bem-sucedida.
        enrichments: Tupla de enriquecimentos produzidos.
        error: Mensagem de erro se falhou.
        duration_ms: Tempo de execução em milissegundos.
        plugin_id: ID do plugin que executou.
        metadata: Dados adicionais de diagnóstico.
    """

    success: bool
    enrichments: tuple[object, ...] = ()
    error: str | None = None
    duration_ms: float = 0.0
    plugin_id: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        enrichments: tuple[object, ...],
        duration_ms: float,
        plugin_id: str,
        metadata: dict[str, object] | None = None,
    ) -> PluginResult:
        return cls(
            success=True,
            enrichments=enrichments,
            duration_ms=duration_ms,
            plugin_id=plugin_id,
            metadata=metadata or {},
        )

    @classmethod
    def fail(
        cls,
        error: str,
        duration_ms: float,
        plugin_id: str,
        metadata: dict[str, object] | None = None,
    ) -> PluginResult:
        return cls(
            success=False,
            error=error,
            duration_ms=duration_ms,
            plugin_id=plugin_id,
            metadata=metadata or {},
        )


@runtime_checkable
class EnrichmentPlugin(Protocol):
    """Contrato de um plugin de enriquecimento Enterprise.

    Cada plugin recebe um ``CanonicalEvent`` e um ``EnrichmentContext``
    e retorna um ``EnrichedEvent`` com os enriquecimentos anexados.
    Nunca muta o evento de entrada (imutabilidade garantida).

    Ciclo de vida:
        1. ``setup()`` - inicialização (conexões, caches, validações)
        2. ``enrich()`` - execução do enriquecimento (pode ser chamado N vezes)
        3. ``shutdown()`` - limpeza (fechar conexões, flush caches)

    Atributos obrigatórios (via metadata):
        - ``metadata``: ``PluginMetadata`` com id, versão, prioridade, etc.
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Metadados declarativos do plugin."""
        ...

    async def setup(self) -> None:
        """Inicializa o plugin (conexões, caches, validações).
        Chamado uma vez antes do primeiro ``enrich()``.
        """
        ...

    async def shutdown(self) -> None:
        """Finaliza o plugin graciosamente (fecha conexões, flush caches).
        Chamado no shutdown do engine.
        """
        ...

    async def enrich(
        self, event: CanonicalEvent, context: EnrichmentContext
    ) -> Result[EnrichedEvent]:
        """Executa o enriquecimento do evento.

        Args:
            event: Evento canônico a ser enriquecido.
            context: Contexto compartilhado (asset DB, geo, threat intel, etc.).

        Returns:
            ``Success(EnrichedEvent)`` com enriquecimentos anexados;
            ``Failure`` se o enriquecimento falhar.
        """
        ...


__all__ = [
    "EnrichmentPlugin",
    "PluginMetadata",
    "PluginPriority",
    "PluginResult",
]
