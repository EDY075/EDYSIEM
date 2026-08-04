"""Implementacao SQLite do CaseRepository (CRUD + consultas)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from edysiem.cases import (
    Case,
    CaseAttachment,
    CaseComment,
    CaseEvidence,
    CaseEvidenceKind,
    CasePriority,
    CaseSeverity,
    CaseStatus,
    CaseTask,
    CaseTaskStatus,
    CaseTimelineEntry,
    Playbook,
    PlaybookStep,
)
from edysiem.domain import RiskScore
from edysiem.persistence.connection import ConnectionManager
from edysiem.persistence.query import Page, QueryFilter, QueryOp, SortOrder
from edysiem.persistence.repository import GenericRepository

_COLUMNS = [
    "id",
    "title",
    "description",
    "owner",
    "status",
    "severity",
    "priority",
    "risk_score",
    "incident_id",
    "alerts",
    "assets",
    "users",
    "iocs",
    "mitre",
    "timeline",
    "comments",
    "attachments",
    "tasks",
    "evidences",
    "playbook",
    "resolution",
    "created_at",
    "updated_at",
    "closed_at",
]


class CaseRepository(GenericRepository[Case]):
    """Persiste ``Case`` em SQLite."""

    TABLE = "cases"

    def __init__(self, manager: ConnectionManager) -> None:
        super().__init__(manager)

    # --- Consultas especificas ---------------------------------------------

    def by_status(self, status: CaseStatus, *, limit: int = 50, offset: int = 0) -> Page[Case]:
        """Busca cases por status."""
        return self.query(
            [QueryFilter(field="status", value=status.value)],
            limit=limit,
            offset=offset,
        )

    def by_incident(self, incident_id: str, *, limit: int = 50, offset: int = 0) -> Page[Case]:
        """Busca cases vinculados a um incidente."""
        return self.query(
            [QueryFilter(field="incident_id", value=incident_id)],
            limit=limit,
            offset=offset,
        )

    def by_owner(self, owner: str, *, limit: int = 50, offset: int = 0) -> Page[Case]:
        """Busca cases por responsavel."""
        return self.query(
            [QueryFilter(field="owner", value=owner)],
            limit=limit,
            offset=offset,
        )

    def by_date_range(
        self, start: datetime, end: datetime, *, limit: int = 50, offset: int = 0
    ) -> Page[Case]:
        """Busca cases em um intervalo de criacao."""
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

    def _to_row(self, c: Case) -> tuple[Any, ...]:
        playbook = None
        if c.playbook:
            playbook = json.dumps(
                {
                    "name": c.playbook.name,
                    "description": c.playbook.description,
                    "steps": [
                        {"order": s.order, "title": s.title, "description": s.description}
                        for s in c.playbook.steps
                    ],
                }
            )
        return (
            c.id,
            c.title,
            c.description,
            c.owner,
            c.status.value,
            c.severity.value,
            c.priority.value,
            c.risk_score.value,
            c.incident_id,
            json.dumps(list(c.alerts)),
            json.dumps(list(c.assets)),
            json.dumps(list(c.users)),
            json.dumps(list(c.iocs)),
            json.dumps(list(c.mitre)),
            json.dumps(
                [
                    {
                        "action": e.action,
                        "detail": e.detail,
                        "actor": e.actor,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in c.timeline
                ]
            ),
            json.dumps(
                [
                    {"body": n.body, "author": n.author, "created_at": n.created_at.isoformat()}
                    for n in c.comments
                ]
            ),
            json.dumps(
                [
                    {
                        "name": a.name,
                        "content_type": a.content_type,
                        "size": a.size,
                        "url": a.url,
                        "added_by": a.added_by,
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in c.attachments
                ]
            ),
            json.dumps(
                [
                    {
                        "id": t.id,
                        "title": t.title,
                        "status": t.status.value,
                        "priority": t.priority.value,
                        "assignee": t.assignee,
                        "due_at": t.due_at.isoformat() if t.due_at else None,
                        "created_by": t.created_by,
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in c.tasks
                ]
            ),
            json.dumps(
                [
                    {
                        "kind": e.kind.value,
                        "value": e.value,
                        "label": e.label,
                        "source": e.source,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in c.evidences
                ]
            ),
            playbook,
            c.resolution,
            c.created_at.isoformat(),
            c.updated_at.isoformat(),
            c.closed_at.isoformat() if c.closed_at else None,
        )

    def _from_row(self, row: sqlite3.Row) -> Case:
        def _timeline(raw: str) -> tuple[CaseTimelineEntry, ...]:
            return tuple(
                CaseTimelineEntry(
                    action=d["action"],
                    detail=d["detail"],
                    actor=d["actor"],
                    created_at=datetime.fromisoformat(d["created_at"]),
                )
                for d in json.loads(raw)
            )

        comments = tuple(
            CaseComment(
                body=d["body"],
                author=d["author"],
                created_at=datetime.fromisoformat(d["created_at"]),
            )
            for d in json.loads(row["comments"])
        )
        attachments = tuple(
            CaseAttachment(
                name=d["name"],
                content_type=d.get("content_type", ""),
                size=d.get("size", 0),
                url=d.get("url", ""),
                added_by=d.get("added_by", "system"),
                created_at=datetime.fromisoformat(d["created_at"]),
            )
            for d in json.loads(row["attachments"])
        )
        tasks = tuple(
            CaseTask(
                id=d["id"],
                title=d["title"],
                status=CaseTaskStatus(d["status"]),
                priority=CasePriority(d["priority"]),
                assignee=d.get("assignee"),
                due_at=datetime.fromisoformat(d["due_at"]) if d.get("due_at") else None,
                created_by=d.get("created_by", "system"),
                created_at=datetime.fromisoformat(d["created_at"]),
            )
            for d in json.loads(row["tasks"])
        )
        evidences = tuple(
            CaseEvidence(
                kind=CaseEvidenceKind(d["kind"]),
                value=d["value"],
                label=d.get("label", ""),
                source=d.get("source", "analyst"),
                created_at=datetime.fromisoformat(d["created_at"]),
            )
            for d in json.loads(row["evidences"])
        )

        playbook = None
        if row["playbook"]:
            pb = json.loads(row["playbook"])
            playbook = Playbook(
                name=pb["name"],
                description=pb.get("description", ""),
                steps=tuple(
                    PlaybookStep(
                        order=s["order"], title=s["title"], description=s.get("description", "")
                    )
                    for s in pb.get("steps", [])
                ),
            )

        return Case(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            owner=row["owner"],
            status=CaseStatus(row["status"]),
            severity=CaseSeverity(row["severity"]),
            priority=CasePriority(row["priority"]),
            risk_score=RiskScore(row["risk_score"]),
            incident_id=row["incident_id"],
            alerts=tuple(json.loads(row["alerts"])),
            assets=frozenset(json.loads(row["assets"])),
            users=frozenset(json.loads(row["users"])),
            iocs=frozenset(json.loads(row["iocs"])),
            mitre=frozenset(json.loads(row["mitre"])),
            timeline=_timeline(row["timeline"]),
            comments=comments,
            attachments=attachments,
            tasks=tasks,
            evidences=evidences,
            playbook=playbook,
            resolution=row["resolution"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            closed_at=datetime.fromisoformat(row["closed_at"]) if row["closed_at"] else None,
        )

    def _entity_id(self, case: Case) -> str:
        return case.id


__all__ = ["CaseRepository"]
