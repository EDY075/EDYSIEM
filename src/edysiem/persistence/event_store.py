"""Event Store do EDY SIEM.

Persiste todo evento que trafega pela pipeline: RawEvent, CanonicalEvent,
EnrichedEvent, CorrelatedEvent, DetectionFinding, Alert, Incident, Case.

Cada evento registrado carrega:
- ``event_id`` (UUID)
- ``timestamp``
- ``correlation_id``
- ``pipeline_stage``
- ``version``
- ``source``
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from edysiem._utils import new_id as _new_id
from edysiem._utils import utcnow as _utcnow
from edysiem.persistence.connection import ConnectionManager
from edysiem.persistence.query import Page, QueryFilter


class PipelineStage:
    """Estagios da pipeline (nomes estaveis)."""

    RAW = "raw"
    CANONICAL = "canonical"
    ENRICHED = "enriched"
    CORRELATED = "correlated"
    DETECTION_FINDING = "detection_finding"
    ALERT = "alert"
    INCIDENT = "incident"
    CASE = "case"


@dataclass(frozen=True, slots=True)
class StoredEvent:
    """Evento persistido no Event Store.

    Attributes:
        event_id: UUID do evento.
        timestamp: Carimbo (UTC) do evento na pipeline.
        correlation_id: ID de correlacao (trace_id/agregacao).
        pipeline_stage: Estagio da pipeline.
        version: Versao da plataforma.
        source: Origem (ex.: "detection", "incident").
        event_type: Tipo do evento (ex.: "Alert", "CanonicalEvent").
        payload: Dados serializados do evento.
        created_at: Carimbo de persistencia.
    """

    event_id: str
    timestamp: datetime
    correlation_id: str
    pipeline_stage: str
    version: str
    source: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)


class EventRepository:
    """Persiste eventos da pipeline em SQLite (append-only)."""

    TABLE = "events"

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    def append(self, event: StoredEvent) -> StoredEvent:
        """Persiste um evento (append-only)."""
        conn = self._manager.connect()
        conn.execute(
            f"INSERT INTO {self.TABLE} (event_id, timestamp, correlation_id, "
            "pipeline_stage, version, source, event_type, payload, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.timestamp.isoformat(),
                event.correlation_id,
                event.pipeline_stage,
                event.version,
                event.source,
                event.event_type,
                json.dumps(event.payload, ensure_ascii=False, default=str),
                event.created_at.isoformat(),
            ),
        )
        return event

    def get(self, event_id: str) -> StoredEvent | None:
        conn = self._manager.connect()
        row = conn.execute(f"SELECT * FROM {self.TABLE} WHERE event_id = ?", (event_id,)).fetchone()
        return self._from_row(row) if row else None

    def by_correlation(self, correlation_id: str) -> list[StoredEvent]:
        """Retorna todos os eventos de uma correlacao (ordenados por tempo)."""
        conn = self._manager.connect()
        rows = conn.execute(
            f"SELECT * FROM {self.TABLE} WHERE correlation_id = ? ORDER BY timestamp ASC",
            (correlation_id,),
        ).fetchall()
        return [self._from_row(r) for r in rows]

    def by_stage(self, stage: str) -> list[StoredEvent]:
        """Retorna eventos de um estagio da pipeline."""
        conn = self._manager.connect()
        rows = conn.execute(
            f"SELECT * FROM {self.TABLE} WHERE pipeline_stage = ? ORDER BY timestamp DESC",
            (stage,),
        ).fetchall()
        return [self._from_row(r) for r in rows]

    def count(self) -> int:
        """Total de eventos persistidos."""
        conn = self._manager.connect()
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {self.TABLE}").fetchone()
        return int(row["c"])

    def query(
        self,
        *,
        stage: str | None = None,
        correlation_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[StoredEvent]:
        """Consulta paginada com filtros opcionais."""
        filters: list[QueryFilter] = []
        if stage:
            filters.append(QueryFilter(field="pipeline_stage", value=stage))
        if correlation_id:
            filters.append(QueryFilter(field="correlation_id", value=correlation_id))

        where = ""
        params: list[Any] = []
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

    def _from_row(self, row: sqlite3.Row) -> StoredEvent:
        return StoredEvent(
            event_id=row["event_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            correlation_id=row["correlation_id"],
            pipeline_stage=row["pipeline_stage"],
            version=row["version"],
            source=row["source"],
            event_type=row["event_type"],
            payload=json.loads(row["payload"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )


class EventStore:
    """Camada de alto nivel para persistir eventos da pipeline.

    Args:
        repository: Repositorio de eventos.
        version: Versao da plataforma (registrada em cada evento).
    """

    def __init__(
        self,
        repository: EventRepository,
        version: str = "0.1.0",
    ) -> None:
        self._repo = repository
        self._version = version

    @property
    def repository(self) -> EventRepository:
        """Repositorio de eventos."""
        return self._repo

    def record(
        self,
        *,
        stage: str,
        correlation_id: str,
        source: str,
        event_type: str,
        payload: dict[str, Any],
        timestamp: datetime | None = None,
        event_id: str | None = None,
    ) -> StoredEvent:
        """Registra um evento da pipeline."""
        event = StoredEvent(
            event_id=event_id or _new_id(),
            timestamp=timestamp or _utcnow(),
            correlation_id=correlation_id,
            pipeline_stage=stage,
            version=self._version,
            source=source,
            event_type=event_type,
            payload=payload,
        )
        return self._repo.append(event)

    def record_event(
        self, stage: str, obj: object, correlation_id: str, source: str = ""
    ) -> StoredEvent:
        """Registra um objeto de dominio, serializando seus campos-chave."""
        from dataclasses import asdict, is_dataclass

        payload: dict[str, Any]
        if is_dataclass(obj) and not isinstance(obj, type):
            payload = {k: str(v) for k, v in asdict(obj).items() if not k.startswith("_")}
            # nao serializar estruturas aninhadas grandes
            payload = {k: v for k, v in payload.items() if not isinstance(v, (tuple, frozenset))}
        else:
            payload = {"value": str(obj)}

        return self.record(
            stage=stage,
            correlation_id=correlation_id,
            source=source or type(obj).__name__,
            event_type=type(obj).__name__,
            payload=payload,
        )


__all__ = ["EventRepository", "EventStore", "PipelineStage", "StoredEvent"]
