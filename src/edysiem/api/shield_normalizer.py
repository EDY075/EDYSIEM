"""EDY Shield contract adapter to the SIEM canonical event model."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..domain import CanonicalEvent, Severity
from .ingestion_schemas import ShieldEventV1

_EVENT_MAPPING: dict[str, tuple[str, str]] = {
    "shield.fim.baseline.created": ("file", "baseline_created"),
    "shield.fim.scan.completed": ("file", "scan_completed"),
    "shield.fim.file.added": ("file", "created"),
    "shield.fim.file.modified": ("file", "modified"),
    "shield.fim.file.removed": ("file", "deleted"),
    "shield.hash.verified": ("file", "hash_verified"),
    "shield.hash.mismatch": ("file", "hash_changed"),
    "shield.alert.created": ("alert", "created"),
    "shield.alert.updated": ("alert", "updated"),
}


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(f"{value[:-1]}+00:00")


def normalize_shield_event(event: ShieldEventV1, *, received_at: datetime) -> CanonicalEvent:
    """Convert one validated Shield event without spreading source-specific rules."""

    category, action = _EVENT_MAPPING[event.event_type]
    raw_payload = event.model_dump(mode="json", exclude_none=True)
    evidence = event.evidence.model_dump(mode="json", exclude_none=True)
    source_metadata = event.metadata.model_dump(mode="json", exclude_none=True)
    metadata: dict[str, Any] = {
        "origin_event_id": event.event_id,
        "contract_schema_version": event.schema_version,
        "source_instance_id": event.source.instance_id,
        "source_component": event.source.component,
        "source_product_version": event.source.product_version,
        "source_sequence": event.sequence,
        "source_severity": event.severity,
        "asset": event.asset.model_dump(mode="json", exclude_none=True),
        "evidence": evidence,
        "source_metadata": source_metadata,
    }
    return CanonicalEvent(
        event_id=event.event_id,
        trace_id=str(source_metadata.get("correlation_id", event.event_id)),
        timestamp=_timestamp(event.timestamp),
        received_at=received_at,
        source_type="edy_shield",
        source_host=event.asset.hostname,
        hostname=event.asset.hostname,
        event_category=category,
        event_action=action,
        severity=Severity(event.severity),
        ip_src=None,
        ip_dst=None,
        vendor="EDY",
        product="EDY Shield",
        event_original=json.dumps(
            raw_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        normalized_fields=frozenset(
            {
                "asset",
                "event_type",
                "evidence",
                "metadata",
                "severity",
                "source",
                "timestamp",
            }
        ),
        tags=frozenset(event.metadata.tags or ()),
        confidence=1.0,
        metadata=metadata,
    )


def canonical_event_payload(event: CanonicalEvent) -> dict[str, object]:
    """Serialize the canonical event without duplicating the preserved raw body."""

    return {
        "event_id": event.event_id,
        "trace_id": event.trace_id,
        "timestamp": event.timestamp.isoformat(),
        "received_at": event.received_at.isoformat(),
        "source_type": event.source_type,
        "source_host": event.source_host,
        "hostname": event.hostname,
        "event_category": event.event_category,
        "event_action": event.event_action,
        "severity": event.severity.value,
        "vendor": event.vendor,
        "product": event.product,
        "normalized_fields": sorted(event.normalized_fields),
        "tags": sorted(event.tags),
        "confidence": event.confidence,
        "metadata": event.metadata,
        "schema_version": event.schema_version,
        "normalized_at": event.normalized_at.isoformat(),
    }


__all__ = ["canonical_event_payload", "normalize_shield_event"]
