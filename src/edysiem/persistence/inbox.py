"""Durable, idempotent inbox for external event producers."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from typing import Literal, cast

from .connection import ConnectionManager
from .exceptions import PersistenceError
from .transactions import Transaction

InboxItemStatus = Literal["accepted", "duplicate", "rejected"]


class IdempotencyConflictError(PersistenceError):
    """An idempotency key was reused with different content."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"idempotency conflict for {identifier}")


@dataclass(frozen=True, slots=True)
class InboxEvent:
    """Validated and normalized event ready for durable acceptance."""

    index: int
    source_instance_id: str
    event_id: str
    batch_id: str
    content_hash: str
    schema_version: str
    source_product: str
    source_product_version: str
    source_component: str
    event_type: str
    severity: str
    event_timestamp: str
    received_at: str
    sequence: int
    asset_id: str
    hostname: str
    ip: str | None
    os: str | None
    payload: dict[str, object]
    normalized_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class InboxItemError:
    """Safe, client-facing validation error for one batch item."""

    code: str
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class InboxItemResult:
    """Per-item acknowledgement persisted with the batch receipt."""

    index: int
    event_id: str | None
    status: InboxItemStatus
    error: InboxItemError | None = None


@dataclass(frozen=True, slots=True)
class InboxBatchResult:
    """Stable response for a batch, including invalid item acknowledgements."""

    batch_id: str
    accepted_count: int
    duplicate_count: int
    rejected_count: int
    results: tuple[InboxItemResult, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible response, omitting absent errors."""

        items: list[dict[str, object]] = []
        for result in self.results:
            item: dict[str, object] = {
                "event_id": result.event_id,
                "status": result.status,
            }
            if result.error is not None:
                item["error"] = asdict(result.error)
            items.append(item)
        return {
            "batch_id": self.batch_id,
            "accepted_count": self.accepted_count,
            "duplicate_count": self.duplicate_count,
            "rejected_count": self.rejected_count,
            "results": items,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> InboxBatchResult:
        """Rehydrate a previously persisted batch response."""

        raw_results = value.get("results", [])
        if not isinstance(raw_results, list):
            raise PersistenceError("stored ingestion response is invalid")
        results: list[InboxItemResult] = []
        for index, raw_item in enumerate(raw_results):
            if not isinstance(raw_item, dict):
                raise PersistenceError("stored ingestion item response is invalid")
            raw_error = raw_item.get("error")
            error = None
            if isinstance(raw_error, dict):
                error = InboxItemError(
                    code=str(raw_error.get("code", "validation_error")),
                    field=str(raw_error.get("field", "")),
                    message=str(raw_error.get("message", "invalid event")),
                )
            status = str(raw_item.get("status", "rejected"))
            if status not in {"accepted", "duplicate", "rejected"}:
                raise PersistenceError("stored ingestion item status is invalid")
            results.append(
                InboxItemResult(
                    index=index,
                    event_id=(
                        str(raw_item["event_id"])
                        if raw_item.get("event_id") is not None
                        else None
                    ),
                    status=cast(InboxItemStatus, status),
                    error=error,
                )
            )
        return cls(
            batch_id=str(value["batch_id"]),
            accepted_count=cls._required_count(value, "accepted_count"),
            duplicate_count=cls._required_count(value, "duplicate_count"),
            rejected_count=cls._required_count(value, "rejected_count"),
            results=tuple(results),
        )

    @staticmethod
    def _required_count(value: dict[str, object], key: str) -> int:
        candidate = value.get(key)
        if isinstance(candidate, bool) or not isinstance(candidate, int) or candidate < 0:
            raise PersistenceError(f"stored ingestion {key} is invalid")
        return candidate


class ShieldInboxRepository:
    """Atomic batch receipt and event inbox for EDY Shield."""

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    @property
    def manager(self) -> ConnectionManager:
        """Underlying connection manager, exposed for health/tests."""

        return self._manager

    def replay(self, batch_id: str, content_hash: str) -> InboxBatchResult | None:
        """Return a stable response for an identical prior batch."""

        row = self._manager.connect().execute(
            "SELECT content_hash, response_payload FROM ingestion_batches WHERE batch_id = ?",
            (batch_id,),
        ).fetchone()
        if row is None:
            return None
        if row["content_hash"] != content_hash:
            raise IdempotencyConflictError(f"batch:{batch_id}")
        try:
            payload = json.loads(row["response_payload"])
        except (TypeError, ValueError) as exc:
            raise PersistenceError("stored ingestion response cannot be decoded") from exc
        if not isinstance(payload, dict):
            raise PersistenceError("stored ingestion response is not an object")
        return InboxBatchResult.from_dict(payload)

    def accept(
        self,
        *,
        batch_id: str,
        batch_hash: str,
        received_at: str,
        events: list[InboxEvent],
        rejected: list[InboxItemResult],
    ) -> InboxBatchResult:
        """Persist accepted events and the batch response in one transaction."""

        conn = self._manager.connect()
        try:
            # IMMEDIATE serializes competing receivers before idempotency checks,
            # preventing a race between SELECT and INSERT across worker threads.
            with Transaction(conn, immediate=True):
                existing_batch = conn.execute(
                    "SELECT content_hash, response_payload FROM ingestion_batches "
                    "WHERE batch_id = ?",
                    (batch_id,),
                ).fetchone()
                if existing_batch is not None:
                    if existing_batch["content_hash"] != batch_hash:
                        raise IdempotencyConflictError(f"batch:{batch_id}")
                    payload = json.loads(existing_batch["response_payload"])
                    if not isinstance(payload, dict):
                        raise PersistenceError("stored ingestion response is not an object")
                    return InboxBatchResult.from_dict(payload)

                statuses: list[InboxItemResult] = list(rejected)
                accepted: list[InboxEvent] = []
                seen: dict[tuple[str, str], str] = {}
                for event in sorted(events, key=lambda item: item.index):
                    key = (event.source_instance_id, event.event_id)
                    seen_hash = seen.get(key)
                    if seen_hash is not None:
                        if seen_hash != event.content_hash:
                            raise IdempotencyConflictError(f"event:{event.event_id}")
                        statuses.append(
                            InboxItemResult(event.index, event.event_id, "duplicate")
                        )
                        continue

                    row = conn.execute(
                        "SELECT content_hash FROM ingestion_inbox "
                        "WHERE source_instance_id = ? AND event_id = ?",
                        key,
                    ).fetchone()
                    if row is not None:
                        if row["content_hash"] != event.content_hash:
                            raise IdempotencyConflictError(f"event:{event.event_id}")
                        statuses.append(
                            InboxItemResult(event.index, event.event_id, "duplicate")
                        )
                        seen[key] = event.content_hash
                        continue

                    seen[key] = event.content_hash
                    accepted.append(event)
                    statuses.append(InboxItemResult(event.index, event.event_id, "accepted"))

                statuses.sort(key=lambda item: item.index)
                result = InboxBatchResult(
                    batch_id=batch_id,
                    accepted_count=sum(item.status == "accepted" for item in statuses),
                    duplicate_count=sum(item.status == "duplicate" for item in statuses),
                    rejected_count=sum(item.status == "rejected" for item in statuses),
                    results=tuple(statuses),
                )
                response_payload = json.dumps(
                    result.as_dict(),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                conn.execute(
                    "INSERT INTO ingestion_batches "
                    "(batch_id, source, content_hash, received_at, response_payload) "
                    "VALUES (?, 'edy-shield', ?, ?, ?)",
                    (batch_id, batch_hash, received_at, response_payload),
                )
                for event in accepted:
                    self._insert_event(conn, event)
                return result
        except IdempotencyConflictError:
            raise
        except (sqlite3.Error, TypeError, ValueError) as exc:
            raise PersistenceError("failed to persist EDY Shield ingestion batch") from exc

    def get_event(self, source_instance_id: str, event_id: str) -> dict[str, object] | None:
        """Return one inbox row as decoded data for processing/investigation."""

        row = self._manager.connect().execute(
            "SELECT * FROM ingestion_inbox WHERE source_instance_id = ? AND event_id = ?",
            (source_instance_id, event_id),
        ).fetchone()
        if row is None:
            return None
        value = dict(row)
        value["payload"] = json.loads(str(value["payload"]))
        value["normalized_payload"] = json.loads(str(value["normalized_payload"]))
        return value

    def count(self) -> int:
        """Return the number of unique accepted inbox events."""

        row = self._manager.connect().execute(
            "SELECT COUNT(*) AS total FROM ingestion_inbox"
        ).fetchone()
        return int(row["total"]) if row is not None else 0

    @staticmethod
    def _insert_event(conn: sqlite3.Connection, event: InboxEvent) -> None:
        conn.execute(
            """
            INSERT INTO ingestion_inbox (
                source_instance_id, event_id, batch_id, content_hash, schema_version,
                source_product, source_product_version, source_component, event_type,
                severity, event_timestamp, received_at, sequence, asset_id, hostname,
                ip, os, payload, normalized_payload, processing_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                event.source_instance_id,
                event.event_id,
                event.batch_id,
                event.content_hash,
                event.schema_version,
                event.source_product,
                event.source_product_version,
                event.source_component,
                event.event_type,
                event.severity,
                event.event_timestamp,
                event.received_at,
                event.sequence,
                event.asset_id,
                event.hostname,
                event.ip,
                event.os,
                json.dumps(
                    event.payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                json.dumps(
                    event.normalized_payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            ),
        )


__all__ = [
    "IdempotencyConflictError",
    "InboxBatchResult",
    "InboxEvent",
    "InboxItemError",
    "InboxItemResult",
    "InboxItemStatus",
    "ShieldInboxRepository",
]
