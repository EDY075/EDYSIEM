"""Testes do pipeline SOC E2E (alerta → incidente → caso) e gestão operacional."""

from __future__ import annotations

import asyncio
from datetime import UTC

from edysiem.cases import CaseEvidenceKind, CaseStatus
from edysiem.incidents import IncidentInvalidStateTransition, IncidentStatus
from edysiem.soc import SocPipeline, SocService
from edysiem.soc.sla import SlaPolicy, compute_sla


def _run(coro):
    return asyncio.run(coro)


def test_soc_demo_flow_persists(tmp_path) -> None:
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    pipe = SocPipeline(svc)
    flow = _run(pipe.run_demo())

    assert flow.alert_ids
    assert flow.incident_id
    assert flow.case_id
    assert flow.stages["alerts"] == 4
    assert flow.stages["incident"] == 1
    assert flow.stages["case"] == 1

    # Persistido em repo (não só em memória)
    assert svc.get_incident(flow.incident_id) is not None
    assert svc.get_case(flow.case_id) is not None
    assert svc.get_alert(flow.alert_ids[0]) is not None


def test_soc_case_management_and_close(tmp_path) -> None:
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    flow = _run(SocPipeline(svc).run_demo())
    cid = flow.case_id

    # Comentário
    case = svc.add_case_comment(cid, "análise inicial", "ana.silva")
    assert case.comments
    assert case.comments[-1].body == "análise inicial"

    # Evidência
    case = svc.add_case_evidence(cid, CaseEvidenceKind.IOC, "185.220.101.4", label="C2")
    assert len(case.evidences) == 1

    # Owners
    case = svc.assign_case_owner(cid, "bruno.lima")
    assert case.owner == "bruno.lima"

    # Encerramento
    case = svc.close_case(cid, "conteúdo legítimo")
    assert case.status is CaseStatus.CLOSED
    assert case.closed_at is not None

    # SLA calculado
    sla = svc.sla_of(case)
    assert sla.state in ("met", "missed")


def test_soc_incident_assign_metrics_investigate(tmp_path) -> None:
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    flow = _run(SocPipeline(svc).run_demo())

    incident = svc.assign_incident_analyst(flow.incident_id, "carla.melo")
    assert incident.owner == "carla.melo"

    metrics = svc.metrics()
    comp = metrics["components"]
    assert comp["total_incidents"] >= 1
    assert comp["total_cases"] >= 1
    assert comp["alerts_by_severity"]["critical"] >= 1
    assert metrics["metrics"]["open_cases"] >= 0

    inv = svc.investigate(flow.case_id)
    assert inv["related_alerts"]
    assert inv["iocs"]
    assert isinstance(inv["pipeline_trail"], list)


def test_soc_management_ops_update_persistence(tmp_path) -> None:
    """As operações de gestão atualizam a persistência (não só o contexto em memória)."""
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    flow = _run(SocPipeline(svc).run_demo())
    cid = flow.case_id

    svc.add_case_comment(cid, "nota persistida", "ana")
    reloaded = svc.get_case(cid)
    assert reloaded is not None
    assert reloaded.comments
    assert reloaded.comments[-1].body == "nota persistida"


def test_soc_pipeline_event_run_requires_container(tmp_path) -> None:
    """run_event exige container de engines (caso contrário, erro claro)."""
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    pipe = SocPipeline(svc, container=None)
    from edysiem.domain import RawEvent

    async def _go():
        try:
            await pipe.run_event(RawEvent(source_type="syslog", source_host="h", raw_payload="x"))
        except ValueError as exc:
            return str(exc)
        return "sem erro"

    assert "exige o container" in _run(_go())


def test_soc_incident_invalid_transition(tmp_path) -> None:
    """Transição inválida de incidente é rejeitada."""
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    flow = _run(SocPipeline(svc).run_demo())
    try:
        svc.transition_incident(flow.incident_id, IncidentStatus.CLOSED)
    except IncidentInvalidStateTransition:
        return
    raise AssertionError("transição inválida deveria falhar")


def test_soc_attachment_task_resolve(tmp_path) -> None:
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    flow = _run(SocPipeline(svc).run_demo())
    cid = flow.case_id

    case = svc.add_case_attachment(cid, "captura.png", content_type="image/png", size=1024)
    assert len(case.attachments) == 1

    from edysiem.cases import CasePriority

    case = svc.case_engine.tasks.create(case, "coletar logs", priority=CasePriority.P2)
    case = svc.persist_case(case)
    assert len(case.tasks) == 1

    case = svc.resolve_case(cid, "incidente confirmado")
    assert case.resolution == "incidente confirmado"


def test_soc_sla_edge_states() -> None:
    from datetime import datetime, timedelta

    now = datetime.now(UTC)
    # Crítico criado há 2h (prazo 1h) -> overdue
    sla = compute_sla("critical", created_at=now - timedelta(hours=2), now=now)
    assert sla.state == "overdue"
    assert sla.overdue is True

    # Baixo criado agora e fechado em seguida -> met
    sla2 = compute_sla("low", created_at=now, closed_at=now + timedelta(minutes=1), now=now)
    assert sla2.state == "met"
    assert sla2.closed_on_time is True

    # Política customizada
    pol = SlaPolicy(critical_hours=0.5)
    assert pol.hours_for("critical") == 0.5
    assert pol.hours_for("desconhecida") == pol.medium_hours
    assert sla.remaining_seconds >= 0


def test_soc_empty_metrics(tmp_path) -> None:
    svc = SocService(db_path=str(tmp_path / "empty.db"))
    m = svc.metrics()
    assert m["components"]["total_alerts"] == 0
    assert m["components"]["total_cases"] == 0
    assert m["metrics"]["mttr_seconds"] == 0
    assert len(m["metrics"]["events_series"]) == 60
    assert all(p["events"] == 0 for p in m["metrics"]["events_series"])
    assert m["metrics"]["events_per_second"] == 0.0


def test_soc_sla_warning_state() -> None:
    from datetime import datetime, timedelta

    now = datetime.now(UTC)
    # Low (prazo 72h), criado 60h atrás → restam 12h (~16%) → warning
    sla = compute_sla("low", created_at=now - timedelta(hours=60), now=now)
    assert sla.state == "warning"
    assert sla.remaining_seconds == sla.remaining.total_seconds()


def test_soc_queries_and_not_found(tmp_path) -> None:
    svc = SocService(db_path=str(tmp_path / "soc.db"))
    flow = _run(SocPipeline(svc).run_demo())

    assert svc.get_alert(flow.alert_ids[0]) is not None
    assert svc.get_alert("nope") is None
    assert svc.get_incident("nope") is None
    assert svc.get_case("nope") is None
    assert len(svc.list_alerts()) >= 4
