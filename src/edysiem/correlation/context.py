"""Contexto de Correlacao do EDY SIEM.

O ``CorrelationContext`` mantem o estado de janela temporal usado pelas
regras de correlacao baseadas em janela (ex.: "N eventos em X minutos").

Design:
- Thread-safe para acesso concorrente por multiplas regras.
- Buffers por ``(rule_id, identity_key)`` com expiracao por TTL.
- Metodos de janela: ``add_event`` / ``get_window`` / ``expire``.
- Rastreio do tamanho do estado para metricas.

O estado e puramente in-memory na v1; persistencia em sprint futura.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class WindowEntry:
    """Entrada em uma janela de correlacao.

    Attributes:
        event_id: ID do evento.
        timestamp: Timestamp monotonic (time.monotonic) do evento.
    """

    event_id: str
    timestamp: float


class CorrelationContext:
    """Estado de janela temporal compartilhado entre regras.

    Cada regra pode acumular eventos por uma chave de identidade
    (ex.: IP de origem). A expiracao e lazy: eventos fora da janela
    sao descartados ao acessar a janela.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # (rule_id, identity_key) -> deque[WindowEntry]
        self._windows: dict[tuple[str, str], deque[WindowEntry]] = defaultdict(deque)
        self._default_ttl_seconds: float = 3600.0

    @property
    def default_ttl_seconds(self) -> float:
        """TTL padrao de retencao das janelas."""
        return self._default_ttl_seconds

    def add_event(
        self,
        rule_id: str,
        identity_key: str,
        event_id: str,
        timestamp: float | None = None,
    ) -> None:
        """Adiciona um evento a janela da regra/chave.

        Args:
            rule_id: Regra de correlacao.
            identity_key: Chave de identidade (ex.: IP de origem).
            event_id: ID do evento.
            timestamp: Timestamp monotonic; usa o corrente se None.
        """
        if not rule_id or not rule_id.strip():
            raise ValueError("rule_id nao pode ser vazio")
        if not identity_key:
            raise ValueError("identity_key nao pode ser vazio")

        entry = WindowEntry(event_id=event_id, timestamp=timestamp or time.monotonic())
        with self._lock:
            self._windows[(rule_id, identity_key)].append(entry)

    def get_window(
        self,
        rule_id: str,
        identity_key: str,
        window_seconds: float,
        now: float | None = None,
    ) -> tuple[str, ...]:
        """Retorna IDs dos eventos dentro da janela (mais recentes primeiro).

        Eventos fora da janela sao descartados (expiracao lazy).

        Args:
            rule_id: Regra de correlacao.
            identity_key: Chave de identidade.
            window_seconds: Largura da janela em segundos.
            now: Timestamp monotonic de referencia; usa o corrente se None.

        Returns:
            Tupla de event_ids dentro da janela.
        """
        if window_seconds <= 0:
            raise ValueError(f"window_seconds deve ser > 0; recebido {window_seconds}")

        reference = now if now is not None else time.monotonic()
        cutoff = reference - window_seconds

        with self._lock:
            dq = self._windows[(rule_id, identity_key)]
            # Descarta do inicio enquanto estiver fora da janela (caso ordenado)
            while dq and dq[0].timestamp < cutoff:
                dq.popleft()

            # Filtra tambem entradas fora da janela que nao estao no inicio
            # (robustez para insercoes fora de ordem)
            if any(entry.timestamp < cutoff for entry in dq):
                valid = [e for e in dq if e.timestamp >= cutoff]
                dq.clear()
                dq.extend(valid)

            result = tuple(entry.event_id for entry in dq)

        # Limpa janela vazia para nao vazar memoria
        if not result:
            with self._lock:
                key = (rule_id, identity_key)
                if key in self._windows and not self._windows[key]:
                    del self._windows[key]

        return result

    def window_size(self, rule_id: str, identity_key: str, window_seconds: float) -> int:
        """Retorna a quantidade de eventos dentro da janela."""
        return len(self.get_window(rule_id, identity_key, window_seconds))

    def expire(
        self,
        rule_id: str,
        identity_key: str,
        window_seconds: float,
        now: float | None = None,
    ) -> int:
        """Descarta eventos fora da janela; retorna quantos permaneceram."""
        return len(self.get_window(rule_id, identity_key, window_seconds, now))

    def clear(self, rule_id: str | None = None, identity_key: str | None = None) -> None:
        """Limpa o estado de correlacao.

        Args:
            rule_id: Se informado, limpa apenas as janelas desta regra.
            identity_key: Se informado (com rule_id), limpa apenas essa chave.
        """
        with self._lock:
            if rule_id is not None and identity_key is not None:
                self._windows.pop((rule_id, identity_key), None)
            elif rule_id is not None:
                keys = [k for k in self._windows if k[0] == rule_id]
                for k in keys:
                    del self._windows[k]
            else:
                self._windows.clear()

    @property
    def state_size(self) -> int:
        """Numero total de janelas (rule_id, key) ativas."""
        with self._lock:
            return len(self._windows)

    def total_entries(self) -> int:
        """Numero total de eventos armazenados em todas as janelas."""
        with self._lock:
            return sum(len(dq) for dq in self._windows.values())

    def snapshot(self) -> dict[str, Any]:
        """Snapshot do estado para diagnostico/metricas."""
        with self._lock:
            return {
                "windows_active": len(self._windows),
                "total_entries": sum(len(dq) for dq in self._windows.values()),
                "default_ttl_seconds": self._default_ttl_seconds,
            }


__all__ = ["CorrelationContext", "WindowEntry"]
