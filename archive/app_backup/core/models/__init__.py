"""Entidades de domínio — dataclasses imutáveis, sem lógica de infraestrutura."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    TRIAGE = "TRIAGE"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Role(str, Enum):
    ANALYST = "analyst"
    ADMIN = "admin"


class HealthStatus(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class IocType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH = "hash"
    EMAIL = "email"


def utc_now() -> datetime:
    return datetime.now().astimezone()


@dataclass(frozen=True)
class CanonicalEvent:
    """Evento canônico normalizado — imutável."""

    event_id: str
    timestamp: datetime
    source_type: str
    source_host: str
    event_type: str
    severity: Severity = Severity.INFO
    user: str | None = None
    process: str | None = None
    ip_src: str | None = None
    ip_dst: str | None = None
    hostname: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    trace_id: str = ""
    normalized_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class MitreRef:
    tactic: str
    technique: str


@dataclass(frozen=True)
class Alert:
    alert_id: str
    rule_id: str
    severity: Severity
    status: AlertStatus = AlertStatus.OPEN
    mitre: MitreRef | None = None
    entities: dict[str, str] = field(default_factory=dict)
    evidence_ids: list[str] = field(default_factory=list)
    first_seen: datetime = field(default_factory=utc_now)
    last_seen: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Asset:
    asset_id: str
    hostname: str
    ip: str
    os: str | None = None
    criticality: Severity = Severity.LOW
    tags: list[str] = field(default_factory=list)
    last_seen: datetime | None = None


@dataclass(frozen=True)
class Case:
    case_id: str
    title: str
    status: CaseStatus = CaseStatus.OPEN
    severity: Severity = Severity.MEDIUM
    alert_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Ioc:
    ioc_id: str
    type: IocType
    value: str
    source: str | None = None
    threat_type: str | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Investigation:
    investigation_id: str
    case_id: str
    status: str = "DRAFT"
    timeline_entry_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class DetectionRule:
    rule_id: str
    name: str
    severity: Severity = Severity.MEDIUM
    mitre: MitreRef | None = None
    condition: dict[str, Any] = field(default_factory=dict)
    timeframe_s: int = 300
    enabled: bool = True
    version: int = 1


@dataclass(frozen=True)
class Health:
    component: str
    status: HealthStatus = HealthStatus.ONLINE
    checked_at: datetime = field(default_factory=utc_now)
    message: str | None = None


@dataclass(frozen=True)
class User:
    user_id: str
    username: str
    role: Role = Role.ANALYST
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class TimelineEntry:
    entry_id: str
    ref_id: str | None = None
    title: str = ""
    at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Notification:
    notification_id: str
    channel: str
    target: str
    subject: str
    body: str
    created_at: datetime = field(default_factory=utc_now)
