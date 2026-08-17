"""CLI Enterprise do EDY SIEM.

Comandos:
- edysiem health
- edysiem version
- edysiem config
- edysiem validate-config
- edysiem run-pipeline
- edysiem ingest
- edysiem demo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from typing import Any

from ..bootstrap import build_container, version
from ..domain import RawEvent
from ..parsers import parse_rfc5424, parse_syslog
from ..soc import SocPipeline, SocService
from .dev import run_dev


def _print(data: Any) -> None:
    """Imprime JSON no stdout (saida canonica do CLI)."""
    print(json.dumps(data, ensure_ascii=False, default=str))


def cmd_version(_args: argparse.Namespace) -> int:
    """Exibe a versao da plataforma."""
    _print({"name": "edysiem", "version": version()})
    return 0


def cmd_health(_args: argparse.Namespace) -> int:
    """Exibe o estado de saude dos engines."""
    container = build_container()
    loop = asyncio.new_event_loop()

    async def check() -> dict[str, str]:
        await container.enrichment.initialize()
        await container.correlation.initialize()
        await container.detection.rule_engine.initialize()
        return {
            "enrichment": (await container.enrichment.health_check())["engine"],
            "correlation": (await container.correlation.health_check())["engine"],
            "detection": (await container.detection.rule_engine.health_check())["engine"],
            "alerts": "online",
            "incidents": "online",
            "cases": "online",
        }

    health = loop.run_until_complete(check())
    loop.close()
    _print(
        {
            "status": "healthy" if all(v == "online" for v in health.values()) else "degraded",
            "components": health,
        }
    )
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Exibe a configuracao carregada."""
    container = build_container()
    cfg = container.config
    _print(
        {
            "name": cfg.project_name,
            "version": cfg.version,
            "environment": cfg.environment.value,
            "app": {"host": cfg.app.host, "port": cfg.app.port, "debug": cfg.app.debug},
            "logging": {"level": cfg.logging.level, "json": cfg.logging.json},
        }
    )
    return 0


def cmd_validate_config(_args: argparse.Namespace) -> int:
    """Valida a configuracao; exit 0 se valida, 1 se invalida."""
    from ..config import load
    from ..result import Failure

    result = load()
    if not isinstance(result, Failure):
        _print({"valid": True, "environment": result.unwrap().environment.value})
        return 0
    _print({"valid": False, "error": result.error.message})
    return 1


async def _run_pipeline(source_type: str, source_host: str, payload: str) -> dict[str, object]:
    """Executa a pipeline ponta a ponta."""
    from ..bootstrap import build_container
    from ..domain import CanonicalEvent, ParsedEvent

    container = build_container()
    await container.enrichment.initialize()
    await container.correlation.initialize()
    await container.detection.rule_engine.initialize()

    raw = RawEvent(source_type=source_type, source_host=source_host, raw_payload=payload)
    from ..result import Failure

    result = parse_rfc5424(raw)
    if isinstance(result, Failure):
        result = parse_syslog(raw)
    if isinstance(result, Failure):
        return {"error": result.error.message}

    fields = result.unwrap()
    parsed = ParsedEvent(
        event_id=raw.event_id,
        timestamp=raw.received_at,
        source_type=raw.source_type,
        source_host=raw.source_host,
        event_category=str(fields.get("event_category", "system")),
        event_action=str(fields.get("event_action", "info")),
        fields=fields,
        raw=raw.raw_payload,
        trace_id=raw.event_id,
    )
    canonical: CanonicalEvent = container.normalizer.normalize(parsed).unwrap()
    enriched = (await container.enrichment.enrich(canonical)).unwrap()
    correlated = await container.correlation.process(enriched)
    outcome = await container.detection.process(correlated)

    await container.enrichment.shutdown()
    await container.correlation.shutdown()
    await container.detection.rule_engine.shutdown()

    return {
        "event_id": canonical.event_id,
        "category": canonical.event_category or "system",
        "action": canonical.event_action or "info",
        "severity": canonical.severity.value,
        "correlated_matches": len(correlated.matches),
        "detected_rule_ids": list(outcome.detected_rule_ids),
        "finding_count": len(outcome.findings),
    }


def cmd_run_pipeline(args: argparse.Namespace) -> int:
    """Executa a pipeline com um payload de exemplo ou fornecido."""
    payload = args.payload or (
        "<134>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - Failed password for admin"
    )
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(_run_pipeline(args.source_type, args.source_host, payload))
    loop.close()
    _print(result)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """Ingere um payload bruto e mostra o resultado do parse+normalize."""
    from ..bootstrap import build_container
    from ..domain import ParsedEvent

    container = build_container()
    raw = RawEvent(
        source_type=args.source_type, source_host=args.source_host, raw_payload=args.payload
    )
    from ..result import Failure

    result = parse_rfc5424(raw)
    if isinstance(result, Failure):
        result = parse_syslog(raw)
    if isinstance(result, Failure):
        _print({"error": result.error.message})
        return 1

    fields = result.unwrap()
    parsed = ParsedEvent(
        event_id=raw.event_id,
        timestamp=raw.received_at,
        source_type=raw.source_type,
        source_host=raw.source_host,
        event_category=str(fields.get("event_category", "system")),
        event_action=str(fields.get("event_action", "info")),
        fields=fields,
        raw=raw.raw_payload,
        trace_id=raw.event_id,
    )
    normalized = container.normalizer.normalize(parsed).unwrap()
    _print(
        {
            "parsed": fields,
            "canonical": {
                "category": normalized.event_category,
                "action": normalized.event_action,
                "severity": normalized.severity.value,
            },
        }
    )
    return 0


def cmd_demo(_args: argparse.Namespace) -> int:
    """Executa uma demo da pipeline com um evento syslog de exemplo."""
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(
        _run_pipeline(
            "syslog",
            "wks-01",
            "<134>1 2026-08-03T12:00:00.000Z wks-01 sshd - - - Failed password for admin",
        )
    )
    loop.close()
    _print({"demo": True, **result})
    return 0


def cmd_soc_run(_args: argparse.Namespace) -> int:
    """Executa o fluxo SOC E2E de demonstração (alerta → incidente → caso)."""
    svc = SocService()
    pipeline = SocPipeline(svc)
    loop = asyncio.new_event_loop()
    flow = loop.run_until_complete(pipeline.run_demo())
    loop.close()
    _print({"soc_demo": True, **asdict(flow)})
    return 0


def cmd_dev(args: argparse.Namespace) -> int:
    """Inicia o ambiente de desenvolvimento (backend + frontend) com um comando."""
    return run_dev(seed=not args.no_seed, open_browser=not args.no_open, lan=args.lan)


def build_parser() -> argparse.ArgumentParser:
    """Constroi o parser de comandos do CLI."""
    parser = argparse.ArgumentParser(prog="edysiem", description="EDY SIEM CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="exibe a versao")
    sub.add_parser("health", help="exibe o estado dos engines")
    sub.add_parser("config", help="exibe a configuracao")
    sub.add_parser("validate-config", help="valida a configuracao")
    sub.add_parser("demo", help="executa a demo da pipeline")
    sub.add_parser("soc-run", help="executa o fluxo SOC E2E (alerta -> incidente -> caso)")

    p_dev = sub.add_parser("dev", help="inicia o ambiente de desenvolvimento (backend + frontend)")
    p_dev.add_argument("--no-seed", action="store_true", help="não popula dados de demonstração")
    p_dev.add_argument(
        "--no-open", action="store_true", help="não abre o navegador automaticamente"
    )
    p_dev.add_argument(
        "--lan",
        action="store_true",
        help="indisponível no EDYSIEM 0.3.0; esta versão é localhost-only",
    )

    p_pipe = sub.add_parser("run-pipeline", help="executa a pipeline ponta a ponta")
    p_pipe.add_argument("--source-type", default="syslog")
    p_pipe.add_argument("--source-host", default="wks-01")
    p_pipe.add_argument("--payload", default=None)

    p_ingest = sub.add_parser("ingest", help="ingere um payload bruto")
    p_ingest.add_argument("--source-type", default="syslog")
    p_ingest.add_argument("--source-host", default="wks-01")
    p_ingest.add_argument("payload")

    return parser


_COMMANDS = {
    "version": cmd_version,
    "health": cmd_health,
    "config": cmd_config,
    "validate-config": cmd_validate_config,
    "run-pipeline": cmd_run_pipeline,
    "ingest": cmd_ingest,
    "demo": cmd_demo,
    "soc-run": cmd_soc_run,
    "dev": cmd_dev,
    "run-dev": cmd_dev,
}


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada do CLI."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse sai com 2 em erro de uso; propaga para o entry point.
        return int(exc.code or 0)
    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return 2
    try:
        return handler(args)
    except Exception as exc:
        _print({"error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
