"""SLA (Service Level Agreement) por severidade — Sprint 2.15.

Define prazos de atendimento por severidade e calcula o status de SLA de uma
entidade (alerta/incidente/caso) a partir de sua criação e encerramento.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .._utils import utcnow as _utcnow


@dataclass(frozen=True, slots=True)
class SlaPolicy:
    """Prazos de atendimento (horas) por severidade.

    Defaults típicos de SOC: crítico 1h, alto 4h, médio 24h, baixo 72h.
    """

    critical_hours: float = 1.0
    high_hours: float = 4.0
    medium_hours: float = 24.0
    low_hours: float = 72.0

    def hours_for(self, severity: str) -> float:
        """Horas de prazo para uma severidade."""
        s = severity.lower()
        return {
            "critical": self.critical_hours,
            "high": self.high_hours,
            "medium": self.medium_hours,
            "low": self.low_hours,
            "info": self.low_hours,
        }.get(s, self.medium_hours)

    def deadline_for(self, severity: str, created_at: datetime) -> datetime:
        """Prazo (deadline) absoluto para uma entidade criada em ``created_at``."""
        return created_at + timedelta(hours=self.hours_for(severity))


@dataclass(frozen=True, slots=True)
class SlaSnapshot:
    """Estado de SLA de uma entidade num instante ``now``.

    ``state`` pode ser: ``overdue`` (excedeu o prazo), ``warning`` (resta ≤ 25%
    da janela), ``ok`` (dentro do prazo) ou ``met`` (encerrada antes do prazo).
    """

    severity: str
    created_at: datetime
    deadline: datetime
    now: datetime
    remaining: timedelta
    overdue: bool
    state: str
    closed_on_time: bool = False

    @property
    def remaining_seconds(self) -> float:
        """Segundos restantes (nunca negativo)."""
        return max(self.remaining.total_seconds(), 0.0)


def compute_sla(
    severity: str,
    created_at: datetime,
    *,
    closed_at: datetime | None = None,
    policy: SlaPolicy | None = None,
    now: datetime | None = None,
) -> SlaSnapshot:
    """Computa o snapshot de SLA de uma entidade.

    Args:
        severity: Severidade da entidade (critical/high/medium/low/info).
        created_at: Momento da criação.
        closed_at: Momento do encerramento (se já encerrada).
        policy: Política de prazo (default: ``SlaPolicy()``).
        now: Instante de referência (default: UTC agora).
    """
    pol = policy or SlaPolicy()
    now = now or _utcnow()
    deadline = pol.deadline_for(severity, created_at)
    remaining = deadline - now
    overdue = remaining < timedelta(0)
    target = deadline - created_at  # janela total (deadline - criacao)

    if closed_at is not None:
        closed_on_time = closed_at <= deadline
        state = "met" if closed_on_time else "missed"
    elif overdue:
        state = "overdue"
    elif remaining <= target * 0.3:  # <=30% da janela restante
        state = "warning"
    else:
        state = "ok"

    return SlaSnapshot(
        severity=severity,
        created_at=created_at,
        deadline=deadline,
        now=now,
        remaining=remaining,
        overdue=overdue,
        state=state,
        closed_on_time=closed_at is not None and closed_at <= deadline,
    )


__all__ = ["SlaPolicy", "SlaSnapshot", "compute_sla"]
