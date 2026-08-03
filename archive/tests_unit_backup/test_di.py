"""Testes do Container DI."""

import pytest

from app.core.di import Container, Lifetime
from app.core.errors import ConfigurationException


def test_register_and_resolve_transient() -> None:
    c = Container()
    c.transient("svc", lambda: {"n": 1})
    assert c.resolve("svc") == {"n": 1}
    assert c.resolve("svc") is not c.resolve("svc")  # transient = nova instância


def test_singleton_same_instance() -> None:
    c = Container()
    c.singleton("svc", lambda: {"n": 1})
    a = c.resolve("svc")
    b = c.resolve("svc")
    assert a is b


def test_scoped_reset_on_scope() -> None:
    c = Container()
    c.scoped("svc", lambda: {"n": 1})
    a = c.resolve("svc")
    c.begin_scope()
    b = c.resolve("svc")
    assert a is not b


def test_resolve_missing() -> None:
    c = Container()
    with pytest.raises(ConfigurationException):
        c.resolve("nao_existe")


def test_has() -> None:
    c = Container()
    c.singleton("a", lambda: 1)
    assert c.has("a")
    assert not c.has("b")


def test_register_generic() -> None:
    c = Container()
    c.register("x", lambda: 5, Lifetime.SINGLETON)
    assert c.resolve("x") == 5
    assert c.resolve("x") == 5


def test_clear() -> None:
    c = Container()
    c.singleton("a", lambda: 1)
    c.clear()
    assert not c.has("a")
