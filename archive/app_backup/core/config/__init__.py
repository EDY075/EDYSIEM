"""Sistema central de configuração — env-driven, validado, tipado, com defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Settings:
    """Configuração central carregada por ambiente com defaults e validação."""

    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO
    log_json: bool = True
    db_path: str = "~/.edysiem/edy_siem.db"
    host: str = "127.0.0.1"
    port: int = 8080
    trace_id_header: str = "X-Trace-Id"
    request_id_header: str = "X-Request-Id"
    ingest_max_payload_bytes: int = 1_048_576
    pipeline_queue_size: int = 10_000
    pipeline_worker_count: int = 4
    rule_default_timeframe_s: int = 300
    api_rate_limit_per_minute: int = 600
    extra: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validar invariantes de configuração."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"port inválida: {self.port}")
        if self.ingest_max_payload_bytes <= 0:
            raise ValueError("ingest_max_payload_bytes deve ser > 0")
        if self.pipeline_queue_size <= 0:
            raise ValueError("pipeline_queue_size deve ser > 0")
        if self.pipeline_worker_count < 1:
            raise ValueError("pipeline_worker_count deve ser >= 1")
        if self.api_rate_limit_per_minute < 1:
            raise ValueError("api_rate_limit_per_minute deve ser >= 1")


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ConfigurationError(f"variável {name} deve ser inteiro, recebeu: {raw!r}")


def _env_enum(name: str, enum_cls: type[Enum], default: Enum) -> Enum:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return enum_cls(raw)
    except ValueError:
        raise ConfigurationError(f"variável {name} inválida: {raw!r}")


def load_settings(prefix: str = "EDYSIEM_") -> Settings:
    """Carregar Settings a partir do ambiente com prefixo configurável."""
    settings = Settings(
        environment=_env_enum(f"{prefix}ENV", Environment, Environment.DEVELOPMENT),
        log_level=_env_enum(f"{prefix}LOG_LEVEL", LogLevel, LogLevel.INFO),
        log_json=os.environ.get(f"{prefix}LOG_JSON", "true").lower() in ("1", "true", "yes"),
        db_path=_env_str(f"{prefix}DB_PATH", "~/.edysiem/edy_siem.db"),
        host=_env_str(f"{prefix}HOST", "127.0.0.1"),
        port=_env_int(f"{prefix}PORT", 8080),
        ingest_max_payload_bytes=_env_int(f"{prefix}INGEST_MAX_PAYLOAD_BYTES", 1_048_576),
        pipeline_queue_size=_env_int(f"{prefix}PIPELINE_QUEUE_SIZE", 10_000),
        pipeline_worker_count=_env_int(f"{prefix}PIPELINE_WORKER_COUNT", 4),
        rule_default_timeframe_s=_env_int(f"{prefix}RULE_DEFAULT_TIMEFRAME_S", 300),
        api_rate_limit_per_minute=_env_int(f"{prefix}API_RATE_LIMIT_PER_MINUTE", 600),
    )
    settings.validate()
    return settings


class ConfigurationError(Exception):
    """Erro de configuração ao carregar ambiente."""
