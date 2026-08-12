"""Testes da API /soc (pipeline E2E, incident/case management, KPIs)."""

from __future__ import annotations

from uuid import uuid4

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


def test_soc_demo_seed_is_idempotent_across_restarts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        first = client.post("/api/v1/soc/pipeline/demo")
        assert first.status_code == 200
        totals = {
            "alerts": client.get("/api/v1/soc/alerts").json()["total"],
            "incidents": client.get("/api/v1/soc/incidents").json()["total"],
            "cases": client.get("/api/v1/soc/cases").json()["total"],
        }

    with TestClient(create_app()) as client:
        second = client.post("/api/v1/soc/pipeline/demo")
        assert second.status_code == 200
        assert second.json()["alert_ids"] == first.json()["alert_ids"]
        assert second.json()["incident_id"] == first.json()["incident_id"]
        assert second.json()["case_id"] == first.json()["case_id"]
        assert client.get("/api/v1/soc/alerts").json()["total"] == totals["alerts"]
        assert client.get("/api/v1/soc/incidents").json()["total"] == totals["incidents"]
        assert client.get("/api/v1/soc/cases").json()["total"] == totals["cases"]


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
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "invalid_case_id"


def test_case_investigation_errors_are_bounded(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        missing = client.get(f"/api/v1/soc/cases/{uuid4()}/investigate")
        assert missing.status_code == 404
        assert missing.json()["detail"] == {
            "code": "case_not_found",
            "message": "case not found",
        }

        case_id = client.post("/api/v1/soc/pipeline/demo").json()["case_id"]

        def unavailable(_: str):
            raise RuntimeError("database password and internal path")

        monkeypatch.setattr(client.app.state.container.soc_service, "investigate", unavailable)
        response = client.get(f"/api/v1/soc/cases/{case_id}/investigate")

        assert response.status_code == 500
        assert response.json()["detail"] == {
            "code": "investigation_unavailable",
            "message": "investigation unavailable",
        }
        assert "password" not in response.text
        r = client.get("/api/v1/soc/cases/nao-existe/investigate")
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "invalid_case_id"


def test_case_mutations_validate_ids_and_bound_not_found(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        mutations = (
            ("comment", {"body": "triagem", "author": "analyst"}),
            ("evidence", {"kind": "ioc", "value": "10.0.0.1"}),
            ("assign", {"owner": "analyst"}),
            ("claim", {"owner": "analyst"}),
            ("resolve", {"resolution": "tratado"}),
            ("close", {"resolution": "encerrado"}),
        )
        for action, params in mutations:
            invalid = client.post(f"/api/v1/soc/cases/not-a-uuid/{action}", params=params)
            assert invalid.status_code == 422
            assert invalid.json()["detail"]["code"] == "invalid_case_id"

        missing_id = uuid4()
        for action, params in mutations:
            missing = client.post(f"/api/v1/soc/cases/{missing_id}/{action}", params=params)
            assert missing.status_code == 404
            assert missing.json()["detail"] == {
                "code": "case_not_found",
                "message": "case not found",
            }


def test_soc_api_alerts_and_series(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        client.post("/api/v1/soc/pipeline/demo")

        r = client.get("/api/v1/soc/alerts")
        assert r.status_code == 200
        items = r.json()["items"]
        assert r.json()["total"] >= 4
        assert items[0]["alert_id"]

        r = client.get(f"/api/v1/soc/alerts/{items[0]['alert_id']}")
        assert r.status_code == 200
        assert "sla" in r.json()

        assert client.get("/api/v1/soc/alerts/nao-existe").status_code == 404

        r = client.get("/api/v1/soc/metrics")
        assert r.status_code == 200
        series = r.json()["metrics"]["events_series"]
        assert len(series) == 60
        assert isinstance(series[0]["events"], int)


def test_soc_decision_queue_list_limits(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        client.post("/api/v1/soc/pipeline/demo")

        alerts = client.get("/api/v1/soc/alerts", params={"limit": 1})
        incidents = client.get("/api/v1/soc/incidents", params={"limit": 1})
        assert alerts.status_code == 200
        assert incidents.status_code == 200
        assert len(alerts.json()["items"]) == 1
        assert len(incidents.json()["items"]) == 1
        assert alerts.json()["total"] >= len(alerts.json()["items"])
        assert incidents.json()["total"] >= len(incidents.json()["items"])

        for path in ("alerts", "incidents"):
            assert client.get(f"/api/v1/soc/{path}", params={"limit": 0}).status_code == 422
            assert client.get(f"/api/v1/soc/{path}", params={"limit": 101}).status_code == 422


def test_soc_api_detection_intel(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        client.post("/api/v1/soc/pipeline/demo")

        r = client.post(
            "/api/v1/soc/rules",
            json={
                "rule_id": "brute-force-ssh",
                "name": "Brute Force SSH",
                "severity": "critical",
                "category": "authentication",
                "tags": ["brute"],
            },
        )
        assert r.status_code == 200
        assert r.json()["rule_id"] == "brute-force-ssh"

        assert client.get("/api/v1/soc/rules").json()["total"] >= 1
        assert client.post("/api/v1/soc/rules/brute-force-ssh/disable").json()["enabled"] is False
        assert client.post("/api/v1/soc/rules/brute-force-ssh/enable").json()["enabled"] is True
        assert client.post("/api/v1/soc/rules/nao-existe/enable").status_code == 404

        r = client.post("/api/v1/soc/simulator", json={"event": {"category": "authentication"}})
        assert r.status_code == 200
        assert r.json()["matches"] >= 1

        client.post(
            "/api/v1/soc/iocs",
            json={"value": "1.2.3.4", "ioc_type": "ip", "reputation": "malicious"},
        )
        assert client.get("/api/v1/soc/iocs").json()["total"] >= 1
        assert client.get("/api/v1/soc/iocs/1.2.3.4/related").status_code == 200

        client.post(
            "/api/v1/soc/assets",
            json={"hostname": "web-01", "ip": "10.0.0.5", "os": "Linux", "criticality": "critical"},
        )
        assert client.get("/api/v1/soc/assets").json()["total"] >= 1
        assert client.get("/api/v1/soc/assets/web-01/related").status_code == 200

        r = client.get("/api/v1/soc/detection")
        assert r.status_code == 200
        assert "top_rules" in r.json()
        assert isinstance(r.json()["critical_assets"], list)
