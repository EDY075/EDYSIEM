"""Registry de plugins de enriquecimento - Plugin Discovery.

O ``EnrichmentRegistry`` permite descobrir, registrar e ordenar
plugins de enriquecimento por prioridade, resolvendo dependências.

Características:
- Registro declarativo (sem if/else gigantes)
- Ordenação topológica por prioridade + dependências
- Descoberta automática de plugins
- Validação de dependências circulares
- Filtragem por categoria de evento
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .base import EnrichmentPlugin, PluginMetadata
from .exceptions import PluginDependencyError, PluginRegistrationError


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """Entrada de um plugin no registry."""

    plugin: EnrichmentPlugin
    metadata: PluginMetadata
    enabled: bool = True


class EnrichmentRegistry:
    """Registry de plugins de enriquecimento com ordenação por prioridade.

    Suporta:
    - Registro declarativo via ``register()``
    - Ordenação por prioridade + dependências (topológica)
    - Filtragem por categoria de evento
    - Validação de dependências (circulares, ausentes)
    - Ativação/desativação de plugins

    Exemplo:
        registry = EnrichmentRegistry()
        registry.register(asset_enricher)
        registry.register(geo_enricher)

        # Plugins ordenados para execução
        for plugin in registry.get_ordered_plugins("auth"):
            ...
    """

    def __init__(self) -> None:
        self._plugins: dict[str, RegistryEntry] = {}
        self._sorted_cache: list[EnrichmentPlugin] | None = None
        self._cache_key: str | None = None
        self._cache_valid = False

    def register(self, plugin: EnrichmentPlugin, *, enabled: bool = True) -> None:
        """Registra um plugin de enriquecimento.

        Args:
            plugin: Instância do plugin implementando ``EnrichmentPlugin``.
            enabled: Se o plugin deve ser ativado por padrão.

        Raises:
            PluginRegistrationError: Se ID duplicado ou metadata inválido.
        """
        metadata = plugin.metadata
        plugin_id = metadata.id

        if not plugin_id or not plugin_id.strip():
            raise PluginRegistrationError("Plugin metadata.id não pode ser vazio")

        if plugin_id in self._plugins:
            raise PluginRegistrationError(f"Plugin com ID '{plugin_id}' já registrado")

        self._plugins[plugin_id] = RegistryEntry(plugin=plugin, metadata=metadata, enabled=enabled)
        self._invalidate_cache()

    def unregister(self, plugin_id: str) -> bool:
        """Remove um plugin do registry.

        Returns:
            ``True`` se removido, ``False`` se não existia.
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            self._invalidate_cache()
            return True
        return False

    def get(self, plugin_id: str) -> EnrichmentPlugin | None:
        """Retorna o plugin pelo ID, ou ``None`` se não encontrado."""
        entry = self._plugins.get(plugin_id)
        return entry.plugin if entry else None

    def get_metadata(self, plugin_id: str) -> PluginMetadata | None:
        """Retorna o metadata do plugin pelo ID."""
        entry = self._plugins.get(plugin_id)
        return entry.metadata if entry else None

    def enable(self, plugin_id: str) -> bool:
        """Ativa um plugin."""
        if plugin_id in self._plugins:
            self._plugins[plugin_id] = RegistryEntry(
                plugin=self._plugins[plugin_id].plugin,
                metadata=self._plugins[plugin_id].metadata,
                enabled=True,
            )
            self._invalidate_cache()
            return True
        return False

    def disable(self, plugin_id: str) -> bool:
        """Desativa um plugin."""
        if plugin_id in self._plugins:
            self._plugins[plugin_id] = RegistryEntry(
                plugin=self._plugins[plugin_id].plugin,
                metadata=self._plugins[plugin_id].metadata,
                enabled=False,
            )
            self._invalidate_cache()
            return True
        return False

    def is_enabled(self, plugin_id: str) -> bool:
        """Verifica se um plugin está ativo."""
        entry = self._plugins.get(plugin_id)
        return entry.enabled if entry else False

    def get_all_plugins(self) -> dict[str, EnrichmentPlugin]:
        """Retorna todos os plugins registrados (ativos e inativos)."""
        return {pid: entry.plugin for pid, entry in self._plugins.items()}

    def get_enabled_plugins(self) -> dict[str, EnrichmentPlugin]:
        """Retorna apenas plugins ativos."""
        return {pid: entry.plugin for pid, entry in self._plugins.items() if entry.enabled}

    def get_plugin_ids(self) -> frozenset[str]:
        """Retorna IDs de todos os plugins registrados."""
        return frozenset(self._plugins.keys())

    def get_ordered_plugins(self, event_category: str | None = None) -> list[EnrichmentPlugin]:
        """Retorna plugins ordenados por prioridade + dependências.

        Aplica ordenação topológica respeitando dependências declaradas.
        Plugins com mesma prioridade mantêm ordem de registro (estável).

        Args:
            event_category: Se fornecido, filtra plugins que suportam
                essa categoria (ou plugins sem filtro = todos).

        Returns:
            Lista de plugins prontos para execução em ordem.

        Raises:
            PluginDependencyError: Se dependência circular ou ausente.
        """
        # Cache is per category (None = no filter)
        cache_key = event_category
        if self._cache_valid and self._sorted_cache is not None and self._cache_key == cache_key:
            return self._sorted_cache

        # Construir grafo de dependências apenas com plugins ativos
        enabled = self.get_enabled_plugins()
        plugin_ids = set(enabled.keys())

        # Validar dependências
        self._validate_dependencies(enabled, plugin_ids)

        # Ordenação topológica (Kahn's algorithm)
        ordered = self._topological_sort(enabled, plugin_ids)

        # Filtrar por categoria
        if event_category is not None:
            ordered = [p for p in ordered if self._supports_category(p, event_category)]

        self._sorted_cache = ordered
        self._cache_key = cache_key
        self._cache_valid = True
        return ordered

    def _supports_category(self, plugin: EnrichmentPlugin, category: str) -> bool:
        """Verifica se plugin suporta a categoria do evento."""
        meta = plugin.metadata
        if not meta.supported_event_categories:
            return True  # Sem filtro = suporta todas
        return category in meta.supported_event_categories

    def _validate_dependencies(
        self, enabled: dict[str, EnrichmentPlugin], plugin_ids: set[str]
    ) -> None:
        """Valida dependências declaradas."""
        for plugin_id, plugin in enabled.items():
            meta = plugin.metadata
            for dep in meta.dependencies:
                if dep not in plugin_ids:
                    raise PluginDependencyError(
                        f"Plugin '{plugin_id}' declara dependência "
                        f"'{dep}' que não está registrada ou ativa",
                        missing_dependency=dep,
                    )

        # Detectar ciclos via DFS
        self._detect_cycles(enabled, plugin_ids)

    def _detect_cycles(self, enabled: dict[str, EnrichmentPlugin], plugin_ids: set[str]) -> None:
        """Detecta ciclos no grafo de dependências."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {pid: WHITE for pid in plugin_ids}

        def dfs(node: str, path: list[str]) -> None:
            color[node] = GRAY
            meta = enabled[node].metadata
            for dep in meta.dependencies:
                if dep not in plugin_ids:
                    continue
                if color[dep] == GRAY:
                    cycle = " -> ".join([*path, dep, node])
                    raise PluginDependencyError(
                        f"Dependência circular detectada: {cycle}", missing_dependency="circular"
                    )
                if color[dep] == WHITE:
                    dfs(dep, [*path, node])
            color[node] = BLACK

        for pid in plugin_ids:
            if color[pid] == WHITE:
                dfs(pid, [pid])

    def _topological_sort(
        self, enabled: dict[str, EnrichmentPlugin], plugin_ids: set[str]
    ) -> list[EnrichmentPlugin]:
        """Ordenação topológica de Kahn com prioridade como tiebreaker."""
        # Calcular in-degree
        in_degree: dict[str, int] = {pid: 0 for pid in plugin_ids}
        adj: dict[str, list[str]] = {pid: [] for pid in plugin_ids}

        for pid, plugin in enabled.items():
            meta = plugin.metadata
            for dep in meta.dependencies:
                if dep in plugin_ids:
                    adj[dep].append(pid)
                    in_degree[pid] += 1

        # Fila de prioridade: (prioridade, ordem_registro, plugin_id)
        # Menor prioridade = executa primeiro
        import heapq

        registration_order = {pid: i for i, pid in enumerate(enabled.keys())}
        queue: list[tuple[int, int, str]] = [
            (enabled[pid].metadata.priority.value, registration_order[pid], pid)
            for pid in plugin_ids
            if in_degree[pid] == 0
        ]
        heapq.heapify(queue)

        result: list[EnrichmentPlugin] = []
        while queue:
            _, _, pid = heapq.heappop(queue)
            result.append(enabled[pid])

            for neighbor in adj[pid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    heapq.heappush(
                        queue,
                        (
                            enabled[neighbor].metadata.priority.value,
                            registration_order[neighbor],
                            neighbor,
                        ),
                    )

        if len(result) != len(plugin_ids):
            raise PluginDependencyError(
                "Não foi possível ordenar todos os plugins (ciclo não detectado?)",
                missing_dependency="unknown",
            )

        return result

    def _invalidate_cache(self) -> None:
        """Invalida cache de plugins ordenados."""
        self._sorted_cache = None
        self._cache_key = None
        self._cache_valid = False

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, plugin_id: str) -> bool:
        return plugin_id in self._plugins

    def __iter__(self) -> Iterable[EnrichmentPlugin]:
        return iter(entry.plugin for entry in self._plugins.values())

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas do registry."""
        enabled = sum(1 for e in self._plugins.values() if e.enabled)
        by_priority: dict[str, int] = {}
        for entry in self._plugins.values():
            p = entry.metadata.priority.name
            by_priority[p] = by_priority.get(p, 0) + 1

        return {
            "total_plugins": len(self._plugins),
            "enabled_plugins": enabled,
            "by_priority": by_priority,
            "cache_valid": self._cache_valid,
        }


__all__ = ["EnrichmentRegistry", "RegistryEntry"]
