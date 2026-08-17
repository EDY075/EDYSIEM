"""Receiver tests for EDY Shield -> EDY SIEM ingestion API v1."""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from edysiem.api.app import create_app
from edysiem.api.deps import get_shield_inbox
from edysiem.api.security import require_shield_ingest_token
from edysiem.persistence import PersistenceError, ShieldInboxRepository

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "shield_events" / "v1"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"
ENDPOINT = "/api/v1/ingestion/sources/edy-shield/events"
TOKEN = "test-shield-token-with-at-least-32-bytes"
INSTANCE_ID = "9df3e3b7-f905-49f8-b6a7-3da64227e3d1"

VALID_TYPES = {
    "baseline_created.json": ("shield.fim.baseline.created", "file", "baseline_created"),
    "file_created.json": ("shield.fim.file.added", "file", "created"),
    "file_modified.json": ("shield.fim.file.modified", "file", "modified"),
    "file_deleted.json": ("shield.fim.file.removed", "file", "deleted"),
    "hash_changed.json": ("shield.hash.mismatch", "file", "hash_changed"),
    "scan_completed.json": ("shield.fim.scan.completed", "file", "scan_completed"),
    "critical_security_alert.json": ("shield.alert.created", "alert", "created"),
}


def load_event(directory: Path, name: str) -> dict[str, Any]:
    value = json.loads((directory / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def batch(events: list[object], batch_id: str | None = None) -> dict[str, object]:
    return {
        "batch_id": batch_id or str(uuid4()),
        "sent_at": "2026-08-11T21:55:00.000Z",
        "events": events,
    }


def headers(batch_id: str, token: str = TOKEN) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Idempotency-Key": batch_id,
    }


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("EDYSIEM_ENABLE_DEV_DOCS", "true")
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "shield-inbox.db"))
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", TOKEN)
    monkeypatch.delenv("EDYSIEM_SHIELD_INGEST_PREVIOUS_TOKEN", raising=False)
    monkeypatch.delenv("EDYSIEM_API_KEY", raising=False)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        yield test_client


def post_batch(client: TestClient, payload: dict[str, object]) -> Any:
    batch_id = payload["batch_id"]
    assert isinstance(batch_id, str)
    return client.post(ENDPOINT, json=payload, headers=headers(batch_id))


def inbox(client: TestClient) -> ShieldInboxRepository:
    return client.app.state.container.shield_inbox


def test_valid_event_is_durably_accepted(client: TestClient) -> None:
    event = load_event(VALID, "file_modified.json")
    payload = batch([event])

    response = post_batch(client, payload)

    assert response.status_code == 202
    assert response.json() == {
        "batch_id": payload["batch_id"],
        "accepted_count": 1,
        "duplicate_count": 0,
        "rejected_count": 0,
        "results": [{"event_id": event["event_id"], "status": "accepted"}],
    }
    assert inbox(client).count() == 1


def test_all_seven_scenarios_are_normalized_and_persisted(client: TestClient) -> None:
    events = [load_event(VALID, filename) for filename in VALID_TYPES]

    response = post_batch(client, batch(events))

    assert response.status_code == 202
    assert response.json()["accepted_count"] == 7
    for filename, (event_type, category, action) in VALID_TYPES.items():
        original = load_event(VALID, filename)
        stored = inbox(client).get_event(INSTANCE_ID, original["event_id"])
        assert stored is not None
        assert stored["event_type"] == event_type
        assert stored["source_product"] == "edy-shield"
        assert stored["source_instance_id"] == INSTANCE_ID
        assert stored["processing_status"] == "pending"
        normalized = stored["normalized_payload"]
        assert isinstance(normalized, dict)
        assert normalized["source_type"] == "edy_shield"
        assert normalized["event_category"] == category
        assert normalized["event_action"] == action
        assert normalized["severity"] == original["severity"]
        assert normalized["hostname"] == original["asset"]["hostname"]
        assert normalized["metadata"]["evidence"] == original["evidence"]


def test_persisted_event_contains_received_at_raw_and_asset(client: TestClient) -> None:
    event = load_event(VALID, "hash_changed.json")

    assert post_batch(client, batch([event])).status_code == 202
    stored = inbox(client).get_event(INSTANCE_ID, event["event_id"])

    assert stored is not None
    assert str(stored["received_at"]).endswith("Z")
    assert stored["event_timestamp"] == event["timestamp"]
    assert stored["schema_version"] == "1.0"
    assert stored["asset_id"] == event["asset"]["asset_id"]
    assert stored["hostname"] == event["asset"]["hostname"]
    assert stored["payload"] == event


def test_authentication_correct_missing_and_invalid(client: TestClient) -> None:
    payload = batch([load_event(VALID, "baseline_created.json")])
    batch_id = str(payload["batch_id"])

    assert client.post(ENDPOINT, json=payload, headers=headers(batch_id)).status_code == 202
    missing = client.post(
        ENDPOINT,
        json=batch([load_event(VALID, "file_created.json")]),
        headers={"Content-Type": "application/json"},
    )
    invalid_payload = batch([load_event(VALID, "file_deleted.json")])
    invalid = client.post(
        ENDPOINT,
        json=invalid_payload,
        headers=headers(str(invalid_payload["batch_id"]), "x" * 32),
    )

    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert invalid.status_code == 401
    assert "x" * 32 not in invalid.text


def test_previous_token_supports_rotation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    previous = "previous-shield-token-with-at-least-32-bytes"
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "rotation.db"))
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", TOKEN)
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_PREVIOUS_TOKEN", previous)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        payload = batch([load_event(VALID, "baseline_created.json")])
        response = test_client.post(
            ENDPOINT,
            json=payload,
            headers=headers(str(payload["batch_id"]), previous),
        )

    assert response.status_code == 202


def test_receiver_fails_closed_when_token_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "disabled.db"))
    monkeypatch.delenv("EDYSIEM_SHIELD_INGEST_TOKEN", raising=False)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        payload = batch([load_event(VALID, "baseline_created.json")])
        response = test_client.post(
            ENDPOINT,
            json=payload,
            headers=headers(str(payload["batch_id"])),
        )

    assert response.status_code == 503
    assert TOKEN not in response.text


def test_receiver_fails_closed_when_configured_token_is_too_short(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "short-token.db"))
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", "too-short")
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        payload = batch([load_event(VALID, "baseline_created.json")])
        response = test_client.post(
            ENDPOINT,
            json=payload,
            headers=headers(str(payload["batch_id"]), "too-short"),
        )

    assert response.status_code == 503
    assert "too-short" not in response.text


def test_receiver_uses_scoped_auth_not_global_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "scoped.db"))
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", TOKEN)
    monkeypatch.setenv("EDYSIEM_API_KEY", "operator-api-key")
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        payload = batch([load_event(VALID, "baseline_created.json")])
        ingest = test_client.post(
            ENDPOINT,
            json=payload,
            headers=headers(str(payload["batch_id"])),
        )
        health = test_client.get("/api/v1/health")
        metrics = test_client.get("/api/v1/metrics")

    assert ingest.status_code == 202
    assert health.status_code == 200
    assert metrics.status_code == 503


def test_https_is_required_outside_loopback() -> None:
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": ENDPOINT,
            "raw_path": ENDPOINT.encode(),
            "query_string": b"",
            "headers": [(b"host", b"localhost")],
            "client": ("203.0.113.10", 45123),
            "server": ("127.0.0.1", 80),
        }
    )

    with pytest.raises(HTTPException) as raised:
        asyncio.run(require_shield_ingest_token(request))

    assert raised.value.status_code == 400
    assert raised.value.detail == "HTTPS is required for Shield ingestion"


def test_same_batch_retry_returns_identical_receipt(client: TestClient) -> None:
    payload = batch([load_event(VALID, "file_modified.json")])

    first = post_batch(client, payload)
    second = post_batch(client, payload)

    assert first.status_code == second.status_code == 202
    assert second.json() == first.json()
    assert second.json()["results"][0]["status"] == "accepted"
    assert inbox(client).count() == 1


def test_response_lost_retry_with_new_batch_is_duplicate(client: TestClient) -> None:
    event = load_event(VALID, "file_modified.json")

    assert post_batch(client, batch([event])).status_code == 202
    retry = post_batch(client, batch([event]))

    assert retry.status_code == 202
    assert retry.json()["duplicate_count"] == 1
    assert retry.json()["results"][0]["status"] == "duplicate"
    assert inbox(client).count() == 1


def test_duplicate_inside_batch_is_acknowledged_per_item(client: TestClient) -> None:
    event = load_event(VALID, "file_created.json")

    response = post_batch(client, batch([event, deepcopy(event)]))

    assert response.status_code == 202
    assert response.json()["accepted_count"] == 1
    assert response.json()["duplicate_count"] == 1
    assert [item["status"] for item in response.json()["results"]] == [
        "accepted",
        "duplicate",
    ]
    assert inbox(client).count() == 1


def test_event_id_content_conflict_rolls_back_batch(client: TestClient) -> None:
    event = load_event(VALID, "file_modified.json")
    conflicting = deepcopy(event)
    conflicting["severity"] = "critical"

    response = post_batch(client, batch([event, conflicting]))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "idempotency_conflict"
    assert inbox(client).count() == 0


def test_event_id_content_conflict_across_batches_preserves_original(
    client: TestClient,
) -> None:
    event = load_event(VALID, "file_modified.json")
    conflicting = deepcopy(event)
    conflicting["severity"] = "critical"

    assert post_batch(client, batch([event])).status_code == 202
    response = post_batch(client, batch([conflicting]))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "idempotency_conflict"
    assert inbox(client).count() == 1
    stored = inbox(client).get_event(INSTANCE_ID, str(event["event_id"]))
    assert stored is not None
    assert stored["severity"] == event["severity"]


def test_batch_id_content_conflict(client: TestClient) -> None:
    batch_id = str(uuid4())
    first_payload = batch([load_event(VALID, "file_created.json")], batch_id)
    second_payload = batch([load_event(VALID, "file_deleted.json")], batch_id)

    assert post_batch(client, first_payload).status_code == 202
    conflict = post_batch(client, second_payload)

    assert conflict.status_code == 409
    assert inbox(client).count() == 1


@pytest.mark.parametrize(
    ("fixture", "error_code"),
    [
        ("invalid_schema_version.json", "unsupported_schema_version"),
        ("invalid_event_type.json", "invalid_event_type"),
        ("invalid_severity.json", "invalid_severity"),
        ("invalid_timestamp.json", "invalid_timestamp"),
    ],
)
def test_specific_invalid_formats_return_item_errors(
    client: TestClient, fixture: str, error_code: str
) -> None:
    response = post_batch(client, batch([load_event(INVALID, fixture)]))

    assert response.status_code == 422
    assert response.json()["rejected_count"] == 1
    assert response.json()["results"][0]["status"] == "rejected"
    assert response.json()["results"][0]["error"]["code"] == error_code
    assert inbox(client).count() == 0


@pytest.mark.parametrize("path", sorted(INVALID.glob("*.json")))
def test_all_invalid_contract_fixtures_are_rejected(client: TestClient, path: Path) -> None:
    response = post_batch(client, batch([load_event(INVALID, path.name)]))

    assert response.status_code == 422
    assert response.json()["accepted_count"] == 0
    assert response.json()["rejected_count"] == 1


def test_all_invalid_batch_receipt_is_durable_and_idempotent(client: TestClient) -> None:
    payload = batch([load_event(INVALID, "invalid_schema_version.json")])

    first = post_batch(client, payload)
    replay = post_batch(client, payload)
    changed = deepcopy(payload)
    changed["events"] = [load_event(INVALID, "invalid_event_type.json")]
    conflict = post_batch(client, changed)

    assert first.status_code == replay.status_code == 422
    assert replay.json() == first.json()
    assert conflict.status_code == 409
    assert inbox(client).count() == 0


def test_partially_invalid_batch_persists_only_valid_items(client: TestClient) -> None:
    valid = load_event(VALID, "file_created.json")
    invalid = load_event(INVALID, "invalid_schema_version.json")

    response = post_batch(client, batch([valid, invalid]))

    assert response.status_code == 202
    assert response.json()["accepted_count"] == 1
    assert response.json()["rejected_count"] == 1
    assert [item["status"] for item in response.json()["results"]] == [
        "accepted",
        "rejected",
    ]
    assert inbox(client).count() == 1


def test_non_object_item_is_rejected_without_invalidating_valid_item(client: TestClient) -> None:
    valid = load_event(VALID, "file_created.json")

    response = post_batch(client, batch([valid, "not-an-event"]))

    assert response.status_code == 202
    assert response.json()["accepted_count"] == 1
    assert response.json()["rejected_count"] == 1
    assert response.json()["results"][1]["event_id"] is None


def test_malformed_json_and_envelope_are_rejected(client: TestClient) -> None:
    malformed = client.post(
        ENDPOINT,
        content=b"{not-json",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid4()),
        },
    )
    missing_events_payload = {"batch_id": str(uuid4()), "sent_at": "2026-08-11T21:55:00Z"}
    invalid_envelope = client.post(
        ENDPOINT,
        json=missing_events_payload,
        headers=headers(str(missing_events_payload["batch_id"])),
    )

    assert malformed.status_code == 400
    assert invalid_envelope.status_code == 400


def test_idempotency_key_is_required_and_must_match(client: TestClient) -> None:
    payload = batch([load_event(VALID, "baseline_created.json")])
    no_key_headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    missing = client.post(ENDPOINT, json=payload, headers=no_key_headers)
    mismatch = client.post(ENDPOINT, json=payload, headers=headers(str(uuid4())))

    assert missing.status_code == 400
    assert mismatch.status_code == 400


def test_content_type_and_compression_are_rejected(client: TestClient) -> None:
    payload = batch([load_event(VALID, "baseline_created.json")])
    batch_id = str(payload["batch_id"])
    wrong_type = headers(batch_id)
    wrong_type["Content-Type"] = "text/plain"
    compressed = headers(batch_id)
    compressed["Content-Encoding"] = "gzip"

    assert client.post(ENDPOINT, content=json.dumps(payload), headers=wrong_type).status_code == 415
    assert client.post(ENDPOINT, content=json.dumps(payload), headers=compressed).status_code == 415


def test_non_finite_json_is_rejected_before_contract_validation(client: TestClient) -> None:
    payload = batch([load_event(VALID, "baseline_created.json")])
    text = json.dumps(payload).replace("1243", "NaN", 1)

    response = client.post(
        ENDPOINT,
        content=text,
        headers=headers(str(payload["batch_id"])),
    )

    assert response.status_code == 400


def test_non_utf8_json_is_rejected(client: TestClient) -> None:
    payload = batch([load_event(VALID, "baseline_created.json")])
    encoded = json.dumps(payload).encode("utf-16")

    response = client.post(
        ENDPOINT,
        content=encoded,
        headers=headers(str(payload["batch_id"])),
    )

    assert response.status_code == 400


def test_duplicate_json_keys_are_rejected(client: TestClient) -> None:
    event = load_event(VALID, "baseline_created.json")
    batch_id = str(uuid4())
    event_json = json.dumps(event)
    text = (
        "{"
        f'"batch_id":"{batch_id}",'
        f'"batch_id":"{batch_id}",'
        '"sent_at":"2026-08-11T21:55:00.000Z",'
        f'"events":[{event_json}]'
        "}"
    )

    response = client.post(ENDPOINT, content=text, headers=headers(batch_id))

    assert response.status_code == 400


def test_event_batch_and_body_limits(client: TestClient) -> None:
    event = load_event(VALID, "baseline_created.json")
    oversized_event = deepcopy(event)
    oversized_event["metadata"] = {"x_blob": "x" * 66_000}
    event_response = post_batch(client, batch([oversized_event]))

    too_many = post_batch(client, batch([event] * 101))

    huge_payload = batch([event])
    huge_payload["padding"] = "x" * (1024 * 1024)
    huge_response = client.post(
        ENDPOINT,
        content=json.dumps(huge_payload),
        headers=headers(str(huge_payload["batch_id"])),
    )

    assert event_response.status_code == 413
    assert too_many.status_code == 413
    assert huge_response.status_code == 413


def test_persistence_failure_returns_503_and_is_atomic(client: TestClient) -> None:
    repository = inbox(client)
    conn = repository.manager.connect()
    conn.execute(
        """
        CREATE TRIGGER fail_shield_inbox_insert
        BEFORE INSERT ON ingestion_inbox
        BEGIN
            SELECT RAISE(ABORT, 'simulated failure');
        END;
        """
    )
    conn.commit()
    payload = batch([load_event(VALID, "file_created.json")])

    response = post_batch(client, payload)

    assert response.status_code == 503
    assert repository.count() == 0
    batch_count = conn.execute("SELECT COUNT(*) AS total FROM ingestion_batches").fetchone()
    assert batch_count["total"] == 0
    assert "simulated failure" not in response.text


def test_dependency_persistence_error_does_not_leak_details(client: TestClient) -> None:
    class BrokenInbox:
        def replay(self, batch_id: str, content_hash: str) -> None:
            raise PersistenceError("database path and secret details")

    client.app.dependency_overrides[get_shield_inbox] = lambda: BrokenInbox()
    payload = batch([load_event(VALID, "file_created.json")])
    try:
        response = post_batch(client, payload)
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "database path" not in response.text
    assert "secret" not in response.text


def test_inbox_initialization_failure_returns_safe_503(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path))
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", TOKEN)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        payload = batch([load_event(VALID, "file_created.json")])
        response = test_client.post(
            ENDPOINT,
            json=payload,
            headers=headers(str(payload["batch_id"])),
        )

    assert response.status_code == 503
    assert str(tmp_path) not in response.text


def test_openapi_contains_only_the_approved_ingestion_endpoint(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    ingestion_paths = [path for path in paths if "/ingestion/sources/edy-shield" in path]

    assert ingestion_paths == [ENDPOINT]
