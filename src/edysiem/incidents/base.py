"""Contratos base do Incident Engine.

Define o protocolo ``IncidentProcessor`` (hook de ciclo de vida) usado
pelo ``IncidentRegistry``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .models import Incident, IncidentStatus


@runtime_checkable
class IncidentProcessor(Protocol):
    """Hook de ciclo de vida de incidentes.

    Recebe o ``Incident`` em momentos-chave e pode persistir, notificar,
    auditar ou enriquecer. Nunca muta o incidente (imutavel).
    """

    def on_created(self, incident: Incident) -> None:
        """Chamado apos um incidente ser criado."""
        ...

    def on_updated(self, incident: Incident) -> None:
        """Chamado apos um incidente ser atualizado (deduplicacao)."""
        ...

    def on_status_changed(
        self, incident: Incident, previous: IncidentStatus, current: IncidentStatus
    ) -> None:
        """Chamado quando o estado do ciclo de vida muda."""
        ...

    def on_reopened(self, incident: Incident) -> None:
        """Chamado quando um incidente e reaberto."""
        ...


__all__ = ["IncidentProcessor"]
