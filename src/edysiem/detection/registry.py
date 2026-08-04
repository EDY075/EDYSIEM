"""Registry de regras de deteccao - Plugin Discovery.

O ``DetectionRegistry`` permite descobrir, registrar e ordenar
regras de deteccao por prioridade, resolvendo dependencias.
Mesmo padrao do ``EnrichmentRegistry``/``CorrelationRegistry``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .base import DetectionRule, RuleMetadata
from .exceptions import (
    DetectionRuleDependencyError,
    DetectionRuleRegistrationError,
)


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """Entrada de uma regra no registry."""

    rule: DetectionRule
    metadata: RuleMetadata
    enabled: bool = True


class DetectionRegistry:
    """Registry de regras de deteccao com ordenacao por prioridade."""

    def __init__(self) -> None:
        self._rules: dict[str, RegistryEntry] = {}
        self._sorted_cache: list[DetectionRule] | None = None
        self._cache_valid = False

    def register(self, rule: DetectionRule, *, enabled: bool | None = None) -> None:
        """Registra uma regra de deteccao.

        Raises:
            DetectionRuleRegistrationError: Se ID duplicado ou invalido.
        """
        metadata = rule.metadata
        rule_id = metadata.id

        if not rule_id or not rule_id.strip():
            raise DetectionRuleRegistrationError("Regra metadata.id nao pode ser vazio")
        if rule_id in self._rules:
            raise DetectionRuleRegistrationError(f"Regra com ID '{rule_id}' ja registrada")

        is_enabled = metadata.enabled if enabled is None else enabled
        self._rules[rule_id] = RegistryEntry(rule=rule, metadata=metadata, enabled=is_enabled)
        self._invalidate_cache()

    def unregister(self, rule_id: str) -> bool:
        """Remove uma regra do registry."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._invalidate_cache()
            return True
        return False

    def get(self, rule_id: str) -> DetectionRule | None:
        """Retorna a regra pelo ID."""
        entry = self._rules.get(rule_id)
        return entry.rule if entry else None

    def get_metadata(self, rule_id: str) -> RuleMetadata | None:
        """Retorna o metadata da regra pelo ID."""
        entry = self._rules.get(rule_id)
        return entry.metadata if entry else None

    def enable(self, rule_id: str) -> bool:
        """Ativa uma regra."""
        if rule_id in self._rules:
            self._rules[rule_id] = RegistryEntry(
                rule=self._rules[rule_id].rule,
                metadata=self._rules[rule_id].metadata,
                enabled=True,
            )
            self._invalidate_cache()
            return True
        return False

    def disable(self, rule_id: str) -> bool:
        """Desativa uma regra."""
        if rule_id in self._rules:
            self._rules[rule_id] = RegistryEntry(
                rule=self._rules[rule_id].rule,
                metadata=self._rules[rule_id].metadata,
                enabled=False,
            )
            self._invalidate_cache()
            return True
        return False

    def is_enabled(self, rule_id: str) -> bool:
        """Verifica se uma regra esta ativa."""
        entry = self._rules.get(rule_id)
        return entry.enabled if entry else False

    def get_all_rules(self) -> dict[str, DetectionRule]:
        """Retorna todas as regras (ativas e inativas)."""
        return {rid: entry.rule for rid, entry in self._rules.items()}

    def get_enabled_rules(self) -> dict[str, DetectionRule]:
        """Retorna apenas regras ativas."""
        return {rid: entry.rule for rid, entry in self._rules.items() if entry.enabled}

    def get_rule_ids(self) -> frozenset[str]:
        """Retorna IDs de todas as regras registradas."""
        return frozenset(self._rules.keys())

    def get_ordered_rules(self) -> list[DetectionRule]:
        """Retorna regras ordenadas por prioridade + dependencias."""
        if self._cache_valid and self._sorted_cache is not None:
            return self._sorted_cache

        enabled = self.get_enabled_rules()
        rule_ids = set(enabled.keys())

        self._validate_dependencies(enabled, rule_ids)
        ordered = self._topological_sort(enabled, rule_ids)

        self._sorted_cache = ordered
        self._cache_valid = True
        return ordered

    def _validate_dependencies(self, enabled: dict[str, DetectionRule], rule_ids: set[str]) -> None:
        """Valida dependencias declaradas e detecta ciclos."""
        for rule_id, rule in enabled.items():
            for dep in rule.metadata.dependencies:
                if dep not in rule_ids:
                    raise DetectionRuleDependencyError(
                        f"Regra '{rule_id}' declara dependencia '{dep}' "
                        f"que nao esta registrada ou ativa",
                        missing_dependency=dep,
                    )

        self._detect_cycles(enabled, rule_ids)

    def _detect_cycles(self, enabled: dict[str, DetectionRule], rule_ids: set[str]) -> None:
        """Detecta ciclos no grafo de dependencias via DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {rid: WHITE for rid in rule_ids}

        def dfs(node: str, path: list[str]) -> None:
            color[node] = GRAY
            for dep in enabled[node].metadata.dependencies:
                if dep not in rule_ids:
                    continue
                if color[dep] == GRAY:
                    cycle = " -> ".join([*path, dep, node])
                    raise DetectionRuleDependencyError(
                        f"Dependencia circular detectada: {cycle}",
                        missing_dependency="circular",
                    )
                if color[dep] == WHITE:
                    dfs(dep, [*path, node])
            color[node] = BLACK

        for rid in rule_ids:
            if color[rid] == WHITE:
                dfs(rid, [rid])

    def _topological_sort(
        self, enabled: dict[str, DetectionRule], rule_ids: set[str]
    ) -> list[DetectionRule]:
        """Ordenacao topologica de Kahn com prioridade como tiebreaker."""
        import heapq

        in_degree: dict[str, int] = {rid: 0 for rid in rule_ids}
        adj: dict[str, list[str]] = {rid: [] for rid in rule_ids}

        for rid, rule in enabled.items():
            for dep in rule.metadata.dependencies:
                if dep in rule_ids:
                    adj[dep].append(rid)
                    in_degree[rid] += 1

        registration_order = {rid: i for i, rid in enumerate(enabled.keys())}
        queue: list[tuple[int, int, str]] = [
            (
                enabled[rid].metadata.priority.value,
                registration_order[rid],
                rid,
            )
            for rid in rule_ids
            if in_degree[rid] == 0
        ]
        heapq.heapify(queue)

        result: list[DetectionRule] = []
        while queue:
            _, _, rid = heapq.heappop(queue)
            result.append(enabled[rid])
            for neighbor in adj[rid]:
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

        if len(result) != len(rule_ids):
            raise DetectionRuleDependencyError(
                "Nao foi possivel ordenar todas as regras (ciclo nao detectado?)",
                missing_dependency="unknown",
            )

        return result

    def _invalidate_cache(self) -> None:
        """Invalida cache de regras ordenadas."""
        self._sorted_cache = None
        self._cache_valid = False

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatisticas do registry."""
        enabled = sum(1 for e in self._rules.values() if e.enabled)
        by_priority: dict[str, int] = {}
        for entry in self._rules.values():
            p = entry.metadata.priority.name
            by_priority[p] = by_priority.get(p, 0) + 1

        return {
            "total_rules": len(self._rules),
            "enabled_rules": enabled,
            "by_priority": by_priority,
            "cache_valid": self._cache_valid,
        }

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def __iter__(self) -> Iterable[DetectionRule]:
        return iter(entry.rule for entry in self._rules.values())


__all__ = ["DetectionRegistry", "RegistryEntry"]
