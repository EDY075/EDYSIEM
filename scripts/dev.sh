#!/usr/bin/env bash
# EDY SIEM — inicia o ambiente de desenvolvimento com um comando.
set -e
cd "$(dirname "$0")/.."
exec python run.py "$@"