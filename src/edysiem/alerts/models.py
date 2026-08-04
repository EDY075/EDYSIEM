"""Modelos do Alert Engine Enterprise.

Define o modelo operacional ``Alert``, o ciclo de vida, prioridade,
fingerprint e metricas do framework. Todos imutaveis (frozen=True,
slots=True) seguindo o padrao do projeto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .._utils import new_id as _new_id
from .._utils import utcnow as _utcnow
from ..domain import RiskScore


class AlertSeverity(Enum):
    """Severidade operacional de um alerta."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """Rank ordinal para comparacao (info=0 .. critical=4)."""
        return {
            AlertSeverity.INFO: 0,
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 4,
        }[self]


class AlertPriority(Enum):
    """Prioridade de triagem operacional."""

    P1 = "p1"  # critica - resposta imediata
    P2 = "p2"  # alta
    P3 = "p3"  # media
    P4 = "p4"  # baixa
    P5 = "p5"  # informativa

    @property
    def rank(self) -> int:
        return {
            AlertPriority.P1: 0,
            AlertPriority.P2: 1,
            AlertPriority.P3: 2,
            AlertPriority.P4: 3,
            AlertPriority.P5: 4,
        }[self]


# Transicoes validas do ciclo de vida: (estado_atual) -> proximos estados.
_LIFECYCLE_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"triage", "false_positive"}),
    "triage": frozenset({"investigating", "resolved", "false_positive"}),
    "investigating": frozenset({"resolved", "false_positive"}),
    "resolved": frozenset({"open"}),
    "false_positive": frozenset({"open"}),
}


class AlertLifecycle(Enum):
    """Estado do ciclo de vida de um alerta (state machine do dominio)."""

    OPEN = "open"
    TRIAGE = "triage"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"

    def can_transition_to(self, target: AlertLifecycle) -> bool:
        """Verifica se a transicao para ``target`` e valida."""
        allowed = _LIFECYCLE_TRANSITIONS.get(self.value, frozenset())
        return target.value in allowed

    def next_states(self) -> frozenset[AlertLifecycle]:
        """Retorna os estados validos a partir do atual."""
        allowed = _LIFECYCLE_TRANSITIONS.get(self.value, frozenset())
        return frozenset(AlertLifecycle(s) for s in allowed)


@dataclass(frozen=True, slots=True)
class AlertFingerprint:
    """Fingerprint deterministico de um alerta.

    Attributes:
        hash: Hash SHA-256 dos campos-chave (16 hex).
        rule_id: Regra de origem.
        identity: Campos de identidade usados no calculo.
        created_at: Carimbo (UTC) do calculo.
    """

    hash: str
    rule_id: str
    identity: frozenset[str] = frozenset()
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.hash or not self.hash.strip():
            raise ValueError("hash nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class AlertReason:
    """Motivo estruturado de um alerta.

    Attributes:
        rule_id: Regra que detectou.
        condition: Condicao satisfeita.
        values: Valores observados.
        details: Detalhes adicionais.
    """

    rule_id: str
    condition: str
    values: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.rule_id or not self.rule_id.strip():
            raise ValueError("rule_id nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class AlertTimelineEntry:
    """Entrada imutavel na timeline de um alerta."""

    action: str
    detail: str = ""
    created_at: datetime = field(default_factory=_utcnow)
    actor: str = "system"


@dataclass(frozen=True, slots=True)
class Alert:
    """Alerta operacional pronto para um SOC.

    Attributes:
        title: Titulo legivel.
        description: Descricao detalhada.
        severity: Severidade operacional.
        priority: Prioridade de triagem.
        risk_score: Pontuacao de risco (0-100).
        confidence: Confianca (0.0-1.0).
        first_seen: Primeira ocorrencia (UTC).
        last_seen: Ultima ocorrencia (UTC).
        occurrences: Numero de ocorrencias (deduplicacao).
        status: Estado do ciclo de vida.
        source: Origem da deteccao (ex.: "detection").
        rule_id: Regra que gerou o alerta.
        mitre: Referencias MITRE (ids).
        asset_id: Ativo afetado, se houver.
        user: Usuario envolvido, se houver.
        ioc_ids: Indicadores de comprometimento.
        tags: Tags de contextualizacao.
        timeline: Historico imutavel de acoes.
        fingerprint: Fingerprint deterministico.
        event_ids: IDs dos eventos que sustentam o alerta.
        id: Identificador unico (auto-gerado).
        created_at: Carimbo de criacao (UTC).
        updated_at: Carimbo de ultima atualizacao (UTC).
    """

    title: str
    description: str = ""
    severity: AlertSeverity = AlertSeverity.MEDIUM
    priority: AlertPriority = AlertPriority.P3
    risk_score: RiskScore = RiskScore(50)  # noqa: RUF009
    confidence: float = 1.0
    first_seen: datetime = field(default_factory=_utcnow)
    last_seen: datetime = field(default_factory=_utcnow)
    occurrences: int = 1
    status: AlertLifecycle = AlertLifecycle.OPEN
    source: str = "detection"
    rule_id: str = ""
    mitre: frozenset[str] = frozenset()
    asset_id: str | None = None
    user: str | None = None
    ioc_ids: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset()
    timeline: tuple[AlertTimelineEntry, ...] = ()
    fingerprint: AlertFingerprint | None = None
    event_ids: tuple[str, ...] = ()
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("title nao pode ser vazio")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence deve estar entre 0.0 e 1.0; recebido {self.confidence}")
        if self.occurrences < 1:
            raise ValueError(f"occurrences deve ser >= 1; recebido {self.occurrences}")

    def bump(self, at: datetime | None = None) -> Alert:
        """Retorna uma copia com occurrences+1 e last_seen atualizado.

        Usado pela deduplicacao quando o mesmo alerta reaparece.
        """
        now = at or _utcnow()
        return Alert(
            title=self.title,
            description=self.description,
            severity=self.severity,
            priority=self.priority,
            risk_score=self.risk_score,
            confidence=self.confidence,
            first_seen=self.first_seen,
            last_seen=now,
            occurrences=self.occurrences + 1,
            status=self.status,
            source=self.source,
            rule_id=self.rule_id,
            mitre=self.mitre,
            asset_id=self.asset_id,
            user=self.user,
            ioc_ids=self.ioc_ids,
            tags=self.tags,
            timeline=self.timeline,
            fingerprint=self.fingerprint,
            event_ids=self.event_ids,
            id=self.id,
            created_at=self.created_at,
            updated_at=now,
        )


@dataclass(slots=True)
class AlertMetrics:
    """Metricas agregadas do Alert Engine (mutavel, nao frozen)."""

    total_created: int = 0
    total_deduplicated: int = 0
    total_updates: int = 0
    total_failures: int = 0
    created_by_rule: dict[str, int] = field(default_factory=dict)
    deduplicated_by_rule: dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=_utcnow)

    def record_created(self, rule_id: str) -> None:
        """Registra um alerta criado."""
        self.total_created += 1
        self.created_by_rule[rule_id] = self.created_by_rule.get(rule_id, 0) + 1
        self.last_updated = _utcnow()

    def record_deduplicated(self, rule_id: str) -> None:
        """Registra um alerta deduplicado (ocorrencia incrementada)."""
        self.total_deduplicated += 1
        self.deduplicated_by_rule[rule_id] = self.deduplicated_by_rule.get(rule_id, 0) + 1
        self.last_updated = _utcnow()


__all__ = [
    "Alert",
    "AlertFingerprint",
    "AlertLifecycle",
    "AlertMetrics",
    "AlertPriority",
    "AlertReason",
    "AlertSeverity",
    "AlertTimelineEntry",
]
