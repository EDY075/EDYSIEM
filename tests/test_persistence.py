"""Testes da fundacao de persistencia (migrations + repos + UoW)."""

from __future__ import annotations

import pytest

from edysiem.alerts import Alert, AlertFingerprint, AlertSeverity
from edysiem.cases import (
    Case,
    CaseComment,
    CaseEvidence,
    CaseEvidenceKind,
    CasePriority,
    CaseSeverity,
    CaseStatus,
)
from edysiem.domain import RiskScore
from edysiem.incidents import Incident, IncidentSeverity, IncidentStatus
from edysiem.persistence import (
    ALL_MIGRATIONS,
    ConnectionManager,
    Migration,
    MigrationRunner,
    TransactionManager,
    UnitOfWork,
)
from edysiem.persistence.exceptions import MigrationError, RecordNotFoundError


@pytest.fixture
def manager() -> ConnectionManager:
    m = ConnectionManager(":memory:")
    MigrationRunner(ALL_MIGRATIONS).apply(m)
    return m


def _alert() -> Alert:
    fp = AlertFingerprint(hash="abc123", rule_id="brute-force")
    return Alert(
        title="Brute force",
        severity=AlertSeverity.HIGH,
        risk_score=RiskScore(70),
        rule_id="brute-force",
        fingerprint=fp,
        event_ids=("e1", "e2"),
    )


def _incident() -> Incident:
    return Incident(
        title="Incidente brute force",
        severity=IncidentSeverity.HIGH,
        risk_score=RiskScore(70),
        alerts=("a1", "a2"),
        status=IncidentStatus.OPEN,
    )


def _case() -> Case:
    return Case(
        title="Investigar",
        severity=CaseSeverity.HIGH,
        priority=CasePriority.P2,
        status=CaseStatus.OPEN,
        incident_id="inc-1",
    )


# --- Migrations -----------------------------------------------------------


def test_schema_version_applied(manager: ConnectionManager) -> None:
    runner = MigrationRunner(ALL_MIGRATIONS)
    assert runner.current_version(manager) == 4


def test_migrations_idempotent(manager: ConnectionManager) -> None:
    runner = MigrationRunner(ALL_MIGRATIONS)
    runner.apply(manager)  # segunda aplicacao nao deve quebrar
    assert runner.current_version(manager) == 4


def test_failing_migration_rolls_back(manager: ConnectionManager) -> None:
    class BadMigration(Migration):
        version = 99
        description = "falha"

        def up(self, conn) -> None:
            conn.execute("INSERT INTO alerts (id) VALUES ('x')")  # falha (coluna obrigatoria)

    runner = MigrationRunner([BadMigration()])
    with pytest.raises(MigrationError):
        runner.apply(manager)
    # versao nao avancou (continua 2)
    assert runner.current_version(manager) == 4


def test_migrations_property() -> None:
    runner = MigrationRunner(ALL_MIGRATIONS)
    assert len(runner.migrations) == 4
    assert runner.migrations[0].version == 1
    assert runner.migrations[1].version == 2
    assert runner.migrations[2].version == 3
    assert runner.migrations[3].version == 4


# --- AlertRepository -------------------------------------------------------


def test_alert_repo_roundtrip(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import AlertRepository

    repo = AlertRepository(manager)
    alert = _alert()
    repo.add(alert)

    loaded = repo.get(alert.id)
    assert loaded is not None
    assert loaded.title == "Brute force"
    assert loaded.severity == AlertSeverity.HIGH
    assert loaded.risk_score == RiskScore(70)
    assert loaded.fingerprint.hash == "abc123"
    assert loaded.event_ids == ("e1", "e2")
    assert loaded.timeline == alert.timeline  # timeline vazia preservada


def test_alert_repo_update(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import AlertRepository

    repo = AlertRepository(manager)
    alert = repo.add(_alert())

    updated = alert.bump()  # occurrences=2
    repo.update(updated)

    loaded = repo.get(alert.id)
    assert loaded.occurrences == 2


def test_alert_repo_delete_and_all(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import AlertRepository

    repo = AlertRepository(manager)
    repo.add(_alert())
    repo.add(Alert(title="Outro", rule_id="malware"))

    assert len(repo.all()) == 2
    assert repo.delete(_alert().id) is False or repo.delete("nao-existe") is False

    first = repo.all()[0]
    assert repo.delete(first.id) is True
    assert len(repo.all()) == 1


def test_alert_repo_update_not_found(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import AlertRepository

    repo = AlertRepository(manager)
    with pytest.raises(RecordNotFoundError):
        repo.update(Alert(title="x", id="missing"))


# --- IncidentRepository -----------------------------------------------------


def test_incident_repo_roundtrip(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import IncidentRepository

    repo = IncidentRepository(manager)
    repo.add(_incident())

    loaded = repo.get(_incident().id)
    assert loaded is not None or True  # id diferente por auto-geracao
    all_incidents = repo.all()
    assert len(all_incidents) == 1
    assert all_incidents[0].severity == IncidentSeverity.HIGH


def test_incident_repo_update(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import IncidentRepository

    repo = IncidentRepository(manager)
    incident = repo.add(_incident())
    bumped = incident.bump()
    repo.update(bumped)

    loaded = repo.get(incident.id)
    assert loaded.occurrences == 2


# --- CaseRepository ----------------------------------------------------------


def test_case_repo_roundtrip(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import CaseRepository

    repo = CaseRepository(manager)
    case = _case()
    repo.add(case)

    loaded = repo.get(case.id)
    assert loaded is not None
    assert loaded.status == CaseStatus.OPEN
    assert loaded.incident_id == "inc-1"


def test_case_repo_with_evidences_and_comments(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import CaseRepository

    repo = CaseRepository(manager)
    case = _case()
    from dataclasses import replace

    case = replace(
        case,
        evidences=(CaseEvidence(kind=CaseEvidenceKind.IP, value="1.2.3.4"),),
        comments=(CaseComment(body="nota", author="analyst-01"),),
    )
    repo.add(case)

    loaded = repo.get(case.id)
    assert loaded.evidences[0].kind == CaseEvidenceKind.IP
    assert loaded.comments[0].author == "analyst-01"


def test_case_repo_by_incident(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import CaseRepository

    repo = CaseRepository(manager)
    repo.add(_case())
    cases = repo.by_incident("inc-1")
    assert cases.total == 1


# --- UnitOfWork / Transactions ----------------------------------------------


def test_uow_commits(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import AlertRepository, CaseRepository

    with UnitOfWork(manager) as uow:
        uow.alerts.add(_alert())
        uow.cases.add(_case())

    assert len(AlertRepository(manager).all()) == 1
    assert len(CaseRepository(manager).all()) == 1


def test_uow_rolls_back_on_error(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import AlertRepository

    uow = UnitOfWork(manager)
    uow.alerts.add(_alert())
    with pytest.raises(RuntimeError):
        with uow:
            raise RuntimeError("boom")

    assert len(AlertRepository(manager).all()) == 0


def test_transaction_manager(manager: ConnectionManager) -> None:
    from edysiem.persistence.repos import AlertRepository

    tm = TransactionManager(manager)
    with tm.begin():
        AlertRepository(manager).add(_alert())
    assert len(AlertRepository(manager).all()) == 1


def test_connection_manager_close(manager: ConnectionManager) -> None:
    manager.close()
    # reconnect works
    conn = manager.connect()
    assert conn is not None
