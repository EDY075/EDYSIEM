"""Testes do Search Engine (2.11.4) e Audit Trail (2.11.5)."""

from __future__ import annotations

import pytest

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.domain import RiskScore
from edysiem.persistence import (
    ALL_MIGRATIONS,
    AuditAction,
    AuditEngine,
    AuditRepository,
    ConnectionManager,
    MigrationRunner,
    SearchEngine,
    SortOrder,
)
from edysiem.persistence.repos import AlertRepository, CaseRepository, IncidentRepository


@pytest.fixture
def manager() -> ConnectionManager:
    m = ConnectionManager(":memory:")
    MigrationRunner(ALL_MIGRATIONS).apply(m)
    return m


# --- Search Engine ---------------------------------------------------------


@pytest.fixture
def engine(manager: ConnectionManager) -> SearchEngine:
    alerts = AlertRepository(manager)
    alert1 = _alert("a1")
    alert2 = Alert(
        id="a2",
        title="Malware detectado",
        severity=AlertSeverity.CRITICAL,
        risk_score=RiskScore(90),
        rule_id="malware",
        user="root",
        ioc_ids=("evil.com",),
        fingerprint=AlertFingerprint(hash="fp-a2", rule_id="malware"),
    )
    alerts.add(alert1)
    alerts.add(alert2)
    return SearchEngine(alerts, IncidentRepository(manager), CaseRepository(manager))


def test_search_alerts_by_rule(manager: ConnectionManager) -> None:
    engine = SearchEngine(
        AlertRepository(manager), IncidentRepository(manager), CaseRepository(manager)
    )
    _populate(manager)
    page = engine.search_alerts(rule="brute-force")
    assert page.total == 2


def _populate(manager: ConnectionManager) -> None:
    repo = AlertRepository(manager)
    repo.add(_alert("a1", "brute-force"))
    repo.add(
        Alert(
            id="a2",
            title="Malware detectado",
            severity=AlertSeverity.CRITICAL,
            risk_score=RiskScore(90),
            rule_id="malware",
            user="root",
            ioc_ids=("evil.com",),
            fingerprint=AlertFingerprint(hash="fp-a2", rule_id="malware"),
        )
    )
    repo.add(
        Alert(
            id="a3",
            title="Brute force SSH",
            severity=AlertSeverity.MEDIUM,
            risk_score=RiskScore(50),
            rule_id="brute-force",
            user="admin",
            fingerprint=AlertFingerprint(hash="fp-a3", rule_id="brute-force"),
        )
    )


def _alert(alert_id: str, rule: str) -> Alert:
    return Alert(
        id=alert_id,
        title=f"Alert {alert_id}",
        severity=AlertSeverity.HIGH,
        risk_score=RiskScore(70),
        rule_id=rule,
        user="admin",
        ioc_ids=("8.8.8.8",),
        fingerprint=AlertFingerprint(hash=f"fp-{alert_id}", rule_id=rule),
    )


def test_search_alerts_partial_term(manager: ConnectionManager) -> None:
    _populate(manager)
    engine = SearchEngine(
        AlertRepository(manager), IncidentRepository(manager), CaseRepository(manager)
    )
    page = engine.search_alerts(term="Brute force")  # parcial (LIKE)
    assert page.total == 1


def test_search_alerts_exact(manager: ConnectionManager) -> None:
    _populate(manager)
    engine = SearchEngine(
        AlertRepository(manager), IncidentRepository(manager), CaseRepository(manager)
    )
    page = engine.search_alerts(term="Alert a1", exact=True)
    assert page.total == 1


def test_search_alerts_by_ioc_severity_status(manager: ConnectionManager) -> None:
    _populate(manager)
    engine = SearchEngine(
        AlertRepository(manager), IncidentRepository(manager), CaseRepository(manager)
    )
    assert engine.search_alerts(severity="critical").total == 1
    assert engine.search_alerts(hash="fp-a2").total == 1


def test_search_incidents(manager: ConnectionManager) -> None:
    from edysiem.incidents import Incident, IncidentSeverity

    incidents = IncidentRepository(manager)
    incidents.add(
        Incident(title="Incidente BF", severity=IncidentSeverity.HIGH, alerts=("a1", "a2"))
    )
    incidents.add(
        Incident(
            title="Incidente Malware", severity=IncidentSeverity.CRITICAL, users=frozenset({"root"})
        )
    )
    engine = SearchEngine(AlertRepository(manager), incidents, CaseRepository(manager))

    assert engine.search_incidents(severity="critical").total == 1
    assert engine.search_incidents(term="Incidente BF", exact=True).total == 1


def test_search_cases(manager: ConnectionManager) -> None:
    from edysiem.cases import Case, CaseStatus

    cases = CaseRepository(manager)
    cases.add(Case(title="Investigar BF", status=CaseStatus.OPEN))
    cases.add(Case(title="Investigar Malware", status=CaseStatus.IN_PROGRESS))
    engine = SearchEngine(AlertRepository(manager), IncidentRepository(manager), cases)

    assert engine.search_cases(status="in_progress").total == 1
    assert engine.search_cases(term="Investigar", exact=False).total == 2


def test_search_multi_entity(manager: ConnectionManager) -> None:
    from edysiem.incidents import Incident, IncidentSeverity

    _populate(manager)
    alerts = AlertRepository(manager)
    incidents = IncidentRepository(manager)
    incidents.add(Incident(title="Incidente BF", severity=IncidentSeverity.HIGH))
    engine = SearchEngine(alerts, incidents, CaseRepository(manager))

    results = engine.search(rule="brute-force", entity="alert")
    assert results.alerts.total == 2
    assert results.total == 2


def test_search_pagination(manager: ConnectionManager) -> None:
    _populate(manager)
    engine = SearchEngine(
        AlertRepository(manager), IncidentRepository(manager), CaseRepository(manager)
    )
    page = engine.search_alerts(
        rule="brute-force", limit=1, offset=0, sort_by="created_at", order=SortOrder.ASC
    )
    assert len(page.items) == 1
    assert page.total == 2
    assert page.has_more is True


# --- Audit Trail ------------------------------------------------------------


def test_audit_repository_crud(manager: ConnectionManager) -> None:
    repo = AuditRepository(manager)
    engine = AuditEngine(repo)

    entry = engine.record_create(actor="analyst-01", entity_type="Alert", entity_id="a1")
    assert repo.get(entry.entry_id) is not None
    assert repo.count() == 1


def test_audit_actions(manager: ConnectionManager) -> None:
    repo = AuditRepository(manager)
    engine = AuditEngine(repo)

    engine.record_create(actor="s", entity_type="Case", entity_id="c1")
    engine.record_status_change(
        actor="analyst", entity_type="Case", entity_id="c1", previous="open", current="in_progress"
    )
    engine.record_owner_change(
        actor="analyst", entity_type="Case", entity_id="c1", previous=None, current="analyst-02"
    )
    engine.record_comment(actor="analyst", entity_type="Case", entity_id="c1", body="nota")
    engine.record_evidence(
        actor="analyst", entity_type="Case", entity_id="c1", kind="ip", value="1.2.3.4"
    )
    engine.record_delete(actor="admin", entity_type="Case", entity_id="c1")

    assert repo.count() == 6
    assert len(repo.by_entity("Case", "c1")) == 6
    assert len(repo.by_action(AuditAction.STATUS_CHANGE)) == 1


def test_audit_entry_validation(manager: ConnectionManager) -> None:
    repo = AuditRepository(manager)
    engine = AuditEngine(repo)
    with pytest.raises(ValueError, match="actor_id"):
        engine.record(actor="", action=AuditAction.CREATE, entity_type="Case", entity_id="c")


def test_audit_query_pagination(manager: ConnectionManager) -> None:
    repo = AuditRepository(manager)
    engine = AuditEngine(repo)
    for i in range(5):
        engine.record_create(actor="s", entity_type="Alert", entity_id=f"a{i}")

    page = repo.query(limit=2, offset=0)
    assert len(page.items) == 2
    assert page.total == 5

    page2 = repo.query(actor_id="s", limit=2, offset=2)
    assert len(page2.items) == 2


def test_audit_entry_preserves_details(manager: ConnectionManager) -> None:
    repo = AuditRepository(manager)
    engine = AuditEngine(repo)
    entry = engine.record_evidence(
        actor="analyst", entity_type="Case", entity_id="c1", kind="hash", value="abc123"
    )
    loaded = repo.get(entry.entry_id)
    assert loaded.details["kind"] == "hash"
    assert loaded.details["value"] == "abc123"
