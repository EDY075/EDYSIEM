"""API tests for the Shield event deep-link investigation flow."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from edysiem.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]
EVENT_FILE = ROOT / "tests" / "fixtures" / "shield_events" / "v1" / "valid" / "hash_changed.json"
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


def test_frontend_contains_all_required_resolution_states() -> None:
    source = (
        ROOT / "frontend" / "src" / "pages" / "ShieldEventInvestigationPage.tsx"
    ).read_text(encoding="utf-8")
    for marker in (
        "loading",
        "Acesso inválido",
        "Evento ainda não ingerido",
        "Origem incompatível",
        "API de investigação indisponível",
        "Criar caso a partir deste evento",
        "Técnica MITRE ainda não associada",
    ):
        assert marker in source
