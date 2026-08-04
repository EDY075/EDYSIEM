"""Registry de hooks do Alert Framework.

Permite registrar ``AlertProcessor`` que reagem a eventos do ciclo de
vida (criacao, atualizacao, mudanca de estado). Mesmo padrao dos
registries anteriores.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .base import AlertProcessor
from .exceptions import AlertRegistrationError
from .models import Alert, AlertLifecycle


class AlertRegistry:
    """Registry de ``AlertProcessor`` (hooks de ciclo de vida).

    Exemplo:
        registry = AlertRegistry()
        registry.register(PersistenceProcessor())
        registry.register(NotificationProcessor())
    """

    def __init__(self) -> None:
        self._processors: dict[str, AlertProcessor] = {}

    def register(self, processor: AlertProcessor, *, name: str | None = None) -> None:
        """Registra um processor.

        Args:
            processor: Implementacao de ``AlertProcessor``.
            name: Nome do hook (default: nome da classe).

        Raises:
            AlertRegistrationError: Se ja registrado.
        """
        key = name or type(processor).__name__
        if key in self._processors:
            raise AlertRegistrationError(f"Processor '{key}' ja registrado")
        self._processors[key] = processor

    def unregister(self, name: str) -> bool:
        """Remove um processor."""
        if name in self._processors:
            del self._processors[name]
            return True
        return False

    def get(self, name: str) -> AlertProcessor | None:
        """Retorna um processor pelo nome."""
        return self._processors.get(name)

    def on_created(self, alert: Alert) -> None:
        """Notifica todos os processors de criacao."""
        for processor in self._processors.values():
            try:
                processor.on_created(alert)
            except Exception:
                # Hook falho nao derruba o pipeline
                continue

    def on_updated(self, alert: Alert) -> None:
        """Notifica todos os processors de atualizacao."""
        for processor in self._processors.values():
            try:
                processor.on_updated(alert)
            except Exception:
                continue

    def on_status_changed(
        self, alert: Alert, previous: AlertLifecycle, current: AlertLifecycle
    ) -> None:
        """Notifica todos os processors de mudanca de estado."""
        for processor in self._processors.values():
            try:
                processor.on_status_changed(alert, previous.value, current.value)
            except Exception:
                continue

    def processor_names(self) -> frozenset[str]:
        """Retorna nomes dos processors registrados."""
        return frozenset(self._processors.keys())

    def get_stats(self) -> dict[str, Any]:
        """Estatisticas do registry."""
        return {"total_processors": len(self._processors), "names": self.processor_names()}

    def __len__(self) -> int:
        return len(self._processors)

    def __iter__(self) -> Iterable[AlertProcessor]:
        return iter(self._processors.values())


__all__ = ["AlertRegistry"]
