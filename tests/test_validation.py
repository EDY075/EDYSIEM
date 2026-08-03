"""Testes dos validadores e do motor de validação."""

from __future__ import annotations

from edysiem.validation import (
    ValidationEngine,
    ValidationResult,
    ValidationRule,
    in_range,
    is_email,
    is_hash,
    is_hostname,
    is_ip,
    is_ipv4,
    is_ipv6,
    is_non_empty,
    is_url,
    validate_uuid,
)


def test_ipv4() -> None:
    assert is_ipv4("192.168.0.1")
    assert not is_ipv4("2001:db8::1")
    assert not is_ipv4("not-an-ip")


def test_ipv6() -> None:
    assert is_ipv6("2001:db8::1")
    assert not is_ipv6("192.168.0.1")


def test_is_ip() -> None:
    assert is_ip("10.0.0.1")
    assert is_ip("::1")
    assert not is_ip("x")


def test_email() -> None:
    assert is_email("user@example.com")
    assert not is_email("user@example")
    assert not is_email("nope")


def test_url() -> None:
    assert is_url("https://edysiem.dev/x")
    assert is_url("http://localhost:8080")
    assert not is_url("localhost:8080")
    assert not is_url("edysiem.dev")


def test_hash() -> None:
    assert is_hash("a" * 64)
    assert not is_hash("xyz")
    assert is_hash("b" * 32, length=32)
    assert not is_hash("c" * 32, length=64)


def test_hostname() -> None:
    assert is_hostname("server-01.corp")
    assert is_hostname("localhost")
    assert not is_hostname("has space")


def test_in_range() -> None:
    assert in_range(5, 1, 10)
    assert in_range(1, 1, 10)
    assert not in_range(11, 1, 10)
    assert not in_range("x", 1, 10)


def test_non_empty() -> None:
    assert is_non_empty("abc")
    assert is_non_empty([1])
    assert not is_non_empty("")
    assert not is_non_empty([])
    assert not is_non_empty(None)


def test_uuid() -> None:
    assert validate_uuid("12345678-1234-5678-1234-567812345678")
    assert not validate_uuid("nope")


def test_engine_validates() -> None:
    engine = ValidationEngine()
    rules = [
        ValidationRule("nonempty", is_non_empty, "deve ser não vazio"),
        ValidationRule("len", lambda v: len(v) >= 3, "deve ter 3+ chars"),
    ]
    result = engine.validate("abc", rules)
    assert isinstance(result, ValidationResult)
    assert result.valid is True
    assert result.is_valid is True
    assert result.errors == []
    assert result.value == "abc"


def test_engine_collects_errors() -> None:
    engine = ValidationEngine()
    rules = [
        ValidationRule("nonempty", is_non_empty, "deve ser não vazio"),
        ValidationRule("len", lambda v: len(v) >= 3, "deve ter 3+ chars"),
    ]
    result = engine.validate("", rules)
    assert result.valid is False
    assert bool(result) is False
    assert len(result.errors) == 2
    assert "deve ser não vazio" in result.errors


def test_engine_normalize() -> None:
    engine = ValidationEngine()
    rules = [ValidationRule("min", lambda v: len(v) >= 5, "muito curto")]
    result = engine.validate("  abc  ", rules, normalize=lambda v: v.strip())
    assert result.valid is False
    assert result.value == "abc"


def test_engine_catches_predicate_errors() -> None:
    engine = ValidationEngine()

    def broken_predicate(_: str) -> bool:
        raise RuntimeError("boom")

    result = engine.validate("x", [ValidationRule("broken", broken_predicate, "falhou")])
    assert result.valid is False
    assert result.errors == ["falhou"]


def test_engine_without_rules() -> None:
    engine = ValidationEngine()
    result = engine.validate("qualquer", [])
    assert result.valid is True
