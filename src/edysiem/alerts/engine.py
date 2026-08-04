"""Alert Engine Enterprise.

Orquestra o fluxo completo de um alerta:
    DetectionFinding -> Risk -> Fingerprint -> Builder -> Dedup -> Lifecycle -> Alert

Decisao:
- NEW: alerta criado
- DEDUP: occurrences+1 / last_seen atualizado (sem novo alerta)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .._utils import utcnow as _utcnow
from ..domain import EnrichedEvent
from .builder import AlertBuilder
from .context import AlertContext
from .dedupe import DedupDecision, DedupEngine
from .fingerprint import FingerprintEngine
from .models import Alert, AlertMetrics
from .registry import AlertRegistry
from .risk import RiskEngine


class AlertResultKind(Enum):
    """Tipo de resultado do Alert Engine."""

    CREATED = "created"
    DEDUPLICATED = "deduplicated"


@dataclass(frozen=True, slots=True)
class AlertResult:
    """Resultado do processamento de um finding.

    Attributes:
        kind: CREATED ou DEDUPLICATED.
        alert: Alerta resultante.
        fingerprint_hash: Fingerprint usado.
        was_new: Se foi criado (True) ou deduplicado (False).
    """

    kind: AlertResultKind
    alert: Alert
    fingerprint_hash: str
    was_new: bool


class AlertEngine:
    """Motor de ciclo de vida de alertas.

    Args:
        builder: Construtor de alertas.
        dedupe: Engine de deduplicacao.
        lifecycle: Gerenciador de transicoes de estado.
        registry: Hooks de ciclo de vida.
        context: Armazenamento in-memory.
    """

    def __init__(
        self,
        builder: AlertBuilder | None = None,
        dedupe: DedupEngine | None = None,
        lifecycle: Any = None,
        registry: AlertRegistry | None = None,
        context: AlertContext | None = None,
    ) -> None:
        from .lifecycle import LifecycleManager

        self._context = context if context is not None else AlertContext()
        self._registry = registry or AlertRegistry()
        self._builder = builder or AlertBuilder(FingerprintEngine(), RiskEngine())
        self._dedupe = dedupe or DedupEngine(self._context)
        self._lifecycle = lifecycle or LifecycleManager()
        self._metrics = AlertMetrics()

    @property
    def context(self) -> AlertContext:
        """Armazenamento de alertas."""
        return self._context

    @property
    def registry(self) -> AlertRegistry:
        """Registry de hooks."""
        return self._registry

    @property
    def metrics(self) -> AlertMetrics:
        """Metricas do engine."""
        return self._metrics

    async def process_finding(
        self,
        finding: Any,
        source_event: EnrichedEvent | None = None,
        *,
        title: str | None = None,
        identity: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> AlertResult:
        """Processa um ``DetectionFinding`` em um alerta.

        Args:
            finding: Finding do Detection Framework.
            source_event: Evento de origem.
            title: Titulo customizado.
            identity: Campos adicionais de identidade.
            now: Carimbo de referencia.

        Returns:
            ``AlertResult`` com kind CREATED/DEDUPLICATED.
        """
        now = now or _utcnow()

        # 1. Construir alerta (risk + fingerprint internos)
        alert = self._builder.build(finding, source_event, title=title, identity=identity, now=now)

        # 2. Deduplicacao
        fingerprint = alert.fingerprint
        if fingerprint is None:
            # Sem fingerprint, sempre cria
            return self._finalize_created(alert, "", now)

        outcome = self._dedupe.check(fingerprint)
        if outcome.decision is DedupDecision.DEDUP and outcome.existing is not None:
            return self._finalize_dedup(outcome.existing, fingerprint.hash, now)

        return self._finalize_created(alert, fingerprint.hash, now)

    def _finalize_created(self, alert: Alert, fingerprint_hash: str, now: datetime) -> AlertResult:
        """Persiste um alerta novo e notifica hooks."""
        self._context.save(alert)
        self._metrics.record_created(alert.rule_id)
        self._registry.on_created(alert)
        return AlertResult(
            kind=AlertResultKind.CREATED,
            alert=alert,
            fingerprint_hash=fingerprint_hash,
            was_new=True,
        )

    def _finalize_dedup(self, existing: Alert, fingerprint_hash: str, now: datetime) -> AlertResult:
        """Incrementa occurrences do alerta existente (sem novo alerta)."""
        updated = existing.bump(at=now)
        self._context.save(updated)
        self._metrics.record_deduplicated(updated.rule_id)
        self._registry.on_updated(updated)
        return AlertResult(
            kind=AlertResultKind.DEDUPLICATED,
            alert=updated,
            fingerprint_hash=fingerprint_hash,
            was_new=False,
        )

    def transition(
        self,
        alert: Alert,
        target: Any,
        *,
        actor: str = "system",
        detail: str = "",
        now: datetime | None = None,
    ) -> Alert:
        """Aplica uma transicao de estado no ciclo de vida.

        Raises:
            AlertInvalidStateTransition: Se a transicao e invalida.
        """
        result = self._lifecycle.transition(alert, target, actor=actor, detail=detail, now=now)
        if result.changed:
            self._context.save(result.alert)
            self._registry.on_status_changed(result.alert, result.previous, result.alert.status)
        return result.alert

    def get_metrics_snapshot(self) -> dict[str, Any]:
        """Snapshot de metricas do engine."""
        m = self._metrics
        return {
            "total_created": m.total_created,
            "total_deduplicated": m.total_deduplicated,
            "total_updates": m.total_updates,
            "total_failures": m.total_failures,
            "created_by_rule": dict(m.created_by_rule),
            "deduplicated_by_rule": dict(m.deduplicated_by_rule),
            "context": self._context.snapshot(),
            "registry": self._registry.get_stats(),
            "last_updated": m.last_updated.isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        """Verifica saude do engine."""
        return {
            "engine": "healthy",
            "context": self._context.snapshot(),
            "metrics": self.get_metrics_snapshot(),
        }


__all__ = ["AlertEngine", "AlertResult", "AlertResultKind"]
