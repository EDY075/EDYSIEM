"""Regra DEMO: mesmo IP gerou mais de N eventos em X minutos.

Regra de exemplo para validar a arquitetura do Correlation Engine.
Nao e uma regra de producao - apenas demonstra como uma regra de janela
usa o ``CorrelationContext`` para acumular estado.

Condicao:
    count(eventos com mesmo ``ip_src`` na janela de ``window_seconds``)
    >= threshold
"""

from __future__ import annotations

import time

from ...domain import EnrichedEvent, Severity
from ..base import (
    CorrelationMatch,
    CorrelationMetadata,
    CorrelationPriority,
    CorrelationReason,
)
from ..context import CorrelationContext
from ..models import CorrelationResult


class ThresholdByIpRule:
    """Dispara quando o mesmo IP gera >= ``threshold`` eventos na janela.

    Args:
        threshold: Quantidade minima de eventos para disparar.
        window_seconds: Largura da janela temporal em segundos.
        rule_id: ID da regra (default: ``"demo-threshold-by-ip"``).
    """

    def __init__(
        self,
        threshold: int = 5,
        window_seconds: float = 300.0,
        rule_id: str = "demo-threshold-by-ip",
    ) -> None:
        if threshold < 2:
            raise ValueError(f"threshold deve ser >= 2; recebido {threshold}")
        if window_seconds <= 0:
            raise ValueError(f"window_seconds deve ser > 0; recebido {window_seconds}")
        self._threshold = threshold
        self._window_seconds = window_seconds
        self._rule_id = rule_id

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(
            id=self._rule_id,
            name="Demo: limite de eventos por IP",
            version="1.0.0",
            description=(
                "DEMO - dispara quando o mesmo IP de origem gera "
                f"{self._threshold} ou mais eventos em "
                f"{self._window_seconds:.0f}s"
            ),
            priority=CorrelationPriority.NORMAL,
            author="edysiem",
            required_fields=frozenset({"ip_src"}),
            window_seconds=self._window_seconds,
        )

    async def setup(self) -> None:
        """Validacao da configuracao; nada a inicializar na demo."""

    async def shutdown(self) -> None:
        """Sem recursos a liberar na demo."""

    async def evaluate(
        self, event: EnrichedEvent, context: CorrelationContext
    ) -> CorrelationResult:
        """Avalia o evento na janela do IP de origem."""
        rule_start = time.perf_counter()

        if not event.ip_src:
            return CorrelationResult.deferred(duration_ms=0.0, rule_id=self._rule_id)

        ip = event.ip_src
        context.add_event(
            rule_id=self._rule_id,
            identity_key=ip,
            event_id=event.event_id,
        )

        window_events = context.get_window(self._rule_id, ip, self._window_seconds)
        duration = (time.perf_counter() - rule_start) * 1000

        if len(window_events) < self._threshold:
            return CorrelationResult.deferred(duration_ms=duration, rule_id=self._rule_id)

        match = CorrelationMatch(
            rule_id=self._rule_id,
            matched_event_ids=window_events,
            reason=CorrelationReason(
                rule_id=self._rule_id,
                condition=(f"{len(window_events)} eventos do mesmo IP dentro da janela"),
                values={"ip_src": ip, "count": len(window_events)},
                details={
                    "threshold": self._threshold,
                    "window_seconds": self._window_seconds,
                },
            ),
            severity=Severity.MEDIUM.value,
            tags=frozenset({"demo", "threshold", "ip"}),
        )

        return CorrelationResult.match(
            matches=(match,), duration_ms=duration, rule_id=self._rule_id
        )


__all__ = ["ThresholdByIpRule"]
