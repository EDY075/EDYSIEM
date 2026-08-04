"""Testes do CaseEngine (workspace completo)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.cases import (
    CaseBuilder,
    CaseContext,
    CaseEngine,
    CaseEvidenceKind,
    CasePriority,
    CaseRegistry,
    CaseResultKind,
    CaseStatus,
)
from edysiem.cases.exceptions import (
    CaseInvalidStateTransition,
    CaseNotFoundError,
    CaseRegistrationError,
)
from edysiem.domain import RiskScore
from edysiem.incidents import Incident, IncidentEngine


def _incident() -> Incident:
    """Cria um incidente via IncidentEngine (DEMO brute force)."""
    base = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    alerts = []
    for i in range(5):
        fp = AlertFingerprint(hash=f"fp-{i}", rule_id="brute-force")
        alerts.append(
            Alert(
                title=f"BF {i}",
                severity=AlertSeverity.HIGH,
                risk_score=RiskScore(70),
                rule_id="brute-force",
                asset_id="asset-1",
                user="admin",
                fingerprint=fp,
                first_seen=base + timedelta(seconds=i),
                last_seen=base + timedelta(seconds=i),
                id=f"bf-{i}",
            )
        )
    engine = IncidentEngine()
    result = asyncio.run(engine.process_alerts(alerts))
    assert result.incident is not None
    return result.incident


def test_builder_from_incident() -> None:
    incident = _incident()
    builder = CaseBuilder()
    case = builder.build(incident, owner="analyst-01")

    assert case.incident_id == incident.id
    assert case.owner == "analyst-01"
    assert case.status == CaseStatus.OPEN
    assert case.alerts == incident.alerts
    assert case.assets == incident.assets
    assert case.users == incident.users
    assert case.risk_score == incident.risk_score
    assert case.timeline  # timeline inicial


def test_case_engine_create() -> None:
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident, owner="analyst-01"))

    assert result.kind is CaseResultKind.CREATED
    assert result.was_new is True
    assert result.case.owner == "analyst-01"
    assert result.case.timeline  # 'created' registrado
    assert result.case.timeline[0].action == "created"


def test_case_engine_transition() -> None:
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident))
    case_id = result.case.id

    updated = engine.transition(case_id, CaseStatus.IN_PROGRESS, actor="analyst-01")
    assert updated.status == CaseStatus.IN_PROGRESS
    assert engine.get(case_id).status == CaseStatus.IN_PROGRESS


def test_case_engine_transition_invalid() -> None:
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident))

    with pytest.raises(CaseInvalidStateTransition):
        engine.transition(result.case.id, CaseStatus.REOPENED)  # OPEN -> REOPENED invalido


def test_case_engine_full_workflow() -> None:
    """Fluxo completo de investigacao."""
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident))
    case_id = result.case.id

    # Timeline/status
    engine.transition(case_id, CaseStatus.IN_PROGRESS, actor="analyst-01")

    # Evidencias
    engine.add_evidence(case_id, CaseEvidenceKind.HASH, "abc123", label="malware sha256")
    engine.add_evidence(case_id, CaseEvidenceKind.IP, "1.2.3.4", label="C2")

    # Comentario
    engine.add_comment(case_id, "Host parece comprometido", "analyst-01")

    # Tarefas
    engine.create_task(case_id, "Coletar memoria", priority=CasePriority.P2, assignee="analyst-02")

    # Owner
    engine.transfer_owner(case_id, "analyst-02", assigned_by="analyst-01")

    # Anexo
    engine.add_attachment(case_id, "memoria.zip", content_type="application/zip")

    # Resolucao
    case = engine.resolve(case_id, "Comprometimento confirmado; host isolado.")

    actions = [e.action for e in case.timeline]
    assert "created" in actions
    assert "status_change" in actions
    assert "evidence" in actions
    assert "comment" in actions
    assert "task" in actions
    assert "owner_change" in actions
    assert "attachment" in actions
    assert "resolved" in actions

    assert case.resolution.startswith("Comprometimento")
    assert len(case.evidences) == 2
    assert len(case.comments) == 1
    assert len(case.tasks) == 1
    assert len(case.attachments) == 1
    assert case.owner == "analyst-02"


def test_case_engine_metrics() -> None:
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident))
    case_id = result.case.id

    engine.add_comment(case_id, "nota", "analyst-01")
    engine.add_evidence(case_id, CaseEvidenceKind.IP, "8.8.8.8")
    engine.create_task(case_id, "tarefa")

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_created"] == 1
    assert snapshot["total_comments"] == 1
    assert snapshot["total_evidences"] == 1
    assert snapshot["total_tasks_created"] == 1


def test_case_engine_close_and_reopen() -> None:
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident))
    case_id = result.case.id

    engine.transition(case_id, CaseStatus.IN_PROGRESS)
    engine.transition(case_id, CaseStatus.ON_HOLD)
    engine.transition(case_id, CaseStatus.IN_PROGRESS)
    engine.transition(case_id, CaseStatus.RESOLVED)
    engine.transition(case_id, CaseStatus.CLOSED)

    closed = engine.get(case_id)
    assert closed.closed_at is not None

    reopened = engine.transition(case_id, CaseStatus.REOPENED)
    assert reopened.status == CaseStatus.REOPENED
    assert any(e.action == "reopened" for e in reopened.timeline)


def test_case_engine_not_found() -> None:
    engine = CaseEngine()
    with pytest.raises(CaseNotFoundError, match="nao encontrado"):
        engine.transition("missing", CaseStatus.IN_PROGRESS)


def test_case_engine_registry_hooks() -> None:
    calls = []

    class Hook:
        def on_created(self, case) -> None:
            calls.append("created")

        def on_updated(self, case) -> None:
            calls.append("updated")

        def on_status_changed(self, case, previous, current) -> None:
            calls.append(f"status:{current.value}")

    registry = CaseRegistry()
    registry.register(Hook(), name="hook")

    context = CaseContext()
    engine = CaseEngine(registry=registry, context=context)

    result = asyncio.run(engine.create_from_incident(_incident()))
    engine.transition(result.case.id, CaseStatus.IN_PROGRESS)

    assert "created" in calls
    assert any(c.startswith("status:") for c in calls)


def test_case_engine_health_check() -> None:
    engine = CaseEngine()
    health = engine.health_check()
    assert health["engine"] == "healthy"


def test_case_engine_by_incident() -> None:
    incident = _incident()
    context = CaseContext()
    engine = CaseEngine(context=context)
    asyncio.run(engine.create_from_incident(incident))

    found = context.by_incident(incident.id)
    assert len(found) == 1


def test_registry_duplicate_fails() -> None:
    class Hook:
        def on_created(self, case) -> None:
            pass

        def on_updated(self, case) -> None:
            pass

        def on_status_changed(self, case, previous, current) -> None:
            pass

    registry = CaseRegistry()
    registry.register(Hook(), name="h")
    with pytest.raises(CaseRegistrationError):
        registry.register(Hook(), name="h")
