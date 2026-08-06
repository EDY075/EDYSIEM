#!/usr/bin/env python3
"""Ponto único de execução do EDY SIEM.

Um único comando inicia backend + frontend, cria o banco, aplica migrações e
(opcional) popula dados de demonstração — e abre o navegador em
http://localhost:5173 (Swagger em http://127.0.0.1:8080/docs).

Uso:
    python run.py                 # ambiente dev + dados de demonstração
    python run.py --no-seed       # sem dados de demonstração
    python run.py --no-open       # não abre o navegador automaticamente
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Permite rodar a partir de um clone sem `pip install -e .`
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "src"))

from edysiem.cli.dev import run_dev  # noqa: E402


def main() -> int:
    argv = sys.argv[1:]
    seed = "--no-seed" not in argv
    open_browser = "--no-open" not in argv
    return run_dev(seed=seed, open_browser=open_browser)


if __name__ == "__main__":
    raise SystemExit(main())