"""Contratos base do Alert Engine.

Define o protocolo ``AlertProcessor`` (hook de ciclo de vida) usado
pelo ``AlertRegistry``. O design segue o padrao de plugins do projeto.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .models import Alert


@runtime_checkable
class AlertProcessor(Protocol):
    """Hook de ciclo de vida de alertas.

    Implementacoes recebem o ``Alert`` em momentos-chave e podem
    persistir, notificar, enriquecer ou auditar. Nunca mutam o alerta
    (imutavel) - retornam acoes/efeitos laterais.
    """

    def on_created(self, alert: Alert) -> None:
        """Chamado apos um alerta ser criado."""
        ...

    def on_updated(self, alert: Alert) -> None:
        """Chamado apos um alerta ser atualizado (deduplicacao)."""
        ...

    def on_status_changed(self, alert: Alert, previous: str, current: str) -> None:
        """Chamado quando o estado do ciclo de vida muda."""
        ...


__all__ = ["AlertProcessor"]
