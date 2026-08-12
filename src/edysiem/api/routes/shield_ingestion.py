"""EDY Shield batch ingestion endpoint backed by a durable inbox."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ...persistence import (
    IdempotencyConflictError,
    InboxBatchResult,
    InboxEvent,
    InboxItemError,
    InboxItemResult,
    PersistenceError,
    ShieldInboxRepository,
)
from ..deps import get_shield_inbox
from ..ingestion_schemas import (
    MAX_BATCH_BYTES,
    MAX_EVENT_BYTES,
    ShieldBatchEnvelopeV1,
    ShieldEventV1,
    ShieldIngestionBatchResponseV1,
    canonical_json_bytes,
)
from ..security import rate_limit, require_shield_ingest_token
from ..shield_normalizer import canonical_event_payload, normalize_shield_event

router = APIRouter(tags=["ingestion"])


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON numeric constant: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


async def _read_body(request: Request) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            parsed_length = int(content_length)
            if parsed_length < 0:
                raise HTTPException(status_code=400, detail="invalid Content-Length")
            if parsed_length > MAX_BATCH_BYTES:
                raise HTTPException(status_code=413, detail="payload exceeds 1 MiB")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid Content-Length") from exc

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_BATCH_BYTES:
            raise HTTPException(status_code=413, detail="payload exceeds 1 MiB")
    return bytes(body)


def _validation_error(exc: ValidationError) -> InboxItemError:
    first = exc.errors(include_url=False, include_context=False)[0]
    location = [str(part) for part in first.get("loc", ())]
    field = ".".join(part for part in location if part not in {"body", "events"})
    leaf = location[-1] if location else "event"
    code_by_field = {
        "schema_version": "unsupported_schema_version",
        "event_type": "invalid_event_type",
        "severity": "invalid_severity",
        "timestamp": "invalid_timestamp",
        "event_id": "invalid_event_id",
    }
    return InboxItemError(
        code=code_by_field.get(leaf, "validation_error"),
        field=field,
        message=str(first.get("msg", "invalid event")),
    )


def _event_id(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    candidate = value.get("event_id")
    return candidate if isinstance(candidate, str) else None


def _response(result: InboxBatchResult, status_code: int) -> JSONResponse:
    content = result.as_dict()
    ShieldIngestionBatchResponseV1.model_validate(content)
    return JSONResponse(status_code=status_code, content=content)


def _result_status(result: InboxBatchResult) -> int:
    if result.accepted_count == 0 and result.duplicate_count == 0:
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    return status.HTTP_202_ACCEPTED


def _inbox_event(
    event: ShieldEventV1,
    *,
    index: int,
    batch_id: str,
    received_at: datetime,
) -> InboxEvent:
    payload = event.model_dump(mode="json", exclude_none=True)
    canonical = normalize_shield_event(event, received_at=received_at)
    return InboxEvent(
        index=index,
        source_instance_id=event.source.instance_id,
        event_id=event.event_id,
        batch_id=batch_id,
        content_hash=hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
        schema_version=event.schema_version,
        source_product=event.source.product,
        source_product_version=event.source.product_version,
        source_component=event.source.component,
        event_type=event.event_type,
        severity=event.severity,
        event_timestamp=event.timestamp,
        received_at=received_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        sequence=event.sequence,
        asset_id=event.asset.asset_id,
        hostname=event.asset.hostname,
        ip=event.asset.ip,
        os=event.asset.os,
        payload=payload,
        normalized_payload=canonical_event_payload(canonical),
    )


@router.post(
    "/ingestion/sources/edy-shield/events",
    response_model=ShieldIngestionBatchResponseV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest EDY Shield event batch",
    dependencies=[
        Depends(require_shield_ingest_token),
        Depends(rate_limit(120, 60)),
    ],
    responses={
        400: {"description": "Malformed envelope or idempotency key"},
        401: {"description": "Missing or invalid M2M credential"},
        409: {"description": "Idempotency conflict"},
        413: {"description": "Payload, event, or batch limit exceeded"},
        415: {"description": "Unsupported content type or encoding"},
        422: {"model": ShieldIngestionBatchResponseV1, "description": "All items rejected"},
        503: {"description": "Inbox unavailable or receiver not configured"},
    },
)
async def ingest_shield_events(
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    inbox: ShieldInboxRepository = Depends(get_shield_inbox),
) -> JSONResponse:
    """Validate, normalize and durably acknowledge a Shield batch."""

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")
    content_encoding = request.headers.get("content-encoding", "identity").strip().lower()
    if content_encoding not in {"", "identity"}:
        raise HTTPException(status_code=415, detail="compressed request bodies are not supported")

    raw_body = await _read_body(request)
    try:
        json_text = raw_body.decode("utf-8")
        decoded: Any = json.loads(
            json_text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="malformed JSON body") from exc
    if not isinstance(decoded, dict):
        raise HTTPException(status_code=400, detail="batch envelope must be an object")

    raw_events = decoded.get("events")
    if isinstance(raw_events, list) and len(raw_events) > 100:
        raise HTTPException(status_code=413, detail="batch exceeds 100 events")
    if isinstance(raw_events, list):
        for raw_event in raw_events:
            try:
                event_size = len(canonical_json_bytes(raw_event))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="event is not valid JSON") from exc
            if event_size > MAX_EVENT_BYTES:
                raise HTTPException(status_code=413, detail="event exceeds 64 KiB")

    try:
        envelope = ShieldBatchEnvelopeV1.model_validate(decoded)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="invalid batch envelope") from exc
    if idempotency_key is None or idempotency_key != envelope.batch_id:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must equal batch_id",
        )

    batch_hash = hashlib.sha256(canonical_json_bytes(decoded)).hexdigest()
    try:
        replay = inbox.replay(envelope.batch_id, batch_hash)
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "idempotency_conflict", "identifier": exc.identifier},
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="ingestion inbox unavailable") from exc
    if replay is not None:
        return _response(replay, _result_status(replay))

    received_at = datetime.now(UTC)
    valid_events: list[InboxEvent] = []
    rejected: list[InboxItemResult] = []
    for index, raw_event in enumerate(envelope.events):
        try:
            event = ShieldEventV1.model_validate(raw_event)
        except ValidationError as exc:
            rejected.append(
                InboxItemResult(
                    index=index,
                    event_id=_event_id(raw_event),
                    status="rejected",
                    error=_validation_error(exc),
                )
            )
            continue
        valid_events.append(
            _inbox_event(
                event,
                index=index,
                batch_id=envelope.batch_id,
                received_at=received_at,
            )
        )

    try:
        result = inbox.accept(
            batch_id=envelope.batch_id,
            batch_hash=batch_hash,
            received_at=received_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            events=valid_events,
            rejected=rejected,
        )
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "idempotency_conflict", "identifier": exc.identifier},
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="ingestion inbox unavailable") from exc
    return _response(result, _result_status(result))


__all__ = ["ingest_shield_events", "router"]
