"""Contexto do Alert Engine.

Mantem o estado in-memory dos alertas e o indice de fingerprints para
deduplicacao. Thread-safe. Persistencia externa em sprint futura.
"""

from __future__ import annotations

import threading
from typing import Any

from .models import Alert, AlertFingerprint


class AlertContext:
    """Armazenamento in-memory de alertas + indice de fingerprints.

    Design:
    - ``_alerts``: mapa ``alert_id -> Alert``.
    - ``_fingerprints``: mapa ``fingerprint_hash -> alert_id``.
    - Thread-safe (RLock).
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._alerts: dict[str, Alert] = {}
        self._fingerprints: dict[str, str] = {}

    def save(self, alert: Alert) -> None:
        """Armazena/atualiza um alerta e registra seu fingerprint."""
        with self._lock:
            self._alerts[alert.id] = alert
            if alert.fingerprint is not None:
                self._fingerprints[alert.fingerprint.hash] = alert.id

    def get(self, alert_id: str) -> Alert | None:
        """Retorna um alerta pelo ID."""
        with self._lock:
            return self._alerts.get(alert_id)

    def get_alert_by_fingerprint(self, fingerprint_hash: str) -> Alert | None:
        """Retorna o alerta correspondente a um fingerprint hash."""
        with self._lock:
            alert_id = self._fingerprints.get(fingerprint_hash)
            if alert_id is None:
                return None
            return self._alerts.get(alert_id)

    def has_fingerprint(self, fingerprint: AlertFingerprint) -> bool:
        """Verifica se o fingerprint ja foi registrado."""
        with self._lock:
            return fingerprint.hash in self._fingerprints

    def all(self) -> tuple[Alert, ...]:
        """Retorna todos os alertas armazenados."""
        with self._lock:
            return tuple(self._alerts.values())

    def __len__(self) -> int:
        with self._lock:
            return len(self._alerts)

    def clear(self) -> None:
        """Limpa o estado."""
        with self._lock:
            self._alerts.clear()
            self._fingerprints.clear()

    def snapshot(self) -> dict[str, Any]:
        """Snapshot do estado para diagnostico/metricas."""
        with self._lock:
            return {
                "alerts": len(self._alerts),
                "fingerprints": len(self._fingerprints),
            }


__all__ = ["AlertContext"]
