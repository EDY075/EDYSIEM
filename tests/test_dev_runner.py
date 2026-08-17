"""Testes do runner de desenvolvimento (`edysiem dev` / `run.py`)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

import edysiem.cli.dev as dev

DEV_API_KEY = "dev-runner-test-key-with-at-least-32-bytes"


@pytest.fixture(autouse=True)
def operator_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDYSIEM_API_KEY", DEV_API_KEY)
    monkeypatch.setenv("EDYSIEM_API_IDENTITY", "dev-runner")
    monkeypatch.setenv("EDYSIEM_API_ROLE", "analyst")


class _FakeProc:
    pid = 12345

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
    calls: list[list[str]] = []

    def fake_run(cmd, **_kw):
        calls.append(cmd)
        return type("_R", (), {"returncode": 0})()

    monkeypatch.setattr(dev, "FRONTEND", d)
    monkeypatch.setattr(dev.subprocess, "run", fake_run)
    assert dev._ensure_frontend_deps() is True
    assert len(calls) == 1
    assert "ci" in " ".join(calls[0])


def test_ensure_backend_deps_present() -> None:
    assert dev._ensure_backend_deps() is True  # edysiem importável


def test_backend_dependency_check_fails_without_runtime(monkeypatch, capsys) -> None:
    real_find_spec = dev.importlib.util.find_spec

    def fake_find_spec(name: str):
        return None if name == "uvicorn" else real_find_spec(name)

    monkeypatch.setattr(dev.importlib.util, "find_spec", fake_find_spec)
    assert dev._ensure_backend_deps() is False
    assert "edy-siem[api]" in capsys.readouterr().out


def test_dotenv_loader_is_non_executable_and_does_not_override(monkeypatch, tmp_path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "EDYSIEM_API_KEY='safe literal $(whoami)'\nEDYSIEM_API_ROLE=analyst\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("EDYSIEM_API_KEY", raising=False)
    monkeypatch.setenv("EDYSIEM_API_ROLE", "viewer")
    assert dev._load_dotenv(dotenv) is True
    assert os.environ["EDYSIEM_API_KEY"] == "safe literal $(whoami)"
    assert os.environ["EDYSIEM_API_ROLE"] == "viewer"


def test_dotenv_loader_rejects_invalid_syntax(tmp_path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("NOT VALID\n", encoding="utf-8")
    assert dev._load_dotenv(dotenv) is False


def test_frontend_bind_is_always_loopback(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_popen(cmd, **_kwargs):
        calls.append(cmd)
        return _FakeProc()

    monkeypatch.setattr(dev.subprocess, "Popen", fake_popen)
    dev._start_frontend()
    assert "127.0.0.1" in calls[0][-1]
    assert "--strictPort" in calls[0][-1]


def test_run_dev_fails_closed_without_operator_configuration(monkeypatch) -> None:
    for name in ("EDYSIEM_API_KEY", "EDYSIEM_API_IDENTITY", "EDYSIEM_API_ROLE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(dev, "_load_dotenv", lambda path=None: True)
    assert dev.run_dev(seed=False, open_browser=False) == 1


def test_run_dev_rejects_lan_before_startup(monkeypatch, capsys) -> None:
    monkeypatch.setattr(dev, "_load_dotenv", lambda path=None: pytest.fail("must not load env"))
    assert dev.run_dev(seed=False, open_browser=False, lan=True) == 1
    assert "localhost" in capsys.readouterr().out


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
    monkeypatch.setattr(dev, "_start_backend", lambda reload: _FakeProc())
    monkeypatch.setattr(dev, "_start_frontend", lambda: _FakeProc())
    monkeypatch.setattr(dev, "_wait_url", lambda url, timeout=45: False)
    assert dev.run_dev(seed=True, open_browser=False) == 2


def test_run_dev_frontend_not_responding(monkeypatch) -> None:
    calls = {"n": 0}

    def wait(url: str, timeout: int = 45) -> bool:
        calls["n"] += 1
        return calls["n"] == 1  # backend ok, frontend não

    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: True)
    monkeypatch.setattr(dev, "_start_backend", lambda reload: _FakeProc())
    monkeypatch.setattr(dev, "_start_frontend", lambda: _FakeProc())
    monkeypatch.setattr(dev, "_wait_url", wait)
    assert dev.run_dev(seed=True, open_browser=False) == 3


def test_run_dev_happy_path(monkeypatch) -> None:
    state = {"seeded": False, "opened": ""}

    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: True)
    monkeypatch.setattr(dev, "_start_backend", lambda reload: _FakeProc())
    monkeypatch.setattr(dev, "_start_frontend", lambda: _FakeProc())
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
    assert state["opened"] == dev.FRONTEND_URL


def test_run_dev_watchdog_restarts_then_aborts(monkeypatch) -> None:
    """Watchdog reinicia com limite e aborta ao exceder (nao entra em loop infinito)."""

    class _Dead:
        pid = 9999

        def poll(self):
            return 0  # sempre "morto" -> forca o watchdog a reiniciar

    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: True)
    monkeypatch.setattr(dev, "_start_backend", lambda reload: _Dead())
    monkeypatch.setattr(dev, "_start_frontend", lambda: _Dead())
    monkeypatch.setattr(dev, "_wait_url", lambda url, timeout=45: True)
    monkeypatch.setattr(dev, "_seed", lambda: None)
    monkeypatch.setattr(dev.webbrowser, "open", lambda url: None)
    monkeypatch.setattr(dev.time, "sleep", lambda _s: None)  # acelera o watchdog

    assert dev.run_dev(seed=True, open_browser=False) == 4


def test_cli_dev_command(monkeypatch) -> None:
    from edysiem.cli import main

    calls: dict = {}

    def fake_run_dev(*, seed: bool, open_browser: bool, lan: bool) -> int:
        calls["seed"] = seed
        calls["open"] = open_browser
        calls["lan"] = lan
        return 1 if lan else 0

    monkeypatch.setattr(main, "run_dev", fake_run_dev)
    assert main.main(["dev"]) == 0
    assert calls == {"seed": True, "open": True, "lan": False}
    assert main.main(["dev", "--no-seed", "--no-open"]) == 0
    assert calls == {"seed": False, "open": False, "lan": False}
    assert main.main(["dev", "--lan"]) == 1
    assert calls == {"seed": True, "open": True, "lan": True}


def test_run_py_importable() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.isfile(os.path.join(root, "run.py"))
    assert os.path.isfile(os.path.join(root, "scripts", "dev.ps1"))
    assert os.path.isfile(os.path.join(root, "scripts", "dev.sh"))


def _load_run_module():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("edysiem_checkout_runner", root / "run.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_py_has_no_sys_path_bootstrap() -> None:
    source = (Path(__file__).resolve().parents[1] / "run.py").read_text(encoding="utf-8")
    assert "sys.path.insert" not in source
    assert 'pip", "install", "-e", ".[api]' in source


def test_run_py_installs_checkout_then_runs_fresh_interpreter(monkeypatch) -> None:
    runner = _load_run_module()
    calls: list[tuple[list[str], Path]] = []

    def fake_run(command, *, cwd, check):
        calls.append((command, cwd))
        return type("_Result", (), {"returncode": 0})()

    monkeypatch.setattr(runner, "_current_checkout_ready", lambda: False)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.sys, "argv", ["run.py", "--no-seed", "--no-open"])
    assert runner.main() == 0
    assert calls[0][0][-3:] == ["install", "-e", ".[api]"]
    assert calls[1][0][-3:] == ["dev", "--no-seed", "--no-open"]
    assert all(cwd == runner._ROOT for _, cwd in calls)


def test_run_py_rejects_lan_without_installing(monkeypatch, capsys) -> None:
    runner = _load_run_module()
    monkeypatch.setattr(
        runner, "_install_current_checkout", lambda: pytest.fail("must not install")
    )
    monkeypatch.setattr(runner.sys, "argv", ["run.py", "--lan"])
    assert runner.main() == 2
    assert "localhost" in capsys.readouterr().out


def test_frontend_installer_is_repo_relative_and_reproducible() -> None:
    root = Path(__file__).resolve().parents[1]
    script = (root / "scripts" / "install-frontend.ps1").read_text(encoding="utf-8")
    assert "$PSScriptRoot" in script
    assert "npm ci" in script
    assert "C:\\Users\\user" not in script


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


def test_terminate_tree_posix(monkeypatch) -> None:
    monkeypatch.setattr(dev.os, "name", "posix")

    class _P:
        pid = 1

        def poll(self):
            return None

        def terminate(self) -> None:
            self.done = True

        def wait(self, timeout=None) -> int:
            return 0

    p = _P()
    dev._terminate_tree(p)
    assert getattr(p, "done", False) is True
    dev._terminate_tree(None)  # no-op


def test_watchdog_restart_once_succeeds(monkeypatch) -> None:
    """Watchdog reinicia uma vez (sem abortar) e segue até Ctrl-C -> 0."""

    class _Seq:
        pid = 7

        def __init__(self) -> None:
            self.n = 0

        def poll(self):
            self.n += 1
            return 0 if self.n == 1 else None  # morre 1x, depois vive

    procs = {"b": _Seq(), "f": _FakeProc()}

    def _mk_backend(reload):
        procs["b"] = _Seq()
        return procs["b"]

    monkeypatch.setattr(dev, "_ensure_backend_deps", lambda: True)
    monkeypatch.setattr(dev, "_ensure_frontend_deps", lambda: True)
    monkeypatch.setattr(dev, "_start_backend", _mk_backend)
    monkeypatch.setattr(dev, "_start_frontend", lambda: procs["f"])
    monkeypatch.setattr(dev, "_wait_url", lambda url, timeout=45: True)
    monkeypatch.setattr(dev, "_seed", lambda: None)
    monkeypatch.setattr(dev.webbrowser, "open", lambda url: None)

    state = {"n": 0}

    def _sleep(_s: float) -> None:
        state["n"] += 1
        if state["n"] >= 3:
            raise KeyboardInterrupt

    monkeypatch.setattr(dev.time, "sleep", _sleep)
    assert dev.run_dev(seed=True, open_browser=False) == 0
