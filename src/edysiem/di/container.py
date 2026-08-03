"""Container de injeção de dependência manual (sem libs externas)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

from .lifetimes import Lifetime

T = TypeVar("T")

Provider = Callable[..., Any]


class ContainerError(Exception):
    """Base dos erros do container."""


class ContainerRegisterError(ContainerError):
    """Erro ao registrar uma dependência."""


class ContainerUnregisterError(ContainerError):
    """Erro ao remover uma dependência."""


class UnregisteredDependencyError(ContainerError):
    """Dependência não registrada solicitada em ``resolve``."""


class CircularDependencyError(ContainerError):
    """Dependência circular detectada durante a resolução."""


class Scope:
    """Escopo de resolução com cache próprio para dependências ``SCOPED``."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._cached: dict[type[object], object] = {}

    def resolve(self, interface: type[T]) -> T:
        return self._container._resolve(interface, self)  # type: ignore[return-value]

    def __enter__(self) -> Scope:
        return self

    def __exit__(self, *exc: object) -> None:
        self._cached.clear()


class Container:
    """Registrador/resolvedor de dependências manual.

    ``transient`` cria nova instância a cada chamada; ``singleton`` compartilha
    uma única instância; ``scoped`` utiliza o cache do escopo atual.
    """

    def __init__(self) -> None:
        self._providers: dict[type[object], Provider] = {}
        self._lifetimes: dict[type[object], Lifetime] = {}
        self._singletons: dict[type[object], object] = {}
        self._resolution_stack: list[type[object]] = []
        self._scope = Scope(self)

    def register(
        self,
        interface: type[object],
        provider: Provider | type[object],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> None:
        if interface in self._providers:
            raise ContainerRegisterError(f"interface já registrada para {interface!r}")
        self._providers[interface] = provider
        self._lifetimes[interface] = lifetime

    def register_instance(self, interface: type[object], instance: object) -> None:
        self.register(interface, lambda: instance, lifetime=Lifetime.SINGLETON)
        self._singletons[interface] = instance

    def unregister(self, interface: type[object]) -> None:
        if interface not in self._providers:
            raise ContainerUnregisterError(f"interface não registrada: {interface!r}")
        del self._providers[interface]
        del self._lifetimes[interface]
        self._singletons.pop(interface, None)

    def is_registered(self, interface: type[object]) -> bool:
        return interface in self._providers

    def create_scope(self) -> Scope:
        return Scope(self)

    @property
    def scope(self) -> Scope:
        return self._scope

    def resolve(self, interface: type[T]) -> T:
        return cast(T, self._resolve(interface, self._scope))

    def _resolve(self, interface: type[object], scope: Scope) -> object:
        if interface not in self._providers:
            raise UnregisteredDependencyError(f"Dependência não registrada: {interface!r}")
        if interface in self._resolution_stack:
            raise CircularDependencyError(f"Ciclo detectado resolvendo {interface!r}")
        lifetime = self._lifetimes.get(interface, Lifetime.TRANSIENT)

        if lifetime is Lifetime.SINGLETON:
            cached = self._singletons.get(interface)
            if cached is not None:
                return cached
            self._resolution_stack.append(interface)
            try:
                instance = self._providers[interface]()
            finally:
                self._resolution_stack.remove(interface)
            self._singletons[interface] = instance
            return instance

        if lifetime is Lifetime.SCOPED:
            cached = scope._cached.get(interface)
            if cached is not None:
                return cached
            self._resolution_stack.append(interface)
            try:
                instance = self._providers[interface]()
            finally:
                self._resolution_stack.remove(interface)
            scope._cached[interface] = instance
            return instance

        self._resolution_stack.append(interface)
        try:
            instance = self._providers[interface]()
        finally:
            self._resolution_stack.remove(interface)
        return instance


__all__ = [
    "CircularDependencyError",
    "Container",
    "ContainerError",
    "ContainerRegisterError",
    "ContainerUnregisterError",
    "Scope",
    "UnregisteredDependencyError",
]