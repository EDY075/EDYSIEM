"""Focused regression tests for localhost-only backend security controls."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message, Receive, Scope, Send

from edysiem.api.app import create_app
from edysiem.api.middleware import (
    HTTPLoggingMiddleware,
    LocalPeerOnlyMiddleware,
    MutationAuditMiddleware,
    PayloadTooLargeError,
    RequestBodyLimitMiddleware,
    RequestIDMiddleware,
)
from edysiem.container import ApplicationContainer
from edysiem.exceptions import ConfigurationException

OPERATOR_KEY = "operator-key-with-at-least-thirty-two-bytes"
SHIELD_KEY = "shield-key-with-at-least-thirty-two-bytes"


def _operator_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDYSIEM_API_KEY", OPERATOR_KEY)
    monkeypatch.setenv("EDYSIEM_API_IDENTITY", "security-test")
    monkeypatch.setenv("EDYSIEM_API_ROLE", "admin")


@pytest.mark.parametrize(
    "shield_variable",
    ["EDYSIEM_SHIELD_INGEST_TOKEN", "EDYSIEM_SHIELD_INGEST_PREVIOUS_TOKEN"],
)
def test_operator_and_shield_credentials_cannot_collide(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, shield_variable: str
) -> None:
    _operator_env(monkeypatch)
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "collision.db"))
    monkeypatch.setenv("EDYSIEM_SHIELD_INGEST_TOKEN", SHIELD_KEY)
    monkeypatch.setenv(shield_variable, OPERATOR_KEY)

    with pytest.raises(ConfigurationException) as raised:
        create_app()

    error = str(raised.value)
    assert error == "credential configuration is invalid"
    assert OPERATOR_KEY not in error
    assert SHIELD_KEY not in error


def test_credential_validation_allows_shield_to_be_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _operator_env(monkeypatch)
    monkeypatch.delenv("EDYSIEM_SHIELD_INGEST_TOKEN", raising=False)
    monkeypatch.delenv("EDYSIEM_SHIELD_INGEST_PREVIOUS_TOKEN", raising=False)

    create_app()


def test_docs_are_closed_by_default_and_require_explicit_local_dev_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EDYSIEM_ENABLE_DEV_DOCS", raising=False)
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404

    monkeypatch.setenv("EDYSIEM_ENABLE_DEV_DOCS", "true")
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200


def test_dev_docs_flag_is_ignored_outside_local_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDYSIEM_ENABLE_DEV_DOCS", "true")
    monkeypatch.setenv("EDYSIEM_ENV", "production")
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        assert client.get("/openapi.json").status_code == 404


def test_trusted_host_rejects_unapproved_host(monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(create_app(), base_url="http://untrusted.example") as client:
        assert client.get("/api/v1/health").status_code == 400


def test_localhost_host_header_does_not_override_nonlocal_peer() -> None:
    async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
        raise AssertionError("nonlocal request reached downstream")

    app = LocalPeerOnlyMiddleware(downstream)
    messages: list[Message] = []
    scope = _scope(client=("203.0.113.10", 45123), host=b"localhost")

    async def send(message: Message) -> None:
        messages.append(message)

    asyncio.run(app(scope, _empty_receive, send))

    starts = [message for message in messages if message["type"] == "http.response.start"]
    assert len(starts) == 1
    assert starts[0]["status"] == 403


def test_inbox_and_audit_connections_close_across_repeated_lifespans(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "lifecycle.db"))
    container = ApplicationContainer()
    app = create_app(container)

    for _ in range(2):
        with TestClient(app, base_url="http://127.0.0.1"):
            container.shield_inbox.manager.connect()
            container.audit_engine.repository.count()
            assert container._shield_inbox_manager is not None
            assert container._audit_manager is not None
            assert container._shield_inbox_manager.active_connections > 0
            assert container._audit_manager.active_connections > 0
        assert container._shield_inbox_manager.active_connections == 0
        assert container._audit_manager.active_connections == 0


def test_request_id_is_bounded_and_safely_regenerated() -> None:
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        invalid = client.get("/api/v1/health", headers={"X-Request-ID": "bad id:" + "x" * 200})
        valid = client.get("/api/v1/health", headers={"X-Request-ID": "trace_123-safe"})

    generated = invalid.headers["x-request-id"]
    assert generated != "bad id:" + "x" * 200
    assert len(generated) == 32
    assert valid.headers["x-request-id"] == "trace_123-safe"


def test_path_controls_cannot_forge_log_or_audit_lines(
    caplog: pytest.LogCaptureFixture,
) -> None:
    records: list[dict[str, Any]] = []

    class Recorder:
        def record(self, **values: Any) -> None:
            records.append(values)

    app = FastAPI()
    app.state.container = type("Container", (), {"audit_engine": Recorder()})()
    scope = _scope()
    scope["app"] = app
    scope["path"] = "/api/v1/alerts\r\nforged\x00"
    scope["raw_path"] = b"/api/v1/alerts%0D%0Aforged%00"
    request = Request(scope)
    request.state.request_id = "trace_safe"

    async def call_next(_: Request) -> Response:
        return Response(status_code=204)

    caplog.set_level(logging.INFO, logger="edysiem.http")
    asyncio.run(HTTPLoggingMiddleware(app).dispatch(request, call_next))
    MutationAuditMiddleware._record(request, status_code=204, outcome="success")

    resource = records[0]["details"]["resource"]
    assert resource.startswith("/api/v1/alerts")
    assert not any(char in resource for char in "\r\n\x00")
    assert len(resource) <= 512
    assert resource in caplog.messages[0]
    messages = [record.getMessage() for record in caplog.records if record.name == "edysiem.http"]
    assert len(messages) == 1
    assert resource in messages[0]
    assert not any(char in messages[0] for char in "\r\n\x00")
    assert len(messages[0].splitlines()) == 1


def test_exception_audit_does_not_store_exception_or_headers() -> None:
    records: list[dict[str, Any]] = []

    class Recorder:
        def record(self, **values: Any) -> None:
            records.append(values)

    app = FastAPI()
    app.state.container = type("Container", (), {"audit_engine": Recorder()})()
    app.add_middleware(MutationAuditMiddleware)
    app.add_middleware(RequestIDMiddleware)

    @app.post("/api/boom")
    async def boom() -> None:
        raise RuntimeError("super-secret-value")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/boom",
            headers={"Authorization": "Bearer super-secret-value"},
        )

    assert response.status_code == 500
    assert len(records) == 1
    assert records[0]["current"] == "exception"
    assert "super-secret-value" not in repr(records[0])


def test_body_limit_handles_chunks_without_double_response_start() -> None:
    chunks = iter(
        [
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"56789", "more_body": False},
        ]
    )
    messages: list[Message] = []

    async def receive() -> Message:
        return next(chunks)

    async def consume(scope: Scope, receive: Receive, send: Send) -> None:
        await receive()
        await receive()

    async def send(message: Message) -> None:
        messages.append(message)

    middleware = RequestBodyLimitMiddleware(consume, max_body_bytes=8)
    asyncio.run(middleware(_scope(), receive, send))

    starts = [message for message in messages if message["type"] == "http.response.start"]
    assert len(starts) == 1
    assert starts[0]["status"] == 413


def test_body_limit_never_emits_second_start_after_response_started() -> None:
    chunks = iter(
        [
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"56789", "more_body": False},
        ]
    )
    messages: list[Message] = []

    async def receive() -> Message:
        return next(chunks)

    async def starts_early(scope: Scope, receive: Receive, send: Send) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await receive()
        await receive()

    async def send(message: Message) -> None:
        messages.append(message)

    middleware = RequestBodyLimitMiddleware(starts_early, max_body_bytes=8)
    with pytest.raises(PayloadTooLargeError):
        asyncio.run(middleware(_scope(), receive, send))

    starts = [message for message in messages if message["type"] == "http.response.start"]
    assert len(starts) == 1
    assert starts[0]["status"] == 200


def _scope(
    *,
    client: tuple[str, int] = ("testclient", 50000),
    host: bytes = b"127.0.0.1",
) -> Scope:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/test",
        "raw_path": b"/api/test",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", host)],
        "client": client,
        "server": ("127.0.0.1", 80),
    }


async def _empty_receive() -> Message:
    return {"type": "http.request", "body": b"", "more_body": False}
