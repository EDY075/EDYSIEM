"""Operator investigation routes for events received from EDY Shield."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ...cases import Case, CaseEvidenceKind
from ...container import ApplicationContainer
from ...domain import RiskScore
from ...incidents import Incident, IncidentPriority, IncidentSeverity
from ...persistence import PersistenceError, ShieldInboxRepository
from ...soc import SocService
from ..deps import get_container, get_shield_inbox

router = APIRouter(tags=["shield-investigation"])
_ROUTE = "/investigation/sources/edy-shield/events/{event_id}"


def _canonical_uuid4(value: str) -> bool:
    try:
        parsed = UUID(value)
    except ValueError:
        return False
    return parsed.version == 4 and str(parsed) == value


def _require_event(
    event_id: str, repository: ShieldInboxRepository
) -> dict[str, object]:
    if not _canonical_uuid4(event_id):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_event_id", "message": "event_id must be a canonical UUIDv4"},
        )
    try:
        row = repository.find_by_event_id(event_id)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "ambiguous_event_id", "message": "event_id is not unique"},
        ) from exc
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "shield_event_not_found", "message": "EDY Shield event not found"},
        )
    if row.get("source_product") != "edy-shield":
        raise HTTPException(
            status_code=404,
            detail={"code": "wrong_source", "message": "event is not from EDY Shield"},
        )
    return row


def _case_summary(case: Case | None, service: SocService) -> dict[str, object] | None:
    if case is None:
        return None
    return {
        "case_id": case.id,
        "title": case.title,
        "status": case.status.value,
        "owner": case.owner,
        "evidence_count": len(case.evidences),
        "sla": asdict(service.sla_of(case)),
    }


def _linked_case(service: SocService, event_id: str) -> Case | None:
    incident_id = f"shield-event:{event_id}"
    return next(
        (case for case in service.list_cases(limit=10000) if case.incident_id == incident_id),
        None,
    )


def _response(
    row: dict[str, object], case: Case | None, service: SocService
) -> dict[str, object]:
    payload = row.get("payload")
    normalized = row.get("normalized_payload")
    if not isinstance(payload, dict) or not isinstance(normalized, dict):
        raise HTTPException(
            status_code=500,
            detail={"code": "invalid_stored_event", "message": "stored Shield event is invalid"},
        )
    source = payload.get("source")
    if not isinstance(source, dict) or source.get("product") != "edy-shield":
        raise HTTPException(
            status_code=404,
            detail={"code": "wrong_source", "message": "event is not from EDY Shield"},
        )
    return {
        "event_id": row["event_id"],
        "schema_version": row["schema_version"],
        "timestamp": row["event_timestamp"],
        "received_at": row["received_at"],
        "processing_status": row["processing_status"],
        "sequence": row["sequence"],
        "event_type": row["event_type"],
        "severity": row["severity"],
        "source": source,
        "asset": payload.get("asset", {}),
        "evidence": payload.get("evidence", {}),
        "metadata": payload.get("metadata", {}),
        "normalized": normalized,
        "case": _case_summary(case, service),
    }


@router.get(
    "/investigation/sources/edy-shield/events",
    summary="List recent EDY Shield events for the operator decision queue",
)
def list_shield_event_investigations(
    limit: int = Query(default=20, ge=1, le=100),
    repository: ShieldInboxRepository = Depends(get_shield_inbox),
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, object]:
    service = cast(SocService, container.soc_service)
    cases: dict[str, Case] = {}
    for case in service.list_cases(limit=10000):
        incident_id = case.incident_id
        if incident_id is not None and incident_id.startswith("shield-event:"):
            cases[incident_id.removeprefix("shield-event:")] = case
    rows = repository.list_recent(limit=limit)
    return {
        "total": repository.count(),
        "items": [
            _response(row, cases.get(str(row["event_id"])), service) for row in rows
        ],
    }


@router.get(_ROUTE, summary="Resolve one EDY Shield event for investigation")
def get_shield_event_investigation(
    event_id: str,
    repository: ShieldInboxRepository = Depends(get_shield_inbox),
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, object]:
    row = _require_event(event_id, repository)
    service = cast(SocService, container.soc_service)
    return _response(row, _linked_case(service, event_id), service)


@router.post(f"{_ROUTE}/cases", summary="Create an idempotent case from one Shield event")
async def create_case_from_shield_event(
    event_id: str,
    repository: ShieldInboxRepository = Depends(get_shield_inbox),
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, object]:
    row = _require_event(event_id, repository)
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500,
            detail={"code": "invalid_stored_event", "message": "stored Shield event is invalid"},
        )
    asset_raw = payload.get("asset")
    metadata_raw = payload.get("metadata")
    asset: dict[object, object] = asset_raw if isinstance(asset_raw, dict) else {}
    metadata: dict[object, object] = metadata_raw if isinstance(metadata_raw, dict) else {}
    event_type = str(row["event_type"])
    severity_value = str(row["severity"])
    hostname = str(asset.get("hostname", "unknown-endpoint"))
    mitre_raw = metadata.get("x_mitre")
    mitre = (
        frozenset(str(value) for value in mitre_raw if isinstance(value, str))
        if isinstance(mitre_raw, list)
        else frozenset()
    )
    severity = IncidentSeverity(severity_value)
    priority = {
        "critical": IncidentPriority.P1,
        "high": IncidentPriority.P2,
        "medium": IncidentPriority.P3,
        "low": IncidentPriority.P4,
        "info": IncidentPriority.P5,
    }[severity_value]
    risk_score = RiskScore(
        {"critical": 95, "high": 80, "medium": 60, "low": 30, "info": 10}[severity_value]
    )
    event_time = datetime.fromisoformat(str(row["event_timestamp"]).replace("Z", "+00:00"))
    incident = Incident(
        id=f"shield-event:{event_id}",
        title=f"EDY Shield | {event_type} | {hostname}",
        description=f"Investigation created from EDY Shield event {event_id}.",
        severity=severity,
        priority=priority,
        risk_score=risk_score,
        first_seen=event_time,
        last_seen=event_time,
        assets=frozenset({hostname}),
        mitre=mitre,
        techniques=mitre,
        tags=frozenset({"edy-shield", event_type}),
    )

    service = cast(SocService, container.soc_service)
    existing = _linked_case(service, event_id)
    case = await service.create_case_from_incident(incident, owner=None)
    evidence_label = f"EDY Shield event {event_id}"
    if not any(item.label == evidence_label for item in case.evidences):
        evidence_value = json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False)
        case = service.add_case_evidence(
            case.id,
            CaseEvidenceKind.JSON,
            evidence_value,
            label=evidence_label,
            source="edy-shield",
        )
    result = _response(row, case, service)
    result["case_created"] = existing is None
    return result


__all__ = ["router"]
