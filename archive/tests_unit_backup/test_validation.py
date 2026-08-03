"""Testes do módulo de validação."""

import pytest

from app.core.errors import ValidationException
from app.core.models import Severity
from app.core.result import ErrorCode
from app.core.validation import (
    try_validate,
    validate_dict_keys,
    validate_enum,
    validate_ipv4,
    validate_not_empty,
    validate_range,
    validate_type,
)


def test_not_empty_ok() -> None:
    assert validate_not_empty("abc", "campo") == "abc"


def test_not_empty_fail() -> None:
    with pytest.raises(ValidationException):
        validate_not_empty("  ", "campo")


def test_type_ok() -> None:
    assert validate_type(5, int, "n") == 5


def test_type_fail() -> None:
    with pytest.raises(ValidationException):
        validate_type("5", int, "n")


def test_ipv4_ok() -> None:
    assert validate_ipv4("10.0.0.5") == "10.0.0.5"


def test_ipv4_bad_format() -> None:
    with pytest.raises(ValidationException):
        validate_ipv4("999.1.1.1")


def test_ipv4_octet() -> None:
    with pytest.raises(ValidationException):
        validate_ipv4("256.1.1.1")


def test_range_ok() -> None:
    assert validate_range(5, 1, 10, "n") == 5


def test_range_fail() -> None:
    with pytest.raises(ValidationException):
        validate_range(11, 1, 10, "n")


def test_dict_keys_missing() -> None:
    with pytest.raises(ValidationException):
        validate_dict_keys({"a": 1}, ["a", "b"])


def test_dict_keys_ok() -> None:
    assert validate_dict_keys({"a": 1, "b": 2}, ["a", "b"]) == {"a": 1, "b": 2}


def test_enum_ok() -> None:
    assert validate_enum("high", Severity, "sev") == Severity.HIGH


def test_enum_fail() -> None:
    with pytest.raises(ValidationException):
        validate_enum("nope", Severity, "sev")


def test_try_validate_success() -> None:
    r = try_validate(lambda: validate_not_empty("x", "f"))
    assert r.is_success and r.unwrap() == "x"


def test_try_validate_failure() -> None:
    r = try_validate(lambda: validate_ipv4("bad"))
    assert r.is_failure
    assert r.failure is not None
    assert r.failure.code == ErrorCode.VALIDATION_ERROR
