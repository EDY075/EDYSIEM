"""Registry de normalizadores - Plugin Discovery.

O ``Registry`` permite descobrir e registrar normalizadores
por ``source_type`` de forma declarativa, sem if/else gigantes.

Uso:
    from edysiem.normalization import Registry, register_default_normalizers
    registry = Registry()
    register_default_normalizers(registry)
    normalizer = StrategyNormalizer()
    for source_type, strategy in registry.strategies():
        normalizer.register(source_type, strategy)
"""

from __future__ import annotations

from collections.abc import Callable

from ..domain import ParsedEvent
from ..result import Result, ok
from .normalizer import _classify_severity


class Registry:
    """Registry de normalizadores por source_type.

    Permite registro declarativo de estrategias de normalizacao.
    Suporta descoberta automatica via registro de plugins.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, Callable[[ParsedEvent], Result[object]]] = {}

    def register(self, source_type: str, strategy: Callable[[ParsedEvent], Result[object]]) -> None:
        """Registra uma estrategia para um source_type."""
        self._strategies[source_type] = strategy

    def unregister(self, source_type: str) -> None:
        """Remove uma estrategia registrada."""
        self._strategies.pop(source_type, None)

    def get(self, source_type: str) -> Callable[[ParsedEvent], Result[object]] | None:
        """Retorna a estrategia registrada para o source_type."""
        return self._strategies.get(source_type)

    def strategies(self) -> dict[str, Callable[[ParsedEvent], Result[object]]]:
        """Retorna um dicionario com todas as estrategias registradas."""
        return dict(self._strategies)

    def source_types(self) -> frozenset[str]:
        """Retorna o conjunto de source_types registrados."""
        return frozenset(self._strategies.keys())


def _syslog_strategy(parsed: ParsedEvent) -> Result[object]:
    """Estrategia de normalizacao para syslog."""
    from ..domain import CanonicalEvent

    severity = _classify_severity(parsed.event_category, parsed.event_action, parsed.confidence)
    canonical = CanonicalEvent(
        event_id=parsed.event_id,
        trace_id=parsed.trace_id,
        timestamp=parsed.timestamp,
        received_at=parsed.timestamp,
        source_type=parsed.source_type,
        source_host=parsed.source_host,
        hostname=parsed.source_host,
        event_category=parsed.event_category,
        event_action=parsed.event_action,
        severity=severity,
        user=parsed.fields.get("user"),
        process=parsed.fields.get("process"),
        command_line=parsed.fields.get("command_line"),
        ip_src=parsed.fields.get("src_ip") or parsed.fields.get("source_ip"),
        ip_dst=parsed.fields.get("dst_ip") or parsed.fields.get("destination_ip"),
        vendor=parsed.vendor,
        product=parsed.product,
        event_original=str(parsed.raw),
        normalized_fields=frozenset(parsed.fields.keys()),
        confidence=parsed.confidence,
        metadata=parsed.fields,
    )
    return ok(canonical)


def _windows_strategy(parsed: ParsedEvent) -> Result[object]:
    """Estrategia de normalizacao para Windows Event Log."""
    from ..domain import CanonicalEvent

    severity = _classify_severity(parsed.event_category, parsed.event_action, parsed.confidence)
    canonical = CanonicalEvent(
        event_id=parsed.event_id,
        trace_id=parsed.trace_id,
        timestamp=parsed.timestamp,
        received_at=parsed.timestamp,
        source_type=parsed.source_type,
        source_host=parsed.source_host,
        hostname=parsed.source_host,
        event_category=parsed.event_category,
        event_action=parsed.event_action,
        severity=severity,
        user=parsed.fields.get("user") or parsed.fields.get("target_user_name"),
        process=parsed.fields.get("process_name"),
        command_line=parsed.fields.get("command_line"),
        ip_src=parsed.fields.get("source_ip"),
        ip_dst=parsed.fields.get("destination_ip"),
        vendor=parsed.vendor,
        product=parsed.product,
        event_original=str(parsed.raw),
        normalized_fields=frozenset(parsed.fields.keys()),
        confidence=parsed.confidence,
        metadata=parsed.fields,
    )
    return ok(canonical)


def register_default_normalizers(registry: Registry) -> None:
    """Registra as estrategias de normalizacao padrao.

    Registra normalizadores para syslog e windows.
    Novas fontes podem ser registradas via ``registry.register()``.
    """
    registry.register("syslog", _syslog_strategy)
    registry.register("windows", _windows_strategy)


__all__ = ["Registry", "_syslog_strategy", "_windows_strategy", "register_default_normalizers"]
