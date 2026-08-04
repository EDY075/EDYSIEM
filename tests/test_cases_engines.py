"""Testes dos sub-engines do Case Framework."""

from __future__ import annotations

import pytest

from edysiem.cases import (
    AttachmentEngine,
    Case,
    CaseEvidenceKind,
    CasePriority,
    CaseStatus,
    CommentEngine,
    EvidenceEngine,
    OwnerEngine,
    TaskEngine,
    TimelineEngine,
)
from edysiem.cases.exceptions import CaseTaskNotFoundError


def _case() -> Case:
    return Case(title="Test case")


def test_timeline_append_only() -> None:
    case = _case()
    engine = TimelineEngine()
    updated = engine.record_created(case)
    updated = engine.record_comment(updated, "analyst-01")
    updated = engine.record_status_change(updated, CaseStatus.OPEN, CaseStatus.IN_PROGRESS)

    assert len(updated.timeline) == 3
    assert updated.timeline[0].action == "created"
    assert updated.timeline[1].action == "comment"
    assert updated.timeline[2].action == "status_change"


def test_timeline_all_actions() -> None:
    case = _case()
    engine = TimelineEngine()
    updated = engine.record_created(case)
    updated = engine.record_alert_added(updated, "alert-1")
    updated = engine.record_attachment(updated, "file.txt")
    updated = engine.record_task(updated, "Tarefa 1")
    updated = engine.record_owner_change(updated, None, "analyst-01")
    updated = engine.record_resolution(updated)
    updated = engine.record_reopen(updated)

    actions = [e.action for e in updated.timeline]
    assert "alert_added" in actions
    assert "attachment" in actions
    assert "task" in actions
    assert "owner_change" in actions
    assert "resolved" in actions
    assert "reopened" in actions


def test_evidence_engine() -> None:
    case = _case()
    engine = EvidenceEngine()
    updated = engine.add_hash(case, "abc123", label="sha256")
    updated = engine.add_ip(updated, "1.2.3.4", label="C2")
    updated = engine.add_domain(updated, "evil.com")
    updated = engine.add_log(updated, "failed login")
    updated = engine.add_ioc(updated, "ioc-1")
    updated = engine.add_json(updated, '{"a":1}')
    updated = engine.add_link(updated, "https://example.com")

    kinds = [e.kind for e in updated.evidences]
    assert CaseEvidenceKind.HASH in kinds
    assert CaseEvidenceKind.IP in kinds
    assert CaseEvidenceKind.DOMAIN in kinds
    assert CaseEvidenceKind.LOG in kinds
    assert CaseEvidenceKind.IOC in kinds
    assert CaseEvidenceKind.JSON in kinds
    assert CaseEvidenceKind.LINK in kinds
    assert len(updated.evidences) == 7


def test_comment_engine() -> None:
    case = _case()
    engine = CommentEngine()
    updated = engine.add(case, "## Hipotesis\ncomprometido", "analyst-01")

    assert len(updated.comments) == 1
    assert updated.comments[0].author == "analyst-01"
    assert updated.comments[0].body.startswith("## Hipotesis")
    assert len(engine.history(updated)) == 1


def test_task_engine_create_complete_reopen() -> None:
    case = _case()
    engine = TaskEngine()
    updated = engine.create(
        case, "Coletar memoria", priority=CasePriority.P2, assignee="analyst-02"
    )

    task_id = updated.tasks[0].id
    assert updated.tasks[0].status.value == "pending"

    updated = engine.complete(updated, task_id)
    assert updated.tasks[0].status.value == "completed"

    updated = engine.reopen(updated, task_id)
    assert updated.tasks[0].status.value == "reopened"


def test_task_engine_not_found() -> None:
    case = _case()
    engine = TaskEngine()
    with pytest.raises(CaseTaskNotFoundError, match="nao encontrada"):
        engine.complete(case, "missing-task")


def test_owner_engine_transfer() -> None:
    case = _case()
    engine = OwnerEngine()
    updated = engine.transfer(case, "analyst-02", assigned_by="analyst-01")

    assert updated.owner == "analyst-02"
    assert any(e.action == "owner_change" for e in updated.timeline)


def test_attachment_engine() -> None:
    case = _case()
    engine = AttachmentEngine()
    updated = engine.add(
        case,
        "memoria.zip",
        content_type="application/zip",
        size=1024,
        added_by="analyst-01",
    )

    assert len(updated.attachments) == 1
    assert updated.attachments[0].name == "memoria.zip"
    assert any(e.action == "attachment" for e in updated.timeline)
