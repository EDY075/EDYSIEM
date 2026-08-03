"""Infraestrutura de ingestão enterprise (Sprint 2.2).

Pacote **totalmente desacoplado e reutilizável**: depende apenas de
``edysiem.domain`` (``RawEvent``), ``edysiem.result``, ``edysiem.exceptions``,
``edysiem.logging`` (logger opcional) e stdlib. Não importa parsers nem outros
pacotes de plugins.

Componentes:
- ``collectors.base``: contrato Enterprise de coletores (``CollectorPlugin``).
- ``queue``: fila FIFO thread-safe e async-ready (``RawEventQueue``).
- ``backpressure``: controle de backpressure com high/low water marks.
- ``retry``: política de retry com backoff exponencial e jitter.
- ``dead_letter``: fila de eventos mortos (auditoria/reprocessamento).
- ``rate_limiter``: token bucket thread-safe.
- ``health``: monitoramento de saúde dos collectors.
- ``metrics``: registro de métricas (contadores/gauges/timers).
"""

from .backpressure import BackpressureConfig, BackpressureController, BackpressureState
from .collectors.base import CollectorCapability, CollectorMetadata, CollectorPlugin
from .dead_letter import DeadLetterQueue, DeadLetterRecord
from .health import CollectorHealth, ComponentStatus, HealthMonitor
from .metrics import MetricsRegistry
from .queue import DropPolicy, QueueConfig, RawEventQueue
from .rate_limiter import RateLimitConfig, TokenBucketRateLimiter
from .retry import RetryPolicy, run_with_retry

__all__ = [
    "BackpressureConfig",
    "BackpressureController",
    "BackpressureState",
    "CollectorCapability",
    "CollectorHealth",
    "CollectorMetadata",
    "CollectorPlugin",
    "ComponentStatus",
    "DeadLetterQueue",
    "DeadLetterRecord",
    "DropPolicy",
    "HealthMonitor",
    "MetricsRegistry",
    "QueueConfig",
    "RateLimitConfig",
    "RawEventQueue",
    "RetryPolicy",
    "TokenBucketRateLimiter",
    "run_with_retry",
]
