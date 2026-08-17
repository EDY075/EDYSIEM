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
    environment: str
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

    source_type: str = Field(min_length=1, max_length=64)
    source_host: str = Field(min_length=1, max_length=255)
    raw_payload: str = Field(min_length=1, max_length=262_144)
    trace_id: str | None = Field(default=None, max_length=128)


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

    rule_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=512)
    event_ids: list[str] = Field(default_factory=list, max_length=1000)
    severity: str = Field(default="medium", max_length=16)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    risk_score: int = Field(default=50, ge=0, le=100)
    tags: list[str] = Field(default_factory=list, max_length=100)


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

    alert_id: str = Field(min_length=1, max_length=255)
    rule_id: str = Field(default="rule", max_length=255)
    title: str = Field(default="Alerta", max_length=512)
    severity: str = Field(default="medium", max_length=16)
    risk_score: int = Field(default=50, ge=0, le=100)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    asset_id: str | None = Field(default=None, max_length=255)
    user: str | None = Field(default=None, max_length=255)
    fingerprint_hash: str = Field(default="", max_length=255)
    mitre: list[str] = Field(default_factory=list, max_length=100)
    ioc_ids: list[str] = Field(default_factory=list, max_length=1000)


class IncidentCreateRequest(BaseModel):
    """Payload para criar um incidente a partir de alertas."""

    alerts: list[AlertPayload] = Field(min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=512)


class IncidentCreateResponse(BaseModel):
    """Resposta da criacao de incidente."""

    incident_id: str
    alerts_count: int
    kind: Literal["created", "deduplicated", "no_group"]


# --- Cases ------------------------------------------------------------------


class CaseCreateRequest(BaseModel):
    """Payload para criar um case a partir de um incidente."""

    incident_id: str = Field(min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=512)
    owner: str | None = Field(default=None, max_length=128)


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
