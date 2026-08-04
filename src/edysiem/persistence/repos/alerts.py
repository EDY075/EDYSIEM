"""Implementacao SQLite do AlertRepository (CRUD + consultas)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from edysiem.alerts import Alert, AlertFingerprint, AlertLifecycle, AlertSeverity
from edysiem.alerts.models import AlertPriority, AlertTimelineEntry
from edysiem.domain import RiskScore
from edysiem.persistence.connection import ConnectionManager
from edysiem.persistence.query import Page, QueryFilter, QueryOp, SortOrder
from edysiem.persistence.repository import GenericRepository

_COLUMNS = [
    "id",
    "title",
    "description",
    "severity",
    "priority",
    "risk_score",
    "confidence",
    "first_seen",
    "last_seen",
    "occurrences",
    "status",
    "source",
    "rule_id",
    "fingerprint_hash",
    "fingerprint_key",
    "event_ids",
    "tags",
    "mitre",
    "asset_id",
    "user",
    "ioc_ids",
    "timeline",
    "created_at",
    "updated_at",
]


class AlertRepository(GenericRepository[Alert]):
    """Persiste ``Alert`` em SQLite."""

    TABLE = "alerts"

    def __init__(self, manager: ConnectionManager) -> None:
        super().__init__(manager)

    # --- Consultas especificas ---------------------------------------------

    def by_fingerprint(self, fingerprint_hash: str) -> Alert | None:
        """Busca um alerta pelo fingerprint hash."""
        result = self.query(
            [QueryFilter(field="fingerprint_hash", value=fingerprint_hash)],
            limit=1,
        )
        return result.items[0] if result.items else None

    def by_status(self, status: AlertLifecycle, *, limit: int = 50, offset: int = 0) -> Page[Alert]:
        """Busca alertas por status do ciclo de vida."""
        return self.query(
            [QueryFilter(field="status", value=status.value)],
            limit=limit,
            offset=offset,
        )

    def by_severity(
        self, severity: AlertSeverity, *, limit: int = 50, offset: int = 0
    ) -> Page[Alert]:
        """Busca alertas por severidade."""
        return self.query(
            [QueryFilter(field="severity", value=severity.value)],
            limit=limit,
            offset=offset,
        )

    def by_rule(self, rule_id: str, *, limit: int = 50, offset: int = 0) -> Page[Alert]:
        """Busca alertas por regra."""
        return self.query(
            [QueryFilter(field="rule_id", value=rule_id)],
            limit=limit,
            offset=offset,
        )

    def by_date_range(
        self,
        start: datetime,
        end: datetime,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[Alert]:
        """Busca alertas em um intervalo de criacao."""
        return self.query(
            [
                QueryFilter(field="created_at", op=QueryOp.GTE, value=start.isoformat()),
                QueryFilter(field="created_at", op=QueryOp.LTE, value=end.isoformat()),
            ],
            sort_by="created_at",
            order=SortOrder.DESC,
            limit=limit,
            offset=offset,
        )

    # --- GenericRepository ------------------------------------------------

    def _row_fields(self) -> list[str]:
        return _COLUMNS

    def _to_row(self, alert: Alert) -> tuple[Any, ...]:
        return (
            alert.id,
            alert.title,
            alert.description,
            alert.severity.value,
            alert.priority.value,
            alert.risk_score.value,
            alert.confidence,
            alert.first_seen.isoformat(),
            alert.last_seen.isoformat(),
            alert.occurrences,
            alert.status.value,
            alert.source,
            alert.rule_id,
            alert.fingerprint.hash if alert.fingerprint else None,
            alert.fingerprint.rule_id if alert.fingerprint else None,
            json.dumps(list(alert.event_ids)),
            json.dumps(list(alert.tags)),
            json.dumps(list(alert.mitre)),
            alert.asset_id,
            alert.user,
            json.dumps(list(alert.ioc_ids)),
            self._serialize_timeline(alert.timeline),
            alert.created_at.isoformat(),
            alert.updated_at.isoformat(),
        )

    def _from_row(self, row: sqlite3.Row) -> Alert:
        fingerprint = None
        if row["fingerprint_hash"]:
            fingerprint = AlertFingerprint(
                hash=row["fingerprint_hash"],
                rule_id=row["fingerprint_key"] or "",
            )
        return Alert(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            severity=AlertSeverity(row["severity"]),
            priority=AlertPriority(row["priority"]),
            risk_score=RiskScore(row["risk_score"]),
            confidence=row["confidence"],
            first_seen=datetime.fromisoformat(row["first_seen"]),
            last_seen=datetime.fromisoformat(row["last_seen"]),
            occurrences=row["occurrences"],
            status=AlertLifecycle(row["status"]),
            source=row["source"],
            rule_id=row["rule_id"],
            fingerprint=fingerprint,
            event_ids=tuple(json.loads(row["event_ids"])),
            tags=frozenset(json.loads(row["tags"])),
            mitre=frozenset(json.loads(row["mitre"])),
            asset_id=row["asset_id"],
            user=row["user"],
            ioc_ids=tuple(json.loads(row["ioc_ids"])),
            timeline=self._deserialize_timeline(row["timeline"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _entity_id(self, alert: Alert) -> str:
        return alert.id

    @staticmethod
    def _serialize_timeline(timeline: tuple[AlertTimelineEntry, ...]) -> str:
        return json.dumps(
            [
                {
                    "action": e.action,
                    "detail": e.detail,
                    "actor": e.actor,
                    "created_at": e.created_at.isoformat(),
                }
                for e in timeline
            ]
        )

    @staticmethod
    def _deserialize_timeline(raw: str) -> tuple[AlertTimelineEntry, ...]:
        data = json.loads(raw)
        return tuple(
            AlertTimelineEntry(
                action=d["action"],
                detail=d["detail"],
                actor=d["actor"],
                created_at=datetime.fromisoformat(d["created_at"]),
            )
            for d in data
        )


__all__ = ["AlertRepository"]
