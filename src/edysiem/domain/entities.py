"""Entidades de domínio e enums do EDY SIEM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    from uuid import uuid4

    return str(uuid4())


class Severity(Enum):
    """Severidade de um evento/alerta."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Estado do ciclo de vida de um alerta."""

    OPEN = "open"
    ACK = "acknowledged"
    CLOSED = "closed"


class LifecycleStatus(Enum):
    """Estado do ciclo de vida de um ativo."""

    ACTIVE = "active"
    DECOMMISSIONED = "decommissioned"
    PENDING = "pending"
    UNKNOWN = "unknown"


class EventType(Enum):
    """Categorias de eventos de segurança."""

    AUTH = "auth"
    NETWORK = "network"
    PROCESS = "process"
    FILE = "file"
    LOGON = "logon"
    THREAT = "threat"
    SYSTEM = "system"


class IOCKind(Enum):
    """Tipos de Indicator of Compromise."""

    IP = "ip"
    DOMAIN = "domain"
    HASH = "hash"
    FILE = "file"
    URL = "url"
    EMAIL = "email"


class ConfidenceLevel(Enum):
    """Nível de confiança de uma inteligência."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(Enum):
    """Estado de um caso."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class InvestigationStatus(Enum):
    """Estado de uma investigação."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class NotificationStatus(Enum):
    """Estado de entrega de uma notificação."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class RuleState(Enum):
    """Estado de uma regra de detecção."""

    DRAFT = "draft"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class StepStatus(Enum):
    """Estado de um passo de investigação."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class UserRole(Enum):
    """Papéis de um usuário no SIEM."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SOC = "soc"
    RISK = "risk"
    MANAGER = "manager"


@dataclass(frozen=True, slots=True)
class RiskScore:
    """Value object de pontuação de risco (0-100)."""

    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(
                f"RiskScore deve estar entre 0 e 100; recebido {self.value}"
            )


@dataclass(frozen=True, slots=True)
class Asset:
    """Um ativo monitorado pela plataforma."""

    label: str
    id: str = field(default_factory=_new_id)
    fqdn: str | None = None
    ip: str | None = None
    asset_type: str = "unknown"
    owner: str | None = None
    department: str | None = None
    tags: frozenset[str] = frozenset()
    risk_score: RiskScore = RiskScore(0)
    lifecycle: LifecycleStatus = LifecycleStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class AssetGroup:
    """Agrupamento lógico de ativos."""

    name: str
    id: str = field(default_factory=_new_id)
    description: str | None = None
    asset_ids: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class IOC:
    """Indicador de Compromise."""

    kind: IOCKind
    value: str
    id: str = field(default_factory=_new_id)
    source: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class Alert:
    """Alerta de segurança gerado pelo motor."""

    title: str
    severity: Severity
    id: str = field(default_factory=_new_id)
    status: AlertStatus = AlertStatus.OPEN
    source_type: EventType = EventType.THREAT
    asset_id: str | None = None
    rule_id: str | None = None
    ioc_ids: tuple[str, ...] = ()
    raw_event_ids: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset()
    risk_score: RiskScore = RiskScore(0)
    body: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class Case:
    """Caso aberto pela equipe de resposta a incidentes."""

    title: str
    id: str = field(default_factory=_new_id)
    description: str | None = None
    status: CaseStatus = CaseStatus.OPEN
    severity: Severity = Severity.MEDIUM
    alert_ids: tuple[str, ...] = ()
    assignee_id: str | None = None
    tags: frozenset[str] = frozenset()
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    """Entrada cronológica em uma investigação."""

    title: str
    id: str = field(default_factory=_new_id)
    timestamp: datetime = field(default_factory=_utcnow)
    entry_type: str = "note"
    body: str | None = None
    author_id: str | None = None


@dataclass(frozen=True, slots=True)
class InvestigationStep:
    """Etapa de ação dentro de uma investigação."""

    order: int
    kind: str
    title: str
    id: str = field(default_factory=_new_id)
    status: StepStatus = StepStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class Investigation:
    """Estrutura mutable de investigação (steps + timeline)."""

    title: str
    id: str = field(default_factory=_new_id)
    case_id: str | None = None
    status: InvestigationStatus = InvestigationStatus.OPEN
    steps: list[InvestigationStep] = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def add_step(self, step: InvestigationStep) -> None:
        self.steps.append(step)

    def add_timeline_entry(self, entry: TimelineEntry) -> None:
        self.timeline.append(entry)


@dataclass(frozen=True, slots=True)
class Rule:
    """Regra de detecção."""

    name: str
    id: str = field(default_factory=_new_id)
    description: str | None = None
    state: RuleState = RuleState.DRAFT
    severity: Severity = Severity.MEDIUM
    expression: dict[str, Any] = field(default_factory=dict)
    tags: frozenset[str] = frozenset()
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class Team:
    """Equipe de resposta."""

    name: str
    id: str = field(default_factory=_new_id)
    description: str | None = None
    member_ids: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class User:
    """Usuário do SIEM — guarda apenas ``password_hash``, nunca senha pura."""

    username: str
    email: str
    id: str = field(default_factory=_new_id)
    display_name: str | None = None
    roles: frozenset[UserRole] = frozenset()
    teams: frozenset[str] = frozenset()
    active: bool = True
    password_hash: str | None = None
    last_login: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    is_superuser: bool = False


@dataclass(frozen=True, slots=True)
class Notification:
    """Notificação de alerta encaminhada a um canal."""

    alert_id: str
    channel: str
    id: str = field(default_factory=_new_id)
    recipient: str | None = None
    status: NotificationStatus = NotificationStatus.PENDING
    subject: str | None = None
    body: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    sent_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RawEvent:
    """Evento bruto oriundo de uma fonte de coleta."""

    source: str
    raw_payload: bytes | str
    id: str = field(default_factory=_new_id)
    timestamp: datetime = field(default_factory=_utcnow)
    normalized: bool = False
    tags: frozenset[str] = frozenset()
    risk_score: RiskScore = RiskScore(0)


__all__ = [
    "IOC",
    "Alert",
    "AlertStatus",
    "Asset",
    "AssetGroup",
    "Case",
    "CaseStatus",
    "ConfidenceLevel",
    "EventType",
    "IOCKind",
    "Investigation",
    "InvestigationStatus",
    "InvestigationStep",
    "LifecycleStatus",
    "Notification",
    "NotificationStatus",
    "RawEvent",
    "RiskScore",
    "Rule",
    "RuleState",
    "Severity",
    "StepStatus",
    "Team",
    "TimelineEntry",
    "User",
    "UserRole",
]
