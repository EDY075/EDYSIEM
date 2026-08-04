"""Registry de hooks do Case Engine."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .base import CaseProcessor
from .exceptions import CaseRegistrationError
from .models import Case, CaseStatus


class CaseRegistry:
    """Registry de ``CaseProcessor`` (hooks de ciclo de vida)."""

    def __init__(self) -> None:
        self._processors: dict[str, CaseProcessor] = {}

    def register(self, processor: CaseProcessor, *, name: str | None = None) -> None:
        """Registra um processor.

        Raises:
            CaseRegistrationError: Se ja registrado.
        """
        key = name or type(processor).__name__
        if key in self._processors:
            raise CaseRegistrationError(f"Processor '{key}' ja registrado")
        self._processors[key] = processor

    def unregister(self, name: str) -> bool:
        """Remove um processor."""
        if name in self._processors:
            del self._processors[name]
            return True
        return False

    def get(self, name: str) -> CaseProcessor | None:
        """Retorna um processor pelo nome."""
        return self._processors.get(name)

    def on_created(self, case: Case) -> None:
        """Notifica todos os processors de criacao."""
        for processor in self._processors.values():
            try:
                processor.on_created(case)
            except Exception:
                continue

    def on_updated(self, case: Case) -> None:
        """Notifica todos os processors de atualizacao."""
        for processor in self._processors.values():
            try:
                processor.on_updated(case)
            except Exception:
                continue

    def on_status_changed(self, case: Case, previous: CaseStatus, current: CaseStatus) -> None:
        """Notifica todos os processors de mudanca de estado."""
        for processor in self._processors.values():
            try:
                processor.on_status_changed(case, previous, current)
            except Exception:
                continue

    def processor_names(self) -> frozenset[str]:
        """Retorna nomes dos processors registrados."""
        return frozenset(self._processors.keys())

    def get_stats(self) -> dict[str, Any]:
        """Estatisticas do registry."""
        return {
            "total_processors": len(self._processors),
            "names": self.processor_names(),
        }

    def __len__(self) -> int:
        return len(self._processors)

    def __iter__(self) -> Iterable[CaseProcessor]:
        return iter(self._processors.values())


__all__ = ["CaseRegistry"]
