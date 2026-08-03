"""Health check dos collectors e da infraestrutura de ingestão.

``HealthMonitor`` agrega o estado de saúde de múltiplos collectors. Cada
componente registrado começa ``OFFLINE`` (ainda não reportado) e passa a ser
atualizado via ``update`` (ou ``refresh``, que consulta o ``health()`` do
próprio collector). ``aggregate`` aplica a regra: qualquer ``OFFLINE`` torna o
conjunto ``OFFLINE``; caso contrário, qualquer ``DEGRADED`` torna ``DEGRADED``;
senão ``ONLINE``.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from .metrics import MetricsRegistry

if TYPE_CHECKING:
    from .collectors.base import CollectorPlugin


class ComponentStatus(Enum):
    """Estado de saúde de um componente."""

    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class CollectorHealth:
    """Snapshot de saúde de um collector.

    Attributes:
        status: Estado corrente do componente.
        uptime_seconds: Tempo de operação (segundos).
        last_event_at: Último evento recebido (UTC), se houver.
        throughput_events_per_sec: Taxa de eventos por segundo.
        errors: Total de erros observados.
        queue_size: Tamanho corrente da fila associada.
        latency_ms: Latência média (ms), quando mensurável.
    """

    status: ComponentStatus
    uptime_seconds: float
    last_event_at: datetime | None
    throughput_events_per_sec: float
    errors: int
    queue_size: int
    latency_ms: float | None = None


def _offline_placeholder() -> CollectorHealth:
    """Health inicial de um componente registrado mas ainda não reportado."""
    return CollectorHealth(
        status=ComponentStatus.OFFLINE,
        uptime_seconds=0.0,
        last_event_at=None,
        throughput_events_per_sec=0.0,
        errors=0,
        queue_size=0,
        latency_ms=None,
    )


class HealthMonitor:
    """Monitora e agrega a saúde dos collectors registrados.

    Thread-safe: ``register``/``update``/``snapshot``/``aggregate`` podem ser
    chamados de qualquer thread. ``refresh`` é async e deve rodar no loop do
    collector consultado.
    """

    def __init__(self, *, metrics: MetricsRegistry | None = None) -> None:
        self._metrics = metrics or MetricsRegistry()
        self._health: dict[str, CollectorHealth] = {}
        self._collectors: dict[str, CollectorPlugin | None] = {}
        self._lock = threading.Lock()

    def register(self, name: str, collector: CollectorPlugin | None = None) -> None:
        """Registra um componente, iniciando como ``OFFLINE``.

        Args:
            name: Identificador estável do componente.
            collector: Collector opcional; quando informado, ``refresh`` pode
                consultar ``health()`` automaticamente.

        Raises:
            ValueError: Se ``name`` for vazio.
        """
        if not name or not name.strip():
            raise ValueError("name não pode ser vazio")
        with self._lock:
            if name not in self._health:
                self._health[name] = _offline_placeholder()
            self._collectors[name] = collector

    def update(self, name: str, health: CollectorHealth) -> None:
        """Atualiza o health de um componente (cria se não registrado)."""
        with self._lock:
            self._health[name] = health
            self._collectors.setdefault(name, None)

    def snapshot(self) -> dict[str, CollectorHealth]:
        """Retorna uma cópia do health de todos os componentes."""
        with self._lock:
            return dict(self._health)

    def aggregate(self) -> ComponentStatus:
        """Agrega o estado de todos os componentes.

        Aplica a regra: ``OFFLINE`` se algum componente está ``OFFLINE``;
        ``DEGRADED`` se algum está ``DEGRADED``; senão ``ONLINE``. Um monitor
        sem componentes é considerado ``ONLINE`` (vazio).
        """
        with self._lock:
            if not self._health:
                return ComponentStatus.ONLINE
            if any(h.status is ComponentStatus.OFFLINE for h in self._health.values()):
                return ComponentStatus.OFFLINE
            if any(h.status is ComponentStatus.DEGRADED for h in self._health.values()):
                return ComponentStatus.DEGRADED
            return ComponentStatus.ONLINE

    def is_healthy(self) -> bool:
        """Retorna ``True`` quando o aggregate é ``ONLINE``."""
        return self.aggregate() is ComponentStatus.ONLINE

    async def refresh(self, name: str) -> CollectorHealth | None:
        """Consulta ``health()`` do collector registrado e atualiza o snapshot.

        Returns:
            O health atualizado, ou ``None`` se não há collector registrado
            para o nome (ou o collector não foi informado no ``register``).
        """
        with self._lock:
            collector = self._collectors.get(name)
        if collector is None:
            return None
        health = await collector.health()
        self.update(name, health)
        return health


__all__ = ["CollectorHealth", "ComponentStatus", "HealthMonitor"]
