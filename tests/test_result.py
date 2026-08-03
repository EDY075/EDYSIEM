"""Testes do Result Pattern e ErrorCode."""

from __future__ import annotations

import pytest

from edysiem.result import (
    Error,
    ErrorCode,
    Failure,
    Result,
    ResultUnwrapError,
    Success,
    and_then,
    err,
    from_exc,
    ok,
)


def test_ok_creates_success() -> None:
    result: Result[int] = ok(42)
    assert isinstance(result, Success)
    assert result.is_ok()
    assert result.is_err() is False
    assert result.value == 42
    assert result.unwrap() == 42
    assert result.unwrap_or(-1) == 42
    assert result.expect("não deveria falhar") == 42


def test_success_map_and_chain() -> None:
    result = ok(2).map(lambda x: x * 3)
    assert isinstance(result, Success)
    assert result.unwrap() == 6
    chained = ok(2).and_then(lambda x: ok(x + 1))
    assert chained.unwrap() == 3


def test_success_map_err_is_noop() -> None:
    result = ok(5).map_err(lambda _: Error(ErrorCode.UNKNOWN, "x"))
    assert result.is_ok()
    assert result.unwrap() == 5


def test_failure_created_by_err() -> None:
    error = Error(ErrorCode.NOT_FOUND, "nada aqui")
    result: Result[int] = err(error)
    assert isinstance(result, Failure)
    assert result.is_ok() is False
    assert result.is_err()
    assert result.error is error
    assert result.unwrap_or(0) == 0
    with pytest.raises(ResultUnwrapError):
        result.unwrap()
    with pytest.raises(ResultUnwrapError):
        result.expect("falhou como esperado")


def test_failure_map_is_noop_and_chain_propagates() -> None:
    failure: Result[int] = err(Error(ErrorCode.CONFLICT, "nope"))
    mapped = failure.map(lambda x: x + 1)
    assert mapped.is_err()
    mapped_err = failure.map_err(lambda e: Error(ErrorCode.TIMEOUT, "timeout"))
    assert mapped_err.error.code is ErrorCode.TIMEOUT
    chained = failure.and_then(lambda x: ok(x))
    assert chained.is_err()


def test_and_then_helper() -> None:
    assert and_then(ok(1), lambda x: ok(x + 1)).unwrap() == 2
    assert and_then(err(Error(ErrorCode.UNKNOWN, "e")), lambda x: ok(x)).is_err()


def test_from_exc() -> None:
    result = from_exc(ValueError("boom"), code=ErrorCode.VALIDATION_ERROR)
    assert result.is_err()
    assert result.error.code is ErrorCode.VALIDATION_ERROR
    assert result.error.message == "boom"


def test_error_to_dict() -> None:
    error = Error(ErrorCode.FORBIDDEN, "sem acesso", details={"role": "viewer"})
    data = error.to_dict()
    assert data["code"] == "forbidden"
    assert data["message"] == "sem acesso"
    assert data["details"] == {"role": "viewer"}
    assert "cause" not in data


def test_error_to_dict_with_cause() -> None:
    cause = RuntimeError("base")
    error = Error(ErrorCode.INTERNAL_ERROR, "falha", cause=cause)
    assert error.to_dict()["cause"] == "RuntimeError: base"


def test_repr() -> None:
    assert "Success" in repr(ok(1))
    assert "Failure" in repr(err(Error(ErrorCode.UNKNOWN, "e")))
