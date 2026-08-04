"""Contratos base do Correlation Engine.

Define o protocolo ``CorrelationRule`` e os metadados declarativos
que toda regra de correlacao deve implementar.

O design segue o padrao de plugins do projeto: Protocol + metadata
declarativos + ciclo de vida async (setup/shutdown). Nenhuma regra
hardcoded, nenhum if/else gigante: cada regra informa o que precisa
via ``CorrelationMetadata`` e o engine decide como/em que ordem executar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .._utils import utcnow as _utcnow

if TYPE_CHECKING:
    from ..domain import EnrichedEvent
    from .context import CorrelationContext
    from .models import CorrelationResult


class CorrelationPriority(Enum):
    """Prioridade de execucao da regra (menor = executa primeiro)."""

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 100
    BACKGROUND = 200


class CorrelationDecision(Enum):
    """Decisao de uma regra de correlacao para o evento corrente.

    Attributes:
        MATCH: A regra disparou e produziu uma correlacao.
        NO_MATCH: A regra nao se aplica a este evento.
        DEFERRED: A regra esta acumulando estado (janela ainda nao disparou).
    """

    MATCH = "match"
    NO_MATCH = "no_match"
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class CorrelationReason:
    """Motivo estruturado de um match de correlacao.

    Attributes:
        rule_id: Regra que disparou.
        condition: Descricao da condicao satisfeita.
        values: Valores observados que dispararam o match.
        details: Detalhes adicionais (ex.: contagem, janela, agregacao).
    """

    rule_id: str
    condition: str
    values: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.rule_id or not self.rule_id.strip():
            raise ValueError("rule_id nao pode ser vazio")
        if not self.condition or not self.condition.strip():
            raise ValueError("condition nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class CorrelationMatch:
    """Resultado de uma regra de correlacao que disparou.

    Attributes:
        rule_id: Regra que disparou.
        matched_event_ids: IDs dos eventos que compoem a correlacao.
        reason: Motivo estruturado do match.
        created_at: Carimbo de tempo (UTC) do match.
        severity: Severidade inferida da correlacao.
        tags: Tags adicionadas pela regra.
    """

    rule_id: str
    matched_event_ids: tuple[str, ...]
    reason: CorrelationReason
    created_at: datetime = field(default_factory=_utcnow)
    severity: str = "info"
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.rule_id or not self.rule_id.strip():
            raise ValueError("rule_id nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class CorrelationMetadata:
    """Metadados declarativos de uma regra de correlacao.

    Attributes:
        id: Identificador unico e estavel da regra.
        name: Nome legivel da regra.
        version: Versao semantica da regra.
        description: Descricao legivel do que a regra detecta.
        priority: Prioridade de execucao (menor = primeiro).
        author: Autor/origem da regra.
        required_fields: Campos que o evento DEVE conter para a regra avaliar
            (ex.: ``{"ip_src"}``). Regra e pulada se faltar campo.
        required_event_types: Tipos de evento suportados
            (ex.: ``{"auth", "network"}``). Vazio = todos.
        window_seconds: Janela temporal de correlacao em segundos. ``None``
            = regra nao usa janela (avalia evento isolado).
        dependencies: IDs de outras regras das quais depende.
        enabled_by_default: Se a regra deve estar ativa por padrao.
        timeout_seconds: Timeout de execucao da regra (0 = default do engine).
        tags: Tags para agrupamento/filtragem.
    """

    id: str
    name: str
    version: str
    description: str = ""
    priority: CorrelationPriority = CorrelationPriority.NORMAL
    author: str = "edysiem"
    required_fields: frozenset[str] = frozenset()
    required_event_types: frozenset[str] = frozenset()
    window_seconds: float | None = None
    dependencies: frozenset[str] = frozenset()
    enabled_by_default: bool = True
    timeout_seconds: float = 0.0
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("id nao pode ser vazio")
        if not self.name or not self.name.strip():
            raise ValueError("name nao pode ser vazio")
        if not self.version or not self.version.strip():
            raise ValueError("version nao pode ser vazio")
        if self.window_seconds is not None and self.window_seconds <= 0:
            raise ValueError(f"window_seconds deve ser > 0; recebido {self.window_seconds}")


@runtime_checkable
class CorrelationRule(Protocol):
    """Contrato de uma regra de correlacao Enterprise.

    Cada regra recebe um ``EnrichedEvent`` e um ``CorrelationContext``
    e retorna um ``CorrelationResult``. Nunca muta o evento de entrada.

    A regra informa via ``metadata``:
    - quais campos/eventos exige (``required_fields``, ``required_event_types``)
    - se usa janela temporal (``window_seconds``)
    - prioridade, dependencias, timeout

    Ciclo de vida:
        1. ``setup()`` - inicializacao (compilar condicoes, validar schema)
        2. ``evaluate()`` - avaliacao (chamado para cada evento)
        3. ``shutdown()`` - limpeza (flush de estado)
    """

    @property
    def metadata(self) -> CorrelationMetadata:
        """Metadados declarativos da regra."""
        ...

    async def setup(self) -> None:
        """Inicializa a regra (compilar condicoes, validar schema)."""
        ...

    async def shutdown(self) -> None:
        """Finaliza a regra graciosamente (flush de estado)."""
        ...

    async def evaluate(
        self, event: EnrichedEvent, context: CorrelationContext
    ) -> CorrelationResult:
        """Avalia o evento contra a regra de correlacao.

        Args:
            event: Evento enriquecido a correlacionar.
            context: Estado de janela temporal compartilhado entre regras.

        Returns:
            ``CorrelationResult`` com zero ou mais matches.
        """
        ...


__all__ = [
    "CorrelationDecision",
    "CorrelationMatch",
    "CorrelationMetadata",
    "CorrelationPriority",
    "CorrelationReason",
    "CorrelationRule",
]
