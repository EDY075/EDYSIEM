"""Testes da hierarquia de exceções."""

from __future__ import annotations

import pytest

from edysiem.exceptions import (
    ConfigurationException,
    DomainException,
    EdysiemException,
    InfrastructureException,
    PluginException,
    SecurityException,
    ValidationException,
)
from edysiem.result import ErrorCode


@pytest.mark.parametrize(
    ("exception_cls", "expected_code"),
    [
        (DomainException, ErrorCode.CONFLICT),
        (ValidationException, ErrorCode.VALIDATION_ERROR),
        (ConfigurationException, ErrorCode.CONFIGURATION_ERROR),
        (InfrastructureException, ErrorCode.INFRASTRUCTURE_ERROR),
        (PluginException, ErrorCode.PLUGIN_ERROR),
        (SecurityException, ErrorCode.UNAUTHORIZED),
    ],
)
def test_error_code_mapping(
    exception_cls: type[EdysiemException], expected_code: ErrorCode
) -> None:
    exc = exception_cls("mensagem")
    assert exc.error_code is expected_code
    assert exc.message == "mensagem"
    assert exc.details == {}


def test_base_exception_with_details_and_cause() -> None:
    cause = ValueError("origem")
    exc = EdysiemException(
        "falha",
        details={"context": "t"},
        cause=cause,
    )
    assert exc.details == {"context": "t"}
    assert exc.cause is cause
    assert str(exc) == "falha"


def test_to_error() -> None:
    exc = ValidationException("inválido", details={"field": "port"})
    error = exc.to_error()
    assert error.code is ErrorCode.VALIDATION_ERROR
    assert error.message == "inválido"
    assert error.details == {"field": "port"}


def test_to_result() -> None:
    exc = SecurityException("sem permissão")
    result = exc.to_result()
    assert result.is_err()
    assert result.error.message == "sem permissão"
    assert result.error.code is ErrorCode.UNAUTHORIZED


def test_raises() -> None:
    with pytest.raises(EdysiemException):
        raise DomainException("regra quebrada")
