"""Excecoes da camada de persistencia."""

from __future__ import annotations

from ..exceptions import InfrastructureException


class PersistenceError(InfrastructureException):
    """Erro base da camada de persistencia."""


class ConnectionError(PersistenceError):
    """Erro ao abrir/manter conexao com o storage."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MigrationError(PersistenceError):
    """Erro na aplicacao/rolagem de migracoes."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TransactionError(PersistenceError):
    """Erro no gerenciamento de transacoes."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class RecordNotFoundError(PersistenceError):
    """Registro nao encontrado no storage."""

    def __init__(self, kind: str, record_id: str) -> None:
        self.kind = kind
        self.record_id = record_id
        super().__init__(f"{kind} '{record_id}' nao encontrado")


__all__ = [
    "ConnectionError",
    "MigrationError",
    "PersistenceError",
    "RecordNotFoundError",
    "TransactionError",
]
