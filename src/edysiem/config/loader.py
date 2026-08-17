"""Loader de configuração orientado a ambiente.

Parte dos defaults, sobrepõe com variáveis de ambiente com prefixo ``EDYSIEM_``
(ex.: ``EDYSIEM_LOG_LEVEL``) e valida o resultado. Retorna sempre um
``Result[SiemConfig]`` — nunca ``None``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import replace
from enum import Enum
from typing import Any, TypeVar

from ..events.base import EventPriority
from ..exceptions import ConfigurationException
from ..result import Failure, Result, ok
from .config import (
    AppConfig,
    Environment,
    EventBusConfig,
    LoggingConfig,
    PluginConfig,
    SecurityConfig,
    SiemConfig,
    StorageConfig,
)

E = TypeVar("E", bound=Enum)


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationException(
            f"variável {name} deve ser inteiro; recebido: {raw!r}",
            cause=exc,
        ) from exc


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_enum(name: str, enum_cls: type[E], default: E) -> E:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise ConfigurationException(
            f"variável {name} inválida; recebido: {raw!r}",
            cause=exc,
        ) from exc


class ConfigLoader:
    """Carrega e valida a configuração do SIEM a partir do ambiente."""

    def __init__(self, prefix: str = "EDYSIEM_") -> None:
        self._prefix = prefix

    def build(self, overrides: Mapping[str, Any] | None = None) -> Result[SiemConfig]:
        """Monta a configuração completa, aplicando ``overrides`` por último.

        Returns:
            ``Success`` com a configuração validada ou ``Failure`` com o erro
            de configuração (nunca ``None``).
        """
        try:
            base = SiemConfig(
                environment=_env_enum(f"{self._prefix}ENV", Environment, Environment.DEVELOPMENT),
                app=AppConfig(
                    host=_env_str(f"{self._prefix}HOST", "127.0.0.1"),
                    port=_env_int(f"{self._prefix}PORT", 8080),
                    name=_env_str(f"{self._prefix}APP_NAME", "edysiem"),
                    debug=_env_bool(f"{self._prefix}DEBUG", False),
                ),
                logging=LoggingConfig(
                    level=_env_str(f"{self._prefix}LOG_LEVEL", "INFO"),
                    json=_env_bool(f"{self._prefix}LOG_JSON", True),
                    path=_env_str(f"{self._prefix}LOG_PATH", "") or None,
                    include_thread=_env_bool(f"{self._prefix}LOG_INCLUDE_THREAD", False),
                ),
                event_bus=EventBusConfig(
                    max_queue=_env_int(f"{self._prefix}EVENT_QUEUE", 10_000),
                    default_priority=_env_enum(
                        f"{self._prefix}EVENT_PRIORITY", EventPriority, EventPriority.NORMAL
                    ),
                ),
                plugin=PluginConfig(
                    directory=_env_str(f"{self._prefix}PLUGIN_DIR", "plugins"),
                    enabled_plugins=tuple(
                        p for p in _env_str(f"{self._prefix}PLUGIN_ENABLED", "").split(",") if p
                    ),
                    autoload=_env_bool(f"{self._prefix}PLUGIN_AUTOLOAD", True),
                ),
                storage=StorageConfig(
                    kind=_env_str(f"{self._prefix}STORAGE_KIND", "memory"),
                ),
                security=SecurityConfig(
                    secret_key_len=_env_int(f"{self._prefix}SECRET_KEY_LEN", 32),
                    token_ttl_seconds=_env_int(f"{self._prefix}TOKEN_TTL_SECONDS", 900),
                    require_2fa=_env_bool(f"{self._prefix}REQUIRE_2FA", False),
                    allowed_origins=tuple(
                        o for o in _env_str(f"{self._prefix}ALLOWED_ORIGINS", "*").split(",") if o
                    ),
                ),
            )
            config = self._apply_overrides(base, overrides or {})
            self._validate(config)
            return ok(config)
        except ConfigurationException as exc:
            return Failure[SiemConfig](exc.to_error())

    def _apply_overrides(self, base: SiemConfig, overrides: Mapping[str, Any]) -> SiemConfig:
        if not overrides:
            return base

        app = base.app
        logging_config = base.logging
        event_bus = base.event_bus
        plugin = base.plugin
        storage = base.storage
        security = base.security
        project_name = base.project_name
        version = base.version
        environment = base.environment

        for key, value in overrides.items():
            if key == "app":
                app = self._replace_subconfig(app, value, "app")
            elif key == "logging":
                logging_config = self._replace_subconfig(logging_config, value, "logging")
            elif key == "event_bus":
                event_bus = self._replace_subconfig(event_bus, value, "event_bus")
            elif key == "plugin":
                plugin = self._replace_subconfig(plugin, value, "plugin")
            elif key == "storage":
                storage = self._replace_subconfig(storage, value, "storage")
            elif key == "security":
                security = self._replace_subconfig(security, value, "security")
            elif key == "project_name":
                project_name = str(value)
            elif key == "version":
                version = str(value)
            elif key == "environment":
                if isinstance(value, str):
                    environment = Environment(value)
                else:
                    environment = value
            else:
                raise ConfigurationException(f"campo de override desconhecido: {key!r}")

        return SiemConfig(
            project_name=project_name,
            version=version,
            environment=environment,
            app=app,
            logging=logging_config,
            event_bus=event_bus,
            plugin=plugin,
            storage=storage,
            security=security,
        )

    @staticmethod
    def _replace_subconfig(target: Any, updates: Mapping[str, Any], name: str) -> Any:  # noqa: ANN401 — fronteira dinâmica (overrides de config)
        """Aplica ``replace`` tipado e converte erro de override em erro de config.

        Se o override contém uma chave desconhecida ou um tipo incompatível,
        ``dataclasses.replace`` levanta ``TypeError``. Para honrar o contrato
        "sempre retorna ``Result``, nunca exceção" do ``build``, o erro é
        normalizado para ``ConfigurationException``.
        """
        try:
            return replace(target, **dict(updates))
        except TypeError as exc:
            raise ConfigurationException(
                f"override inválido para {name}: {exc}", cause=exc
            ) from exc

    @staticmethod
    def _validate(config: SiemConfig) -> None:
        """Valida invariantes numéricos e de enum da configuração."""
        if config.app.host != "127.0.0.1":
            raise ConfigurationException(
                "EDYSIEM 0.3.0 aceita somente o host 127.0.0.1 (localhost-only)"
            )
        if not 1 <= config.app.port <= 65535:
            raise ConfigurationException(f"porta inválida: {config.app.port}; esperado 1..65535")
        if config.event_bus.max_queue <= 0:
            raise ConfigurationException("event_bus.max_queue deve ser > 0")
        if config.security.secret_key_len < 16:
            raise ConfigurationException("security.secret_key_len deve ser >= 16")
        if config.security.token_ttl_seconds <= 0:
            raise ConfigurationException("security.token_ttl_seconds deve ser > 0")
        if config.logging.level not in {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }:
            raise ConfigurationException(f"logging.level inválido: {config.logging.level!r}")


def load(
    prefix: str = "EDYSIEM_", overrides: Mapping[str, Any] | None = None
) -> Result[SiemConfig]:
    """Atalho de topo: constrói um ``ConfigLoader`` e chama ``build``."""
    return ConfigLoader(prefix).build(overrides)


__all__ = ["ConfigLoader", "load"]
