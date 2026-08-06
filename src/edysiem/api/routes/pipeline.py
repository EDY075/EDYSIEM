"""Rota de execucao da pipeline ponta a ponta."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ...container import ApplicationContainer
from ...domain import CanonicalEvent, ParsedEvent, RawEvent
from ...parsers import parse_rfc5424, parse_syslog
from ...result import Failure
from ..deps import get_container
from ..schemas import PipelineRunRequest, PipelineRunResponse
from ..security import rate_limit

router = APIRouter(tags=["pipeline"])


def _parse(raw: RawEvent) -> dict[str, Any] | None:
    """Tenta RFC5424 primeiro; fallback para RFC3164."""
    result = parse_rfc5424(raw)
    if result.is_ok():
        return result.unwrap()
    result = parse_syslog(raw)
    if result.is_ok():
        return result.unwrap()
    return None


@router.post(
    "/pipeline/run",
    response_model=PipelineRunResponse,
    summary="Executa a pipeline ponta a ponta",
    dependencies=[Depends(rate_limit(120, 60))],
)
async def run_pipeline(
    body: PipelineRunRequest,
    container: ApplicationContainer = Depends(get_container),
) -> PipelineRunResponse:
    """Recebe um payload bruto e o processa: parse -> normalize -> enrich
    -> correlate -> detect."""
    raw = RawEvent(
        source_type=body.source_type,
        source_host=body.source_host,
        raw_payload=body.raw_payload,
    )

    fields = _parse(raw)
    if fields is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="formato de log nao reconhecido")

    parsed = ParsedEvent(
        event_id=raw.event_id,
        timestamp=raw.received_at,
        source_type=raw.source_type,
        source_host=raw.source_host,
        event_category=str(fields.get("event_category", "system")),
        event_action=str(fields.get("event_action", "info")),
        fields=fields,
        raw=raw.raw_payload,
        trace_id=body.trace_id or raw.event_id,
    )

    canonical_result = container.normalizer.normalize(parsed)
    if isinstance(canonical_result, Failure):
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=canonical_result.error.message)

    canonical: CanonicalEvent = canonical_result.unwrap()

    # Enrichment (plugins opcionais)
    enriched = (await container.enrichment.enrich(canonical)).unwrap()

    # Correlation (regras opcionais)
    correlated = await container.correlation.process(enriched)

    # Detection (regras opcionais)
    outcome = await container.detection.process(correlated)

    return PipelineRunResponse(
        event_id=canonical.event_id,
        category=canonical.event_category or "system",
        action=canonical.event_action or "info",
        severity=canonical.severity.value,
        correlated_matches=len(correlated.matches),
        detected_rule_ids=list(outcome.detected_rule_ids),
        finding_count=len(outcome.findings),
    )


__all__ = ["router"]
