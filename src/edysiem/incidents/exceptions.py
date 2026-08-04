"""Excecoes do Incident Engine Enterprise."""

from __future__ import annotations

from ..exceptions import EdysiemException


class IncidentError(EdysiemException):
    """Erro base do Incident Engine."""


class IncidentNotFoundError(IncidentError):
    """Incidente nao encontrado no contexto/registry."""

    def __init__(self, incident_id: str) -> None:
        self.incident_id = incident_id
        super().__init__(f"Incidente '{incident_id}' nao encontrado")


class IncidentInvalidStateTransition(IncidentError):
    """Transicao de ciclo de vida invalida."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Transicao invalida de estado '{current}' para '{target}'")


class IncidentBuilderError(IncidentError):
    """Erro ao construir um incidente a partir de alertas."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class IncidentRegistrationError(IncidentError):
    """Erro ao registrar hook no registry."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "IncidentBuilderError",
    "IncidentError",
    "IncidentInvalidStateTransition",
    "IncidentNotFoundError",
    "IncidentRegistrationError",
]
