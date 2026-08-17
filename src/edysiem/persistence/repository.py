"""Repository Protocol e implementacoes base.

Define o contrato de repositorio por agregado (Protocol) e o
``GenericRepository`` com CRUD completo + paginacao, ordenacao e
filtros. O SQL fica isolado nas implementacoes.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from .connection import ConnectionManager
from .exceptions import RecordNotFoundError
from .query import Page, QueryFilter, SortOrder, validate_sql_identifier

T = TypeVar("T")


@runtime_checkable
class Repository(Protocol[T]):
    """Contrato de um repositorio por agregado."""

    def add(self, entity: T) -> T: ...

    def get(self, entity_id: str) -> T | None: ...

    def update(self, entity: T) -> T: ...

    def delete(self, entity_id: str) -> bool: ...

    def all(self) -> list[T]: ...


class GenericRepository(Generic[T]):
    """Base com CRUD completo + paginacao/ordenacao/filtros.

    Subclasses definem ``TABLE``, ``_to_row`` e ``_from_row``.
    O ``query()`` usa ``QueryFilter`` declarativos (sem SQL espalhado).
    """

    TABLE: str = ""

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    # --- CRUD -------------------------------------------------------------

    def add(self, entity: T) -> T:
        cols = ", ".join(self._row_fields())
        placeholders = ", ".join("?" for _ in self._row_fields())
        conn = self._manager.connect()
        conn.execute(
            f"INSERT INTO {self.TABLE} ({cols}) VALUES ({placeholders})",
            self._to_row(entity),
        )
        return entity

    def get(self, entity_id: str) -> T | None:
        conn = self._manager.connect()
        row = conn.execute(f"SELECT * FROM {self.TABLE} WHERE id = ?", (entity_id,)).fetchone()
        return self._from_row(row) if row else None

    def update(self, entity: T) -> T:
        sets = ", ".join(f"{f} = ?" for f in self._row_fields())
        conn = self._manager.connect()
        rows = conn.execute(
            f"UPDATE {self.TABLE} SET {sets} WHERE id = ?",
            (*self._to_row(entity), self._entity_id(entity)),
        ).rowcount
        if rows == 0:
            raise RecordNotFoundError(self.TABLE, self._entity_id(entity))
        return entity

    def delete(self, entity_id: str) -> bool:
        conn = self._manager.connect()
        rows = conn.execute(f"DELETE FROM {self.TABLE} WHERE id = ?", (entity_id,)).rowcount
        return rows > 0

    def all(self) -> list[T]:
        conn = self._manager.connect()
        rows = conn.execute(f"SELECT * FROM {self.TABLE}").fetchall()
        return [self._from_row(r) for r in rows]

    # --- Consulta ----------------------------------------------------------

    def query(
        self,
        filters: list[QueryFilter] | None = None,
        *,
        sort_by: str = "created_at",
        order: SortOrder = SortOrder.DESC,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[T]:
        """Executa uma consulta com filtros, ordenacao e paginacao.

        Args:
            filters: Filtros declarativos (AND).
            sort_by: Campo de ordenacao (coluna).
            order: Direcao da ordenacao.
            limit: Tamanho da pagina.
            offset: Deslocamento.

        Returns:
            ``Page[T]`` com os itens e o total.
        """
        conn = self._manager.connect()
        allowed_fields = self._query_fields()
        sort_by = validate_sql_identifier(sort_by, allowed_fields)
        where, params = self._build_where(filters or [])
        direction = "ASC" if order is SortOrder.ASC else "DESC"
        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        total = conn.execute(f"SELECT COUNT(*) AS c FROM {self.TABLE} {where}", params).fetchone()[
            "c"
        ]

        rows = conn.execute(
            f"SELECT * FROM {self.TABLE} {where} ORDER BY {sort_by} {direction} LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()

        return Page(
            items=[self._from_row(r) for r in rows],
            total=int(total),
            offset=offset,
            limit=limit,
        )

    def count(self, filters: list[QueryFilter] | None = None) -> int:
        """Conta registros que casam com os filtros."""
        conn = self._manager.connect()
        where, params = self._build_where(filters or [])
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {self.TABLE} {where}", params).fetchone()
        return int(row["c"])

    def search(
        self,
        *,
        field: str,
        value: Any,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[T]:
        """Busca por igualdade em um campo (conveniencia)."""
        return self.query(
            [QueryFilter(field=field, value=value)],
            limit=limit,
            offset=offset,
        )

    # --- Helpers ------------------------------------------------------------

    def _build_where(self, filters: list[QueryFilter]) -> tuple[str, list[Any]]:
        """Converte filtros em clausula WHERE parametrizada."""
        if not filters:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        for i, f in enumerate(filters):
            validate_sql_identifier(f.field, self._query_fields())
            sql, p = f.to_sql(i)
            clauses.append(sql)
            params.extend(p)
        return "WHERE " + " AND ".join(clauses), params

    def _row_fields(self) -> list[str]:
        """Retorna as colunas na ordem de ``_to_row``."""
        raise NotImplementedError

    def _query_fields(self) -> frozenset[str]:
        """Return the only columns accepted in dynamic filters and ordering."""

        return frozenset({"id", *self._row_fields()})

    def _to_row(self, entity: T) -> tuple[Any, ...]:
        """Converte entidade em tupla de valores (ordem de ``_row_fields``)."""
        raise NotImplementedError

    def _from_row(self, row: sqlite3.Row) -> T:
        """Converte linha SQL em entidade."""
        raise NotImplementedError

    def _entity_id(self, entity: T) -> str:
        """Retorna o ID da entidade."""
        raise NotImplementedError


__all__ = ["GenericRepository", "Repository"]
