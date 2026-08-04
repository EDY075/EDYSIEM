"""Base de migracoes e runner de schema version.

Cada ``Migration`` tem um ``version`` (inteiro monotonic) e metodos
``up``/``down``. O ``MigrationRunner`` aplica as migracoes pendentes em
ordem e registra em ``schema_migrations``.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .exceptions import MigrationError

if TYPE_CHECKING:
    from .connection import ConnectionManager


class Migration(ABC):
    """Uma migracao de schema (version + up/down)."""

    version: int = 0
    description: str = ""

    @abstractmethod
    def up(self, conn: sqlite3.Connection) -> None:
        """Aplica a migracao (schema upgrade)."""

    def down(self, conn: sqlite3.Connection) -> None:  # noqa: B027
        """Reverte a migracao (schema downgrade)."""


class MigrationRunner:
    """Aplica migracoes pendentes e mantem o schema version.

    Args:
        migrations: Lista de migracoes (version > 0), ordenada por versao.
    """

    _MIGRATIONS_TABLE = "schema_migrations"

    def __init__(self, migrations: list[Migration] | None = None) -> None:
        self._migrations = sorted(migrations or [], key=lambda m: m.version)

    @property
    def migrations(self) -> list[Migration]:
        """Migracoes registradas (ordenadas por versao)."""
        return list(self._migrations)

    def apply(self, manager: ConnectionManager) -> None:
        """Aplica todas as migracoes pendentes em uma transacao.

        Raises:
            MigrationError: Se uma migracao falhar (rollback).
        """
        conn = manager.connect()
        self._ensure_migrations_table(conn)

        for migration in self._migrations:
            applied = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (migration.version,),
            ).fetchone()
            if applied is not None:
                continue

            try:
                conn.execute("BEGIN")
                migration.up(conn)
                conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    (migration.version, migration.description),
                )
                conn.commit()
            except sqlite3.Error as exc:
                conn.rollback()
                raise MigrationError(f"falha na migracao {migration.version}: {exc}") from exc

    def current_version(self, manager: ConnectionManager) -> int:
        """Retorna a versao corrente do schema (0 se nenhuma aplicada)."""
        conn = manager.connect()
        self._ensure_migrations_table(conn)
        row = conn.execute("SELECT MAX(version) AS v FROM schema_migrations").fetchone()
        return int(row["v"] or 0) if row else 0

    def _ensure_migrations_table(self, conn: sqlite3.Connection) -> None:
        """Cria a tabela de controle de versao se necessario."""
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._MIGRATIONS_TABLE} (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL DEFAULT '',
                applied_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                )
            )
            """
        )
        conn.commit()


__all__ = ["Migration", "MigrationRunner"]
