"""Ciclos de vida das dependências no container DI."""

from __future__ import annotations

from enum import Enum


class Lifetime(Enum):
    """Estratégia de vida de uma dependência resolvida."""

    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


__all__ = ["Lifetime"]
