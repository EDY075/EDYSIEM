"""Testes do Result Pattern."""

import pytest

from app.core.errors import DomainException
from app.core.result import ErrorCode, Failure, Result, fail, success


def test_success() -> None:
    r = success(42)
    assert r.ok is True
    assert r.value == 42
    assert r.is_success is True
    assert r.unwrap() == 42


def test_failure() -> None:
    r = Result.fail(ErrorCode.NOT_FOUND, "não achou")
    assert r.ok is False
    assert r.failure is not None
    assert r.failure.code == ErrorCode.NOT_FOUND
    assert r.is_failure is True


def test_fail_helper() -> None:
    r = fail(ErrorCode.CONFLICT, "conflito")
    assert r.is_failure


def test_from_failure() -> None:
    f = Failure(code=ErrorCode.INTERNAL_ERROR, message="boom")
    r = Result.from_failure(f)
    assert r.ok is False
    assert r.failure == f


def test_unwrap_success() -> None:
    assert success("x").unwrap() == "x"


def test_unwrap_failure_raises() -> None:
    r = Result.fail(ErrorCode.VALIDATION_ERROR, "inválido")
    with pytest.raises(AssertionError):
        r.unwrap()


def test_expect_success() -> None:
    assert success([1]).expect("lista") == [1]


def test_map_success() -> None:
    r = success(2).map(lambda x: x * 3)
    assert r.ok and r.value == 6


def test_map_failure_preserves() -> None:
    r = Result.fail(ErrorCode.NOT_FOUND, "x").map(lambda v: v * 2)
    assert r.is_failure


def test_failure_str() -> None:
    assert "not_found" in str(Failure(ErrorCode.NOT_FOUND, "m"))


def test_success_value_none_not_allowed() -> None:
    r = Result.fail(ErrorCode.INTERNAL_ERROR, "sem valor")
    assert r.value is None
    assert r.is_failure


def test_typed_result() -> None:
    r: Result[int] = success(1)
    assert isinstance(r.unwrap(), int)
