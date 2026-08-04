"""Timeline Engine do Case Framework.

Registra automaticamente acoes no historico imutavel de um case:
criacao, novo alerta, mudanca de status, comentario, anexo, tarefa,
mudanca de owner, resolucao e reabertura.

Cada metodo recebe um ``Case`` e retorna uma copia com uma nova
entrada na timeline (append-only).
"""

from __future__ import annotations

from .._utils import utcnow as _utcnow
from .models import Case, CaseStatus, CaseTimelineEntry


class TimelineEngine:
    """Registra eventos na timeline de um case (append-only)."""

    def record(self, case: Case, action: str, detail: str, actor: str = "system") -> Case:
        """Registra uma acao arbitraria na timeline."""
        entry = CaseTimelineEntry(action=action, detail=detail, actor=actor, created_at=_utcnow())
        return self._append(case, entry)

    def record_created(self, case: Case, actor: str = "system") -> Case:
        """Registra a criacao do case."""
        return self.record(case, "created", f"Case '{case.title}' criado", actor)

    def record_alert_added(self, case: Case, alert_id: str, actor: str = "system") -> Case:
        """Registra a adicao de um alerta ao case."""
        return self.record(case, "alert_added", f"Alerta {alert_id} adicionado", actor)

    def record_status_change(
        self, case: Case, previous: CaseStatus, current: CaseStatus, actor: str = "system"
    ) -> Case:
        """Registra uma mudanca de status."""
        return self.record(
            case,
            "status_change",
            f"{previous.value} -> {current.value}",
            actor,
        )

    def record_comment(self, case: Case, author: str, snippet: str = "") -> Case:
        """Registra um comentario na timeline."""
        detail = f"Comentario por {author}"
        if snippet:
            detail += f": {snippet[:80]}"
        return self.record(case, "comment", detail, author)

    def record_attachment(self, case: Case, name: str, actor: str = "system") -> Case:
        """Registra um anexo na timeline."""
        return self.record(case, "attachment", f"Anexo '{name}' adicionado", actor)

    def record_task(self, case: Case, task_title: str, actor: str = "system") -> Case:
        """Registra uma tarefa na timeline."""
        return self.record(case, "task", f"Tarefa '{task_title}' criada", actor)

    def record_owner_change(
        self, case: Case, previous: str | None, current: str, actor: str = "system"
    ) -> Case:
        """Registra a transferencia de responsavel."""
        detail = f"Owner {previous or 'nenhum'} -> {current}"
        return self.record(case, "owner_change", detail, actor)

    def record_resolution(self, case: Case, actor: str = "system") -> Case:
        """Registra a resolucao do case."""
        return self.record(case, "resolved", "Case resolvido", actor)

    def record_reopen(self, case: Case, actor: str = "system") -> Case:
        """Registra a reabertura do case."""
        return self.record(case, "reopened", "Case reaberto", actor)

    def _append(self, case: Case, entry: CaseTimelineEntry) -> Case:
        """Retorna uma copia do case com a entrada anexada (append-only)."""
        from dataclasses import replace

        return replace(
            case,
            timeline=(*case.timeline, entry),
            updated_at=entry.created_at,
        )


__all__ = ["TimelineEngine"]
