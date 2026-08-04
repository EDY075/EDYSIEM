"""Schemas da API v1 do EDY SIEM (Pydantic)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# --- Respostas base -------------------------------------------------------


class ApiResponse(BaseModel):
    """Resposta padrao da API."""

    data: Any = None
    error: str | None = None
    trace_id: str | None = None


class HealthComponent(BaseModel):
    """Estado de um componente."""

    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Resposta do endpoint /health."""

    status: str
    version: str
    components: dict[str, HealthComponent] = Field(default_factory=dict)


class VersionResponse(BaseModel):
    """Resposta do endpoint /version."""

    name: str
    version: str
    environment: str


class MetricsResponse(BaseModel):
    """Resposta do endpoint /metrics."""

    metrics: dict[str, float]
    components: dict[str, Any] = Field(default_factory=dict)


# --- Pipeline -------------------------------------------------------------


class PipelineRunRequest(BaseModel):
    """Payload para executar a pipeline ponta a ponta."""

    source_type: str
    source_host: str
    raw_payload: str
    trace_id: str | None = None


class PipelineRunResponse(BaseModel):
    """Resposta da execucao da pipeline."""

    event_id: str
    category: str
    action: str
    severity: str
    correlated_matches: int = 0
    detected_rule_ids: list[str] = Field(default_factory=list)
    finding_count: int = 0


# --- Alerts ---------------------------------------------------------------


class AlertCreateRequest(BaseModel):
    """Payload para criar um alerta a partir de um finding."""

    rule_id: str
    title: str
    event_ids: list[str] = Field(default_factory=list)
    severity: str = "medium"
    confidence: float = 1.0
    risk_score: int = 50
    tags: list[str] = Field(default_factory=list)


class AlertCreateResponse(BaseModel):
    """Resposta da criacao de alerta."""

    alert_id: str
    rule_id: str
    severity: str
    occurrences: int = 1
    kind: Literal["created", "deduplicated"]


# --- Incidents -------------------------------------------------------------


class AlertPayload(BaseModel):
    """Definicao minima de um alerta para criacao de incidente."""

    alert_id: str
    rule_id: str = "rule"
    title: str = "Alerta"
    severity: str = "medium"
    risk_score: int = 50
    confidence: float = 1.0
    asset_id: str | None = None
    user: str | None = None
    fingerprint_hash: str = ""
    mitre: list[str] = Field(default_factory=list)
    ioc_ids: list[str] = Field(default_factory=list)


class IncidentCreateRequest(BaseModel):
    """Payload para criar um incidente a partir de alertas."""

    alerts: list[AlertPayload]
    title: str | None = None


class IncidentCreateResponse(BaseModel):
    """Resposta da criacao de incidente."""

    incident_id: str
    alerts_count: int
    kind: Literal["created", "deduplicated", "no_group"]


# --- Cases ------------------------------------------------------------------


class CaseCreateRequest(BaseModel):
    """Payload para criar um case a partir de um incidente."""

    incident_id: str
    title: str | None = None
    owner: str | None = None


class CaseCreateResponse(BaseModel):
    """Resposta da criacao de case."""

    case_id: str
    title: str
    status: str


__all__ = [
    "AlertCreateRequest",
    "AlertCreateResponse",
    "AlertPayload",
    "ApiResponse",
    "CaseCreateRequest",
    "CaseCreateResponse",
    "HealthComponent",
    "HealthResponse",
    "IncidentCreateRequest",
    "IncidentCreateResponse",
    "MetricsResponse",
    "PipelineRunRequest",
    "PipelineRunResponse",
    "VersionResponse",
]
