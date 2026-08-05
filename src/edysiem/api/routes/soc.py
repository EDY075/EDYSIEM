"""Rotas SOC (Sprint 2.15) — fluxo operacional persistido.

Pipeline E2E, Incident/Case Management, Investigation e Dashboard KPIs,
todos alimentados pela persistência real através do ``SocService``.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException

from ...alerts import Alert
from ...cases import Case, CaseEvidenceKind
from ...container import ApplicationContainer
from ...domain import RawEvent
from ...incidents import Incident
from ...incidents.models import IncidentStatus
from ...soc import SocPipeline, SocService
from ..deps import get_container

router = APIRouter(tags=["soc"])

_CASE_STATUS_LABELS = {
    "open": "Aberto",
    "in_progress": "Em Andamento",
    "on_hold": "Em Espera",
    "resolved": "Resolvido",
    "closed": "Encerrado",
    "reopened": "Reaberto",
}


# --- Serializadores ---------------------------------------------------------


def _a(a: Alert) -> dict[str, Any]:
    return {
        "alert_id": a.id,
        "title": a.title,
        "rule_id": a.rule_id,
        "severity": a.severity.value,
        "status": a.status.value,
        "risk_score": a.risk_score.value,
        "source": a.source,
        "occurrences": a.occurrences,
        "iocs": list(a.ioc_ids),
        "mitre": list(a.mitre),
        "created_at": a.created_at.isoformat(),
    }


def _i(i: Incident) -> dict[str, Any]:
    return {
        "incident_id": i.id,
        "title": i.title,
        "severity": i.severity.value,
        "status": i.status.value,
        "risk_score": i.risk_score.value,
        "owner": i.owner,
        "alerts_count": len(i.alerts),
        "assets": list(i.assets),
        "users": list(i.users),
        "iocs": list(i.iocs),
        "mitre": list(i.mitre),
        "created_at": i.created_at.isoformat(),
        "closed_at": i.closed_at.isoformat() if i.closed_at else None,
    }


def _c(c: Case) -> dict[str, Any]:
    return {
        "case_id": c.id,
        "title": c.title,
        "status": c.status.value,
        "status_label": _CASE_STATUS_LABELS.get(c.status.value, c.status.value),
        "severity": c.severity.value,
        "priority": c.priority.value,
        "owner": c.owner,
        "incident_id": c.incident_id,
        "risk_score": c.risk_score.value,
        "comments_count": len(c.comments),
        "evidence_count": len(c.evidences),
        "tasks_count": len(c.tasks),
        "attachments_count": len(c.attachments),
        "resolution": c.resolution,
        "created_at": c.created_at.isoformat(),
        "closed_at": c.closed_at.isoformat() if c.closed_at else None,
    }


def _service(container: ApplicationContainer) -> SocService:
    return cast(SocService, container.soc_service)


# --- Incident Management ------------------------------------------------------------


@router.get("/soc/incidents", summary="Lista incidentes persistidos")
def list_incidents(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    svc = _service(container)
    return {
        "total": len(svc.list_incidents(limit=10000)),
        "items": [_i(i) for i in svc.list_incidents(limit=100)],
    }


@router.get("/soc/incidents/{incident_id}", summary="Detalhe de um incidente")
def get_incident(
    incident_id: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    incident = svc.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incidente não encontrado")
    return {**_i(incident), "sla": asdict(svc.sla_of(incident))}


@router.post("/soc/incidents/{incident_id}/assign", summary="Atribui analista a um incidente")
def assign_incident(
    incident_id: str, analyst: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return _i(svc.assign_incident_analyst(incident_id, analyst))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/soc/incidents/{incident_id}/transition", summary="Transiciona o status de um incidente"
)
def transition_incident(
    incident_id: str, target: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return _i(svc.transition_incident(incident_id, IncidentStatus(target)))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- Case Management ---------------------------------------------------------------------


@router.get("/soc/cases", summary="Lista cases persistidos")
def list_cases(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    svc = _service(container)
    return {
        "total": len(svc.list_cases(limit=10000)),
        "items": [_c(c) for c in svc.list_cases(limit=100)],
    }


@router.get("/soc/cases/{case_id}", summary="Detalhe de um case")
def get_case(
    case_id: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    case = svc.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="caso não encontrado")
    return {**_c(case), "sla": asdict(svc.sla_of(case))}


@router.get("/soc/cases/{case_id}/investigate", summary="Pivôs de investigação de um caso")
def investigate(
    case_id: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return svc.investigate(case_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/soc/cases/{case_id}/comment", summary="Adiciona comentário")
def add_comment(
    case_id: str, body: str, author: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return _c(svc.add_case_comment(case_id, body, author))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/soc/cases/{case_id}/evidence", summary="Anexa evidência")
def add_evidence(
    case_id: str,
    kind: str,
    value: str,
    label: str = "",
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return _c(svc.add_case_evidence(case_id, CaseEvidenceKind(kind), value, label=label))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/soc/cases/{case_id}/assign", summary="Atribui responsável")
def assign_case(
    case_id: str, owner: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return _c(svc.assign_case_owner(case_id, owner))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/soc/cases/{case_id}/resolve", summary="Resolve um case")
def resolve_case(
    case_id: str, resolution: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return _c(svc.resolve_case(case_id, resolution))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/soc/cases/{case_id}/close", summary="Encerra um case")
def close_case(
    case_id: str,
    resolution: str | None = None,
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, Any]:
    svc = _service(container)
    try:
        return _c(svc.close_case(case_id, resolution))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- Pipeline E2E ---------------------------------------------------------------------


@router.post(
    "/soc/pipeline/demo", summary="Executa o fluxo E2E de demonstração (alerta → incidente → caso)"
)
async def demo_flow(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    """Gera um fluxo SOC de teste (4 alertas → 1 incidente → 1 caso) e persiste."""
    pipeline = cast(SocPipeline, container.soc_pipeline)
    flow = await pipeline.run_demo()
    return asdict(flow)


@router.post("/soc/pipeline/run", summary="Executa um evento bruto pela pipeline de engines")
async def run_event(
    body: dict[str, Any], container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    raw = RawEvent(
        source_type=str(body.get("source_type", "syslog")),
        source_host=str(body.get("source_host", "host")),
        raw_payload=str(body.get("raw_payload", "")),
    )
    try:
        pipeline = cast(SocPipeline, container.soc_pipeline)
        return await pipeline.run_event(raw)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# --- Dashboard KPIs ------------------------------------------------------------------


@router.get("/soc/metrics", summary="KPIs do dashboard alimentadas pela persistência real")
def soc_metrics(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    return _service(container).metrics()


__all__ = ["router"]
