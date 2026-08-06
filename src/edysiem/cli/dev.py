"""Runner de desenvolvimento: inicia backend + frontend com um único comando.

Usado pelo CLI (``edysiem dev`` / ``edysiem run-dev``) e pelo ``run.py``.

Responsabilidades:
- verificar/instalar dependências (backend + frontend)
- criar banco + aplicar migrações
- iniciar backend (uvicorn, ``--reload``) e frontend (vite, HMR)
- abrir o navegador UMA única vez na URL final
- watchdog: reinicia um serviço que cair (com limite, sem loop infinito)
- seed opcional em /soc
- logs claros + cleanup obrigatório no erro

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
MAX_RESTARTS = 3  # limite por serviço (evita loop infinito)


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
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]", "-q"], cwd=ROOT
        )
        return ok.returncode == 0


def _ensure_frontend_deps() -> bool:
    if (FRONTEND / "node_modules").exists():
        return True
    _log("node_modules ausente; executando `npm install` (1 tentativa) ...")
    ok = subprocess.run(_node_argv(["npm", "install"]), cwd=FRONTEND)
    return ok.returncode == 0


def _start_backend(reload: bool) -> subprocess.Popen[bytes]:
    env = {**os.environ, "EDYSIEM_DB": str(INSTANCE / "edysiem.db")}
    args = [
        sys.executable,
        "-m",
        "uvicorn",
        "edysiem.api.app:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
    ]
    if reload:
        args.append("--reload")
    return subprocess.Popen(args, cwd=ROOT, env=env)


def _start_frontend() -> subprocess.Popen[bytes]:
    return subprocess.Popen(_node_argv(["npm", "run", "dev", "--", "--host"]), cwd=FRONTEND)


def _wait_url(url: str, timeout: int = 45) -> bool:
    """Espera (tempo limitado) por um serviço. 1 tentativa por serviço."""
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
            base + path, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            urllib.request.urlopen(req, timeout=20)
        except Exception as exc:  # noqa: BLE001
            _log(f"aviso: seed {path} falhou (não fatal): {exc}")

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


def _terminate_tree(proc: subprocess.Popen[bytes] | None) -> None:
    """Encerra o processo (e a árvore no Windows) de forma segura."""
    if proc is None or proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            check=False,
        )
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def run_dev(
    *,
    seed: bool = True,
    open_browser: bool = True,
    reload: bool = True,
    max_restarts: int = MAX_RESTARTS,
) -> int:
    """Inicia backend + frontend (com reload/watchdog) e bloqueia até Ctrl-C.

    Returns:
        0 sucesso; 1 dependência; 2 backend não subiu; 3 frontend não subiu;
        4 serviço reiniciou além do limite (aborta).
    """
    if not _ensure_backend_deps():
        print("  [dev] falha ao instalar dependências do backend")
        return 1
    if not _ensure_frontend_deps():
        print("  [dev] falha ao instalar dependências do frontend")
        return 1

    INSTANCE.mkdir(exist_ok=True)

    _log("iniciando backend (uvicorn --reload) em http://127.0.0.1:8080")
    backend = _start_backend(reload)
    _log("iniciando frontend (vite HMR) em http://localhost:5173")
    frontend = _start_frontend()

    if not _wait_url(BACKEND_URL + "/api/v1/health"):
        _terminate_tree(backend)
        _terminate_tree(frontend)
        print("  [dev] backend não respondeu a tempo")
        return 2
    _log("backend online")
    if not _wait_url(FRONTEND_URL):
        _terminate_tree(backend)
        _terminate_tree(frontend)
        print("  [dev] frontend não respondeu a tempo; confira a porta 5173")
        return 3
    _log("frontend online")

    if seed:
        try:
            _seed()
        except Exception as exc:  # noqa: BLE001
            _log(f"seed falhou (não fatal): {exc}")

    if open_browser:
        _log(f"abrindo o navegador em {FRONTEND_URL} (uma vez)")
        webbrowser.open(FRONTEND_URL)
    _log(f"pronto! -> {FRONTEND_URL}  (API/Swagger {BACKEND_URL}/docs)")

    restarts: dict[str, int] = {"backend": 0, "frontend": 0}

    def _restart(service: str) -> bool:
        nonlocal backend, frontend
        restarts[service] += 1
        if restarts[service] > max_restarts:
            print(
                f"  [dev] '{service}' reiniciou além do limite ({max_restarts}x); abortando.",
                flush=True,
            )
            return False
        _log(f"'{service}' caiu; reiniciando ({restarts[service]}/{max_restarts})...")
        time.sleep(2)  # backoff curto
        if service == "backend":
            backend = _start_backend(reload)
        else:
            frontend = _start_frontend()
        return True

    try:
        while True:
            time.sleep(2)
            if backend.poll() is not None and not _restart("backend"):
                break
            if frontend.poll() is not None and not _restart("frontend"):
                break
    except KeyboardInterrupt:
        print("\n  [dev] encerrando...")
    finally:
        _terminate_tree(backend)
        _terminate_tree(frontend)

    if restarts["backend"] > max_restarts or restarts["frontend"] > max_restarts:
        return 4
    return 0


__all__ = ["run_dev"]
