"""Implementacao SQLite do IncidentRepository (CRUD + consultas)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from edysiem.domain import RiskScore
from edysiem.incidents import (
    Incident,
    IncidentEvidence,
    IncidentFingerprint,
    IncidentPriority,
    IncidentReason,
    IncidentSeverity,
    IncidentStatus,
    IncidentTimelineEntry,
)
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
    "status",
    "first_seen",
    "last_seen",
    "closed_at",
    "occurrences",
    "alerts",
    "assets",
    "users",
    "iocs",
    "mitre",
    "tactics",
    "techniques",
    "tags",
    "timeline",
    "owner",
    "fingerprint_hash",
    "fingerprint_key",
    "reason",
    "evidence",
    "created_at",
    "updated_at",
]


class IncidentRepository(GenericRepository[Incident]):
    """Persiste ``Incident`` em SQLite."""

    TABLE = "incidents"

    def __init__(self, manager: ConnectionManager) -> None:
        super().__init__(manager)

    # --- Consultas especificas ---------------------------------------------

    def by_status(
        self, status: IncidentStatus, *, limit: int = 50, offset: int = 0
    ) -> Page[Incident]:
        """Busca incidentes por status."""
        return self.query(
            [QueryFilter(field="status", value=status.value)],
            limit=limit,
            offset=offset,
        )

    def by_severity(
        self, severity: IncidentSeverity, *, limit: int = 50, offset: int = 0
    ) -> Page[Incident]:
        """Busca incidentes por severidade."""
        return self.query(
            [QueryFilter(field="severity", value=severity.value)],
            limit=limit,
            offset=offset,
        )

    def by_fingerprint(self, fingerprint_hash: str) -> Incident | None:
        """Busca um incidente pelo fingerprint hash."""
        result = self.query(
            [QueryFilter(field="fingerprint_hash", value=fingerprint_hash)],
            limit=1,
        )
        return result.items[0] if result.items else None

    def by_date_range(
        self, start: datetime, end: datetime, *, limit: int = 50, offset: int = 0
    ) -> Page[Incident]:
        """Busca incidentes em um intervalo de criacao."""
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

    def _to_row(self, i: Incident) -> tuple[Any, ...]:
        return (
            i.id,
            i.title,
            i.description,
            i.severity.value,
            i.priority.value,
            i.risk_score.value,
            i.confidence,
            i.status.value,
            i.first_seen.isoformat(),
            i.last_seen.isoformat(),
            i.closed_at.isoformat() if i.closed_at else None,
            i.occurrences,
            json.dumps(list(i.alerts)),
            json.dumps(list(i.assets)),
            json.dumps(list(i.users)),
            json.dumps(list(i.iocs)),
            json.dumps(list(i.mitre)),
            json.dumps(list(i.tactics)),
            json.dumps(list(i.techniques)),
            json.dumps(list(i.tags)),
            json.dumps(
                [
                    {
                        "action": e.action,
                        "detail": e.detail,
                        "actor": e.actor,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in i.timeline
                ]
            ),
            i.owner,
            i.fingerprint.hash if i.fingerprint else None,
            i.fingerprint.key if i.fingerprint else None,
            json.dumps(
                {
                    "criteria": list(i.reason.criteria) if i.reason else [],
                    "alerts_count": i.reason.alerts_count if i.reason else 0,
                    "score": i.reason.score if i.reason else 0,
                }
            )
            if i.reason
            else "{}",
            json.dumps(
                [
                    {
                        "alert_id": e.alert_id,
                        "title": e.title,
                        "rule_id": e.rule_id,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in i.evidence
                ]
            ),
            i.created_at.isoformat(),
            i.updated_at.isoformat(),
        )

    def _from_row(self, row: sqlite3.Row) -> Incident:
        def _entries(raw: str) -> tuple[IncidentTimelineEntry, ...]:
            data = json.loads(raw)
            return tuple(
                IncidentTimelineEntry(
                    action=d["action"],
                    detail=d["detail"],
                    actor=d["actor"],
                    created_at=datetime.fromisoformat(d["created_at"]),
                )
                for d in data
            )

        reason_raw = json.loads(row["reason"] or "{}")
        reason = IncidentReason(
            criteria=frozenset(reason_raw.get("criteria", [])),
            alerts_count=int(reason_raw.get("alerts_count", 0)),
            score=int(reason_raw.get("score", 0)),
        )
        evidence = tuple(
            IncidentEvidence(
                alert_id=d["alert_id"],
                title=d.get("title", ""),
                rule_id=d.get("rule_id", ""),
                created_at=datetime.fromisoformat(d["created_at"]),
            )
            for d in json.loads(row["evidence"])
        )
        fingerprint = None
        if row["fingerprint_hash"]:
            fingerprint = IncidentFingerprint(
                hash=row["fingerprint_hash"], key=row["fingerprint_key"] or ""
            )
        return Incident(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            severity=IncidentSeverity(row["severity"]),
            priority=IncidentPriority(row["priority"]),
            risk_score=RiskScore(row["risk_score"]),
            confidence=row["confidence"],
            status=IncidentStatus(row["status"]),
            first_seen=datetime.fromisoformat(row["first_seen"]),
            last_seen=datetime.fromisoformat(row["last_seen"]),
            closed_at=datetime.fromisoformat(row["closed_at"]) if row["closed_at"] else None,
            occurrences=row["occurrences"],
            alerts=tuple(json.loads(row["alerts"])),
            assets=frozenset(json.loads(row["assets"])),
            users=frozenset(json.loads(row["users"])),
            iocs=frozenset(json.loads(row["iocs"])),
            mitre=frozenset(json.loads(row["mitre"])),
            tactics=frozenset(json.loads(row["tactics"])),
            techniques=frozenset(json.loads(row["techniques"])),
            tags=frozenset(json.loads(row["tags"])),
            timeline=_entries(row["timeline"]),
            owner=row["owner"],
            fingerprint=fingerprint,
            reason=reason,
            evidence=evidence,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _entity_id(self, incident: Incident) -> str:
        return incident.id


__all__ = ["IncidentRepository"]
