"""Persistence do EDY SIEM.

- ``ConnectionManager``: conexoes SQLite (WAL, foreign keys)
- ``TransactionManager`` / ``UnitOfWork``: transacoes atomicas
- ``Repository`` / ``GenericRepository``: repositorios por agregado com
  CRUD completo + paginacao/ordenacao/filtros (sem SQL espalhado)
- ``Migration`` / ``MigrationRunner``: schema versionado
- ``EventRepository`` / ``EventStore``: Event Store da pipeline
- Repositorios: ``AlertRepository``, ``IncidentRepository``, ``CaseRepository``
"""

from .connection import ConnectionManager
from .event_store import EventRepository, EventStore, PipelineStage, StoredEvent
from .exceptions import (
    ConnectionError,
    MigrationError,
    PersistenceError,
    RecordNotFoundError,
    TransactionError,
)
from .migrations import Migration, MigrationRunner
from .query import Page, QueryFilter, QueryOp, SortOrder
from .repository import GenericRepository, Repository
from .schema import ALL_MIGRATIONS
from .transactions import Transaction, TransactionManager, UnitOfWork

__all__ = [
    "ALL_MIGRATIONS",
    "ConnectionError",
    "ConnectionManager",
    "EventRepository",
    "EventStore",
    "GenericRepository",
    "Migration",
    "MigrationError",
    "MigrationRunner",
    "Page",
    "PersistenceError",
    "PipelineStage",
    "QueryFilter",
    "QueryOp",
    "RecordNotFoundError",
    "Repository",
    "SortOrder",
    "StoredEvent",
    "Transaction",
    "TransactionError",
    "TransactionManager",
    "UnitOfWork",
]
