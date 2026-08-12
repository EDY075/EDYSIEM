"""API tests for the Shield event deep-link investigation flow."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from edysiem.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]
EVENT_FILE = ROOT / "tests" / "fixtures" / "shield_events" / "v1" / "valid" / "hash_changed.json"
FILE_ADDED = ROOT / "tests" / "fixtures" / "shield_events" / "v1" / "valid" / "file_created.json"
TOKEN = "test-shield-token-with-at-least-32-bytes"
INGEST = "/api/v1/ingestion/sources/edy-shield/events"
INVESTIGATE = "/api/v1/investigation/sources/edy-shield/events"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "investigation.db"))
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", TOKEN)
    monkeypatch.delenv("EDYSIEM_API_KEY", raising=False)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        yield test_client


def _event() -> dict[str, object]:
    value = json.loads(EVENT_FILE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _ingest(client: TestClient, event: dict[str, object]) -> None:
    batch_id = str(uuid4())
    response = client.post(
        INGEST,
        json={"batch_id": batch_id, "sent_at": "2026-08-12T12:00:00.000Z", "events": [event]},
        headers={"Authorization": f"Bearer {TOKEN}", "Idempotency-Key": batch_id},
    )
    assert response.status_code == 202


def test_resolves_exact_shield_event_with_evidence_and_provenance(client: TestClient) -> None:
    event = _event()
    _ingest(client, event)

    response = client.get(f"{INVESTIGATE}/{event['event_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == event["event_id"]
    assert body["source"]["product"] == "edy-shield"
    assert body["asset"] == event["asset"]
    assert body["evidence"] == event["evidence"]
    assert body["metadata"] == event["metadata"]
    assert body["processing_status"] == "pending"
    assert body["sequence"] == event["sequence"]
    assert body["case"] is None


def test_resolves_file_added_without_previous_hash(client: TestClient) -> None:
    event = json.loads(FILE_ADDED.read_text(encoding="utf-8"))
    assert isinstance(event, dict)
    _ingest(client, event)

    response = client.get(f"{INVESTIGATE}/{event['event_id']}")

    assert response.status_code == 200
    evidence = response.json()["evidence"]
    assert "previous_hash" not in evidence
    assert evidence["current_hash"] == event["evidence"]["current_hash"]
    assert evidence["file_size_bytes"] == 49152
    assert evidence["mtime"] == "2026-08-11T18:44:07.400Z"


def test_returns_read_only_entity_inventory_context(client: TestClient) -> None:
    event = _event()
    asset = event["asset"]
    assert isinstance(asset, dict)
    hostname = str(asset["hostname"])
    service = client.app.state.container.soc_service
    service.register_asset(
        hostname,
        ip="10.20.30.40",
        os_name="Inventário confiável",
        criticality="high",
        owner="asset.owner",
        status="active",
    )
    _ingest(client, event)

    response = client.get(f"{INVESTIGATE}/{event['event_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["asset"]["ip"] == asset["ip"]
    assert body["entity"]["inventory_status"] == "registered"
    assert body["entity"]["inventory"]["ip"] == "10.20.30.40"
    assert body["entity"]["inventory"]["os"] == "Inventário confiável"
    assert body["entity"]["related_file"] == event["evidence"]["file_path"]
    assert service.get_asset(hostname)["ip"] == "10.20.30.40"


def test_normalizes_mitre_context_and_preserves_it_in_case(client: TestClient) -> None:
    event = _event()
    metadata = dict(event["metadata"])
    metadata["x_mitre"] = [" T1059.001 ", "T1059.001", "javascript:alert(1)", "T1110"]
    metadata["x_mitre_details"] = [
        {
            "technique_id": "T1059.001",
            "name": "PowerShell <img src=x onerror=alert(1)>",
            "tactic": "Execution",
        }
    ]
    event["metadata"] = metadata
    _ingest(client, event)

    response = client.get(f"{INVESTIGATE}/{event['event_id']}")
    created = client.post(f"{INVESTIGATE}/{event['event_id']}/cases")

    assert response.status_code == 200
    assert response.json()["mitre"] == [
        {
            "technique_id": "T1059.001",
            "source": "EDY Shield · metadata x_mitre",
            "name": "PowerShell <img src=x onerror=alert(1)>",
            "tactic": "Execution",
        },
        {"technique_id": "T1110", "source": "EDY Shield · metadata x_mitre"},
    ]
    assert created.status_code == 200
    cases = client.app.state.container.soc_service.list_cases(limit=10)
    assert cases[0].mitre == frozenset({"T1059.001", "T1110"})


def test_lists_recent_shield_events_with_linked_case_context(client: TestClient) -> None:
    first = _event()
    second = _event()
    second["event_id"] = str(uuid4())
    second["timestamp"] = "2026-08-11T18:44:00.000Z"
    evidence = dict(second["evidence"])
    evidence["details"] = {"title": "<img src=x onerror=alert(1)>"}
    second["evidence"] = evidence
    _ingest(client, first)
    _ingest(client, second)
    client.post(f"{INVESTIGATE}/{second['event_id']}/cases")

    response = client.get(f"{INVESTIGATE}?limit=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["event_id"] for item in body["items"]] == [
        second["event_id"],
        first["event_id"],
    ]
    assert body["items"][0]["source"]["product"] == "edy-shield"
    assert body["items"][0]["case"]["evidence_count"] == 1
    assert body["items"][0]["case"]["sla"]["state"] in {"ok", "warning", "overdue"}
    assert body["items"][0]["evidence"]["details"]["title"] == "<img src=x onerror=alert(1)>"


def test_shield_event_queue_rejects_invalid_limits(client: TestClient) -> None:
    assert client.get(f"{INVESTIGATE}?limit=0").status_code == 422
    assert client.get(f"{INVESTIGATE}?limit=101").status_code == 422


def test_invalid_missing_and_wrong_source_states(client: TestClient) -> None:
    invalid = client.get(f"{INVESTIGATE}/not-a-uuid")
    missing = client.get(f"{INVESTIGATE}/{uuid4()}")
    event = _event()
    _ingest(client, event)
    connection = client.app.state.container.shield_inbox.manager.connect()
    connection.execute(
        "UPDATE ingestion_inbox SET source_product = 'other' WHERE event_id = ?",
        (event["event_id"],),
    )
    connection.commit()
    wrong_source = client.get(f"{INVESTIGATE}/{event['event_id']}")

    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "invalid_event_id"
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "shield_event_not_found"
    assert wrong_source.status_code == 404
    assert wrong_source.json()["detail"]["code"] == "wrong_source"


def test_case_creation_is_idempotent_and_preserves_original_event(client: TestClient) -> None:
    event = _event()
    _ingest(client, event)
    endpoint = f"{INVESTIGATE}/{event['event_id']}/cases"

    first = client.post(endpoint)
    second = client.post(endpoint)
    fetched = client.get(f"{INVESTIGATE}/{event['event_id']}")

    assert first.status_code == 200
    assert first.json()["case_created"] is True
    assert second.status_code == 200
    assert second.json()["case_created"] is False
    assert first.json()["case"]["case_id"] == second.json()["case"]["case_id"]
    assert second.json()["case"]["evidence_count"] == 1
    assert fetched.json()["case"]["case_id"] == first.json()["case"]["case_id"]
    cases = client.app.state.container.soc_service.list_cases(limit=100)
    assert len(cases) == 1
    assert json.loads(cases[0].evidences[0].value) == event
    investigated = client.get(f"/api/v1/soc/cases/{cases[0].id}/investigate")
    assert investigated.status_code == 200
    assert investigated.json()["sla"]["state"] in {"ok", "warning", "overdue"}
    assert investigated.json()["evidence"][0]["source"] == "edy-shield"
    assert investigated.json()["evidence"][0]["label"] == f"EDY Shield event {event['event_id']}"


def test_concurrent_case_creation_returns_one_link_and_one_evidence(client: TestClient) -> None:
    event = _event()
    event["event_id"] = str(uuid4())
    _ingest(client, event)
    endpoint = f"{INVESTIGATE}/{event['event_id']}/cases"

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post(endpoint), range(2)))

    assert [response.status_code for response in responses] == [200, 200]
    payloads = [response.json() for response in responses]
    assert sorted(payload["case_created"] for payload in payloads) == [False, True]
    assert len({payload["case"]["case_id"] for payload in payloads}) == 1
    cases = client.app.state.container.soc_service.list_cases(limit=100)
    linked = [case for case in cases if case.incident_id == f"shield-event:{event['event_id']}"]
    assert len(linked) == 1
    assert len(linked[0].evidences) == 1


def test_claim_is_conditional_and_preserves_first_owner(client: TestClient) -> None:
    event = _event()
    event["event_id"] = str(uuid4())
    _ingest(client, event)
    created = client.post(f"{INVESTIGATE}/{event['event_id']}/cases").json()
    case_id = created["case"]["case_id"]

    first = client.post(f"/api/v1/soc/cases/{case_id}/claim", params={"owner": "analyst.one"})
    second = client.post(f"/api/v1/soc/cases/{case_id}/claim", params={"owner": "analyst.two"})

    assert first.status_code == 200
    assert first.json()["owner"] == "analyst.one"
    assert second.status_code == 409
    assert second.json()["detail"] == {
        "code": "case_already_assigned",
        "message": "case already assigned",
        "owner": "analyst.one",
    }
    assert client.get(f"/api/v1/soc/cases/{case_id}").json()["owner"] == "analyst.one"


def test_frontend_contains_all_required_resolution_states() -> None:
    source = (ROOT / "frontend" / "src" / "pages" / "ShieldEventInvestigationPage.tsx").read_text(
        encoding="utf-8"
    )
    for marker in (
        "loading",
        "Acesso inválido",
        "Evento ainda não ingerido",
        "Origem incompatível",
        "API de investigação indisponível",
        "Criar caso",
        "Técnica MITRE ainda não associada",
        "HASH ANTERIOR",
        "Abrir caso",
        "Próxima decisão",
        "Assumir",
        "Continuar investigação",
        "ENTIDADE · ENDPOINT",
        "/cases?case=",
        "/claim?",
    ):
        assert marker in source


def test_frontend_case_handoff_preserves_exact_context_and_errors() -> None:
    hook = (ROOT / "frontend" / "src" / "hooks" / "useCases.ts").read_text(encoding="utf-8")
    case_center = (ROOT / "frontend" / "src" / "pages" / "CaseCenterPage.tsx").read_text(
        encoding="utf-8"
    )
    investigation = (ROOT / "frontend" / "src" / "pages" / "InvestigationPage.tsx").read_text(
        encoding="utf-8"
    )

    assert "requestedCaseId" in hook
    assert "/soc/cases/${encodeURIComponent(requestedCaseId)}" in hook
    assert "Origem EDY Shield" in case_center
    assert "event_id" in case_center
    assert "detailsError" in case_center
    assert 'title="Contexto indisponível"' in case_center
    assert "Voltar à investigação" in case_center
    assert "useCases(60, requestedCaseId)" in investigation
