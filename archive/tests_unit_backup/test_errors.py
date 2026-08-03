"""Testes da hierarquia de exceções."""

import pytest

from app.core.errors import (
    ConfigurationException,
    DomainException,
    EdySiemError,
    InfrastructureException,
    PluginException,
    SecurityException,
    ValidationException,
)
from app.core.result import ErrorCode


def test_base_error() -> None:
    e = EdySiemError("erro")
    assert e.message == "erro"
    assert e.code == ErrorCode.INTERNAL_ERROR


def test_domain_exception() -> None:
    e = DomainException("regra")
    assert e.code == ErrorCode.CONFLICT


def test_validation_exception() -> None:
    e = ValidationException("campo inválido", details={"field": "x"})
    assert e.code == ErrorCode.VALIDATION_ERROR
    assert e.details == {"field": "x"}


def test_configuration_exception() -> None:
    assert ConfigurationException("cfg").code == ErrorCode.CONFIGURATION_ERROR


def test_infrastructure_exception() -> None:
    assert InfrastructureException("io").code == ErrorCode.INFRASTRUCTURE_ERROR


def test_plugin_exception() -> None:
    assert PluginException("plg").code == ErrorCode.PLUGIN_ERROR


def test_security_exception() -> None:
    assert SecurityException("auth").code == ErrorCode.UNAUTHORIZED


def test_is_exception_instance() -> None:
    assert issubclass(ValidationException, EdySiemError)
    assert issubclass(SecurityException, EdySiemError)


def test_raise_and_catch_base() -> None:
    with pytest.raises(EdySiemError):
        raise DomainException("boom")
