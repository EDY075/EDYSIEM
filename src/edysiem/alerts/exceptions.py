"""Excecoes do Alert Engine Enterprise.

Hierarquia de erros especifica para o ciclo de vida de alertas.
"""

from __future__ import annotations

from ..exceptions import EdysiemException


class AlertError(EdysiemException):
    """Erro base do Alert Engine."""


class AlertNotFoundError(AlertError):
    """Alerta nao encontrado no contexto/registry."""

    def __init__(self, alert_id: str) -> None:
        self.alert_id = alert_id
        super().__init__(f"Alerta '{alert_id}' nao encontrado")


class AlertInvalidStateTransition(AlertError):
    """Transicao de ciclo de vida invalida."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Transicao invalida de estado '{current}' para '{target}'")


class AlertBuilderError(AlertError):
    """Erro ao construir um alerta a partir de um finding."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AlertRegistrationError(AlertError):
    """Erro ao registrar processor/hook no registry."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "AlertBuilderError",
    "AlertError",
    "AlertInvalidStateTransition",
    "AlertNotFoundError",
    "AlertRegistrationError",
]
