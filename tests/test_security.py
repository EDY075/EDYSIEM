"""Security regression tests for fail-closed auth, RBAC and rate limits."""

from __future__ import annotations

import asyncio

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import edysiem.api.security as sec
from edysiem.api.app import create_app

API_KEY = "security-test-key-with-at-least-32-random-bytes"


def _configure(monkeypatch, *, role: str = "analyst", identity: str = "analyst-01") -> None:
    monkeypatch.setenv("EDYSIEM_API_KEY", API_KEY)
    monkeypatch.setenv("EDYSIEM_API_IDENTITY", identity)
    monkeypatch.setenv("EDYSIEM_API_ROLE", role)


def _clear(monkeypatch) -> None:
    for name in ("EDYSIEM_API_KEY", "EDYSIEM_API_IDENTITY", "EDYSIEM_API_ROLE"):
        monkeypatch.delenv(name, raising=False)


def _app_with_dep(dep) -> FastAPI:
    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(dep)])
    def ping():
        return {"ok": True}

    return app


def test_api_key_is_fail_closed_when_unset(monkeypatch) -> None:
    _clear(monkeypatch)
    client = TestClient(_app_with_dep(sec.require_api_key))
    assert client.get("/ping").status_code == 503


def test_api_key_rejects_partial_or_placeholder_configuration(monkeypatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("EDYSIEM_API_KEY", API_KEY)
    assert TestClient(_app_with_dep(sec.require_api_key)).get("/ping").status_code == 503


def test_invalid_server_role_and_identity_are_never_accepted(monkeypatch) -> None:
    _configure(monkeypatch, role="root", identity="invalid identity")
    assert sec.operator_auth_configured() is False
    assert sec._is_loopback(None) is False
    assert sec._is_loopback("localhost") is True

    monkeypatch.setenv("EDYSIEM_API_IDENTITY", "operator")
    monkeypatch.setenv("EDYSIEM_API_ROLE", "admin")
    monkeypatch.setenv("EDYSIEM_API_KEY", "replace-with-a-random-secret-of-at-least-32-bytes")
    assert TestClient(_app_with_dep(sec.require_api_key)).get("/ping").status_code == 503


def test_api_key_enforced_with_server_side_identity(monkeypatch) -> None:
    _configure(monkeypatch)
    client = TestClient(_app_with_dep(sec.require_api_key))
    assert client.get("/ping").status_code == 401
    assert client.get("/ping", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/ping", headers={"X-API-Key": API_KEY}).status_code == 200
    assert sec.operator_auth_configured() is True


def test_health_is_public_but_operational_data_is_protected(monkeypatch, tmp_path) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "security.db"))
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/version").status_code == 200
        assert client.get("/api/v1/metrics").status_code == 503

    _configure(monkeypatch)
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/metrics").status_code == 401
        assert client.get("/api/v1/metrics", headers={"X-API-Key": API_KEY}).status_code == 200


def test_identity_endpoint_returns_server_binding_not_role_header(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, role="viewer", identity="viewer-01")
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "identity.db"))
    with TestClient(create_app()) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": API_KEY, "X-EDY-Role": "admin"},
        )
    assert response.status_code == 200
    assert response.json() == {"identity": "viewer-01", "role": "viewer", "auth_type": "api_key"}


def test_rbac_cannot_be_elevated_by_caller_header(monkeypatch) -> None:
    app = FastAPI()

    @app.post("/write", dependencies=[Depends(sec.require_permission("case:write"))])
    def write():
        return {"ok": True}

    _configure(monkeypatch, role="viewer")
    client = TestClient(app)
    denied = client.post("/write", headers={"X-API-Key": API_KEY, "X-EDY-Role": "admin"})
    assert denied.status_code == 403

    _configure(monkeypatch, role="analyst")
    assert client.post("/write", headers={"X-API-Key": API_KEY}).status_code == 200


def test_rbac_on_real_mutating_route(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    _configure(monkeypatch, role="viewer")
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/soc/rules/brute-force-ssh/enable",
            headers={"X-API-Key": API_KEY, "X-EDY-Role": "admin"},
        )
        assert response.status_code == 403

    _configure(monkeypatch, role="analyst")
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/soc/rules/brute-force-ssh/enable", headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 404


def test_rate_limit_429() -> None:
    async def go() -> tuple[int, str | None]:
        dep = sec.rate_limit(max_requests=2, window_seconds=60)

        class _Req:
            client = None

        req = _Req()
        await dep(req)
        await dep(req)
        try:
            await dep(req)
        except Exception as exc:
            return getattr(exc, "status_code", 0), getattr(exc, "headers", {}).get("Retry-After")
        return 0, None

    assert asyncio.run(go()) == (429, "60")


def test_permissions_matrix() -> None:
    assert "*" in sec.PERMISSIONS[sec.ROLE_ADMIN]
    assert "pipeline:write" in sec.PERMISSIONS[sec.ROLE_ANALYST]
    assert "case:write" not in sec.PERMISSIONS[sec.ROLE_VIEWER]
    assert "alert:read" in sec.PERMISSIONS[sec.ROLE_VIEWER]
