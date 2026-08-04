"""Transaction Manager e Unit of Work.

- ``TransactionManager``: BEGIN/COMMIT/ROLLBACK com context manager.
- ``UnitOfWork``: agrupa repositorios em uma transacao atomica.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .connection import ConnectionManager
from .exceptions import TransactionError
from .repos import AlertRepository, CaseRepository, IncidentRepository


@dataclass(frozen=True, slots=True)
class Transaction:
    """Wrapper de transacao SQLite (context manager).

    Commita ao sair sem erro; faz rollback se levantar excecao.
    """

    conn: sqlite3.Connection

    def __enter__(self) -> Transaction:
        self.conn.execute("BEGIN")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        except sqlite3.Error as e:
            raise TransactionError(f"falha ao finalizar transacao: {e}") from e


class TransactionManager:
    """Gerencia transacoes sobre um ``ConnectionManager``."""

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    @property
    def manager(self) -> ConnectionManager:
        """ConnectionManager subjacente."""
        return self._manager

    def begin(self) -> Transaction:
        """Inicia uma transacao."""
        return Transaction(self._manager.connect())


class UnitOfWork:
    """Agrupa repositorios em uma transacao atomica.

    Uso:
        with uow:
            uow.alerts.add(alert)
            uow.incidents.add(incident)
        # commit automatico ao sair do bloco
    """

    def __init__(
        self,
        manager: ConnectionManager,
        alerts: AlertRepository | None = None,
        incidents: IncidentRepository | None = None,
        cases: CaseRepository | None = None,
    ) -> None:
        self._manager = manager
        self._alerts = alerts or AlertRepository(manager)
        self._incidents = incidents or IncidentRepository(manager)
        self._cases = cases or CaseRepository(manager)

    @property
    def alerts(self) -> AlertRepository:
        """Repositorio de alertas."""
        return self._alerts

    @property
    def incidents(self) -> IncidentRepository:
        """Repositorio de incidentes."""
        return self._incidents

    @property
    def cases(self) -> CaseRepository:
        """Repositorio de cases."""
        return self._cases

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        conn = self._manager.connect()
        try:
            if exc_type is None:
                conn.commit()
            else:
                conn.rollback()
        except sqlite3.Error as e:
            raise TransactionError(f"falha ao finalizar UoW: {e}") from e


__all__ = ["Transaction", "TransactionManager", "UnitOfWork"]
