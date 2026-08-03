"""Gerenciamento de contexto de correlação para logs."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass, field


def _new_uuid() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True, slots=True)
class CorrelationId:
    """Identificador de correlação para rastrear uma operação distribuída."""

    value: str = field(default_factory=_new_uuid)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RequestId:
    """Identificador de um request (ex.: solicitação HTTP/CLI)."""

    value: str = field(default_factory=_new_uuid)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SessionId:
    """Identificador de uma sessão de usuário."""

    value: str = field(default_factory=_new_uuid)

    def __str__(self) -> str:
        return self.value


_ID_NAMES = ("correlation_id", "request_id", "session_id")


class ContextManager:
    """Propaga IDs de contexto através de ``ContextVar``.

    Cada ID é armazenado em uma ``ContextVar`` própria, permitindo herança
    natural entre tarefas assíncronas.
    """

    def __init__(self) -> None:
        self._vars: dict[str, ContextVar[str]] = {
            name: ContextVar(name, default="") for name in _ID_NAMES
        }

    def initialize(self) -> ContextManager:
        """Gera novos IDs para todos os canais de contexto."""
        for _name, var in self._vars.items():
            var.set(_new_uuid())
        return self

    def get(self, name: str) -> str:
        """Retorna o valor atual de um canal de contexto (ou vazio)."""
        if name not in self._vars:
            raise KeyError(f"canal de contexto desconhecido: {name!r}")
        return self._vars[name].get()

    def get_id(self, name: str) -> str:
        return self.get(name)

    def set(self, name: str, value: str) -> ContextManager:
        if name not in self._vars:
            raise KeyError(f"canal de contexto desconhecido: {name!r}")
        self._vars[name].set(value)
        return self

    def new_session(self) -> str:
        """Renova a session id e a retorna."""
        sid = SessionId()
        self._vars["session_id"].set(sid.value)
        return sid.value

    def snapshot(self) -> dict[str, str]:
        """Captura o contexto atual como um mapa imutável."""
        return {name: self._vars[name].get() for name in _ID_NAMES}

    def record(self, extra: Mapping[str, object]) -> dict[str, object]:
        """Mescla ``extra`` com o contexto para gravação no log."""
        merged: dict[str, object] = dict(self.snapshot())
        merged.update(extra)
        return merged


__all__ = [
    "ContextManager",
    "CorrelationId",
    "RequestId",
    "SessionId",
]