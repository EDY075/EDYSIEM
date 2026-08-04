"""Contratos base do Detection Framework.

Define o protocolo ``DetectionRule``, o ``RuleMetadata`` declarativo e
os tipos de decisao/reason do processo de deteccao.

O design segue o padrao de plugins do projeto: Protocol + metadata
declarativos + ciclo de vida async. Nenhuma regra hardcoded no engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .._utils import utcnow as _utcnow
from ..domain import RiskScore, Severity

if TYPE_CHECKING:
    from ..correlation import CorrelatedEvent
    from .context import DetectionContext
    from .models import DetectionResult


class DetectionPriority(Enum):
    """Prioridade de execucao da regra (menor = executa primeiro)."""

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 100
    BACKGROUND = 200


class DetectionDecision(Enum):
    """Decisao de deteccao para o evento correlacionado.

    Attributes:
        DETECTED: A regra detectou uma condicao de interesse.
        NO_DETECTION: A regra nao se aplicou.
        DEFERRED: A regra esta acumulando estado (janela ainda nao disparou).
    """

    DETECTED = "detected"
    NO_DETECTION = "no_detection"
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class DetectionReason:
    """Motivo estruturado de uma deteccao.

    Attributes:
        rule_id: Regra que detectou.
        condition: Descricao da condicao satisfeita.
        values: Valores observados.
        details: Detalhes adicionais (ex.: contagem, janela).
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
class DetectionFinding:
    """Resultado de uma regra de deteccao que detectou.

    Attributes:
        rule_id: Regra que detectou.
        event_ids: IDs dos eventos que sustentam a deteccao.
        reason: Motivo estruturado.
        severity: Severidade classificada da deteccao.
        confidence: Confianca (0.0-1.0).
        risk_score: Pontuacao de risco (0-100).
        created_at: Carimbo (UTC).
        tags: Tags adicionadas pela regra.
    """

    rule_id: str
    event_ids: tuple[str, ...]
    reason: DetectionReason
    severity: Severity = Severity.MEDIUM
    confidence: float = 1.0
    risk_score: RiskScore = RiskScore(50)  # noqa: RUF009
    created_at: datetime = field(default_factory=_utcnow)
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.rule_id or not self.rule_id.strip():
            raise ValueError("rule_id nao pode ser vazio")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence deve estar entre 0.0 e 1.0; recebido {self.confidence}")


@dataclass(frozen=True, slots=True)
class RuleMetadata:
    """Metadados declarativos de uma regra de deteccao.

    Attributes:
        id: Identificador unico e estavel da regra.
        name: Nome legivel.
        version: Versao semantica.
        description: Descricao do que a regra detecta.
        author: Autor/origem.
        priority: Prioridade de execucao.
        severity: Severidade atribuida a deteccao.
        confidence: Confianca padrao (0.0-1.0).
        risk_score: Pontuacao de risco (0-100).
        required_fields: Campos que o evento DEVE conter.
        dependencies: IDs de regras das quais depende.
        enabled: Se a regra esta ativa por padrao.
        tags: Tags para agrupamento/filtragem.
        timeout_seconds: Timeout de execucao (0 = default do engine).
    """

    id: str
    name: str
    version: str
    description: str = ""
    author: str = "edysiem"
    priority: DetectionPriority = DetectionPriority.NORMAL
    severity: Severity = Severity.MEDIUM
    confidence: float = 1.0
    risk_score: RiskScore = RiskScore(50)  # noqa: RUF009
    required_fields: frozenset[str] = frozenset()
    dependencies: frozenset[str] = frozenset()
    enabled: bool = True
    tags: frozenset[str] = frozenset()
    timeout_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("id nao pode ser vazio")
        if not self.name or not self.name.strip():
            raise ValueError("name nao pode ser vazio")
        if not self.version or not self.version.strip():
            raise ValueError("version nao pode ser vazio")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence deve estar entre 0.0 e 1.0; recebido {self.confidence}")


@runtime_checkable
class DetectionRule(Protocol):
    """Contrato de uma regra de deteccao Enterprise.

    Cada regra recebe um ``CorrelatedEvent`` e um ``DetectionContext``
    e retorna um ``DetectionResult``. Nunca muta o evento de entrada.

    Ciclo de vida:
        1. ``setup()`` - inicializacao (compilar condicoes, validar schema)
        2. ``evaluate()`` - avaliacao (chamado para cada evento)
        3. ``shutdown()`` - limpeza (flush de estado)
    """

    @property
    def metadata(self) -> RuleMetadata:
        """Metadados declarativos da regra."""
        ...

    async def setup(self) -> None:
        """Inicializa a regra (compilar condicoes, validar schema)."""
        ...

    async def shutdown(self) -> None:
        """Finaliza a regra graciosamente (flush de estado)."""
        ...

    async def evaluate(self, event: CorrelatedEvent, context: DetectionContext) -> DetectionResult:
        """Avalia o evento correlacionado contra a regra.

        Args:
            event: Evento correlacionado a analisar.
            context: Estado compartilhado entre regras.

        Returns:
            ``DetectionResult`` com zero ou mais findings.
        """
        ...


__all__ = [
    "DetectionDecision",
    "DetectionFinding",
    "DetectionPriority",
    "DetectionReason",
    "DetectionRule",
    "RuleMetadata",
]
