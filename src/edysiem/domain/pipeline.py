"""Modelos da pipeline oficial de eventos do EDY SIEM.

A pipeline aprovada pelo PO é:

    Collector → RawEvent → Parser → ParsedEvent → Normalizer → CanonicalEvent
    → Enrichment → EnrichedEvent → Correlation → Detection → Alert
    → Incident → Case

Este módulo concentra os modelos imutáveis dessa jornada, do evento bruto
(``RawEvent``) ao evento enriquecido (``EnrichedEvent``), além do value
object ``Enrichment``. Foi separado de ``entities.py`` porque representa
uma unidade coesa do fluxo de dados (e não entidades de negócio como ativos,
alertas, casos e usuários), facilitando a evolução em sprints futuros.

Todos os modelos seguem o padrão do projeto: ``@dataclass(frozen=True,
slots=True)``, tipagem estrita, docstrings descritivas e validação em
``__post_init__`` (``ValueError`` para campos obrigatórios vazios,
consistente com ``RiskScore``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .._utils import new_id as _new_id
from .._utils import utcnow as _utcnow
from .entities import RiskScore, Severity


@dataclass(frozen=True, slots=True)
class RawEvent:
    """Evento bruto oriundo de uma fonte de coleta (saída do Collector).

    Primeiro modelo da pipeline: contém apenas o payload não interpretado e
    a identificação da origem. A transformação para a forma canônica é feita
    por etapas posteriores — o lifecycle é por transformação imutável, sem
    flags de estado.

    Attributes:
        source_type: Tipo da fonte (ex.: ``"windows"``, ``"syslog"``).
        source_host: Host/equipamento de origem (ex.: ``"wks-01"``).
        raw_payload: Payload bruto como recebido pela fonte.
        event_id: Identificador único do evento (auto-gerado).
        received_at: Carimbo de tempo (UTC) de recebimento pela plataforma.
        tags: Conjunto imutável de tags de contextualização.
        risk_score: Pontuação de risco preliminar atribuída na coleta.
    """

    source_type: str
    source_host: str
    raw_payload: bytes | str
    event_id: str = field(default_factory=_new_id)
    received_at: datetime = field(default_factory=_utcnow)
    tags: frozenset[str] = frozenset()
    # RiskScore é um value object frozen (imutável): um default compartilhado
    # entre instâncias é seguro. noqa: RUF009 (função call em default) porque
    # a classe vem de entities.py e o ruff não resolve imutabilidade cross-module.
    risk_score: RiskScore = RiskScore(0)  # noqa: RUF009

    def __post_init__(self) -> None:
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type não pode ser vazio")
        if not self.source_host or not self.source_host.strip():
            raise ValueError("source_host não pode ser vazio")


@dataclass(frozen=True, slots=True)
class ParsedEvent:
    """Evento com campos estruturados extraídos pelo Parser.

    Resultado da etapa de parsing: o payload bruto foi decomposto em campos
    tipados (``fields``), mantendo a referência ao conteúdo original.

    Attributes:
        event_id: Identificador único do evento (ligado ao ``RawEvent``).
        timestamp: Carimbo de tempo (UTC) do evento na fonte.
        source_type: Tipo da fonte (ex.: ``"windows"``).
        source_host: Host/equipamento de origem.
        event_category: Categoria ampla do evento (ex.: ``"auth"``,
            ``"network"``, ``"process"``, ``"file"``).
        event_action: Ação específica (ex.: ``"logon"``, ``"create"``,
            ``"delete"``, ``"connect"``).
        fields: Dicionário de campos estruturados extraídos do payload.
        raw: Payload original recebido pelo parser.
        trace_id: Identificador de rastreabilidade da pipeline.
        vendor: Fabricante/origem do log (ex.: ``"microsoft"``,
            ``"cisco"``, ``"linux"``).
        product: Produto específico que gerou o log (ex.: ``"winlog"``,
            ``"ios"``, ``"sshd"``).
        confidence: Nível de confiança da extração (0.0-1.0).
    """

    event_id: str
    timestamp: datetime
    source_type: str
    source_host: str
    event_category: str
    event_action: str
    fields: dict[str, Any]
    raw: str | bytes
    trace_id: str
    vendor: str | None = None
    product: str | None = None
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type não pode ser vazio")
        if not self.event_category or not self.event_category.strip():
            raise ValueError("event_category não pode ser vazio")
        if not self.event_action or not self.event_action.strip():
            raise ValueError("event_action não pode ser vazio")
        if not self.trace_id or not self.trace_id.strip():
            raise ValueError("trace_id não pode ser vazio")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence deve estar entre 0.0 e 1.0; recebido {self.confidence}")


SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class CanonicalEvent:
    """Modelo canônico de evento normalizado — contrato central da pipeline.

    Representa o evento totalmente normalizado, com campos de segurança
    universais preenchidos. É o modelo central consumido por enrichment,
    correlation, detection e exporters. Projetado para ser vendor-neutral,
    imutável e versionado.

    O design incorpora lições de ECS (Elastic), CIM (Splunk) e CES
    (Sentinel) sem copiar nenhum deles: campos são semânticos e
    independentes de vendor, o schema é versionado, e o raw é
    preservado para re-parsing.

    Attributes:
        event_id: Identificador único do evento.
        trace_id: Rastreabilidade ponta a ponta da pipeline.
        timestamp: Carimbo de tempo (UTC) do evento na fonte.
        received_at: Carimbo de tempo (UTC) em que a plataforma recebeu.
        source_type: Tipo da fonte (ex.: ``"syslog"``, ``"windows"``).
        source_host: Host/equipamento de origem.
        hostname: Hostname resolvido do equipamento de origem.
        event_category: Categoria ampla (``"auth"``, ``"network"``,
            ``"process"``, ``"file"``, ``"system"``, ``"threat"``).
        event_action: Ação específica (``"logon"``, ``"create"``,
            ``"delete"``, ``"connect"``, ``"disconnect"``).
        severity: Severidade classificada pelo normalizer.
        user: Usuário associado ao evento, se houver.
        process: Processo associado ao evento, se houver.
        command_line: Linha de comando do processo, se aplicável.
        ip_src: Endereço IP de origem, se houver.
        ip_dst: Endereço IP de destino, se houver.
        vendor: Fabricante do produto que gerou o log.
        product: Nome do produto específico.
        event_original: Linha raw original preservada para auditoria e
            re-parsing.
        normalized_fields: Conjunto dos nomes dos campos que foram
            normalizados pelo parser/normalizer (auditoria).
        tags: Tags de contextualização herdadas da coleta.
        confidence: Nível de confiança da normalização
            (0.0-1.0).
        metadata: Campos arbitrários de extensibilidade (vendor-specific
            que não se encaixam nos campos canônicos).
        schema_version: Versão do schema canônico (ex.: ``"1.0.0"``).
        normalized_at: Carimbo de tempo (UTC) da normalização.
    """

    event_id: str
    trace_id: str
    timestamp: datetime
    received_at: datetime
    source_type: str
    source_host: str
    hostname: str | None = None
    event_category: str = ""
    event_action: str = ""
    severity: Severity = Severity.INFO
    user: str | None = None
    process: str | None = None
    command_line: str | None = None
    ip_src: str | None = None
    ip_dst: str | None = None
    vendor: str | None = None
    product: str | None = None
    event_original: str = ""
    normalized_fields: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    normalized_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id não pode ser vazio")
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type não pode ser vazio")
        if not self.source_host or not self.source_host.strip():
            raise ValueError("source_host não pode ser vazio")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence deve estar entre 0.0 e 1.0; recebido {self.confidence}")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version deve ser {SCHEMA_VERSION!r}; recebido {self.schema_version!r}"
            )


@dataclass(frozen=True, slots=True)
class Enrichment:
    """Value object de contexto enriquecido anexado a um evento.

    Produzido por um ``EnrichmentPlugin`` e agregado em ``EnrichedEvent``.

    Attributes:
        kind: Categoria do enriquecimento (ex.: ``"asset"``, ``"geo"``,
            ``"intel"``).
        provider: Provedor da informação (ex.: ``"asset-db"``,
            ``"maxmind"``).
        data: Dados estruturados do enriquecimento.
        created_at: Carimbo de tempo (UTC) de criação.
    """

    kind: str
    provider: str
    data: dict[str, Any]
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.kind or not self.kind.strip():
            raise ValueError("kind não pode ser vazio")
        if not self.provider or not self.provider.strip():
            raise ValueError("provider não pode ser vazio")


@dataclass(frozen=True, slots=True)
class EnrichedEvent(CanonicalEvent):
    """Evento canônico acrescido de contexto de enrichment.

    Herda todos os campos de ``CanonicalEvent`` (dataclass inheritance com
    ``frozen=True`` e ``slots=True`` é suportada em Python 3.12) e adiciona
    a lista imutável de ``Enrichment`` aplicados. A validação canônica do
    ``__post_init__`` da base é herdada automaticamente.

    Attributes:
        enrichments: Tupla de enriquecimentos aplicados ao evento (vazia
            quando nenhum contexto foi anexado).
    """

    enrichments: tuple[Enrichment, ...] = ()


__all__ = [
    "SCHEMA_VERSION",
    "CanonicalEvent",
    "EnrichedEvent",
    "Enrichment",
    "ParsedEvent",
    "RawEvent",
]
