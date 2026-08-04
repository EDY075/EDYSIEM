"""Contratos base do Case Engine.

Define o protocolo ``CaseProcessor`` (hook de ciclo de vida) usado
pelo ``CaseRegistry``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .models import Case, CaseStatus


@runtime_checkable
class CaseProcessor(Protocol):
    """Hook de ciclo de vida de cases.

    Recebe o ``Case`` em momentos-chave e pode persistir, notificar,
    auditar ou enriquecer. Nunca muta o case (imutavel).
    """

    def on_created(self, case: Case) -> None:
        """Chamado apos um case ser criado."""
        ...

    def on_updated(self, case: Case) -> None:
        """Chamado apos um case ser atualizado."""
        ...

    def on_status_changed(self, case: Case, previous: CaseStatus, current: CaseStatus) -> None:
        """Chamado quando o estado do ciclo de vida muda."""
        ...


__all__ = ["CaseProcessor"]
