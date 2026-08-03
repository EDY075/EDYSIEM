"""Utilitários privados compartilhados entre módulos do núcleo.

Este módulo é **interno** (não exportado na API pública) e centraliza
funções simples e repetidas — carimbo de tempo UTC e geração de UUID —
para evitar duplicação entre ``domain`` e ``events`` (ADR: utilitários
únicos em ``_utils``, 100% stdlib).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


def utcnow() -> datetime:
    """Retorna o instante atual como ``datetime`` UTC (timezone-aware).

    Convenção de carimbo de tempo da plataforma: sempre UTC, nunca naive.
    """
    return datetime.now(UTC)


def new_id() -> str:
    """Gera um identificador único (UUID v4) em formato string."""
    return str(uuid4())


__all__ = ["new_id", "utcnow"]
