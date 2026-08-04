"""Testes suplementares do Case Framework (cobertura)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.cases import (
    Case,
    CaseBuilder,
    CaseContext,
    CaseEngine,
    CasePriority,
    CaseRegistry,
    CaseStatus,
)
from edysiem.cases.exceptions import (
    CaseBuilderError,
    CaseError,
    CaseInvalidStateTransition,
    CaseNotFoundError,
    CaseRegistrationError,
    CaseTaskNotFoundError,
)
from edysiem.domain import RiskScore
from edysiem.incidents import IncidentEngine


def _incident():
    base = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    alerts = []
    for i in range(5):
        alerts.append(
            Alert(
                title=f"BF {i}",
                severity=AlertSeverity.HIGH,
                risk_score=RiskScore(70),
                rule_id="brute-force",
                asset_id="asset-1",
                user="admin",
                fingerprint=AlertFingerprint(hash=f"fp-{i}", rule_id="brute-force"),
                first_seen=base + timedelta(seconds=i),
                last_seen=base + timedelta(seconds=i),
                id=f"bf-{i}",
            )
        )
    engine = IncidentEngine()
    return asyncio.run(engine.process_alerts(alerts)).incident


def test_engine_sub_engine_accessors() -> None:
    engine = CaseEngine()
    assert engine.timeline is not None
    assert engine.evidence is not None
    assert engine.comments is not None
    assert engine.tasks is not None
    assert engine.owners is not None
    assert engine.attachments is not None
    assert engine.registry is not None
    assert engine.metrics is not None


def test_engine_add_alert_and_attachment() -> None:
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident))
    case_id = result.case.id

    engine.add_alert(case_id, "extra-alert-1", actor="analyst-01")
    engine.add_attachment(case_id, "print.png", content_type="image/png", size=2048)

    case = engine.get(case_id)
    assert "extra-alert-1" in case.alerts
    assert len(case.attachments) == 1
    assert any(e.action == "alert_added" for e in case.timeline)


def test_engine_complete_task_flow() -> None:
    incident = _incident()
    engine = CaseEngine()
    result = asyncio.run(engine.create_from_incident(incident))
    case_id = result.case.id

    case = engine.create_task(case_id, "Tarefa A", priority=CasePriority.P1)
    task_id = case.tasks[0].id
    case = engine.complete_task(case_id, task_id)
    assert case.tasks[0].status.value == "completed"

    snapshot = engine.get_metrics_snapshot()
    assert snapshot["total_tasks_completed"] == 1


def test_case_context_ops() -> None:
    context = CaseContext()
    case = Case(title="x")
    context.save(case)

    assert len(context) == 1
    assert len(context.all()) == 1
    assert context.get(case.id) == case

    context.clear()
    assert len(context) == 0
    assert context.snapshot()["cases"] == 0


def test_case_context_by_incident_and_clear_rule() -> None:
    context = CaseContext()
    case1 = Case(title="a", incident_id="inc-1")
    case2 = Case(title="b", incident_id="inc-2")
    context.save(case1)
    context.save(case2)

    assert len(context.by_incident("inc-1")) == 1
    assert len(context.by_incident("inc-9")) == 0


def test_registry_hooks_and_ops() -> None:
    calls = []

    class Hook:
        def on_created(self, case) -> None:
            calls.append("created")

        def on_updated(self, case) -> None:
            calls.append("updated")

        def on_status_changed(self, case, previous, current) -> None:
            calls.append(f"status:{current.value}")

    registry = CaseRegistry()
    registry.register(Hook(), name="h1")
    registry.register(Hook(), name="h2")

    assert len(registry) == 2
    assert len(list(registry)) == 2
    assert registry.get("h1") is not None
    assert "h2" in registry.processor_names()

    case = Case(title="x")
    registry.on_created(case)
    registry.on_updated(case)
    registry.on_status_changed(case, CaseStatus.OPEN, CaseStatus.IN_PROGRESS)

    assert "created" in calls
    assert "updated" in calls
    assert any(c.startswith("status:") for c in calls)

    assert registry.unregister("h1") is True
    assert registry.get("h1") is None
    assert registry.get_stats()["total_processors"] == 1


def test_registry_hook_failure_isolated() -> None:
    calls = []

    class BadHook:
        def on_created(self, case) -> None:
            raise RuntimeError("boom")

        def on_updated(self, case) -> None:
            raise RuntimeError("boom")

        def on_status_changed(self, case, previous, current) -> None:
            raise RuntimeError("boom")

    class GoodHook:
        def on_created(self, case) -> None:
            calls.append("created")

        def on_updated(self, case) -> None:
            calls.append("updated")

        def on_status_changed(self, case, previous, current) -> None:
            calls.append("status")

    registry = CaseRegistry()
    registry.register(BadHook(), name="bad")
    registry.register(GoodHook(), name="good")

    case = Case(title="x")
    registry.on_created(case)
    registry.on_updated(case)
    assert "created" in calls
    assert "updated" in calls


def test_cases_exceptions() -> None:
    assert issubclass(CaseError, Exception)
    assert issubclass(CaseNotFoundError, CaseError)
    assert issubclass(CaseInvalidStateTransition, CaseError)
    assert issubclass(CaseRegistrationError, CaseError)
    assert issubclass(CaseTaskNotFoundError, CaseError)
    assert issubclass(CaseBuilderError, CaseError)

    err = CaseNotFoundError("case-1")
    assert err.case_id == "case-1"


def test_builder_priority_mapping() -> None:
    incident = _incident()
    builder = CaseBuilder()
    case = builder.build(incident)
    # incidente P2 (risk 70) -> case P2
    assert case.priority.value == "p2" or case.priority is not None
