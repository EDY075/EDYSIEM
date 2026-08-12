"""Testes de segurança da API: API Key, RBAC e Rate Limit (Sprint Final)."""

from __future__ import annotations

import asyncio

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import edysiem.api.security as sec
from edysiem.api.app import create_app


def _app_with_dep(dep) -> FastAPI:
    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(dep)])
    def ping():
        return {"ok": True}

    return app


def test_api_key_opt_in_enforced(monkeypatch) -> None:
    monkeypatch.setenv("EDYSIEM_API_KEY", "sekret")
    client = TestClient(_app_with_dep(sec.require_api_key))
    assert client.get("/ping").status_code == 401
    assert client.get("/ping", headers={"X-API-Key": "errada"}).status_code == 401
    assert client.get("/ping", headers={"X-API-Key": "sekret"}).status_code == 200


def test_api_key_off_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("EDYSIEM_API_KEY", raising=False)
    client = TestClient(_app_with_dep(sec.require_api_key))
    assert client.get("/ping").status_code == 200


def test_api_key_app_wiring(monkeypatch) -> None:
    monkeypatch.setenv("EDYSIEM_API_KEY", "sekret")
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/health").status_code == 401
        assert client.get("/api/v1/health", headers={"X-API-Key": "sekret"}).status_code == 200


def test_rbac_permission(monkeypatch) -> None:
    app = FastAPI()

    @app.post("/w", dependencies=[Depends(sec.require_permission("case:write"))])
    def w():
        return {"ok": True}

    client = TestClient(app)
    assert client.post("/w", headers={"X-EDY-Role": "viewer"}).status_code == 403
    assert client.post("/w", headers={"X-EDY-Role": "desconhecida"}).status_code == 403
    assert client.post("/w").status_code == 200  # default admin
    assert client.post("/w", headers={"X-EDY-Role": "analyst"}).status_code == 200


def test_rbac_on_real_route(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EDYSIEM_DB", str(tmp_path / "soc.db"))
    with TestClient(create_app()) as client:
        # viewer não pode habilitar regra (rule:write)
        r = client.post(
            "/api/v1/soc/rules/brute-force-ssh/enable", headers={"X-EDY-Role": "viewer"}
        )
        assert r.status_code == 403
        # admin (default) pode chamar (regra não existe -> 404, mas passa a permissão)
        assert client.post("/api/v1/soc/rules/brute-force-ssh/enable").status_code == 404


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
    assert "case:write" in sec.PERMISSIONS[sec.ROLE_ANALYST]
    assert "case:write" not in sec.PERMISSIONS[sec.ROLE_VIEWER]
    assert "alert:read" in sec.PERMISSIONS[sec.ROLE_VIEWER]
