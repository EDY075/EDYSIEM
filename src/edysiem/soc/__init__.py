"""Pacote SOC (Sprint 2.15) — fluxo operacional persistido.

- ``SocPipeline``: orquestração E2E (Evento → Regra → Alerta → Incidente → Caso)
- ``SocService``: gestão operacional (incident/case management, investigação, SLA, KPIs)
- ``sla``: política e cálculo de SLA por severidade
"""

from __future__ import annotations

from .pipeline import SocFlowResult, SocPipeline
from .service import SocService
from .sla import SlaPolicy, SlaSnapshot, compute_sla

__all__ = [
    "SlaPolicy",
    "SlaSnapshot",
    "SocFlowResult",
    "SocPipeline",
    "SocService",
    "compute_sla",
]
