"""Contexto do Incident Engine.

Mantem o estado in-memory dos incidentes e o indice de fingerprints
para deduplicacao. Thread-safe. Persistencia externa em sprint futura.
"""

from __future__ import annotations

import threading
from typing import Any

from .models import Incident


class IncidentContext:
    """Armazenamento in-memory de incidentes + indice de fingerprints.

    Design:
    - ``_incidents``: mapa ``incident_id -> Incident``.
    - ``_fingerprints``: mapa ``fingerprint_hash -> incident_id``.
    - Thread-safe (RLock).
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._incidents: dict[str, Incident] = {}
        self._fingerprints: dict[str, str] = {}

    def save(self, incident: Incident) -> None:
        """Armazena/atualiza um incidente e registra seu fingerprint."""
        with self._lock:
            self._incidents[incident.id] = incident
            if incident.fingerprint is not None:
                self._fingerprints[incident.fingerprint.hash] = incident.id

    def get(self, incident_id: str) -> Incident | None:
        """Retorna um incidente pelo ID."""
        with self._lock:
            return self._incidents.get(incident_id)

    def get_incident_by_fingerprint(self, fingerprint_hash: str) -> Incident | None:
        """Retorna o incidente correspondente a um fingerprint hash."""
        with self._lock:
            incident_id = self._fingerprints.get(fingerprint_hash)
            if incident_id is None:
                return None
            return self._incidents.get(incident_id)

    def all(self) -> tuple[Incident, ...]:
        """Retorna todos os incidentes armazenados."""
        with self._lock:
            return tuple(self._incidents.values())

    def __len__(self) -> int:
        with self._lock:
            return len(self._incidents)

    def clear(self) -> None:
        """Limpa o estado."""
        with self._lock:
            self._incidents.clear()
            self._fingerprints.clear()

    def snapshot(self) -> dict[str, Any]:
        """Snapshot do estado para diagnostico/metricas."""
        with self._lock:
            return {
                "incidents": len(self._incidents),
                "fingerprints": len(self._fingerprints),
            }


__all__ = ["IncidentContext"]
