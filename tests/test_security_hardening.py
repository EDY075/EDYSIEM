"""End-to-end regressions for the security hardening release."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from edysiem.api.app import create_app
from edysiem.container import ApplicationContainer
from edysiem.persistence import AuditAction
from edysiem.soc import SocService

API_KEY = "hardening-test-key-with-at-least-32-random-bytes"
SHIELD_PATH = "/api/v1/ingestion/sources/edy-shield/events"
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
PUBLIC_MUTATION_ALLOWLIST = frozenset({("POST", SHIELD_PATH)})
PUBLIC_GET_ALLOWLIST = frozenset({"/api/v1/health", "/api/v1/version"})


def _configure(monkeypatch: pytest.MonkeyPatch, db: Path, *, role: str = "analyst") -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(db))
    monkeypatch.setenv("EDYSIEM_API_KEY", API_KEY)
    monkeypatch.setenv("EDYSIEM_API_IDENTITY", "authenticated-analyst")
    monkeypatch.setenv("EDYSIEM_API_ROLE", role)


def _operator_mutations(app) -> list[tuple[str, str]]:
    operations = [
        (method.upper(), path)
        for path, item in app.openapi()["paths"].items()
        for method in item
        if method.upper() in MUTATING_METHODS
        and (method.upper(), path) not in PUBLIC_MUTATION_ALLOWLIST
    ]
    assert operations, "the RBAC regression matrix must never be empty"
    assert len(operations) >= 21, "operator mutation inventory unexpectedly shrank"
    return sorted(operations)


def _protected_operator_reads(app) -> list[str]:
    paths = [
        path
        for path, item in app.openapi()["paths"].items()
        if "get" in item and path not in PUBLIC_GET_ALLOWLIST
    ]
    assert paths, "the protected GET regression matrix must never be empty"
    return sorted(paths)


def _concrete_path(path: str) -> str:
    value = str(uuid4())
    return re.sub(r"\{[^}]+\}", value, path)


def _assert_mutation_statuses(
    client: TestClient,
    operations: list[tuple[str, str]],
    *,
    headers: dict[str, str],
    expected: int | None = None,
) -> None:
    for method, path in operations:
        response = client.request(method, _concrete_path(path), headers=headers, json={})
        if expected is None:
            assert response.status_code not in {401, 403}, (
                f"authenticated role unexpectedly rejected: {method} {path} "
                f"-> {response.status_code}"
            )
        else:
            assert response.status_code == expected, (
                f"RBAC mismatch: {method} {path} -> {response.status_code}, expected {expected}"
            )


def test_mutation_method_inventory_covers_all_write_verbs() -> None:
    assert MUTATING_METHODS == {"POST", "PUT", "PATCH", "DELETE"}


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-API-Key": "invalid-key"}, {"X-EDY-Role": "admin"}],
)
def test_every_nonpublic_get_requires_operator_authentication(
    monkeypatch, tmp_path, headers
) -> None:
    _configure(monkeypatch, tmp_path / f"reads-auth-{uuid4()}.db", role="admin")
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        for path in _protected_operator_reads(app):
            response = client.get(_concrete_path(path), headers=headers)
            assert response.status_code == 401, (
                f"protected GET accepted without operator authentication: {path} "
                f"-> {response.status_code}"
            )


def test_every_operator_mutation_rejects_viewer_and_forged_role(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path / "routes-viewer.db", role="viewer")
    app = create_app()
    operations = _operator_mutations(app)
    headers = {"X-API-Key": API_KEY, "X-EDY-Role": "admin"}
    with TestClient(app, raise_server_exceptions=False) as client:
        _assert_mutation_statuses(client, operations, headers=headers, expected=403)


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "invalid-key"}])
def test_every_operator_mutation_rejects_missing_or_invalid_key(
    monkeypatch, tmp_path, headers
) -> None:
    _configure(monkeypatch, tmp_path / f"routes-auth-{uuid4()}.db", role="admin")
    app = create_app()
    operations = _operator_mutations(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        _assert_mutation_statuses(client, operations, headers=headers, expected=401)


@pytest.mark.parametrize("role", ["analyst", "admin"])
def test_every_operator_mutation_accepts_authorized_roles(monkeypatch, tmp_path, role) -> None:
    _configure(monkeypatch, tmp_path / f"routes-{role}.db", role=role)
    app = create_app()
    operations = _operator_mutations(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        _assert_mutation_statuses(
            client,
            operations,
            headers={"X-API-Key": API_KEY, "X-EDY-Role": "viewer"},
        )


def test_shield_ingestion_is_not_an_operator_key_exception(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path / "shield-scope.db", role="admin")
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", "shield-scope-token-with-32-random-bytes")
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        missing = client.post(SHIELD_PATH, json={})
        operator_only = client.post(SHIELD_PATH, headers={"X-API-Key": API_KEY}, json={})
    assert missing.status_code == 401
    assert operator_only.status_code == 401


def test_distinct_shield_token_never_authenticates_as_operator(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path / "shield-not-operator.db", role="admin")
    shield_token = "distinct-shield-token-with-at-least-32-random-bytes"
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", shield_token)
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.get("/api/v1/metrics", headers={"X-API-Key": shield_token})
    assert response.status_code == 401


def test_mutation_audit_records_authenticated_identity_and_result(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path / "audit.db")
    container = ApplicationContainer()
    with TestClient(create_app(container), headers={"X-API-Key": API_KEY}) as client:
        response = client.post(
            "/api/v1/alerts",
            json={"rule_id": "manual", "title": "Manual", "event_ids": ["e-1"]},
        )
    assert response.status_code == 200
    page = container.audit_engine.repository.query(action=AuditAction.API_REQUEST)
    entry = page.items[0]
    assert entry.actor_id == "authenticated-analyst"
    assert entry.entity_id == "/api/v1/alerts"
    assert entry.current == "success"
    assert entry.details["method"] == "POST"
    assert entry.details["result"] == 200
    assert entry.details["request_id"]


def test_comment_author_comes_from_authenticated_identity(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path / "comment.db")
    container = ApplicationContainer()
    headers = {"X-API-Key": API_KEY}
    with TestClient(create_app(container), headers=headers) as client:
        demo = client.post("/api/v1/soc/pipeline/demo")
        case_id = demo.json()["case_id"]
        response = client.post(
            f"/api/v1/soc/cases/{case_id}/comment",
            params={"body": "verified note", "author": "forged-admin"},
        )
    assert response.status_code == 200
    service = container.soc_service
    assert isinstance(service, SocService)
    case = service.get_case(case_id)
    assert case is not None
    assert case.comments[-1].author == "authenticated-analyst"


def test_global_body_limit_rejects_large_payload(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path / "payload.db")
    with TestClient(create_app(), headers={"X-API-Key": API_KEY}) as client:
        response = client.post(
            "/api/v1/pipeline/run",
            content=b"x" * 1_048_577,
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
        )
    assert response.status_code == 413
    assert response.json()["detail"] == "request body too large"


def test_schema_rejects_oversized_log_before_processing(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path / "schema-limit.db")
    with TestClient(create_app(), headers={"X-API-Key": API_KEY}) as client:
        response = client.post(
            "/api/v1/pipeline/run",
            json={"source_type": "syslog", "source_host": "host", "raw_payload": "x" * 262_145},
        )
    assert response.status_code == 422
