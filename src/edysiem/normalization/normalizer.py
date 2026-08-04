"""Normalizador de eventos - Strategy pattern.

O ``Normalizer`` converte ``ParsedEvent`` em ``CanonicalEvent``
aplicando uma estrategia especifica por tipo de fonte.

A estrategia padrao mapeia campos genericos do ``ParsedEvent``
para os campos canonicos, classificando severidade com base
no processo e na mensagem.

O design segue o padrao Strategy: cada ``source_type`` pode ter
sua propria estrategia de normalizacao, registrada no
``StrategyNormalizer``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, cast

from ..domain import CanonicalEvent, ParsedEvent, Severity
from ..result import Error, ErrorCode, Failure, Result, ok


class Normalizer(Protocol):
    """Contrato do normalizador de eventos.

    Cada implementacao converte um ``ParsedEvent`` em um
    ``CanonicalEvent`` aplicando regras especificas do tipo
    de fonte.
    """

    def normalize(self, parsed: ParsedEvent) -> Result[CanonicalEvent]:
        """Normaliza um ``ParsedEvent`` em ``CanonicalEvent``.

        Args:
            parsed: Evento parseado com campos estruturados.

        Returns:
            ``Success(CanonicalEvent)`` com o evento canonicamente
            normalizado; ``Failure`` se a normalizacao falhar.
        """


def _classify_severity(event_category: str, event_action: str, confidence: float) -> Severity:
    """Classifica a severidade com base na categoria e acao."""
    if event_category == "auth" and event_action in ("reject", "error"):
        return Severity.HIGH
    if event_category == "auth" and event_action == "accept":
        return Severity.LOW
    if event_category == "network" and event_action == "reject":
        return Severity.HIGH
    if event_category == "threat":
        return Severity.CRITICAL
    if confidence < 0.5:
        return Severity.LOW
    return Severity.INFO


class StrategyNormalizer:
    """Normalizador com registro de estrategias por source_type.

    Usa o padrao Strategy: cada tipo de fonte pode ter sua
    propria logica de normalizacao. A estrategia padrao aplica
    mapeamento generico de campos.

    Attributes:
        _strategies: Mapa source_type -> funcao de normalizacao.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, Callable[[ParsedEvent], Result[object]]] = {}

    def register(
        self,
        source_type: str,
        strategy: Callable[[ParsedEvent], Result[object]],
    ) -> None:
        """Registra uma estrategia para um source_type."""
        self._strategies[source_type] = strategy

    def normalize(self, parsed: ParsedEvent) -> Result[CanonicalEvent]:
        """Normaliza um ``ParsedEvent`` em ``CanonicalEvent``.

        Se existir uma estrategia registrada para o ``source_type``
        do evento, ela e utilizada. Caso contrario, aplica a
        estrategia padrao.

        Returns:
            ``Success(CanonicalEvent)`` em caso de sucesso;
            ``Failure`` com ``ErrorCode.PLUGIN_ERROR`` se a
            normalizacao falhar.
        """
        strategy = self._strategies.get(parsed.source_type)
        if strategy is not None:
            return cast(Result[CanonicalEvent], strategy(parsed))
        return self._default_normalize(parsed)

    def _default_normalize(self, parsed: ParsedEvent) -> Result[CanonicalEvent]:
        """Estrategia padrao de normalizacao."""
        try:
            severity = _classify_severity(
                parsed.event_category,
                parsed.event_action,
                parsed.confidence,
            )
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
        except Exception as exc:
            return Failure[CanonicalEvent](
                Error(
                    ErrorCode.PLUGIN_ERROR,
                    f"normalizacao falhou para {parsed.source_type}: {exc}",
                )
            )


__all__ = ["Normalizer", "StrategyNormalizer", "_classify_severity"]
