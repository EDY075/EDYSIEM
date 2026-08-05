"""Testes da API /soc (pipeline E2E, incident/case management, KPIs)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from edysiem.api.app import create_app


def test_soc_api_full_flow(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        # Pipeline demo → alertas/incidente/caso
        r = client.post("/api/v1/soc/pipeline/demo")
        assert r.status_code == 200
        data = r.json()
        assert data["case_id"]
        assert data["incident_id"]
        cid = data["case_id"]

        # Incidentes e cases persistidos
        assert client.get("/api/v1/soc/incidents").json()["total"] >= 1
        assert client.get("/api/v1/soc/cases").json()["total"] >= 1

        # Gestão de case
        r = client.post(
            f"/api/v1/soc/cases/{cid}/comment",
            params={"body": "triagem manual", "author": "ana.silva"},
        )
        assert r.status_code == 200
        assert r.json()["comments_count"] == 1

        r = client.post(
            f"/api/v1/soc/cases/{cid}/evidence",
            params={"kind": "ioc", "value": "185.220.101.4"},
        )
        assert r.status_code == 200
        assert r.json()["evidence_count"] == 1

        # Investigação
        assert client.get(f"/api/v1/soc/cases/{cid}/investigate").status_code == 200

        # Encerramento
        r = client.post(f"/api/v1/soc/cases/{cid}/close", params={"resolution": "encerrado"})
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

        # KPIs reais
        r = client.get("/api/v1/soc/metrics")
        assert r.status_code == 200
        assert r.json()["components"]["total_cases"] >= 1
        assert r.json()["components"]["cases_closed"] >= 1


def test_soc_api_incident_not_found(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        r = client.get("/api/v1/soc/incidents/nao-existe")
        assert r.status_code == 404


def test_soc_api_pipeline_run_event(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        r = client.post(
            "/api/v1/soc/pipeline/run",
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
        assert isinstance(body["alert_ids"], list)

        # payload inválido -> 422
        r = client.post(
            "/api/v1/soc/pipeline/run",
            json={"source_type": "syslog", "source_host": "wks-01", "raw_payload": "garbage"},
        )
        assert r.status_code == 422


def test_soc_api_case_resolve_and_incident_assign(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        demo = client.post("/api/v1/soc/pipeline/demo").json()
        cid = demo["case_id"]
        iid = demo["incident_id"]

        r = client.post(f"/api/v1/soc/cases/{cid}/resolve", params={"resolution": "confirmado"})
        assert r.status_code == 200
        assert r.json()["resolution"] == "confirmado"

        r = client.post(f"/api/v1/soc/cases/{cid}/assign", params={"owner": "bruno.lima"})
        assert r.status_code == 200
        assert r.json()["owner"] == "bruno.lima"

        r = client.post(f"/api/v1/soc/incidents/{iid}/assign", params={"analyst": "carla.melo"})
        assert r.status_code == 200
        assert r.json()["owner"] == "carla.melo"

        r = client.post(f"/api/v1/soc/cases/{cid}/close", params={"resolution": "encerrado"})
        assert r.status_code == 200
        assert r.json()["status"] == "closed"


def test_soc_api_details_transition_and_400(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        demo = client.post("/api/v1/soc/pipeline/demo").json()
        cid = demo["case_id"]
        iid = demo["incident_id"]

        r = client.get(f"/api/v1/soc/incidents/{iid}")
        assert r.status_code == 200
        assert "sla" in r.json()
        r = client.get(f"/api/v1/soc/cases/{cid}")
        assert r.status_code == 200
        assert r.json()["status"]

        r = client.post(f"/api/v1/soc/incidents/{iid}/transition", params={"target": "triage"})
        assert r.status_code == 200
        assert r.json()["status"] == "triage"

        r = client.post(f"/api/v1/soc/incidents/{iid}/transition", params={"target": "closed"})
        assert r.status_code == 400

        r = client.post(
            f"/api/v1/soc/cases/{cid}/evidence",
            params={"kind": "tipo-invalido", "value": "x"},
        )
        assert r.status_code == 400

        r = client.get("/api/v1/soc/cases/nao-existe")
        assert r.status_code == 404
        r = client.get("/api/v1/soc/cases/nao-existe/investigate")
        assert r.status_code == 404
