"""Regra DEMO: mais de 5 falhas de login em 5 minutos.

Regra de exemplo para validar a arquitetura do Detection Framework.
Nao e uma regra de producao - apenas demonstra como uma regra de
threshold usa o ``DetectionContext`` para acumular estado.

Condicao:
    count(eventos de falha de login no mesmo ``source_host`` na janela)
    > threshold
"""

from __future__ import annotations

import time

from ...correlation import CorrelatedEvent
from ...domain import RiskScore, Severity
from ..base import (
    DetectionFinding,
    DetectionPriority,
    DetectionReason,
    RuleMetadata,
)
from ..context import DetectionContext
from ..models import DetectionResult


class LoginFailuresRule:
    """Dispara quando o mesmo host acumula > ``threshold`` falhas de login.

    Args:
        threshold: Quantidade minima de falhas para disparar (default 5).
        window_seconds: Largura da janela temporal em segundos (default 300).
        rule_id: ID da regra (default: ``"demo-login-failures"``).
    """

    def __init__(
        self,
        threshold: int = 5,
        window_seconds: float = 300.0,
        rule_id: str = "demo-login-failures",
    ) -> None:
        if threshold < 2:
            raise ValueError(f"threshold deve ser >= 2; recebido {threshold}")
        if window_seconds <= 0:
            raise ValueError(f"window_seconds deve ser > 0; recebido {window_seconds}")
        self._threshold = threshold
        self._window_seconds = window_seconds
        self._rule_id = rule_id

    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id=self._rule_id,
            name="Demo: multiplas falhas de login",
            version="1.0.0",
            description=(
                "DEMO - dispara quando o mesmo host acumula mais de "
                f"{self._threshold} falhas de login em "
                f"{self._window_seconds:.0f}s"
            ),
            priority=DetectionPriority.NORMAL,
            severity=Severity.MEDIUM,
            confidence=0.9,
            risk_score=RiskScore(60),
            required_fields=frozenset({"source_host"}),
            tags=frozenset({"demo", "auth", "brute-force"}),
        )

    async def setup(self) -> None:
        """Validacao da configuracao; nada a inicializar na demo."""

    async def shutdown(self) -> None:
        """Sem recursos a liberar na demo."""

    async def evaluate(self, event: CorrelatedEvent, context: DetectionContext) -> DetectionResult:
        """Avalia o evento correlacionado contra a regra."""
        rule_start = time.perf_counter()
        source = event.source_event

        # Identifica falha de login
        is_login_failure = (
            source is not None
            and source.event_category == "auth"
            and source.event_action in ("reject", "failed")
        )

        if not is_login_failure or not source.source_host:
            return DetectionResult.no_detection(duration_ms=0.0, rule_id=self._rule_id)

        host = source.source_host
        context.add_event(
            rule_id=self._rule_id,
            identity_key=host,
            event_id=event.event_id,
        )

        window = context.get_window(self._rule_id, host, self._window_seconds)
        duration = (time.perf_counter() - rule_start) * 1000

        if len(window) <= self._threshold:
            return DetectionResult.deferred(duration_ms=duration, rule_id=self._rule_id)

        finding = DetectionFinding(
            rule_id=self._rule_id,
            event_ids=window,
            reason=DetectionReason(
                rule_id=self._rule_id,
                condition=(f"{len(window)} falhas de login no mesmo host dentro da janela"),
                values={"source_host": host, "count": len(window)},
                details={
                    "threshold": self._threshold,
                    "window_seconds": self._window_seconds,
                },
            ),
            severity=Severity.MEDIUM,
            confidence=0.9,
            risk_score=RiskScore(60),
            tags=frozenset({"demo", "auth", "brute-force"}),
        )

        return DetectionResult.detected(
            findings=(finding,), duration_ms=duration, rule_id=self._rule_id
        )


__all__ = ["LoginFailuresRule"]
