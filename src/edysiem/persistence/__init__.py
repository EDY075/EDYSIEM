"""Persistence do EDY SIEM.

- ``ConnectionManager``: conexoes SQLite (WAL, foreign keys)
- ``TransactionManager`` / ``UnitOfWork``: transacoes atomicas
- ``Repository`` / ``GenericRepository``: repositorios por agregado com
  CRUD completo + paginacao/ordenacao/filtros (sem SQL espalhado)
- ``Migration`` / ``MigrationRunner``: schema versionado
- ``EventRepository`` / ``EventStore``: Event Store da pipeline
- Repositorios: ``AlertRepository``, ``IncidentRepository``, ``CaseRepository``
"""

from .audit import AuditAction, AuditEngine, AuditEntry, AuditRepository
from .connection import ConnectionManager
from .event_store import EventRepository, EventStore, PipelineStage, StoredEvent
from .exceptions import (
    ConnectionError,
    MigrationError,
    PersistenceError,
    RecordNotFoundError,
    TransactionError,
)
from .inbox import (
    IdempotencyConflictError,
    InboxBatchResult,
    InboxEvent,
    InboxItemError,
    InboxItemResult,
    ShieldInboxRepository,
)
from .migrations import Migration, MigrationRunner
from .query import Page, QueryFilter, QueryOp, SortOrder
from .repository import GenericRepository, Repository
from .schema import ALL_MIGRATIONS
from .search import SearchEngine, SearchResults
from .transactions import Transaction, TransactionManager, UnitOfWork

__all__ = [
    "ALL_MIGRATIONS",
    "AuditAction",
    "AuditEngine",
    "AuditEntry",
    "AuditRepository",
    "ConnectionError",
    "ConnectionManager",
    "EventRepository",
    "EventStore",
    "GenericRepository",
    "IdempotencyConflictError",
    "InboxBatchResult",
    "InboxEvent",
    "InboxItemError",
    "InboxItemResult",
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
    "SearchEngine",
    "SearchResults",
    "ShieldInboxRepository",
    "SortOrder",
    "StoredEvent",
    "Transaction",
    "TransactionError",
    "TransactionManager",
    "UnitOfWork",
]
