"""Bootstrap do EDY SIEM.

Configuracao, container e ciclo de vida da aplicacao.
"""

from __future__ import annotations

import logging

from .config import SiemConfig, load
from .container import ApplicationContainer
from .logging import configure_logging
from .result import Failure


def load_config() -> SiemConfig:
    """Carrega e valida a configuracao do ambiente."""
    result = load()
    if isinstance(result, Failure):
        raise RuntimeError(f"configuracao invalida: {result.error.message}")
    return result.unwrap()


def build_container(config: SiemConfig | None = None) -> ApplicationContainer:
    """Constroi o container unico da aplicacao."""
    cfg = config or load_config()
    log_cfg = cfg.logging
    configure_logging(
        cfg.project_name,
        level=getattr(logging, str(log_cfg.level).upper(), logging.INFO),
        use_json=log_cfg.json,
    )
    return ApplicationContainer(config=cfg)


def version() -> str:
    """Versao da plataforma."""
    from . import __version__

    return __version__


__all__ = ["ApplicationContainer", "build_container", "load_config", "version"]
