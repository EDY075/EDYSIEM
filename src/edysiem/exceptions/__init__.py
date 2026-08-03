"""Hierarquia de exceções específicas do EDY SIEM.

Cada exceção carrega um ``error_code`` de classe e é capaz de se converter em
``Error``/``Result`` para integração com o tipo resultado do núcleo.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NoReturn

from ..result.errors import Error, ErrorCode
from ..result.result import Failure, Result


class EdysiemException(Exception):
    """Base das exceções da plataforma."""

    error_code: ErrorCode = ErrorCode.UNKNOWN

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.message: str = message
        self.details: Mapping[str, object] = dict(details) if details else {}
        self.cause: Exception | None = cause
        super().__init__(message)

    def to_error(self) -> Error:
        """Converte a exceção em um ``Error`` estruturado."""
        return Error(
            code=self.error_code,
            message=self.message,
            details=self.details,
            cause=self.cause,
        )

    def to_result(self) -> Result[NoReturn]:
        """Converte a exceção em uma ``Failure`` tipada."""
        return Failure(self.to_error())


class DomainException(EdysiemException):
    """Erro de regra de negócio do domínio."""

    error_code: ErrorCode = ErrorCode.CONFLICT


class ValidationException(EdysiemException):
    """Erro de validação de entrada/estado."""

    error_code: ErrorCode = ErrorCode.VALIDATION_ERROR


class ConfigurationException(EdysiemException):
    """Erro de configuração inválida."""

    error_code: ErrorCode = ErrorCode.CONFIGURATION_ERROR


class InfrastructureException(EdysiemException):
    """Erro de infraestrutura (I/O, rede, storage)."""

    error_code: ErrorCode = ErrorCode.INFRASTRUCTURE_ERROR


class PluginException(EdysiemException):
    """Erro originado em um plugin externo."""

    error_code: ErrorCode = ErrorCode.PLUGIN_ERROR


class SecurityException(EdysiemException):
    """Erro de segurança/autorização."""

    error_code: ErrorCode = ErrorCode.UNAUTHORIZED


__all__ = [
    "ConfigurationException",
    "DomainException",
    "EdysiemException",
    "InfrastructureException",
    "PluginException",
    "SecurityException",
    "ValidationException",
]
