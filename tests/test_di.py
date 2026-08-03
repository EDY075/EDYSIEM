"""Testes do container de injeção de dependência."""

from __future__ import annotations

import pytest

from edysiem.di import (
    CircularDependencyError,
    Container,
    ContainerRegisterError,
    ContainerUnregisterError,
    Lifetime,
    Scope,
    UnregisteredDependencyError,
)


class Greeter:
    def __init__(self, greeting: str = "olá") -> None:
        self.greeting = greeting

    def greet(self, name: str) -> str:
        return f"{self.greeting}, {name}"


class Counter:
    """Objeto com estado para provar ciclos de vida."""

    def __init__(self) -> None:
        self.calls = 0

    def tick(self) -> int:
        self.calls += 1
        return self.calls


def test_transient_creates_new_instance() -> None:
    container = Container()
    container.register(Counter, lambda: Counter(), lifetime=Lifetime.TRANSIENT)
    first = container.resolve(Counter)
    second = container.resolve(Counter)
    assert first is not second
    assert first.tick() == 1
    assert second.tick() == 1


def test_singleton_shares_instance() -> None:
    container = Container()
    container.register(Counter, lambda: Counter(), lifetime=Lifetime.SINGLETON)
    first = container.resolve(Counter)
    second = container.resolve(Counter)
    assert first is second
    assert first.tick() == 1
    assert second.tick() == 2


def test_scoped_cached_within_scope() -> None:
    container = Container()
    container.register(Counter, lambda: Counter(), lifetime=Lifetime.SCOPED)
    scope_a = container.create_scope()
    scope_b = container.create_scope()
    a1 = scope_a.resolve(Counter)
    a2 = scope_a.resolve(Counter)
    b1 = scope_b.resolve(Counter)
    assert a1 is a2
    assert a1 is not b1
    assert a1.tick() == 1
    assert b1.tick() == 1


def test_register_instance() -> None:
    container = Container()
    instance = Greeter("oi")
    container.register_instance(Greeter, instance)
    assert container.resolve(Greeter) is instance


def test_register_duplicate_raises() -> None:
    container = Container()
    container.register(Greeter, lambda: Greeter())
    with pytest.raises(ContainerRegisterError):
        container.register(Greeter, lambda: Greeter())


def test_unregister_and_errors() -> None:
    container = Container()
    with pytest.raises(ContainerUnregisterError):
        container.unregister(Greeter)
    container.register(Greeter, lambda: Greeter())
    container.unregister(Greeter)
    assert not container.is_registered(Greeter)


def test_unregistered_dependency_raises() -> None:
    container = Container()
    with pytest.raises(UnregisteredDependencyError):
        container.resolve(Greeter)


def test_circular_dependency_raises() -> None:
    container = Container()

    class A:
        def __init__(self, b: B) -> None:
            self.b = b

    class B:
        def __init__(self, a: A) -> None:
            self.a = a

    container.register(A, lambda: A(container.resolve(B)))
    container.register(B, lambda: B(container.resolve(A)))
    with pytest.raises(CircularDependencyError):
        container.resolve(A)


def test_scope_context_manager_clears() -> None:
    container = Container()
    container.register(Counter, lambda: Counter(), lifetime=Lifetime.SCOPED)
    with container.create_scope() as scope:
        assert isinstance(scope, Scope)
        first = scope.resolve(Counter)
        assert scope.resolve(Counter) is first
    # O cache do escopo anterior foi limpo.
    scope2 = container.create_scope()
    assert scope2.resolve(Counter) is not first


def test_default_scope_property() -> None:
    container = Container()
    assert isinstance(container.scope, Scope)
    container.register(Counter, lambda: Counter(), lifetime=Lifetime.SINGLETON)
    assert container.scope.resolve(Counter) is container.resolve(Counter)
