"""Case Engine (Investigation Workspace).

Orquestra os sub-engines operacionais de um case:
- ``TimelineEngine``: auto-registro de acoes (append-only)
- ``EvidenceEngine``: anexar evidencias (logs/hashes/IPs/domains/arquivos/prints/JSON/IOC/links)
- ``CommentEngine``: notas markdown com autor/data
- ``TaskEngine``: tarefas (criar/concluir/reabrir, prioridade, responsavel, prazo)
- ``OwnerEngine``: transferencia de responsavel
- ``AttachmentEngine``: anexos

Fluxo:
    Incident -> CaseBuilder -> Case -> (engines operacionais) -> Resolution
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .._utils import utcnow as _utcnow
from ..incidents import Incident
from .attachments import AttachmentEngine
from .builder import CaseBuilder
from .context import CaseContext
from .evidence import EvidenceEngine
from .exceptions import CaseNotFoundError
from .models import (
    Case,
    CaseEvidenceKind,
    CaseMetrics,
    CasePriority,
    CaseStatus,
)
from .notes import CommentEngine
from .owners import OwnerEngine
from .registry import CaseRegistry
from .tasks import TaskEngine
from .timeline import TimelineEngine


class CaseResultKind(Enum):
    """Tipo de resultado do Case Engine."""

    CREATED = "created"
    ALREADY_EXISTS = "already_exists"


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Resultado do processamento de um incidente.

    Attributes:
        kind: CREATED / ALREADY_EXISTS.
        case: Case resultante.
        was_new: Se foi criado.
    """

    kind: CaseResultKind
    case: Case
    was_new: bool


class CaseEngine:
    """Workspace operacional do analista SOC.

    Args:
        builder: Construtor de cases a partir de incidentes.
        registry: Hooks de ciclo de vida.
        context: Armazenamento in-memory.
    """

    def __init__(
        self,
        builder: CaseBuilder | None = None,
        registry: CaseRegistry | None = None,
        context: CaseContext | None = None,
    ) -> None:
        self._context = context if context is not None else CaseContext()
        self._registry = registry or CaseRegistry()
        self._builder = builder or CaseBuilder()

        self._timeline = TimelineEngine()
        self._evidence = EvidenceEngine(self._timeline)
        self._comments = CommentEngine(self._timeline)
        self._tasks = TaskEngine(self._timeline)
        self._owners = OwnerEngine(self._timeline)
        self._attachments = AttachmentEngine(self._timeline)

        self._metrics = CaseMetrics()

    # --- Sub-engines ------------------------------------------------------

    @property
    def timeline(self) -> TimelineEngine:
        """Engine de timeline."""
        return self._timeline

    @property
    def evidence(self) -> EvidenceEngine:
        """Engine de evidencias."""
        return self._evidence

    @property
    def comments(self) -> CommentEngine:
        """Engine de comentarios/notas."""
        return self._comments

    @property
    def tasks(self) -> TaskEngine:
        """Engine de tarefas."""
        return self._tasks

    @property
    def owners(self) -> OwnerEngine:
        """Engine de ownership."""
        return self._owners

    @property
    def attachments(self) -> AttachmentEngine:
        """Engine de anexos."""
        return self._attachments

    @property
    def context(self) -> CaseContext:
        """Armazenamento de cases."""
        return self._context

    @property
    def registry(self) -> CaseRegistry:
        """Registry de hooks."""
        return self._registry

    @property
    def metrics(self) -> CaseMetrics:
        """Metricas do engine."""
        return self._metrics

    # --- Operacoes principais ---------------------------------------------

    async def create_from_incident(
        self,
        incident: Incident,
        *,
        title: str | None = None,
        owner: str | None = None,
        now: datetime | None = None,
    ) -> CaseResult:
        """Cria um case a partir de um incidente.

        Returns:
            ``CaseResult`` com kind CREATED.
        """
        now = now or _utcnow()
        case = self._builder.build(incident, title=title, owner=owner, now=now)
        case = self._timeline.record_created(case)
        self._context.save(case)
        self._metrics.total_created += 1
        self._registry.on_created(case)
        return CaseResult(kind=CaseResultKind.CREATED, case=case, was_new=True)

    def get(self, case_id: str) -> Case | None:
        """Retorna um case pelo ID."""
        return self._context.get(case_id)

    def _must_get(self, case_id: str) -> Case:
        """Retorna um case ou levanta ``CaseNotFoundError``."""
        case = self._context.get(case_id)
        if case is None:
            raise CaseNotFoundError(case_id)
        return case

    def _save(self, case: Case) -> Case:
        """Persiste um case e notifica hooks."""
        self._context.save(case)
        self._registry.on_updated(case)
        return case

    def transition(
        self,
        case_id: str,
        target: CaseStatus,
        *,
        actor: str = "system",
        detail: str = "",
        now: datetime | None = None,
    ) -> Case:
        """Aplica uma transicao de estado no ciclo de vida.

        Raises:
            CaseNotFoundError: Se o case nao existe.
            CaseInvalidStateTransition: Se a transicao e invalida.
        """
        case = self._must_get(case_id)
        now = now or _utcnow()
        current = case.status

        if not current.can_transition_to(target):
            from .exceptions import CaseInvalidStateTransition

            raise CaseInvalidStateTransition(current.value, target.value)

        from dataclasses import replace

        closed_at = now if target is CaseStatus.CLOSED else case.closed_at
        updated = replace(case, status=target, closed_at=closed_at)
        updated = self._timeline.record_status_change(updated, current, target, actor=actor)
        if detail:
            updated = self._timeline.record(updated, "note", detail, actor)
        if target is CaseStatus.RESOLVED:
            updated = self._timeline.record_resolution(updated, actor)
        if target is CaseStatus.REOPENED:
            updated = self._timeline.record_reopen(updated, actor)

        self._metrics.total_transitions += 1
        self._save(updated)
        self._registry.on_status_changed(updated, current, target)
        return updated

    def resolve(self, case_id: str, resolution: str, *, actor: str = "system") -> Case:
        """Resolve um case registrando a resolucao."""
        case = self._must_get(case_id)

        from dataclasses import replace

        updated = replace(case, resolution=resolution)
        updated = self._timeline.record_resolution(updated, actor)
        self._save(updated)
        return updated

    def add_alert(self, case_id: str, alert_id: str, *, actor: str = "system") -> Case:
        """Vincula um alerta ao case."""
        case = self._must_get(case_id)

        from dataclasses import replace

        updated = replace(case, alerts=(*case.alerts, alert_id))
        updated = self._timeline.record_alert_added(updated, alert_id, actor)
        self._save(updated)
        return updated

    # --- Conveniencias de operacao ----------------------------------------

    def add_comment(self, case_id: str, body: str, author: str) -> Case:
        """Adiciona uma nota markdown."""
        case = self._must_get(case_id)
        updated = self._comments.add(case, body, author)
        self._metrics.total_comments += 1
        return self._save(updated)

    def add_evidence(
        self,
        case_id: str,
        kind: CaseEvidenceKind,
        value: str,
        *,
        label: str = "",
        actor: str = "system",
    ) -> Case:
        """Anexa uma evidencia ao case."""
        case = self._must_get(case_id)
        updated = self._evidence.add(case, kind, value, label=label, actor=actor)
        self._metrics.total_evidences += 1
        return self._save(updated)

    def create_task(
        self,
        case_id: str,
        title: str,
        *,
        priority: CasePriority = CasePriority.P3,
        assignee: str | None = None,
        due_at: datetime | None = None,
        created_by: str = "system",
    ) -> Case:
        """Cria uma tarefa no case."""
        case = self._must_get(case_id)
        updated = self._tasks.create(
            case,
            title,
            priority=priority,
            assignee=assignee,
            due_at=due_at,
            created_by=created_by,
        )
        self._metrics.total_tasks_created += 1
        return self._save(updated)

    def complete_task(self, case_id: str, task_id: str, *, actor: str = "system") -> Case:
        """Conclui uma tarefa."""
        case = self._must_get(case_id)
        updated = self._tasks.complete(case, task_id, actor=actor)
        self._metrics.total_tasks_completed += 1
        return self._save(updated)

    def transfer_owner(self, case_id: str, new_owner: str, *, assigned_by: str = "system") -> Case:
        """Transfere o responsavel do case."""
        case = self._must_get(case_id)
        updated = self._owners.transfer(case, new_owner, assigned_by=assigned_by)
        self._metrics.total_owner_changes += 1
        return self._save(updated)

    def add_attachment(
        self,
        case_id: str,
        name: str,
        *,
        content_type: str = "",
        size: int = 0,
        url: str = "",
        added_by: str = "system",
    ) -> Case:
        """Anexa um arquivo/URL ao case."""
        case = self._must_get(case_id)
        updated = self._attachments.add(
            case, name, content_type=content_type, size=size, url=url, added_by=added_by
        )
        return self._save(updated)

    # --- Metricas / health ------------------------------------------------

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Snapshot de metricas do engine."""
        m = self._metrics
        return {
            "total_created": m.total_created,
            "total_transitions": m.total_transitions,
            "total_comments": m.total_comments,
            "total_evidences": m.total_evidences,
            "total_tasks_created": m.total_tasks_created,
            "total_tasks_completed": m.total_tasks_completed,
            "total_owner_changes": m.total_owner_changes,
            "context": self._context.snapshot(),
            "registry": self._registry.get_stats(),
            "last_updated": m.last_updated.isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        """Verifica saude do engine."""
        return {
            "engine": "healthy",
            "context": self._context.snapshot(),
            "metrics": self.get_metrics_snapshot(),
        }


__all__ = ["CaseEngine", "CaseResult", "CaseResultKind"]
