"""Runner de desenvolvimento: inicia backend + frontend com um único comando.

Usado pelo CLI (``edysiem dev``) e pelo ``run.py`` da raiz. Responsável por:
- verificar/instalar dependências (backend + frontend)
- criar banco + aplicar migrações
- iniciar backend (uvicorn) e frontend (vite)
- (opcional) popular dados de demonstração no ``/soc``
- abrir http://localhost:5173 e exibir logs claros

Frontend (npm) é invocado via ``cmd /c`` no Windows — nunca via ``shell=True``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]  # repo root (src/edysiem/cli/dev.py -> EDYSIEM)
FRONTEND = ROOT / "frontend"
INSTANCE = ROOT / "instance"
BACKEND_URL = "http://127.0.0.1:8080"
FRONTEND_URL = "http://localhost:5173"


def _log(msg: str) -> None:
    print(f"  [dev] {msg}", flush=True)


def _node_argv(args: list[str]) -> list[str]:
    """Retorna argv para o subprocess usando `cmd /c` no Windows (sem shell=True)."""
    if os.name == "nt":
        return ["cmd", "/c", subprocess.list2cmdline(args)]
    return args


def _ensure_backend_deps() -> bool:
    try:
        import edysiem  # noqa: F401

        return True
    except ImportError:
        _log("backend não instalado; instalando `pip install -e .[dev]` ...")
        ok = subprocess.run(
            _node_argv_py([sys.executable, "-m", "pip", "install", "-e", ".[dev]", "-q"]),
            cwd=ROOT,
        )
        return ok.returncode == 0


def _node_argv_py(args: list[str]) -> list[str]:
    return args  # pip/python sempre direto, sem shell


def _ensure_frontend_deps() -> bool:
    if (FRONTEND / "node_modules").exists():
        return True
    _log("node_modules ausente; executando `npm install` ...")
    return subprocess.run(_node_argv(["npm", "install"]), cwd=FRONTEND).returncode == 0


def _npm(argv: list[str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(_node_argv(argv), cwd=FRONTEND)


def _start_dev_server() -> tuple[subprocess.Popen[bytes], subprocess.Popen[bytes]]:
    env = {**os.environ, "EDYSIEM_DB": str(INSTANCE / "edysiem.db")}
    backend = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "edysiem.api.app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            "8080",
        ],
        cwd=ROOT,
        env=env,
    )
    frontend = _npm(["npm", "run", "dev", "--", "--host"])
    return backend, frontend


def _wait_url(url: str, timeout: int = 45) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except Exception:
            time.sleep(1)
    return False


def _seed() -> None:
    import json

    _log("populando dados de demonstração em /soc ...")
    base = BACKEND_URL + "/api/v1"

    def post(path: str, body: dict[str, Any] | None = None) -> None:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            base + path, data=data, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=20)

    post("/soc/pipeline/demo", None)
    post(
        "/soc/rules",
        {
            "rule_id": "brute-force-ssh",
            "name": "Brute Force SSH",
            "severity": "critical",
            "category": "authentication",
            "mitre": ["T1110"],
            "tags": ["brute-force"],
        },
    )
    post(
        "/soc/rules",
        {
            "rule_id": "malware-exec",
            "name": "Malware Execution",
            "severity": "high",
            "category": "execution",
            "mitre": ["T1059"],
            "tags": ["malware"],
        },
    )
    post("/soc/iocs", {"value": "185.220.101.4", "ioc_type": "ip", "reputation": "malicious"})
    post(
        "/soc/assets",
        {"hostname": "web-01", "ip": "10.0.0.5", "os": "Linux", "criticality": "critical"},
    )
    _log("demonstração criada (alertas, incidente, caso, regras, IOC, asset)")


def run_dev(*, seed: bool = True, open_browser: bool = True) -> int:
    """Inicia backend + frontend e bloqueia até Ctrl-C.

    Returns:
        0 sucesso; 1 falha de dependência; 2 backend não subiu; 3 frontend não subiu.
    """
    if not _ensure_backend_deps():
        print("  [dev] falha ao instalar dependências do backend")
        return 1
    if not _ensure_frontend_deps():
        print("  [dev] falha ao instalar dependências do frontend")
        return 1

    INSTANCE.mkdir(exist_ok=True)
    (INSTANCE / ".gitkeep").touch(exist_ok=True)

    _log("iniciando backend (uvicorn) em http://127.0.0.1:8080")
    backend, frontend = _start_dev_server()

    if not _wait_url(BACKEND_URL + "/api/v1/health"):
        _cleanup(backend, frontend)
        print("  [dev] backend não respondeu a tempo")
        return 2
    _log("backend online")
    if not _wait_url(FRONTEND_URL):
        _cleanup(backend, frontend)
        print("  [dev] frontend não respondeu a tempo; confira a porta 5173")
        return 3
    _log("frontend online")

    if seed:
        _seed()

    _log("pronto! -> frontend http://localhost:5173  (API http://127.0.0.1:8080)")
    if open_browser:
        webbrowser.open(FRONTEND_URL)

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n  [dev] encerrando...")
    finally:
        _cleanup(backend, frontend)
    return 0


def _cleanup(*procs: subprocess.Popen[bytes] | None) -> None:
    """Encerra processos de forma segura (obrigatório no erro ou no Ctrl-C)."""
    for proc in procs:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


__all__ = ["run_dev"]
