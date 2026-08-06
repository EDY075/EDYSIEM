"""Testes do runner de desenvolvimento (`edysiem dev` / `run.py`)."""

from __future__ import annotations

import os
from pathlib import Path

import edysiem.cli.dev as dev


class _FakeProc:
    def poll(self) -> None:
        return None

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout: float | None = None) -> int:
        return 0


def test_node_argv_windows(monkeypatch) -> None:
    monkeypatch.setattr(dev.os, "name", "nt")
    argv = dev._node_argv(["npm", "install"])
    assert argv[0] == "cmd"
    assert argv[1] == "/c"
    assert argv[2] == "npm install"


def test_node_argv_posix(monkeypatch) -> None:
    monkeypatch.setattr(dev.os, "name", "posix")
    assert dev._node_argv(["npm", "install"]) == ["npm", "install"]


def test_ensure_frontend_deps_present(monkeypatch) -> None:
    import tempfile

    d = Path(tempfile.mkdtemp())
    (d / "node_modules").mkdir()
    monkeypatch.setattr(dev, "FRONTEND", d)
    assert dev._ensure_frontend_deps() is True


def test_ensure_frontend_deps_install(monkeypatch) -> None:
    import tempfile

    d = Path(tempfile.mkdtemp())  # sem node_modules
    calls = {"n": 0}

    def fake_run(_cmd, **_kw):
        calls["n"] += 1
        return type("_R", (), {"returncode": 0})()

    monkeypatch.setattr(dev, "FRONTEND", d)
    monkeypatch.setattr(dev.subprocess, "run", fake_run)
    assert dev._ensure_frontend_deps() is True
    assert calls["n"] == 1


def test_ensure_backend_deps_present() -> None:
    assert dev._ensure_backend_deps() is True  # edysiem importável


def test_wait_url_false_fast() -> None:
    # porta sem serviço -> False rapidamente (timeout 1s)
    assert dev._wait_url("http://127.0.0.1:1/health", timeout=1) is False


def test_run_dev_backend_deps_fail(monkeypatch) -> None:
    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: False)
    assert dev.run_dev(seed=True, open_browser=False) == 1


def test_run_dev_frontend_deps_fail(monkeypatch) -> None:
    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: False)
    assert dev.run_dev(seed=True, open_browser=False) == 1


def test_run_dev_backend_not_responding(monkeypatch) -> None:
    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: True)
    monkeypatch.setattr(dev, "_start_dev_server", lambda: (_FakeProc(), _FakeProc()))
    monkeypatch.setattr(dev, "_wait_url", lambda url, timeout=45: False)
    assert dev.run_dev(seed=True, open_browser=False) == 2


def test_run_dev_frontend_not_responding(monkeypatch) -> None:
    calls = {"n": 0}

    def wait(url: str, timeout: int = 45) -> bool:
        calls["n"] += 1
        return calls["n"] == 1  # backend ok, frontend não

    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: True)
    monkeypatch.setattr(dev, "_start_dev_server", lambda: (_FakeProc(), _FakeProc()))
    monkeypatch.setattr(dev, "_wait_url", wait)
    assert dev.run_dev(seed=True, open_browser=False) == 3


def test_run_dev_happy_path(monkeypatch) -> None:
    state = {"seeded": False, "terminated": 0, "opened": ""}

    class _Proc:
        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            state["terminated"] += 1

        def wait(self, timeout: float | None = None) -> int:
            return 0

    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: True)
    monkeypatch.setattr(dev, "_start_dev_server", lambda: (_Proc(), _Proc()))
    monkeypatch.setattr(dev, "_wait_url", lambda url, timeout=45: True)
    monkeypatch.setattr(dev, "_seed", lambda: state.update(seeded=True))

    def _open(url: str) -> None:
        state["opened"] = url

    def _sleep(_s: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(dev.webbrowser, "open", _open)
    monkeypatch.setattr(dev.time, "sleep", _sleep)

    assert dev.run_dev(seed=True, open_browser=True) == 0
    assert state["seeded"] is True
    assert state["terminated"] == 2
    assert state["opened"] == dev.FRONTEND_URL


def test_cli_dev_command(monkeypatch) -> None:
    from edysiem.cli import main

    calls: dict = {}

    def fake_run_dev(*, seed: bool, open_browser: bool) -> int:
        calls["seed"] = seed
        calls["open"] = open_browser
        return 0

    monkeypatch.setattr(main, "run_dev", fake_run_dev)
    assert main.main(["dev"]) == 0
    assert calls == {"seed": True, "open": True}
    assert main.main(["dev", "--no-seed", "--no-open"]) == 0
    assert calls == {"seed": False, "open": False}


def test_run_py_importable() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.isfile(os.path.join(root, "run.py"))
    assert os.path.isfile(os.path.join(root, "scripts", "dev.ps1"))
    assert os.path.isfile(os.path.join(root, "scripts", "dev.sh"))


def test_dev_log_prints(capsys) -> None:
    dev._log("msg-teste")
    captured = capsys.readouterr()
    assert "msg-teste" in captured.out


def test_seed_posts(monkeypatch) -> None:
    posts: list[str] = []

    class _Resp:
        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *exc) -> None:
            return None

    def fake_urlopen(req, timeout=20):
        posts.append(req.full_url)
        return _Resp()

    monkeypatch.setattr(dev.urllib.request, "urlopen", fake_urlopen)
    dev._seed()
    assert len(posts) >= 5  # demo + rules + iocs + assets


def test_npm_invokes_popen(monkeypatch) -> None:
    state = {"p": 0}

    class _P:
        def __init__(self, *args, **kwargs) -> None:
            state["p"] += 1

    monkeypatch.setattr(dev.subprocess, "Popen", _P)
    monkeypatch.setattr(dev, "FRONTEND", Path("."))
    dev._npm(["npm", "run", "dev", "--", "--host"])
    assert state["p"] == 1
