"""Contexto de Deteccao do EDY SIEM.

O ``DetectionContext`` mantem o estado compartilhado entre regras de
deteccao: buffers temporais (para regras de threshold como a DEMO),
cache de valores e configuracao.

Design:
- Thread-safe para acesso concorrente por multiplas regras.
- Buffers por ``(rule_id, identity_key)`` com expiracao por TTL.
- Cache simples por chave.
- Rastreio do tamanho do estado para metricas.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BufferEntry:
    """Entrada em um buffer temporal de deteccao.

    Attributes:
        event_id: ID do evento.
        timestamp: Timestamp monotonic (time.monotonic).
    """

    event_id: str
    timestamp: float


class DetectionContext:
    """Estado compartilhado entre regras de deteccao.

    Cada regra pode acumular eventos por uma chave de identidade
    (ex.: host de origem). A expiracao e lazy e robusta a insercao
    fora de ordem.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._buffers: dict[tuple[str, str], deque[BufferEntry]] = defaultdict(deque)
        self._cache: dict[str, Any] = {}

    # --- Buffers temporais (para regras de threshold) ---------------------

    def add_event(
        self,
        rule_id: str,
        identity_key: str,
        event_id: str,
        timestamp: float | None = None,
    ) -> None:
        """Adiciona um evento ao buffer da regra/chave."""
        if not rule_id or not rule_id.strip():
            raise ValueError("rule_id nao pode ser vazio")
        if not identity_key:
            raise ValueError("identity_key nao pode ser vazio")

        entry = BufferEntry(event_id=event_id, timestamp=timestamp or time.monotonic())
        with self._lock:
            self._buffers[(rule_id, identity_key)].append(entry)

    def get_window(
        self,
        rule_id: str,
        identity_key: str,
        window_seconds: float,
        now: float | None = None,
    ) -> tuple[str, ...]:
        """Retorna IDs dos eventos dentro da janela (mais recentes primeiro)."""
        if window_seconds <= 0:
            raise ValueError(f"window_seconds deve ser > 0; recebido {window_seconds}")

        reference = now if now is not None else time.monotonic()
        cutoff = reference - window_seconds

        with self._lock:
            dq = self._buffers[(rule_id, identity_key)]
            while dq and dq[0].timestamp < cutoff:
                dq.popleft()
            if any(e.timestamp < cutoff for e in dq):
                valid = [e for e in dq if e.timestamp >= cutoff]
                dq.clear()
                dq.extend(valid)

            result = tuple(e.event_id for e in dq)

        if not result:
            with self._lock:
                key = (rule_id, identity_key)
                if key in self._buffers and not self._buffers[key]:
                    del self._buffers[key]

        return result

    def window_size(self, rule_id: str, identity_key: str, window_seconds: float) -> int:
        """Retorna a quantidade de eventos dentro da janela."""
        return len(self.get_window(rule_id, identity_key, window_seconds))

    def clear(self, rule_id: str | None = None, identity_key: str | None = None) -> None:
        """Limpa o estado do contexto."""
        with self._lock:
            if rule_id is not None and identity_key is not None:
                self._buffers.pop((rule_id, identity_key), None)
            elif rule_id is not None:
                keys = [k for k in self._buffers if k[0] == rule_id]
                for k in keys:
                    del self._buffers[k]
            else:
                self._buffers.clear()

    @property
    def state_size(self) -> int:
        """Numero total de buffers (rule_id, key) ativos."""
        with self._lock:
            return len(self._buffers)

    # --- Cache simples -----------------------------------------------------

    def set_cache(self, key: str, value: Any) -> None:
        """Armazena um valor no cache compartilhado."""
        with self._lock:
            self._cache[key] = value

    def get_cache(self, key: str, default: Any = None) -> Any:
        """Obtem um valor do cache compartilhado."""
        with self._lock:
            return self._cache.get(key, default)

    def clear_cache(self) -> None:
        """Limpa o cache compartilhado."""
        with self._lock:
            self._cache.clear()

    # --- Estado ------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Snapshot do estado para diagnostico/metricas."""
        with self._lock:
            return {
                "buffers_active": len(self._buffers),
                "total_entries": sum(len(dq) for dq in self._buffers.values()),
                "cache_entries": len(self._cache),
            }


__all__ = ["BufferEntry", "DetectionContext"]
