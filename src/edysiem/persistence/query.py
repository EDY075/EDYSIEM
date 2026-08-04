"""Tipos de consulta da camada de persistencia.

- ``QueryFilter``: filtro declarativo (sem SQL espalhado).
- ``Page``: resultado paginado.
- ``SortOrder``: ordenacao.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class QueryOp(Enum):
    """Operadores de filtro."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"


class SortOrder(Enum):
    """Direcao de ordenacao."""

    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class QueryFilter:
    """Filtro declarativo sobre um campo.

    Attributes:
        field: Nome do campo (coluna).
        op: Operador de comparacao.
        value: Valor de referencia.
    """

    field: str
    op: QueryOp = QueryOp.EQ
    value: Any = None

    def to_sql(self, index: int) -> tuple[str, list[Any]]:
        """Converte o filtro em clausula SQL parametrizada.

        Returns:
            (clausula WHERE, params).
        """
        ops: dict[QueryOp, str] = {
            QueryOp.EQ: "=",
            QueryOp.NEQ: "!=",
            QueryOp.GT: ">",
            QueryOp.GTE: ">=",
            QueryOp.LT: "<",
            QueryOp.LTE: "<=",
        }
        if self.op is QueryOp.CONTAINS:
            return f"{self.field} LIKE ?", [f"%{self.value}%"]
        return f"{self.field} {ops[self.op]} ?", [self.value]


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    """Resultado paginado de uma consulta.

    Attributes:
        items: Itens da pagina.
        total: Total de registros que casam (sem paginacao).
        offset: Deslocamento da pagina.
        limit: Tamanho da pagina.
    """

    items: list[T]
    total: int
    offset: int = 0
    limit: int = 50

    @property
    def has_more(self) -> bool:
        """Indica se existem mais paginas alem da atual."""
        return self.offset + len(self.items) < self.total


__all__ = ["Page", "QueryFilter", "QueryOp", "SortOrder"]
