"""Testes do sistema de configuração."""

import pytest

from app.core.config import Environment, LogLevel, Settings, load_settings


def test_defaults_valid() -> None:
    s = Settings()
    s.validate()
    assert s.environment == Environment.DEVELOPMENT
    assert s.port == 8080
    assert s.log_json is True


def test_validate_port() -> None:
    with pytest.raises(ValueError):
        Settings(port=0).validate()


def test_validate_payload() -> None:
    with pytest.raises(ValueError):
        Settings(ingest_max_payload_bytes=0).validate()


def test_validate_queue() -> None:
    with pytest.raises(ValueError):
        Settings(pipeline_queue_size=-1).validate()


def test_validate_workers() -> None:
    with pytest.raises(ValueError):
        Settings(pipeline_worker_count=0).validate()


def test_validate_rate() -> None:
    with pytest.raises(ValueError):
        Settings(api_rate_limit_per_minute=0).validate()


def test_load_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDYSIEM_PORT", "9090")
    monkeypatch.setenv("EDYSIEM_ENV", "testing")
    s = load_settings()
    assert s.port == 9090
    assert s.environment == Environment.TESTING


def test_load_settings_bad_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDYSIEM_PORT", "abc")
    from app.core.config import ConfigurationError

    with pytest.raises(ConfigurationError):
        load_settings()


def test_load_settings_bad_enum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDYSIEM_ENV", "nope")
    from app.core.config import ConfigurationError

    with pytest.raises(ConfigurationError):
        load_settings()


def test_frozen_settings() -> None:
    s = Settings()
    with pytest.raises(Exception):
        s.port = 1111  # type: ignore[misc]
