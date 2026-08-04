"""Testes do Persistence Engine (CRUD + filtros + paginacao) e Event Store."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.domain import RiskScore
from edysiem.persistence import (
    ALL_MIGRATIONS,
    ConnectionManager,
    EventRepository,
    EventStore,
    MigrationRunner,
    PipelineStage,
    QueryFilter,
    QueryOp,
    SortOrder,
)
from edysiem.persistence.repos import AlertRepository


@pytest.fixture
def manager() -> ConnectionManager:
    m = ConnectionManager(":memory:")
    MigrationRunner(ALL_MIGRATIONS).apply(m)
    return m


def _alert(alert_id: str, rule: str, sev: AlertSeverity, days: int) -> Alert:
    now = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    return Alert(
        id=alert_id,
        title=f"Alert {alert_id}",
        severity=sev,
        risk_score=RiskScore(70),
        rule_id=rule,
        fingerprint=AlertFingerprint(hash=f"fp-{alert_id}", rule_id=rule),
        first_seen=now - timedelta(days=days),
        last_seen=now - timedelta(days=days),
        created_at=now - timedelta(days=days),
        updated_at=now - timedelta(days=days),
    )


# --- AlertRepository: CRUD + filtros + paginacao ---------------------------


def test_alert_repo_crud(manager: ConnectionManager) -> None:
    repo = AlertRepository(manager)
    alert = _alert("a1", "brute-force", AlertSeverity.HIGH, 1)
    repo.add(alert)
    assert repo.get("a1") is not None
    assert repo.get("missing") is None

    bumped = alert.bump()
    repo.update(bumped)
    assert repo.get("a1").occurrences == 2

    assert repo.delete("a1") is True
    assert repo.get("a1") is None


def test_alert_repo_query_filters(manager: ConnectionManager) -> None:
    repo = AlertRepository(manager)
    repo.add(_alert("a1", "brute-force", AlertSeverity.HIGH, 1))
    repo.add(_alert("a2", "brute-force", AlertSeverity.MEDIUM, 2))
    repo.add(_alert("a3", "malware", AlertSeverity.CRITICAL, 3))

    # filtro por regra
    page = repo.by_rule("brute-force")
    assert page.total == 2

    # filtro por severidade
    page = repo.by_severity(AlertSeverity.CRITICAL)
    assert page.total == 1

    # busca por fingerprint
    assert repo.by_fingerprint("fp-a1").id == "a1"
    assert repo.by_fingerprint("nao-existe") is None


def test_alert_repo_pagination(manager: ConnectionManager) -> None:
    repo = AlertRepository(manager)
    for i in range(10):
        repo.add(_alert(f"a{i}", "rule", AlertSeverity.MEDIUM, i))

    page1 = repo.query(limit=4, offset=0, sort_by="created_at", order=SortOrder.ASC)
    assert len(page1.items) == 4
    assert page1.total == 10
    assert page1.has_more is True

    page3 = repo.query(limit=4, offset=8, sort_by="created_at", order=SortOrder.ASC)
    assert len(page3.items) == 2
    assert page3.has_more is False


def test_alert_repo_date_range(manager: ConnectionManager) -> None:
    repo = AlertRepository(manager)
    repo.add(_alert("a1", "r", AlertSeverity.MEDIUM, 30))  # criado 30 dias atras
    repo.add(_alert("a2", "r", AlertSeverity.MEDIUM, 1))  # criado 1 dia atras

    start = datetime(2026, 8, 2, tzinfo=UTC)
    end = datetime(2026, 8, 4, tzinfo=UTC)
    page = repo.by_date_range(start, end)
    assert page.total == 1
    assert page.items[0].id == "a2"


def test_generic_count(manager: ConnectionManager) -> None:
    repo = AlertRepository(manager)
    repo.add(_alert("a1", "r", AlertSeverity.HIGH, 1))
    repo.add(_alert("a2", "r", AlertSeverity.LOW, 1))
    assert repo.count() == 2
    assert repo.count([QueryFilter(field="severity", value="high")]) == 1


def test_query_filter_ops(manager: ConnectionManager) -> None:
    repo = AlertRepository(manager)
    repo.add(_alert("a1", "r", AlertSeverity.HIGH, 1))

    # gte/lt sobre occurrences
    page = repo.query([QueryFilter(field="occurrences", op=QueryOp.GTE, value=1)])
    assert page.total == 1
    page = repo.query([QueryFilter(field="occurrences", op=QueryOp.LT, value=1)])
    assert page.total == 0


# --- Event Store ------------------------------------------------------------


def test_event_store_append_and_get(manager: ConnectionManager) -> None:
    repo = EventRepository(manager)
    store = EventStore(repo)
    event = store.record(
        stage=PipelineStage.CANONICAL,
        correlation_id="corr-1",
        source="normalizer",
        event_type="CanonicalEvent",
        payload={"category": "auth"},
    )
    loaded = repo.get(event.event_id)
    assert loaded is not None
    assert loaded.pipeline_stage == PipelineStage.CANONICAL
    assert loaded.payload["category"] == "auth"
    assert loaded.correlation_id == "corr-1"


def test_event_store_by_correlation(manager: ConnectionManager) -> None:
    store = EventStore(EventRepository(manager))
    for stage in (PipelineStage.RAW, PipelineStage.CANONICAL, PipelineStage.ENRICHED):
        store.record(
            stage=stage,
            correlation_id="corr-1",
            source="pipeline",
            event_type=stage,
            payload={"step": stage},
        )
    store.record(
        stage=PipelineStage.ALERT,
        correlation_id="corr-2",
        source="detection",
        event_type="Alert",
        payload={},
    )

    chain = store.repository.by_correlation("corr-1")
    assert len(chain) == 3
    assert [e.pipeline_stage for e in chain] == [
        PipelineStage.RAW,
        PipelineStage.CANONICAL,
        PipelineStage.ENRICHED,
    ]


def test_event_store_by_stage_and_count(manager: ConnectionManager) -> None:
    store = EventStore(EventRepository(manager))
    store.record(
        stage=PipelineStage.ALERT, correlation_id="c1", source="d", event_type="Alert", payload={}
    )
    store.record(
        stage=PipelineStage.ALERT, correlation_id="c2", source="d", event_type="Alert", payload={}
    )
    store.record(
        stage=PipelineStage.INCIDENT,
        correlation_id="c3",
        source="i",
        event_type="Incident",
        payload={},
    )

    assert store.repository.count() == 3
    assert len(store.repository.by_stage(PipelineStage.ALERT)) == 2
    assert len(store.repository.by_stage(PipelineStage.INCIDENT)) == 1


def test_event_store_query_pagination(manager: ConnectionManager) -> None:
    store = EventStore(EventRepository(manager))
    for i in range(5):
        store.record(
            stage=PipelineStage.RAW,
            correlation_id=f"c{i}",
            source="s",
            event_type="RawEvent",
            payload={"i": i},
        )

    page = store.repository.query(stage=PipelineStage.RAW, limit=2, offset=0)
    assert len(page.items) == 2
    assert page.total == 5

    page2 = store.repository.query(stage=PipelineStage.RAW, limit=2, offset=2)
    assert len(page2.items) == 2


def test_event_store_record_domain_object(manager: ConnectionManager) -> None:
    store = EventStore(EventRepository(manager))
    alert = Alert(title="Teste", rule_id="brute-force", severity=AlertSeverity.HIGH)
    event = store.record_event(PipelineStage.ALERT, alert, correlation_id="corr-9")

    assert event.event_type == "Alert"
    assert event.pipeline_stage == PipelineStage.ALERT
    assert event.payload["rule_id"] == "brute-force"


def test_event_store_query_filter(manager: ConnectionManager) -> None:
    store = EventStore(EventRepository(manager))
    store.record(
        stage=PipelineStage.ALERT, correlation_id="c1", source="d", event_type="Alert", payload={}
    )
    page = store.repository.query(correlation_id="c1")
    assert page.total == 1
