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
from ..security import rate_limit, require_permission

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


# --- Alerts --------------------------------------------------------------------


@router.get("/soc/alerts", summary="Lista alertas persistidos")
def list_alerts(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    svc = _service(container)
    return {
        "total": len(svc.list_alerts(limit=10000)),
        "items": [_a(a) for a in svc.list_alerts(limit=100)],
    }


@router.get("/soc/alerts/{alert_id}", summary="Detalhe de um alerta")
def get_alert(
    alert_id: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    svc = _service(container)
    alert = svc.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta não encontrado")
    return {**_a(alert), "sla": asdict(svc.sla_of(alert))}


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


@router.post(
    "/soc/cases/{case_id}/close",
    summary="Encerra um case",
    dependencies=[Depends(require_permission("case:write"))],
)
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


@router.post(
    "/soc/pipeline/run",
    summary="Executa um evento bruto pela pipeline de engines",
    dependencies=[Depends(rate_limit(120, 60))],
)
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


# --- Detection Engineering + Threat Intel (Sprint 2.17) ------------------------------


@router.post("/soc/rules", summary="Registra uma regra no catálogo")
def create_rule(
    body: dict[str, Any], container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    return _service(container).register_rule(
        rule_id=str(body.get("rule_id", "")),
        name=str(body.get("name", "")),
        severity=str(body.get("severity", "medium")),
        category=str(body.get("category", "")),
        mitre=tuple(body.get("mitre", [])),
        tags=tuple(body.get("tags", [])),
        description=str(body.get("description", "")),
    )


@router.get("/soc/rules", summary="Lista regras do catálogo")
def list_rules(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    svc = _service(container)
    rules = svc.list_rules()
    return {"total": len(rules), "enabled": sum(1 for r in rules if r["enabled"]), "items": rules}


@router.post(
    "/soc/rules/{rule_id}/enable",
    summary="Habilita uma regra",
    dependencies=[Depends(require_permission("rule:write"))],
)
def enable_rule(
    rule_id: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    rule = _service(container).set_rule_enabled(rule_id, True)
    if rule is None:
        raise HTTPException(status_code=404, detail="regra não encontrada")
    return rule


@router.post(
    "/soc/rules/{rule_id}/disable",
    summary="Desabilita uma regra",
    dependencies=[Depends(require_permission("rule:write"))],
)
def disable_rule(
    rule_id: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    rule = _service(container).set_rule_enabled(rule_id, False)
    if rule is None:
        raise HTTPException(status_code=404, detail="regra não encontrada")
    return rule


@router.post(
    "/soc/simulator",
    summary="Simula aplicação de regras sobre um evento JSON",
    dependencies=[Depends(rate_limit(120, 60))],
)
def simulate(
    body: dict[str, Any], container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    event = body.get("event", {})
    results = _service(container).simulate_rule(dict(event))
    return {"applied": [r for r in results if r["applied"]], "matches": len(results)}


@router.get("/soc/iocs", summary="Lista IOCs")
def list_iocs(
    ioc_type: str | None = None, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    items = _service(container).list_iocs(ioc_type=ioc_type)
    return {"total": len(items), "items": items}


@router.post("/soc/iocs", summary="Registra um IOC")
def register_ioc(
    body: dict[str, Any], container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    return _service(container).register_ioc(
        str(body.get("value", "")),
        str(body.get("ioc_type", "ip")),
        reputation=str(body.get("reputation", "unknown")),
        source=str(body.get("source", "analyst")),
        labels=tuple(body.get("labels", [])),
    )


@router.get("/soc/iocs/{value}/related", summary="Incidentes/casos relacionados a um IOC")
def ioc_related(
    value: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    return _service(container).ioc_related(value)


@router.get("/soc/assets", summary="Lista assets do inventário")
def list_assets(
    criticality: str | None = None, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    items = _service(container).list_assets(criticality=criticality)
    return {"total": len(items), "items": items}


@router.post("/soc/assets", summary="Registra um asset")
def register_asset(
    body: dict[str, Any], container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    return _service(container).register_asset(
        str(body.get("hostname", "")),
        ip=str(body.get("ip", "")),
        os_name=str(body.get("os", "")),
        criticality=str(body.get("criticality", "medium")),
        owner=str(body.get("owner", "")),
        status=str(body.get("status", "active")),
    )


@router.get("/soc/assets/{hostname}/related", summary="Incidentes/casos relacionados a um asset")
def asset_related(
    hostname: str, container: ApplicationContainer = Depends(get_container)
) -> dict[str, Any]:
    return _service(container).asset_related(hostname)


@router.get("/soc/detection", summary="Detection Dashboard (agregações reais)")
def detection(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    return _service(container).detection_stats()


# --- Dashboard KPIs ------------------------------------------------------------------


@router.get("/soc/metrics", summary="KPIs do dashboard alimentadas pela persistência real")
def soc_metrics(container: ApplicationContainer = Depends(get_container)) -> dict[str, Any]:
    return _service(container).metrics()


__all__ = ["router"]
