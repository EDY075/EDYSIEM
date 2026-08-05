"""Testes da API v1 (FastAPI + TestClient)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from edysiem.api import create_app
from edysiem.config import load
from edysiem.container import ApplicationContainer


@pytest.fixture
def client() -> TestClient:
    app = create_app(ApplicationContainer(load().unwrap()))
    with TestClient(app) as c:
        yield c


def test_version_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/version")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "0.2.0"
    assert body["name"] == "EDY SIEM"


def test_health_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "components" in body
    assert "alerts" in body["components"]
    assert "cases" in body["components"]


def test_metrics_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "metrics" in body
    assert "enrichment" in body["components"]
    assert "cases" in body["components"]


def test_pipeline_run_endpoint(client: TestClient) -> None:
    r = client.post(
        "/api/v1/pipeline/run",
        json={
            "source_type": "syslog",
            "source_host": "wks-01",
            "raw_payload": (
                "<134>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - Failed password for admin"
            ),
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["event_id"]
    assert body["category"] == "auth"
    assert body["action"] == "reject"


def test_pipeline_run_invalid(client: TestClient) -> None:
    r = client.post(
        "/api/v1/pipeline/run",
        json={"source_type": "syslog", "source_host": "wks-01", "raw_payload": "garbage"},
    )
    assert r.status_code == 422


def test_alerts_endpoint(client: TestClient) -> None:
    r = client.post(
        "/api/v1/alerts",
        json={
            "rule_id": "brute-force",
            "title": "BF",
            "severity": "high",
            "risk_score": 70,
            "event_ids": ["e1"],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["alert_id"]
    assert body["rule_id"] == "brute-force"
    assert body["kind"] == "created"


def test_incidents_endpoint(client: TestClient) -> None:
    alerts = [
        {
            "alert_id": f"a{i}",
            "rule_id": "brute-force",
            "severity": "high",
            "risk_score": 70,
            "asset_id": "asset-1",
            "user": "admin",
            "fingerprint_hash": f"fp-{i}",
        }
        for i in range(5)
    ]
    r = client.post("/api/v1/incidents", json={"alerts": alerts})
    assert r.status_code == 200
    body = r.json()
    assert body["incident_id"]
    assert body["alerts_count"] == 5
    assert body["kind"] == "created"


def test_cases_endpoint(client: TestClient) -> None:
    r = client.post(
        "/api/v1/cases",
        json={"incident_id": "inc-1", "title": "Investigar", "owner": "analyst-01"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["case_id"]
    assert body["status"] == "open"


def test_validation_error_handler(client: TestClient) -> None:
    r = client.post("/api/v1/alerts", json={})  # payload invalido
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert "details" in body


def test_request_id_middleware(client: TestClient) -> None:
    r = client.get("/api/v1/version")
    assert r.headers.get("x-request-id")


def test_openapi_available(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()


def test_docs_available(client: TestClient) -> None:
    r = client.get("/docs")
    assert r.status_code == 200
