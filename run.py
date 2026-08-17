#!/usr/bin/env python3
"""Ponto único de execução do EDY SIEM.

Um único comando prepara o checkout local pelo extra ``api`` e inicia backend
+ frontend somente em loopback. O bootstrap não importa código por caminhos
adicionados manualmente ao ``sys.path``.

Uso:
    python run.py                 # ambiente dev + dados de demonstração
    python run.py --no-seed       # sem dados de demonstração
    python run.py --no-open       # não abre o navegador automaticamente
    python run.py --lan           # recusado no EDYSIEM 0.3.0 (localhost-only)
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_PACKAGE_ROOT = (_ROOT / "src" / "edysiem").resolve()
_API_MODULES = ("fastapi", "pydantic", "uvicorn")


def _module_origin(module: str) -> Path | None:
    """Return the resolved module origin without importing project code."""

    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None:
        return None
    try:
        return Path(spec.origin).resolve()
    except OSError:
        return None


def _current_checkout_ready() -> bool:
    """Return whether this checkout and its API runtime are importable."""

    origin = _module_origin("edysiem")
    if origin is None or not origin.is_relative_to(_PACKAGE_ROOT):
        return False
    return all(importlib.util.find_spec(module) is not None for module in _API_MODULES)


def _install_current_checkout() -> bool:
    """Install this checkout with the API extra using pip's normal build flow."""

    print("  [bootstrap] preparando checkout local com `pip install -e .[api]` ...", flush=True)
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", ".[api]"],
        cwd=_ROOT,
        check=False,
    )
    return completed.returncode == 0


def _run_installed(argv: list[str]) -> int:
    """Run the installed checkout in a fresh interpreter."""

    completed = subprocess.run(  # noqa: S603 - fixed interpreter/module, no shell
        [sys.executable, "-m", "edysiem.cli.main", "dev", *argv],
        cwd=_ROOT,
        check=False,
    )
    return completed.returncode


def main() -> int:
    argv = sys.argv[1:]
    if "--lan" in argv:
        print(
            "  [bootstrap] --lan está bloqueado no EDYSIEM 0.3.0; "
            "esta versão aceita somente localhost.",
            flush=True,
        )
        return 2
    if not _current_checkout_ready() and not _install_current_checkout():
        print("  [bootstrap] falha ao instalar o checkout local com o extra api", flush=True)
        return 1
    return _run_installed(argv)


if __name__ == "__main__":
    raise SystemExit(main())
