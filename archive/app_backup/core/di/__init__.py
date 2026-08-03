"""Container de Dependency Injection — registrar, resolver, singleton/scoped/transient."""

from __future__ import annotations

import threading
from enum import Enum
from typing import Any, Callable, TypeVar

from app.core.errors import ConfigurationException

T = TypeVar("T")

Factory = Callable[[], Any]


class Lifetime(str, Enum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class _Registration:
    def __init__(self, factory: Factory, lifetime: Lifetime) -> None:
        self.factory = factory
        self.lifetime = lifetime
        self.singleton_instance: Any | None = None


class Container:
    """Contêiner de injeção de dependência (leve, sem deps externas)."""

    def __init__(self) -> None:
        self._registrations: dict[str, _Registration] = {}
        self._scoped: dict[str, Any] = {}
        self._lock = threading.Lock()

    def register(self, key: str, factory: Factory, lifetime: Lifetime = Lifetime.TRANSIENT) -> None:
        with self._lock:
            self._registrations[key] = _Registration(factory, lifetime)

    def singleton(self, key: str, factory: Factory) -> None:
        self.register(key, factory, Lifetime.SINGLETON)

    def scoped(self, key: str, factory: Factory) -> None:
        self.register(key, factory, Lifetime.SCOPED)

    def transient(self, key: str, factory: Factory) -> None:
        self.register(key, factory, Lifetime.TRANSIENT)

    def resolve(self, key: str) -> Any:
        reg = self._registrations.get(key)
        if reg is None:
            raise ConfigurationException(f"serviço não registrado: {key}")
        with self._lock:
            if reg.lifetime == Lifetime.SINGLETON:
                if reg.singleton_instance is None:
                    reg.singleton_instance = reg.factory()
                return reg.singleton_instance
            if reg.lifetime == Lifetime.SCOPED:
                if key not in self._scoped:
                    self._scoped[key] = reg.factory()
                return self._scoped[key]
            return reg.factory()

    def resolve_typed(self, key: str) -> T:
        return self.resolve(key)  # type: ignore[no-any-return]

    def has(self, key: str) -> bool:
        return key in self._registrations

    def begin_scope(self) -> None:
        """Iniciar novo escopo (limpa instâncias scoped)."""
        self._scoped.clear()

    def clear(self) -> None:
        with self._lock:
            self._registrations.clear()
            self._scoped.clear()
