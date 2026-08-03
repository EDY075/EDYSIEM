"""Hierarquia de exceções de domínio."""

from __future__ import annotations

from typing import Any

from app.core.result import ErrorCode


class EdySiemError(Exception):
    """Exceção base do EDY SIEM."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class DomainException(EdySiemError):
    """Violação de regra de negócio."""

    code = ErrorCode.CONFLICT


class ValidationException(EdySiemError):
    """Entrada inválida."""

    code = ErrorCode.VALIDATION_ERROR


class ConfigurationException(EdySiemError):
    """Configuração inválida ou ausente."""

    code = ErrorCode.CONFIGURATION_ERROR


class InfrastructureException(EdySiemError):
    """Falha de infraestrutura (storage, rede)."""

    code = ErrorCode.INFRASTRUCTURE_ERROR


class PluginException(EdySiemError):
    """Falha de plugin."""

    code = ErrorCode.PLUGIN_ERROR


class SecurityException(EdySiemError):
    """Falha de segurança (auth/autorização)."""

    code = ErrorCode.UNAUTHORIZED
