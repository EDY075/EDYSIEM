"""Exceções do Enrichment Engine.

Hierarquia de exceções específicas para o framework de enriquecimento.
"""

from __future__ import annotations

from ..exceptions import EdysiemException


class EnrichmentError(EdysiemException):
    """Erro base do Enrichment Engine."""


class EnrichmentTimeoutError(EnrichmentError):
    """Tempo de execução do plugin excedido."""

    def __init__(self, plugin_name: str, timeout_seconds: float) -> None:
        self.plugin_name = plugin_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Plugin '{plugin_name}' excedeu timeout de {timeout_seconds}s")


class PluginNotFoundError(EnrichmentError):
    """Plugin de enriquecimento não encontrado no registry."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        super().__init__(f"Plugin de enriquecimento '{plugin_id}' não encontrado")


class PluginRegistrationError(EnrichmentError):
    """Erro ao registrar plugin (duplicado, inválido, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PluginDependencyError(EnrichmentError):
    """Dependência de plugin não satisfeita."""

    def __init__(self, plugin_id: str, missing_dependency: str) -> None:
        self.plugin_id = plugin_id
        self.missing_dependency = missing_dependency
        super().__init__(
            f"Plugin '{plugin_id}' requer dependência '{missing_dependency}' não satisfeita"
        )


class EnrichmentContextError(EnrichmentError):
    """Erro no contexto de enriquecimento (asset DB, geo, etc.)."""

    def __init__(self, message: str, context_key: str | None = None) -> None:
        self.context_key = context_key
        msg = message
        if context_key:
            msg = f"Contexto '{context_key}': {message}"
        super().__init__(msg)


__all__ = [
    "EnrichmentContextError",
    "EnrichmentError",
    "EnrichmentTimeoutError",
    "PluginDependencyError",
    "PluginNotFoundError",
    "PluginRegistrationError",
]
