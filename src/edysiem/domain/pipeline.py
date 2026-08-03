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
        event_type: Categoria do evento (ex.: ``"logon"``, ``"network"``).
        fields: Dicionário de campos estruturados extraídos do payload.
        raw: Payload original recebido pelo parser.
        trace_id: Identificador de rastreabilidade da pipeline.
    """

    event_id: str
    timestamp: datetime
    source_type: str
    source_host: str
    event_type: str
    fields: dict[str, Any]
    raw: str | bytes
    trace_id: str

    def __post_init__(self) -> None:
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type não pode ser vazio")
        if not self.event_type or not self.event_type.strip():
            raise ValueError("event_type não pode ser vazio")
        if not self.trace_id or not self.trace_id.strip():
            raise ValueError("trace_id não pode ser vazio")


@dataclass(frozen=True, slots=True)
class CanonicalEvent:
    """Modelo canônico de evento normalizado (espelha DATAFLOW.md §2.4).

    Representa o evento já normalizado, com campos de segurança comuns
    preenchidos (usuário, processo, IPs, hostname) e severidade classificada.
    É o modelo central da pipeline — consumido por exporters e pelo
    enrichment.

    Attributes:
        event_id: Identificador único do evento.
        timestamp: Carimbo de tempo (UTC) do evento na fonte.
        source_type: Tipo da fonte.
        source_host: Host/equipamento de origem.
        event_type: Categoria do evento normalizado.
        severity: Severidade classificada pelo normalizer.
        user: Usuário associado ao evento, se houver.
        process: Processo associado ao evento, se houver.
        ip_src: Endereço IP de origem, se houver.
        ip_dst: Endereço IP de destino, se houver.
        hostname: Hostname associado ao evento, se houver.
        payload: Campos adicionais enriquecidos durante a normalização.
        raw: Payload original (texto) preservado para auditoria.
        trace_id: Identificador de rastreabilidade; a pipeline preenche
            obrigatoriamente em produção. Não é validado aqui para permitir
            construção simples em testes e ferramentas locais.
        normalized_at: Carimbo de tempo (UTC) da normalização.
    """

    event_id: str
    timestamp: datetime
    source_type: str
    source_host: str
    event_type: str
    severity: Severity
    user: str | None = None
    process: str | None = None
    ip_src: str | None = None
    ip_dst: str | None = None
    hostname: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    trace_id: str = ""
    normalized_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id não pode ser vazio")
        if not self.source_type or not self.source_type.strip():
            raise ValueError("source_type não pode ser vazio")
        if not self.source_host or not self.source_host.strip():
            raise ValueError("source_host não pode ser vazio")
        if not self.event_type or not self.event_type.strip():
            raise ValueError("event_type não pode ser vazio")


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
    "CanonicalEvent",
    "EnrichedEvent",
    "Enrichment",
    "ParsedEvent",
    "RawEvent",
]
