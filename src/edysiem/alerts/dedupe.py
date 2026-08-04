"""Dedup Engine do Alert Framework.

Se um alerta com o mesmo fingerprint ja existir, incrementa
``occurrences`` e atualiza ``last_seen`` em vez de criar um novo.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import AlertContext
from .models import Alert, AlertFingerprint


class DedupDecision(Enum):
    """Decisao da deduplicacao.

    Attributes:
        NEW: Nenhum alerta existente; criar novo.
        DEDUP: Alerta existente; incrementar occurrences.
    """

    NEW = "new"
    DEDUP = "dedup"


@dataclass(frozen=True, slots=True)
class DedupOutcome:
    """Resultado da deduplicacao.

    Attributes:
        decision: NEW ou DEDUP.
        existing: Alerta existente com mesmo fingerprint (DEDUP).
        fingerprint: Fingerprint calculado.
    """

    decision: DedupDecision
    fingerprint: AlertFingerprint
    existing: Alert | None = None


class DedupEngine:
    """Consulta o estado de fingerprints no ``AlertContext``.

    Args:
        context: Contexto que guarda ``fingerprint_hash -> alert_id``.
    """

    def __init__(self, context: AlertContext) -> None:
        self._context = context

    def check(self, fingerprint: AlertFingerprint) -> DedupOutcome:
        """Verifica se o fingerprint ja foi visto.

        Returns:
            ``DedupOutcome`` com decision NEW/DEDUP. Em DEDUP, ``existing``
            aponta para o alerta correspondente.
        """
        alert = self._context.get_alert_by_fingerprint(fingerprint.hash)
        if alert is None:
            return DedupOutcome(decision=DedupDecision.NEW, fingerprint=fingerprint)
        return DedupOutcome(decision=DedupDecision.DEDUP, fingerprint=fingerprint, existing=alert)


__all__ = ["DedupDecision", "DedupEngine", "DedupOutcome"]
