"""Registro de métricas de observabilidade (sem dependência externa).

Fornece ``MetricsRegistry`` — um agregador thread-safe de contadores
(monotônicos), gauges (valores correntes) e timers (durações com média),
usado pela infraestrutura de ingestão (fila, dead letter, health) e pronto
para ser exportado por exporters de métricas em sprints futuras.

Os nomes de métrica são constantes estáveis, documentadas em ``__all__`` e
usadas de forma consistente por todos os módulos de ``edysiem.ingestion``.
"""

from __future__ import annotations

import threading

# Nomes padronizados de métricas da infraestrutura de ingestão.
METRIC_QUEUE_SIZE = "queue_size"
METRIC_THROUGHPUT = "throughput"
METRIC_PROCESSING_TIME_MS = "processing_time_ms"
METRIC_DROPS = "drops"
METRIC_RETRIES = "retries"
METRIC_DEAD_LETTERS = "dead_letters"
METRIC_LATENCY_MS = "latency_ms"
METRIC_ERRORS = "errors"


class MetricsRegistry:
    """Agregador thread-safe de métricas simples.

    Mantém três espaços de nomes independentes: contadores, gauges e timers.
    ``increment``/``set_gauge``/``observe`` são operações atômicas protegidas
    por um ``threading.Lock``; ``snapshot`` devolve uma cópia consolidada.

    Para timers, o registry guarda a soma e a contagem de observações e
    ``get``/``snapshot`` retornam a **média** até o momento.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._timers: dict[str, tuple[float, int]] = {}

    def increment(self, name: str, value: int | float = 1) -> None:
        """Incrementa um contador monotônico.

        Se o nome já existir em outro espaço (gauge/timer), o contador é
        mantido em espaço próprio e o valor corrente via ``get`` prioriza
        contadores — documente nomes exclusivos por categoria para evitar
        ambiguidade.
        """
        with self._lock:
            current = self._counters.get(name, 0.0)
            self._counters[name] = current + float(value)

    def set_gauge(self, name: str, value: int | float) -> None:
        """Define o valor corrente de um gauge."""
        with self._lock:
            self._gauges[name] = float(value)

    def observe(self, name: str, value: int | float) -> None:
        """Observa uma duração/amostra (timer); guarda soma e contagem."""
        with self._lock:
            total, count = self._timers.get(name, (0.0, 0))
            self._timers[name] = (total + float(value), count + 1)

    def get(self, name: str) -> float:
        """Retorna o valor corrente da métrica.

        Prioridade: contador → gauge → timer (média). Nomes inexistentes
        retornam ``0.0`` (convenção de observabilidade: zero é o valor neutro
        de um contador).
        """
        with self._lock:
            if name in self._counters:
                return self._counters[name]
            if name in self._gauges:
                return self._gauges[name]
            if name in self._timers:
                total, count = self._timers[name]
                return total / count if count else 0.0
            return 0.0

    def snapshot(self) -> dict[str, float]:
        """Retorna uma cópia consolidada de todas as métricas.

        Em caso de colisão de nomes entre categorias, a ordem de precedência
        é contador → gauge → timer, espelhando ``get``.
        """
        with self._lock:
            data: dict[str, float] = {}
            data.update(self._counters)
            data.update(self._gauges)
            for name, (total, count) in self._timers.items():
                data[name] = total / count if count else 0.0
            return data

    def reset(self) -> None:
        """Zera todas as métricas registradas."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()


__all__ = [
    "METRIC_DEAD_LETTERS",
    "METRIC_DROPS",
    "METRIC_ERRORS",
    "METRIC_LATENCY_MS",
    "METRIC_PROCESSING_TIME_MS",
    "METRIC_QUEUE_SIZE",
    "METRIC_RETRIES",
    "METRIC_THROUGHPUT",
    "MetricsRegistry",
]
