"""Owner Engine do Case Framework.

Permite transferir o responsavel (owner) de um case. Toda transferencia
e registrada na timeline.
"""

from __future__ import annotations

from dataclasses import replace

from .models import Case
from .timeline import TimelineEngine


class OwnerEngine:
    """Gerencia ownership de um case.

    Args:
        timeline: Engine de timeline (para auto-registro).
    """

    def __init__(self, timeline: TimelineEngine | None = None) -> None:
        self._timeline = timeline or TimelineEngine()

    def transfer(
        self,
        case: Case,
        new_owner: str,
        *,
        assigned_by: str = "system",
    ) -> Case:
        """Transfere o responsavel do case.

        Returns:
            ``Case`` atualizado com o novo owner e registro na timeline.
        """
        previous = case.owner
        # O registro de ownership fica implícito via timeline (append-only).
        updated = replace(case, owner=new_owner)
        return self._timeline.record_owner_change(updated, previous, new_owner, actor=assigned_by)


__all__ = ["OwnerEngine"]
