"""Audit Trail do EDY SIEM.

Registra automaticamente toda alteracao relevante: criacao, atualizacao,
delete logico, mudanca de status, owner, comentarios, evidencias, playbooks.

Nada pode ser perdido: o ``AuditRepository`` persiste em SQLite (schema v3).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from edysiem._utils import new_id as _new_id
from edysiem._utils import utcnow as _utcnow
from edysiem.persistence.connection import ConnectionManager
from edysiem.persistence.query import Page, QueryFilter


class AuditAction(StrEnum):
    """Acoes registradas no audit trail."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"
    OWNER_CHANGE = "owner_change"
    COMMENT = "comment"
    EVIDENCE = "evidence"
    PLAYBOOK = "playbook"
    ATTACHMENT = "attachment"
    TASK = "task"
    RESOLUTION = "resolution"
    REOPEN = "reopen"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Entrada imutavel do audit trail.

    Attributes:
        entry_id: UUID da entrada.
        timestamp: Carimbo (UTC) do evento.
        actor_id: Ator que executou (ex.: "analyst-01", "system").
        action: Acao executada (AuditAction).
        entity_type: Tipo da entidade (ex.: "Alert", "Case").
        entity_id: ID da entidade.
        previous: Valor anterior (ex.: status antigo).
        current: Valor atual.
        details: Detalhes adicionais (ex.: comentario, evidencia).
        correlation_id: Correlacao com a pipeline.
    """

    entry_id: str
    timestamp: datetime
    actor_id: str
    action: AuditAction
    entity_type: str
    entity_id: str
    previous: str | None = None
    current: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""

    def __post_init__(self) -> None:
        if not self.actor_id or not self.actor_id.strip():
            raise ValueError("actor_id nao pode ser vazio")
        if not self.entity_type or not self.entity_type.strip():
            raise ValueError("entity_type nao pode ser vazio")
        if not self.entity_id or not self.entity_id.strip():
            raise ValueError("entity_id nao pode ser vazio")


class AuditRepository:
    """Persiste ``AuditEntry`` em SQLite (append-only)."""

    TABLE = "audit_entries"

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    def append(self, entry: AuditEntry) -> AuditEntry:
        conn = self._manager.connect()
        conn.execute(
            f"INSERT INTO {self.TABLE} (entry_id, timestamp, actor_id, action, "
            "entity_type, entity_id, previous, current, details, correlation_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                entry.entry_id,
                entry.timestamp.isoformat(),
                entry.actor_id,
                entry.action.value,
                entry.entity_type,
                entry.entity_id,
                entry.previous,
                entry.current,
                json.dumps(entry.details, ensure_ascii=False, default=str),
                entry.correlation_id,
            ),
        )
        return entry

    def get(self, entry_id: str) -> AuditEntry | None:
        conn = self._manager.connect()
        row = conn.execute(f"SELECT * FROM {self.TABLE} WHERE entry_id = ?", (entry_id,)).fetchone()
        return self._from_row(row) if row else None

    def by_entity(self, entity_type: str, entity_id: str) -> list[AuditEntry]:
        """Retorna todas as entradas de uma entidade (mais recentes primeiro)."""
        conn = self._manager.connect()
        rows = conn.execute(
            f"SELECT * FROM {self.TABLE} WHERE entity_type = ? AND entity_id = ? "
            f"ORDER BY timestamp DESC",
            (entity_type, entity_id),
        ).fetchall()
        return [self._from_row(r) for r in rows]

    def by_action(self, action: AuditAction) -> list[AuditEntry]:
        """Retorna entradas de uma acao."""
        conn = self._manager.connect()
        rows = conn.execute(
            f"SELECT * FROM {self.TABLE} WHERE action = ? ORDER BY timestamp DESC",
            (action.value,),
        ).fetchall()
        return [self._from_row(r) for r in rows]

    def count(self) -> int:
        conn = self._manager.connect()
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {self.TABLE}").fetchone()
        return int(row["c"])

    def query(
        self,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action: AuditAction | None = None,
        actor_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[AuditEntry]:
        """Consulta paginada de entradas de auditoria."""
        filters: list[QueryFilter] = []
        if entity_type:
            filters.append(QueryFilter(field="entity_type", value=entity_type))
        if entity_id:
            filters.append(QueryFilter(field="entity_id", value=entity_id))
        if action:
            filters.append(QueryFilter(field="action", value=action.value))
        if actor_id:
            filters.append(QueryFilter(field="actor_id", value=actor_id))

        where, params = "", []
        if filters:
            clauses = []
            for i, f in enumerate(filters):
                sql, p = f.to_sql(i)
                clauses.append(sql)
                params.extend(p)
            where = "WHERE " + " AND ".join(clauses)

        conn = self._manager.connect()
        total = conn.execute(f"SELECT COUNT(*) AS c FROM {self.TABLE} {where}", params).fetchone()[
            "c"
        ]
        rows = conn.execute(
            f"SELECT * FROM {self.TABLE} {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()

        return Page(
            items=[self._from_row(r) for r in rows],
            total=int(total),
            offset=offset,
            limit=limit,
        )

    def _from_row(self, row: sqlite3.Row) -> AuditEntry:
        return AuditEntry(
            entry_id=row["entry_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            actor_id=row["actor_id"],
            action=AuditAction(row["action"]),
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            previous=row["previous"],
            current=row["current"],
            details=json.loads(row["details"] or "{}"),
            correlation_id=row["correlation_id"] or "",
        )


class AuditEngine:
    """Camada de alto nivel para registrar alteracoes.

    Args:
        repository: Repositorio de auditoria.
    """

    def __init__(self, repository: AuditRepository) -> None:
        self._repo = repository

    @property
    def repository(self) -> AuditRepository:
        """Repositorio de auditoria."""
        return self._repo

    def record(
        self,
        *,
        actor: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        previous: str | None = None,
        current: str | None = None,
        details: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        """Registra uma entrada de auditoria."""
        entry = AuditEntry(
            entry_id=_new_id(),
            timestamp=_utcnow(),
            actor_id=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            previous=previous,
            current=current,
            details=details or {},
            correlation_id=correlation_id,
        )
        return self._repo.append(entry)

    # --- Conveniencias ----------------------------------------------------

    def record_create(
        self, actor: str, entity_type: str, entity_id: str, **details: Any
    ) -> AuditEntry:
        return self.record(
            actor=actor,
            action=AuditAction.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

    def record_update(
        self, actor: str, entity_type: str, entity_id: str, **details: Any
    ) -> AuditEntry:
        return self.record(
            actor=actor,
            action=AuditAction.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

    def record_delete(
        self, actor: str, entity_type: str, entity_id: str, **details: Any
    ) -> AuditEntry:
        return self.record(
            actor=actor,
            action=AuditAction.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

    def record_status_change(
        self, actor: str, entity_type: str, entity_id: str, previous: str, current: str
    ) -> AuditEntry:
        return self.record(
            actor=actor,
            action=AuditAction.STATUS_CHANGE,
            entity_type=entity_type,
            entity_id=entity_id,
            previous=previous,
            current=current,
        )

    def record_owner_change(
        self, actor: str, entity_type: str, entity_id: str, previous: str | None, current: str
    ) -> AuditEntry:
        return self.record(
            actor=actor,
            action=AuditAction.OWNER_CHANGE,
            entity_type=entity_type,
            entity_id=entity_id,
            previous=previous,
            current=current,
        )

    def record_comment(self, actor: str, entity_type: str, entity_id: str, body: str) -> AuditEntry:
        return self.record(
            actor=actor,
            action=AuditAction.COMMENT,
            entity_type=entity_type,
            entity_id=entity_id,
            details={"body": body},
        )

    def record_evidence(
        self, actor: str, entity_type: str, entity_id: str, kind: str, value: str
    ) -> AuditEntry:
        return self.record(
            actor=actor,
            action=AuditAction.EVIDENCE,
            entity_type=entity_type,
            entity_id=entity_id,
            details={"kind": kind, "value": value},
        )


__all__ = ["AuditAction", "AuditEngine", "AuditEntry", "AuditRepository"]
