"""Testes dos modelos do Case Framework."""

from __future__ import annotations

import pytest

from edysiem.cases import (
    Case,
    CaseComment,
    CaseEvidence,
    CaseEvidenceKind,
    CasePriority,
    CaseSeverity,
    CaseStatus,
    CaseTask,
    CaseTaskStatus,
    Playbook,
    PlaybookStep,
)
from edysiem.domain import RiskScore


def test_case_severity_rank() -> None:
    assert CaseSeverity.INFO.rank == 0
    assert CaseSeverity.CRITICAL.rank == 4


def test_case_priority_rank() -> None:
    assert CasePriority.P1.rank == 0
    assert CasePriority.P5.rank == 4


def test_case_status_transitions() -> None:
    assert CaseStatus.OPEN.can_transition_to(CaseStatus.IN_PROGRESS)
    assert CaseStatus.IN_PROGRESS.can_transition_to(CaseStatus.ON_HOLD)
    assert CaseStatus.ON_HOLD.can_transition_to(CaseStatus.IN_PROGRESS)
    assert CaseStatus.RESOLVED.can_transition_to(CaseStatus.CLOSED)
    assert CaseStatus.CLOSED.can_transition_to(CaseStatus.REOPENED)
    assert CaseStatus.REOPENED.can_transition_to(CaseStatus.IN_PROGRESS)

    assert not CaseStatus.OPEN.can_transition_to(CaseStatus.REOPENED)
    assert not CaseStatus.OPEN.can_transition_to(CaseStatus.ON_HOLD)


def test_case_creation() -> None:
    case = Case(
        title="Investigar exfil",
        severity=CaseSeverity.HIGH,
        priority=CasePriority.P2,
        risk_score=RiskScore(75),
        owner="analyst-01",
    )
    assert case.title == "Investigar exfil"
    assert case.status == CaseStatus.OPEN
    assert case.owner == "analyst-01"
    assert case.id  # auto-gerado


def test_case_requires_title() -> None:
    with pytest.raises(ValueError, match="title nao pode ser vazio"):
        Case(title="")


def test_case_evidence_requires_value() -> None:
    with pytest.raises(ValueError, match="value nao pode ser vazio"):
        CaseEvidence(kind=CaseEvidenceKind.IP, value="")


def test_case_comment_requires_body_and_author() -> None:
    with pytest.raises(ValueError, match="body nao pode ser vazio"):
        CaseComment(body="", author="a")
    with pytest.raises(ValueError, match="author nao pode ser vazio"):
        CaseComment(body="x", author="")


def test_case_task_requires_title() -> None:
    with pytest.raises(ValueError, match="title nao pode ser vazio"):
        CaseTask(title="")


def test_case_task_defaults() -> None:
    task = CaseTask(title="Coletar memoria")
    assert task.status == CaseTaskStatus.PENDING
    assert task.priority == CasePriority.P3
    assert task.id  # auto-gerado


def test_playbook_step_validation() -> None:
    with pytest.raises(ValueError, match="order deve ser >= 1"):
        PlaybookStep(order=0, title="x")
    with pytest.raises(ValueError, match="title nao pode ser vazio"):
        PlaybookStep(order=1, title="")


def test_playbook_requires_name() -> None:
    with pytest.raises(ValueError, match="name nao pode ser vazio"):
        Playbook(name="")


def test_playbook_with_steps() -> None:
    playbook = Playbook(
        name="Isolamento",
        steps=(
            PlaybookStep(order=1, title="Isolar host"),
            PlaybookStep(order=2, title="Coletar evidencias"),
        ),
    )
    assert len(playbook.steps) == 2
    assert playbook.steps[0].order == 1
