"""Modelos do Incident Engine Enterprise.

Define o modelo ``Incident``, o ciclo de vida, prioridade, evidencia,
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
from ..alerts import AlertSeverity
from ..domain import RiskScore


class IncidentSeverity(Enum):
    """Severidade operacional de um incidente."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return {
            IncidentSeverity.INFO: 0,
            IncidentSeverity.LOW: 1,
            IncidentSeverity.MEDIUM: 2,
            IncidentSeverity.HIGH: 3,
            IncidentSeverity.CRITICAL: 4,
        }[self]


class IncidentPriority(Enum):
    """Prioridade de resposta a um incidente."""

    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"
    P5 = "p5"

    @property
    def rank(self) -> int:
        return {
            IncidentPriority.P1: 0,
            IncidentPriority.P2: 1,
            IncidentPriority.P3: 2,
            IncidentPriority.P4: 3,
            IncidentPriority.P5: 4,
        }[self]


# Transicoes validas do ciclo de vida (nivel de modulo; Enum nao expoe dict).
_INCIDENT_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"triage"}),
    "triage": frozenset({"investigating"}),
    "investigating": frozenset({"contained", "resolved"}),
    "contained": frozenset({"resolved", "closed"}),
    "resolved": frozenset({"closed", "reopened"}),
    "closed": frozenset({"reopened"}),
    "reopened": frozenset({"investigating", "triage"}),
}


class IncidentStatus(Enum):
    """Estado do ciclo de vida de um incidente."""

    OPEN = "open"
    TRIAGE = "triage"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

    def can_transition_to(self, target: IncidentStatus) -> bool:
        """Verifica se a transicao para ``target`` e valida."""
        allowed = _INCIDENT_TRANSITIONS.get(self.value, frozenset())
        return target.value in allowed

    def next_states(self) -> frozenset[IncidentStatus]:
        """Retorna os estados validos a partir do atual."""
        allowed = _INCIDENT_TRANSITIONS.get(self.value, frozenset())
        return frozenset(IncidentStatus(s) for s in allowed)


@dataclass(frozen=True, slots=True)
class IncidentFingerprint:
    """Fingerprint deterministico de um incidente.

    Attributes:
        hash: Hash SHA-256 dos campos-chave (16 hex).
        key: Chave de agrupamento usada no calculo.
        created_at: Carimbo (UTC) do calculo.
    """

    hash: str
    key: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.hash or not self.hash.strip():
            raise ValueError("hash nao pode ser vazio")
        if not self.key or not self.key.strip():
            raise ValueError("key nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class IncidentReason:
    """Motivo estruturado de um incidente.

    Attributes:
        criteria: Criterios que agruparam os alertas.
        alerts_count: Numero de alertas agrupados.
        score: Pontuacao de agrupamento.
        details: Detalhes adicionais.
    """

    criteria: frozenset[str] = frozenset()
    alerts_count: int = 0
    score: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.alerts_count < 0:
            raise ValueError(f"alerts_count nao pode ser negativo; recebido {self.alerts_count}")


@dataclass(frozen=True, slots=True)
class IncidentEvidence:
    """Evidencia de um incidente (referencia a um alerta)."""

    alert_id: str
    title: str = ""
    rule_id: str = ""
    severity: AlertSeverity = AlertSeverity.MEDIUM
    created_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class IncidentTimelineEntry:
    """Entrada imutavel na timeline de um incidente."""

    action: str
    detail: str = ""
    created_at: datetime = field(default_factory=_utcnow)
    actor: str = "system"


@dataclass(frozen=True, slots=True)
class Incident:
    """Incidente de seguranca agregando alertas relacionados.

    Attributes:
        title: Titulo legivel.
        description: Descricao detalhada.
        severity: Severidade (max dos alertas).
        priority: Prioridade de resposta.
        risk_score: Pontuacao de risco (0-100).
        confidence: Confianca (0.0-1.0).
        status: Estado do ciclo de vida.
        first_seen: Primeiro alerta (UTC).
        last_seen: Ultimo alerta (UTC).
        closed_at: Data de fechamento (se fechado).
        occurrences: Numero de ocorrencias (deduplicacao).
        alerts: IDs dos alertas agrupados.
        assets: Ativos envolvidos.
        users: Usuarios envolvidos.
        iocs: IOCs envolvidos.
        mitre: Referencias MITRE (tecnicas).
        tactics: Taticas MITRE.
        techniques: Tecnicas MITRE.
        tags: Tags de contextualizacao.
        timeline: Historico imutavel de acoes.
        owner: Responsavel pelo incidente.
        fingerprint: Fingerprint deterministico.
        reason: Motivo do agrupamento.
        evidence: Evidencias (alertas) que sustentam o incidente.
        id: Identificador unico (auto-gerado).
        created_at: Carimbo de criacao (UTC).
        updated_at: Carimbo de ultima atualizacao (UTC).
    """

    title: str
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    priority: IncidentPriority = IncidentPriority.P3
    risk_score: RiskScore = RiskScore(50)  # noqa: RUF009
    confidence: float = 1.0
    status: IncidentStatus = IncidentStatus.OPEN
    first_seen: datetime = field(default_factory=_utcnow)
    last_seen: datetime = field(default_factory=_utcnow)
    closed_at: datetime | None = None
    occurrences: int = 1
    alerts: tuple[str, ...] = ()
    assets: frozenset[str] = frozenset()
    users: frozenset[str] = frozenset()
    iocs: frozenset[str] = frozenset()
    mitre: frozenset[str] = frozenset()
    tactics: frozenset[str] = frozenset()
    techniques: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()
    timeline: tuple[IncidentTimelineEntry, ...] = ()
    owner: str | None = None
    fingerprint: IncidentFingerprint | None = None
    reason: IncidentReason | None = None
    evidence: tuple[IncidentEvidence, ...] = ()
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

    def bump(self, at: datetime | None = None) -> Incident:
        """Retorna uma copia com occurrences+1 e last_seen atualizado."""
        now = at or _utcnow()
        return Incident(
            title=self.title,
            description=self.description,
            severity=self.severity,
            priority=self.priority,
            risk_score=self.risk_score,
            confidence=self.confidence,
            status=self.status,
            first_seen=self.first_seen,
            last_seen=now,
            closed_at=self.closed_at,
            occurrences=self.occurrences + 1,
            alerts=self.alerts,
            assets=self.assets,
            users=self.users,
            iocs=self.iocs,
            mitre=self.mitre,
            tactics=self.tactics,
            techniques=self.techniques,
            tags=self.tags,
            timeline=self.timeline,
            owner=self.owner,
            fingerprint=self.fingerprint,
            reason=self.reason,
            evidence=self.evidence,
            id=self.id,
            created_at=self.created_at,
            updated_at=now,
        )


@dataclass(slots=True)
class IncidentMetrics:
    """Metricas agregadas do Incident Engine (mutavel, nao frozen)."""

    total_created: int = 0
    total_deduplicated: int = 0
    total_reopened: int = 0
    total_failures: int = 0
    total_grouped_alerts: int = 0
    created_by_rule: dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=_utcnow)

    @property
    def avg_alerts_per_incident(self) -> float:
        """Media de alertas por incidente criado."""
        return self.total_grouped_alerts / self.total_created if self.total_created else 0.0

    def record_created(self, alerts_count: int, key: str) -> None:
        """Registra um incidente criado."""
        self.total_created += 1
        self.total_grouped_alerts += alerts_count
        self.created_by_rule[key] = self.created_by_rule.get(key, 0) + 1
        self.last_updated = _utcnow()

    def record_deduplicated(self) -> None:
        """Registra um incidente deduplicado."""
        self.total_deduplicated += 1
        self.last_updated = _utcnow()

    def record_reopened(self) -> None:
        """Registra um incidente reaberto."""
        self.total_reopened += 1
        self.last_updated = _utcnow()


__all__ = [
    "Incident",
    "IncidentEvidence",
    "IncidentFingerprint",
    "IncidentMetrics",
    "IncidentPriority",
    "IncidentReason",
    "IncidentSeverity",
    "IncidentStatus",
    "IncidentTimelineEntry",
]
