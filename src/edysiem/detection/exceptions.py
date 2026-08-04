"""Excecoes do Detection Framework.

Hierarquia de erros especifica para o processo de deteccao.
"""

from __future__ import annotations

from ..exceptions import EdysiemException


class DetectionError(EdysiemException):
    """Erro base do Detection Framework."""


class DetectionRuleNotFoundError(DetectionError):
    """Regra de deteccao nao encontrada no registry."""

    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Regra de deteccao '{rule_id}' nao encontrada")


class DetectionRuleTimeoutError(DetectionError):
    """Tempo de execucao da regra excedido."""

    def __init__(self, rule_id: str, timeout_seconds: float) -> None:
        self.rule_id = rule_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Regra '{rule_id}' excedeu timeout de {timeout_seconds}s")


class DetectionRuleRegistrationError(DetectionError):
    """Erro ao registrar regra (duplicada, invalida, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DetectionRuleDependencyError(DetectionError):
    """Dependencia de regra nao satisfeita."""

    def __init__(self, rule_id: str, missing_dependency: str) -> None:
        self.rule_id = rule_id
        self.missing_dependency = missing_dependency
        super().__init__(
            f"Regra '{rule_id}' requer dependencia '{missing_dependency}' nao satisfeita"
        )


class DetectionContextError(DetectionError):
    """Erro no contexto de deteccao (estado invalido)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class RuleValidationError(DetectionError):
    """Erro de validacao de regra (schema invalido, metadados ausentes)."""

    def __init__(self, rule_id: str, message: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Regra '{rule_id}' invalida: {message}")


__all__ = [
    "DetectionContextError",
    "DetectionError",
    "DetectionRuleDependencyError",
    "DetectionRuleNotFoundError",
    "DetectionRuleRegistrationError",
    "DetectionRuleTimeoutError",
    "RuleValidationError",
]
