"""Task Engine do Case Framework.

Permite criar, concluir e reabrir tarefas de investigacao, com
prioridade, responsavel e prazo.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .._utils import new_id as _new_id
from .._utils import utcnow as _utcnow
from .exceptions import CaseTaskNotFoundError
from .models import Case, CasePriority, CaseTask, CaseTaskStatus
from .timeline import TimelineEngine


class TaskEngine:
    """Gerencia tarefas de um case.

    Args:
        timeline: Engine de timeline (para auto-registro).
    """

    def __init__(self, timeline: TimelineEngine | None = None) -> None:
        self._timeline = timeline or TimelineEngine()

    def create(
        self,
        case: Case,
        title: str,
        *,
        priority: CasePriority = CasePriority.P3,
        assignee: str | None = None,
        due_at: datetime | None = None,
        created_by: str = "system",
    ) -> Case:
        """Cria uma tarefa no case.

        Returns:
            ``Case`` atualizado com a tarefa e registro na timeline.
        """
        task = CaseTask(
            title=title,
            priority=priority,
            assignee=assignee,
            due_at=due_at,
            created_by=created_by,
            id=_new_id(),
            created_at=_utcnow(),
        )
        updated = replace(case, tasks=(*case.tasks, task))
        return self._timeline.record_task(updated, title, actor=created_by)

    def complete(self, case: Case, task_id: str, *, actor: str = "system") -> Case:
        """Conclui uma tarefa do case.

        Raises:
            CaseTaskNotFoundError: Se a tarefa nao existe.
        """
        tasks = [self._find(case, task_id)]
        updated_tasks = tuple(
            replace(t, status=CaseTaskStatus.COMPLETED) if t.id == task_id else t
            for t in case.tasks
        )
        updated = replace(case, tasks=updated_tasks)
        return self._timeline.record(
            updated, "task_completed", f"Tarefa '{tasks[0].title}' concluida", actor
        )

    def reopen(self, case: Case, task_id: str, *, actor: str = "system") -> Case:
        """Reabre uma tarefa concluida.

        Raises:
            CaseTaskNotFoundError: Se a tarefa nao existe.
        """
        self._find(case, task_id)
        updated_tasks = tuple(
            replace(t, status=CaseTaskStatus.REOPENED) if t.id == task_id else t for t in case.tasks
        )
        updated = replace(case, tasks=updated_tasks)
        return self._timeline.record(
            updated, "task_reopened", f"Tarefa '{task_id}' reaberta", actor
        )

    def _find(self, case: Case, task_id: str) -> CaseTask:
        """Localiza uma tarefa por ID."""
        for task in case.tasks:
            if task.id == task_id:
                return task
        raise CaseTaskNotFoundError(task_id)


__all__ = ["TaskEngine"]
