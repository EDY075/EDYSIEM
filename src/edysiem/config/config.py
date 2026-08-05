"""Definições tipadas da configuração central do EDY SIEM.

Modelos imutáveis (``frozen=True``) com defaults seguros. A validação acontece
no ``loader``, retornando sempre um ``Result`` — nunca ``None``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..events.base import EventPriority


class Environment(StrEnum):
    """Ambiente de execução da plataforma."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Configuração da aplicação HTTP/CLI."""

    host: str = "127.0.0.1"
    port: int = 8080
    name: str = "edysiem"
    debug: bool = False


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Configuração do logger estruturado."""

    level: str = "INFO"
    json: bool = True
    path: str | None = None
    include_thread: bool = False


@dataclass(frozen=True, slots=True)
class EventBusConfig:
    """Configuração do barramento de eventos interno."""

    max_queue: int = 10_000
    default_priority: EventPriority = EventPriority.NORMAL


@dataclass(frozen=True, slots=True)
class PluginConfig:
    """Configuração da camada de plugins."""

    directory: str = "plugins"
    enabled_plugins: tuple[str, ...] = ()
    autoload: bool = True


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Configuração da persistência (kind + conexão opaca)."""

    kind: str = "memory"
    connection: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    """Configuração de segurança da plataforma."""

    secret_key_len: int = 32
    token_ttl_seconds: int = 900
    require_2fa: bool = False
    allowed_origins: tuple[str, ...] = ("*",)


@dataclass(frozen=True, slots=True)
class SiemConfig:
    """Configuração raiz que agrega todos os sub-configs."""

    project_name: str = "EDY SIEM"
    version: str = "0.2.0"
    environment: Environment = Environment.DEVELOPMENT
    app: AppConfig = field(default_factory=AppConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    event_bus: EventBusConfig = field(default_factory=EventBusConfig)
    plugin: PluginConfig = field(default_factory=PluginConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)


__all__ = [
    "AppConfig",
    "Environment",
    "EventBusConfig",
    "LoggingConfig",
    "PluginConfig",
    "SecurityConfig",
    "SiemConfig",
    "StorageConfig",
]
