"""Testes do CLI Enterprise."""

from __future__ import annotations

import json

from edysiem.cli.main import build_parser, main


def _run(*args: str) -> tuple[int, dict]:
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    code = 0
    with redirect_stdout(buf):
        code = main(list(args))
    out = buf.getvalue().strip()
    try:
        return code, json.loads(out)
    except json.JSONDecodeError:
        return code, {"raw": out}


def test_cli_version() -> None:
    code, data = _run("version")
    assert code == 0
    assert data["version"] == "0.2.0"


def test_cli_health() -> None:
    code, data = _run("health")
    assert code == 0
    assert "components" in data


def test_cli_validate_config() -> None:
    code, data = _run("validate-config")
    assert code == 0
    assert data["valid"] is True


def test_cli_demo() -> None:
    code, data = _run("demo")
    assert code == 0
    assert data["demo"] is True
    assert data["category"] == "auth"


def test_cli_ingest() -> None:
    code, data = _run(
        "ingest",
        "<134>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - Failed password for admin",
    )
    assert code == 0
    assert "parsed" in data
    assert data["canonical"]["category"] == "auth"


def test_cli_run_pipeline() -> None:
    code, data = _run("run-pipeline")
    assert code == 0
    assert data["event_id"]


def test_cli_parser_help() -> None:
    parser = build_parser()
    # lista os subcomandos
    assert parser._subparsers is not None


def test_cli_unknown_command() -> None:
    import io
    from contextlib import redirect_stderr

    err = io.StringIO()
    with redirect_stderr(err):
        code = main(["nao-existe"])
    assert code == 2
