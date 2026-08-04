"""Registry de hooks do Incident Engine.

Permite registrar ``IncidentProcessor`` que reagem a eventos do ciclo de
vida (criacao, atualizacao, mudanca de estado, reabertura).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .base import IncidentProcessor
from .exceptions import IncidentRegistrationError
from .models import Incident, IncidentStatus


class IncidentRegistry:
    """Registry de ``IncidentProcessor`` (hooks de ciclo de vida)."""

    def __init__(self) -> None:
        self._processors: dict[str, IncidentProcessor] = {}

    def register(self, processor: IncidentProcessor, *, name: str | None = None) -> None:
        """Registra um processor.

        Raises:
            IncidentRegistrationError: Se ja registrado.
        """
        key = name or type(processor).__name__
        if key in self._processors:
            raise IncidentRegistrationError(f"Processor '{key}' ja registrado")
        self._processors[key] = processor

    def unregister(self, name: str) -> bool:
        """Remove um processor."""
        if name in self._processors:
            del self._processors[name]
            return True
        return False

    def get(self, name: str) -> IncidentProcessor | None:
        """Retorna um processor pelo nome."""
        return self._processors.get(name)

    def on_created(self, incident: Incident) -> None:
        """Notifica todos os processors de criacao."""
        for processor in self._processors.values():
            try:
                processor.on_created(incident)
            except Exception:
                continue

    def on_updated(self, incident: Incident) -> None:
        """Notifica todos os processors de atualizacao."""
        for processor in self._processors.values():
            try:
                processor.on_updated(incident)
            except Exception:
                continue

    def on_status_changed(
        self, incident: Incident, previous: IncidentStatus, current: IncidentStatus
    ) -> None:
        """Notifica todos os processors de mudanca de estado."""
        for processor in self._processors.values():
            try:
                processor.on_status_changed(incident, previous, current)
            except Exception:
                continue

    def on_reopened(self, incident: Incident) -> None:
        """Notifica todos os processors de reabertura."""
        for processor in self._processors.values():
            try:
                processor.on_reopened(incident)
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

    def __iter__(self) -> Iterable[IncidentProcessor]:
        return iter(self._processors.values())


__all__ = ["IncidentRegistry"]
