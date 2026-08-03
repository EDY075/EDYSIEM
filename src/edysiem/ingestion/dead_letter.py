"""Fila de eventos mortos (Dead Letter Queue) da ingestão.

Eventos que falham de forma definitiva (ex.: fila cheia com política
``DEAD_LETTER``) nunca são descartados em silêncio: são registrados como
``DeadLetterRecord`` e podem ser auditados ou reprocessados. A implementação
atual é in-memory e thread-safe; persistência em SQLite é sprint futura.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from .._utils import utcnow
from ..domain import RawEvent
from .metrics import METRIC_DEAD_LETTERS, MetricsRegistry


@dataclass(frozen=True, slots=True)
class DeadLetterRecord:
    """Registro imutável de um evento que não pôde ser processado.

    Attributes:
        payload: Evento (ou objeto) que falhou; tipicamente ``RawEvent``.
        error: Mensagem de erro que motivou o descarte.
        timestamp: Carimbo de tempo (UTC) do descarte.
        collector: Nome do collector de origem, se conhecido.
        stacktrace: Stacktrace da falha, se disponível.
    """

    payload: RawEvent | object
    error: str
    timestamp: datetime
    collector: str | None = None
    stacktrace: str | None = None


class DeadLetterQueue:
    """Fila in-memory e thread-safe de registros de eventos mortos.

    Args:
        max_records: Capacidade máxima; ao exceder, o registro mais antigo é
            descartado (``deque(maxlen=...)``). Registros nunca são perdidos
            antes desse limite.
        metrics: Registry opcional; cada ``submit`` incrementa a métrica
            ``dead_letters``.
    """

    def __init__(
        self, *, max_records: int = 10_000, metrics: MetricsRegistry | None = None
    ) -> None:
        if max_records <= 0:
            raise ValueError(f"max_records deve ser > 0; recebido {max_records}")
        self._max_records = max_records
        self._metrics = metrics or MetricsRegistry()
        self._records: deque[DeadLetterRecord] = deque(maxlen=max_records)
        self._lock = threading.Lock()

    def submit(
        self,
        payload: RawEvent | object,
        error: str,
        *,
        collector: str | None = None,
        stacktrace: str | None = None,
    ) -> None:
        """Registra um evento morto e incrementa a métrica correspondente."""
        record = DeadLetterRecord(
            payload=payload,
            error=error,
            timestamp=utcnow(),
            collector=collector,
            stacktrace=stacktrace,
        )
        with self._lock:
            self._records.append(record)
        self._metrics.increment(METRIC_DEAD_LETTERS)

    def records(self) -> tuple[DeadLetterRecord, ...]:
        """Retorna uma tupla imutável com os registros atuais."""
        with self._lock:
            return tuple(self._records)

    def __len__(self) -> int:
        """Número de registros atuais."""
        with self._lock:
            return len(self._records)

    def drain(self) -> tuple[DeadLetterRecord, ...]:
        """Esvazia a fila e retorna os registros coletados."""
        with self._lock:
            items = tuple(self._records)
            self._records.clear()
        return items

    def reset(self) -> None:
        """Descarta todos os registros (auditoria manual)."""
        with self._lock:
            self._records.clear()


__all__ = ["DeadLetterQueue", "DeadLetterRecord"]
