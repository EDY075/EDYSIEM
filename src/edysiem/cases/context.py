"""Contexto do Case Engine.

Mantem o estado in-memory dos cases. Thread-safe. Persistencia externa
em sprint futura.
"""

from __future__ import annotations

import threading
from typing import Any

from .models import Case


class CaseContext:
    """Armazenamento in-memory de cases.

    Design:
    - ``_cases``: mapa ``case_id -> Case``.
    - Thread-safe (RLock).
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cases: dict[str, Case] = {}

    def save(self, case: Case) -> None:
        """Armazena/atualiza um case."""
        with self._lock:
            self._cases[case.id] = case

    def get(self, case_id: str) -> Case | None:
        """Retorna um case pelo ID."""
        with self._lock:
            return self._cases.get(case_id)

    def all(self) -> tuple[Case, ...]:
        """Retorna todos os cases."""
        with self._lock:
            return tuple(self._cases.values())

    def by_incident(self, incident_id: str) -> tuple[Case, ...]:
        """Retorna cases vinculados a um incidente."""
        with self._lock:
            return tuple(c for c in self._cases.values() if c.incident_id == incident_id)

    def __len__(self) -> int:
        with self._lock:
            return len(self._cases)

    def clear(self) -> None:
        """Limpa o estado."""
        with self._lock:
            self._cases.clear()

    def discard(self, case_id: str) -> None:
        """Remove somente um case transiente que nao chegou a ser persistido."""
        with self._lock:
            self._cases.pop(case_id, None)

    def snapshot(self) -> dict[str, Any]:
        """Snapshot do estado."""
        with self._lock:
            return {"cases": len(self._cases)}


__all__ = ["CaseContext"]
