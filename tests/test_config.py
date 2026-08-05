"""Testes do sistema de configuração central."""

from __future__ import annotations

from typing import Any

from edysiem.config import (
    AppConfig,
    ConfigLoader,
    Environment,
    EventBusConfig,
    LoggingConfig,
    PluginConfig,
    SecurityConfig,
    SiemConfig,
    StorageConfig,
    load,
)
from edysiem.events import EventPriority
from edysiem.result import ErrorCode, Failure, Success


def test_load_defaults() -> None:
    result = load()
    assert isinstance(result, Success)
    config = result.value
    assert config.project_name == "EDY SIEM"
    assert config.version == "0.2.0"
    assert config.environment is Environment.DEVELOPMENT
    assert config.app.port == 8080
    assert config.logging.level == "INFO"
    assert config.event_bus.max_queue == 10_000
    assert config.event_bus.default_priority is EventPriority.NORMAL
    assert config.plugin.directory == "plugins"
    assert config.storage.kind == "memory"
    assert config.security.secret_key_len == 32


def test_load_with_overrides() -> None:
    overrides: dict[str, Any] = {
        "environment": "production",
        "version": "9.9.9",
        "app": {"port": 9090, "host": "0.0.0.0"},
        "logging": {"level": "DEBUG", "json": False},
        "event_bus": {"max_queue": 5},
        "security": {"secret_key_len": 64},
    }
    config = load(overrides=overrides).unwrap()
    assert config.environment is Environment.PRODUCTION
    assert config.version == "9.9.9"
    assert config.app.port == 9090
    assert config.app.host == "0.0.0.0"
    assert config.logging.level == "DEBUG"
    assert config.logging.json is False
    assert config.event_bus.max_queue == 5
    assert config.security.secret_key_len == 64


def test_load_unknown_override_fails(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("EDYSIEM_PORT", raising=False)
    result = load(overrides={"nao_existe": 1})
    assert isinstance(result, Failure)
    assert result.error.code is ErrorCode.CONFIGURATION_ERROR


def test_load_invalid_subconfig_key_fails() -> None:
    # Chave desconhecida DENTRO de uma sub-config era um TypeError não capturado
    # (violava o contrato "sempre Result, nunca exceção"). Deve virar Failure.
    result = load(overrides={"app": {"chave_inexistente": 1}})
    assert isinstance(result, Failure)
    assert result.error.code is ErrorCode.CONFIGURATION_ERROR
    assert "override inválido" in result.error.message


def test_load_invalid_port_fails() -> None:
    result = load(overrides={"app": {"port": 70000}})
    assert isinstance(result, Failure)
    assert result.error.code is ErrorCode.CONFIGURATION_ERROR


def test_load_invalid_log_level_fails() -> None:
    result = load(overrides={"logging": {"level": "SILENCIO"}})
    assert isinstance(result, Failure)


def test_load_invalid_secret_key_fails() -> None:
    result = load(overrides={"security": {"secret_key_len": 4}})
    assert isinstance(result, Failure)
    assert "secret_key_len" in result.error.message


def test_loader_from_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EDYSIEM_ENV", "production")
    monkeypatch.setenv("EDYSIEM_PORT", "8443")
    monkeypatch.setenv("EDYSIEM_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("EDYSIEM_DEBUG", "true")
    monkeypatch.setenv("EDYSIEM_EVENT_QUEUE", "42")
    monkeypatch.setenv("EDYSIEM_SECRET_KEY_LEN", "48")
    config = load().unwrap()
    assert config.environment is Environment.PRODUCTION
    assert config.app.port == 8443
    assert config.app.debug is True
    assert config.logging.level == "WARNING"
    assert config.event_bus.max_queue == 42
    assert config.security.secret_key_len == 48


def test_loader_invalid_env_int(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EDYSIEM_PORT", "nao-numero")
    result = load()
    assert isinstance(result, Failure)
    assert result.error.code is ErrorCode.CONFIGURATION_ERROR


def test_loader_invalid_env_enum(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EDYSIEM_ENV", "marte")
    result = load()
    assert isinstance(result, Failure)


def test_loader_plugin_enabled_csv(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EDYSIEM_PLUGIN_ENABLED", "parser,enricher,")
    config = load().unwrap()
    assert config.plugin.enabled_plugins == ("parser", "enricher")


def test_loader_origins_csv(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EDYSIEM_ALLOWED_ORIGINS", "a.com,b.com")
    config = load().unwrap()
    assert config.security.allowed_origins == ("a.com", "b.com")


def test_config_default_factories() -> None:
    config = SiemConfig()
    assert isinstance(config.app, AppConfig)
    assert isinstance(config.logging, LoggingConfig)
    assert isinstance(config.event_bus, EventBusConfig)
    assert isinstance(config.plugin, PluginConfig)
    assert isinstance(config.storage, StorageConfig)
    assert isinstance(config.security, SecurityConfig)


def test_config_loader_instance_and_empty_overrides() -> None:
    loader = ConfigLoader()
    result = loader.build({})
    assert result.is_ok()
