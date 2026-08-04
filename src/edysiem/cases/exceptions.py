"""Excecoes do Case Engine."""

from __future__ import annotations

from ..exceptions import EdysiemException


class CaseError(EdysiemException):
    """Erro base do Case Engine."""


class CaseNotFoundError(CaseError):
    """Case nao encontrado no contexto."""

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        super().__init__(f"Case '{case_id}' nao encontrado")


class CaseInvalidStateTransition(CaseError):
    """Transicao de ciclo de vida invalida."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Transicao invalida de estado '{current}' para '{target}'")


class CaseBuilderError(CaseError):
    """Erro ao construir um case a partir de um incidente."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CaseRegistrationError(CaseError):
    """Erro ao registrar hook no registry."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CaseTaskNotFoundError(CaseError):
    """Tarefa nao encontrada em um case."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Tarefa '{task_id}' nao encontrada no case")


__all__ = [
    "CaseBuilderError",
    "CaseError",
    "CaseInvalidStateTransition",
    "CaseNotFoundError",
    "CaseRegistrationError",
    "CaseTaskNotFoundError",
]
